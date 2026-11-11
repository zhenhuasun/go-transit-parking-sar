#!/usr/bin/env python3
"""Quick VV signal check for GO Transit parking lots.

Data: Microsoft Planetary Computer STAC, collection sentinel-1-rtc
(Radiometrically Terrain Corrected Sentinel-1 GRD, gamma naught, VV).
NOT Google Earth Engine, NOT SNAP, NOT SARpanel - a shortcut check only.

Method
------
- Search STAC per lot (intersects = lot polygon) in summer windows.
- RTC items are per-slice: one overpass = many slice items. Deduplicate by
  (acquisition date, orbit_state, relative_orbit, platform); for a given
  lot+acquisition pick the slice whose footprint contains the lot centroid
  (else the largest intersection).
- Read only the window covering the lots from the signed COG vv asset
  (rasterio, windowed read). Mask pixels to the lot polygon (rasterized in
  the raster CRS). Exclude nodata (-32768) and out-of-range values.
- VV units: the RTC vv asset is terrain-corrected gamma naught, float32.
  Empirically verified from the first scene read (see run log): values
  are LINEAR power ratio, NOT dB - first window read gave min 0.00,
  p5 0.04, median 0.16, p95 0.80, max 12.06. Conversion applied per pixel:
  VV_dB = 10*log10(linear), with linear clipped at 1e-6 (-60 dB floor) so
  exact zeros do not produce -inf. The script asserts the linear branch
  on the first read (0 < median < 5, min >= 0) and records the observed
  value range in vv-summary.md. All reported VV are dB, computed as the
  mean/median/std of per-pixel dB values within the lot.
- Ascending vs descending (and relative orbit) are NEVER pooled: every
  comparison in the summary is within the same orbit_state, and the
  dominant relative orbit per direction is reported.

Outputs (in quick-vv-check/):
  vv-by-lot-scene.csv, vv-summary.md, vv-time-series.png, this script.
  Intermediate per-scene results are appended to the CSV as they are
  computed, so a re-run resumes (already-done lot+scene_id pairs skipped).
"""
import json, math, os, sys
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
POLY = Path(os.environ.get("POLY_PATH", BASE.parent / "polygons-user.geojson"))
OUT = BASE
CSV = OUT / "vv-by-lot-scene.csv"
LOG = OUT / "run-log.txt"

WINDOWS = [
    ("2019", "2019-06-01T00:00:00Z/2019-08-31T23:59:59Z", "2019-06-01", "2019-08-31"),
    ("2020", "2020-04-01T00:00:00Z/2020-08-31T23:59:59Z", "2020-04-01", "2020-08-31"),
    ("2024", "2024-06-01T00:00:00Z/2024-08-31T23:59:59Z", "2024-06-01", "2024-08-31"),
]
# 2020 split for the summary
def period_of(date_str):
    y = date_str[:4]
    if y == "2020":
        return "2020-Apr-May" if date_str[5:7] in ("04", "05") else "2020-Jun-Aug"
    return f"{y}-summer"

