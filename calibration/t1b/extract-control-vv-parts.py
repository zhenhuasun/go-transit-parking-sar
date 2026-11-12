#!/usr/bin/env python3
"""T1b round-4 per-roof DIAGNOSTIC extraction (not part of the decision).

Reads per-scene mean VV for each of the 3 Bronte roofs separately
(control-areas-v4-parts.geojson), for exactly the 114 summer scenes
used by T1 (scene_ids from
quick-vv-check-2018-2026/vv-by-lot-scene-2018-2026.csv).

Same collection and VV processing as extract-control-vv.py. Output:
t1b_control_vv_r4_parts.csv — one row per roof per scene. Used only by
t1b_per_roof_diagnostic.py to check that no single roof carries a
weekend effect hidden inside the pooled control.

Same collection (sentinel-1-rtc) and same VV processing as
quick-vv-check-2018-2026.py: per-pixel VV_dB = 10*log10(linear), linear
clipped at 1e-6; per-scene mean is the mean of per-pixel dB values;
nodata / out-of-range excluded; unit check on the first scene asserts
the linear branch and aborts otherwise.

Output: calibration/t1b/t1b_control_vv.csv. Rows are appended as computed,
so a re-run resumes (already-done control+scene pairs skipped).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[1]
CTRL = BASE / "control-areas-v4-parts.geojson"
LOT_CSV = REPO / "quick-vv-check-2018-2026" / "vv-by-lot-scene-2018-2026.csv"
OUT_CSV = BASE / "t1b_control_vv_r4_parts.csv"
LOG = BASE / "extract-log-r4-parts.txt"


def log(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def main():
    from pystac_client import Client
    import planetary_computer
    from shapely.geometry import shape
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.features import geometry_mask
    from rasterio.warp import transform_geom, transform_bounds

    controls = []
    gj = json.loads(CTRL.read_text())
    for feat in gj["features"]:
        p = feat["properties"]
        controls.append({"id": p.get("id"), "name": p.get("name", p.get("id")),
                         "geom": shape(feat["geometry"])})
    # station from control name prefix ("Oakville GO — Control" -> "oakville")
    for c in controls:
        c["station"] = c["name"].split(" ")[0].lower()
    log(f"Loaded {len(controls)} control areas from {CTRL}")

    lot = pd.read_csv(LOT_CSV)
    scenes = (lot[["scene_id", "date", "datetime_utc", "orbit_state",
                   "relative_orbit", "platform"]]
              .drop_duplicates("scene_id").sort_values("datetime_utc"))
    log(f"T1 scenes to extract: {len(scenes)}")

    done = set()
    if OUT_CSV.exists():
        old = pd.read_csv(OUT_CSV)
        done = set(zip(old["control_id"], old["scene_id"]))
        log(f"Resuming: {len(done)} control-scene rows already done")

    client = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",
                         modifier=planetary_computer.sign_inplace)
    search = client.search(collections=["sentinel-1-rtc"],
                           ids=list(scenes["scene_id"]), limit=500)
    items = {it.id: it for it in search.items()}
    log(f"STAC returned {len(items)} of {len(scenes)} scene ids")
    missing = sorted(set(scenes["scene_id"]) - set(items))
    for m in missing:
        log(f"MISSING from STAC: {m}")

    rows = []
    unit_checked = False
    unit_mode = None
    for _, s in scenes.iterrows():
        item_id = s["scene_id"]
        if item_id not in items:
            continue
        todo = [c for c in controls if (c["id"], item_id) not in done]
        if not todo:
            continue
        item = items[item_id]
        props = item.properties
        dt = item.datetime
        href = planetary_computer.sign_url(item.assets["vv"].href)
        try:
            with rasterio.Env(GDAL_HTTP_UNSAFESSL="YES",
                              GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
                with rasterio.open(href) as src:
                    crs = src.crs
                    geoms = [c["geom"] for c in todo]
                    minx = min(g.bounds[0] for g in geoms)
                    miny = min(g.bounds[1] for g in geoms)
                    maxx = max(g.bounds[2] for g in geoms)
                    maxy = max(g.bounds[3] for g in geoms)
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
                            f"n={vals.size} min={vals.min():.4f} "
                            f"p5={np.percentile(vals, 5):.4f} "
                            f"median={np.median(vals):.4f} "
                            f"p95={np.percentile(vals, 95):.4f} max={vals.max():.2f}")
                        med = float(np.median(vals))
                        if 0 < med < 5 and float(vals.min()) >= 0:
                            unit_mode = "linear"
                            log("UNIT CHECK: values are LINEAR gamma naught. "
                                "Conversion: VV_dB = 10*log10(linear), clipped at 1e-6.")
                        elif -40 < med < 0:
                            unit_mode = "db"
                            log("UNIT CHECK: values are already in dB. No conversion applied.")
                        else:
                            raise AssertionError(
                                "VV values match neither linear nor dB branch - abort")
                        unit_checked = True
                    for c in todo:
                        g_raster = transform_geom("EPSG:4326", crs,
                                                  c["geom"].__geo_interface__)
                        mask = geometry_mask([g_raster], out_shape=arr.shape,
                                             transform=win_transform, invert=True)
                        vals = arr[mask]
                        vals = vals[(vals != nodata) & np.isfinite(vals)]
                        if vals.size == 0:
                            log(f"  {c['id']} {dt.date()}: NO VALID PIXELS")
                            continue
                        if unit_mode == "linear":
                            vals_db = 10 * np.log10(np.clip(vals.astype(np.float64), 1e-6, None))
                        else:
                            vals_db = vals.astype(np.float64)
                        vals_db = vals_db[(vals_db > -60) & (vals_db < 20)]
                        if vals_db.size == 0:
                            log(f"  {c['id']} {dt.date()}: NO VALID PIXELS AFTER dB FILTER")
                            continue
                        rows.append({
                            "control_id": c["id"], "control_name": c["name"],
                            "station": c["station"], "scene_id": item_id,
                            "date": dt.date().isoformat(),
                            "datetime_utc": dt.isoformat(),
                            "orbit_state": s["orbit_state"],
                            "relative_orbit": int(s["relative_orbit"]),
                            "platform": s["platform"],
                            "n_pixels": int(vals.size),
                            "mean_VV_dB": round(float(np.mean(vals_db)), 3),
                            "median_VV_dB": round(float(np.median(vals_db)), 3),
                            "std_VV_dB": round(float(np.std(vals_db)), 3),
                        })
        except Exception as e:
            log(f"ERROR reading {item_id} {dt.date()}: {type(e).__name__}: {e}")
        if rows:
            df_new = pd.DataFrame(rows)
            header = not OUT_CSV.exists()
            df_new.to_csv(OUT_CSV, mode="a", header=header, index=False)
            done |= set(zip(df_new["control_id"], df_new["scene_id"]))
            log(f"  wrote {len(rows)} rows (total done {len(done)})")
            rows = []

    log("Done. CSV rows total: " + str(len(done)))


if __name__ == "__main__":
    main()