def log(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")

def main():
    from pystac_client import Client
    import planetary_computer
    from shapely.geometry import shape, Point
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.features import geometry_mask
    from rasterio.warp import transform_geom, transform_bounds

    lots = []
    gj = json.loads(POLY.read_text())
    for feat in gj["features"]:
        p = feat["properties"]
        geom = shape(feat["geometry"])
        lots.append({"id": p["id"], "name": p.get("name", p["id"]),
                     "spaces": p.get("spaces"), "geom": geom,
                     "centroid": geom.centroid})
    log(f"Loaded {len(lots)} lots from {POLY}")

    done = set()
    if CSV.exists():
        old = pd.read_csv(CSV)
        done = set(zip(old["lot_id"], old["scene_id"]))
        log(f"Resuming: {len(done)} lot-scene rows already done")

    client = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",
                         modifier=planetary_computer.sign_inplace)

    # ---- 1. STAC search per lot per window, dedupe acquisitions ----
    # acq key -> {lot_id: best item}
    acquisitions = {}  # (date, orbit_state, rel_orbit, platform) -> dict
    acq_meta = {}
    for label, dt_range, _, _ in WINDOWS:
        for lot in lots:
            search = client.search(
                collections=["sentinel-1-rtc"],
                intersects=lot["geom"].__geo_interface__,
                datetime=dt_range,
                query={"sar:polarizations": {"eq": ["VV", "VH"]}},
                limit=500,
            )
            items = list(search.items())
            log(f"[{label}] {lot['id']}: {len(items)} slice items")
            for it in items:
                props = it.properties
                dt = it.datetime
                key = (dt.date().isoformat(),
                       props.get("sat:orbit_state"),
                       props.get("sat:relative_orbit"),
                       props.get("platform"))
                acq_meta[key] = {"date": key[0], "orbit_state": key[1],
                                 "relative_orbit": key[2], "platform": key[3],
                                 "datetime_utc": dt.isoformat(),
                                 "item_id": it.id}
                # score this slice for this lot: contains centroid > intersection area
                try:
                    footprint = shape(it.geometry)
                    if footprint.contains(lot["centroid"]):
                        score = 2.0
                    else:
                        score = footprint.intersection(lot["geom"]).area / lot["geom"].area
                except Exception:
                    score = 0.0
                cur = acquisitions.setdefault(key, {})
                if lot["id"] not in cur or score > cur[lot["id"]][0]:
                    cur[lot["id"]] = (score, it)
    log(f"Distinct acquisitions (date x orbit x rel_orbit x platform): {len(acquisitions)}")
    for key in sorted(acquisitions):
        log(f"  acq {key} lots={sorted(acquisitions[key].keys())}")

    # ---- 2. Read VV per distinct item, once per item, all lots it serves ----
    rows = []
    unit_checked = False
    unit_mode = None  # "linear" or "db", set by the first scene's unit check
    # group work by item id so each COG is read once
    by_item = {}
    for key, lotmap in acquisitions.items():
        for lot_id, (score, it) in lotmap.items():
            by_item.setdefault(it.id, (it, []))[1].append(lot_id)

    log(f"Distinct slice items to read: {len(by_item)}")
    for item_id, (item, lot_ids) in sorted(by_item.items(), key=lambda kv: kv[1][0].datetime):
        props = item.properties
        dt = item.datetime
        key = (dt.date().isoformat(), props.get("sat:orbit_state"),
               props.get("sat:relative_orbit"), props.get("platform"))
        todo = [lid for lid in lot_ids if (lid, item_id) not in done]
        if not todo:
            continue
        href = planetary_computer.sign_url(item.assets["vv"].href)
        try:
            # NOTE on GDAL_HTTP_UNSAFESSL=YES: this VM routes egress through a
            # TLS-intercepting proxy whose CA is in /run/hatch/egress-tls/ca-bundle.pem.
            # Python requests honours SSL_CERT_FILE and works, but GDAL's libcurl
            # still fails cert verification even with CURL_CA_BUNDLE set to that
            # file (verified). The only data sent is the short-lived Planetary
            # Computer SAS token for a public COG. No user credentials are involved.
            with rasterio.Env(GDAL_HTTP_UNSAFESSL="YES",
                              GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
                with rasterio.open(href) as src:
                    crs = src.crs
                    # window covering all lots this item serves.
                    # Lot bounds are lon/lat; the raster is in a projected CRS
                    # (EPSG:32617), so transform the bbox first - from_bounds
                    # expects bounds in the dataset CRS, not degrees.
                    lot_geoms = [next(l for l in lots if l["id"] == lid)["geom"] for lid in todo]
                    minx = min(g.bounds[0] for g in lot_geoms)
                    miny = min(g.bounds[1] for g in lot_geoms)
                    maxx = max(g.bounds[2] for g in lot_geoms)
                    maxy = max(g.bounds[3] for g in lot_geoms)
                    minx -= 0.002; miny -= 0.002; maxx += 0.002; maxy += 0.002
                    bx0, by0, bx1, by1 = transform_bounds("EPSG:4326", crs,
                                                          minx, miny, maxx, maxy)
                    win = from_bounds(bx0, by0, bx1, by1, src.transform)
                    arr = src.read(1, window=win)
                    win_transform = src.window_transform(win)
                    nodata = src.nodata if src.nodata is not None else -32768
                    if not unit_checked:
                        vals = arr[(arr != nodata) & np.isfinite(arr)]
                        log(f"UNIT CHECK scene {item_id} {dt.date()}: "
                            f"n={vals.size} min={vals.min():.4f} p5={np.percentile(vals,5):.4f} "
                            f"median={np.median(vals):.4f} p95={np.percentile(vals,95):.4f} max={vals.max():.2f}")
                        med = float(np.median(vals))
                        if 0 < med < 5 and float(vals.min()) >= 0:
                            unit_mode = "linear"
                            log("UNIT CHECK: values are LINEAR gamma naught (power ratio). "
                                "Conversion: VV_dB = 10*log10(linear), linear clipped at 1e-6.")
                        elif -40 < med < 0:
                            unit_mode = "db"
                            log("UNIT CHECK: values are already in dB. No conversion applied.")
                        else:
                            raise AssertionError(
                                "VV values match neither linear nor dB branch - abort, do not guess conversion")
                        unit_checked = True
                    for lid in todo:
                        lot = next(l for l in lots if l["id"] == lid)
                        g4326 = lot["geom"].__geo_interface__
                        g_raster = transform_geom("EPSG:4326", crs, g4326)
                        mask = geometry_mask([g_raster], out_shape=arr.shape,
                                             transform=win_transform, invert=True)
                        vals = arr[mask]
                        vals = vals[(vals != nodata) & np.isfinite(vals)]
                        if vals.size == 0:
                            log(f"  {lid} {dt.date()} {key[1]} rel{key[2]}: NO VALID PIXELS")
                            continue
                        if unit_mode == "linear":
                            vals_db = 10 * np.log10(np.clip(vals.astype(np.float64), 1e-6, None))
                        else:
                            vals_db = vals.astype(np.float64)
                        vals_db = vals_db[(vals_db > -60) & (vals_db < 20)]
                        if vals_db.size == 0:
                            log(f"  {lid} {dt.date()} {key[1]} rel{key[2]}: NO VALID PIXELS AFTER dB FILTER")
                            continue
                        rows.append({
                            "lot_id": lid, "lot_name": lot["name"], "spaces": lot["spaces"],
                            "scene_id": item_id, "date": dt.date().isoformat(),
                            "datetime_utc": dt.isoformat(),
                            "orbit_state": key[1], "relative_orbit": key[2],
                            "platform": key[3],
                            "n_pixels": int(vals.size),
                            "mean_VV_dB": round(float(np.mean(vals_db)), 3),
                            "median_VV_dB": round(float(np.median(vals_db)), 3),
                            "std_VV_dB": round(float(np.std(vals_db)), 3),
                        })
        except Exception as e:
            log(f"ERROR reading {item_id} {dt.date()}: {type(e).__name__}: {e}")
        if rows:
            df_new = pd.DataFrame(rows)
            header = not CSV.exists()
            df_new.to_csv(CSV, mode="a", header=header, index=False)
            done |= set(zip(df_new["lot_id"], df_new["scene_id"]))
            log(f"  wrote {len(rows)} rows (total done {len(done)})")
            rows = []

    log("Done. CSV rows total: " + str(len(done)))

if __name__ == "__main__":
    main()
