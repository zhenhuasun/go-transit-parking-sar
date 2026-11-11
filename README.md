# GO Transit Parking Occupancy via Sentinel-1 SAR

**Status: preliminary proof of concept — November 2026.** Not a formal
delivery, not calibrated, and not an occupancy percentage. See
[Limits](#limits) before quoting any number from this repo.

GO Transit publishes parking **capacity** for its stations, but no
**occupancy**, no historical record, and no sensors in its outdoor lots.
This project reconstructs that missing history from space for 2018–2026
using Sentinel-1 synthetic aperture radar (SAR): smooth asphalt is
radar-dark (it reflects the radar pulse away), while cars are metal and
form ground–vehicle double-bounce / corner reflectors, so a full lot is
brighter. A lot's mean VV backscatter over successive passes is a
long-term parking-demand proxy.

## 中文摘要

GO 只公布停车场容量，不公布占用率，也没有历史记录，露天停车场里没有
传感器。本项目用 Sentinel-1 雷达 VV 后向散射重建 2018–2026 年 GO 火车站
停车场的使用趋势：车多则亮，车少则暗。试点为 Oakville、Clarkson、
Bronte 三站 6 个露天 lot，polygon 由作者在卫星图上手绘；全网清点覆盖
71 个火车站、69,338 个车位。结果：2020–2021 年需求崩塌（恢复指数
61–84，2019 年 = 100），2023–2024 年恢复到 2019 年水平，2025–2026 年
持平。**这不是占用率百分比**：雷达测的是夏天约 19:10 的晚间残余量，
且未经地面真值标定；业务价值在于停车指数与 PRESTO 客流的**分叉**，
而不是重讲客流恢复的故事。

## Results in brief

Pilot: Oakville, Clarkson, Bronte — 6 outdoor lots, summers June–August
2018–2026, 114 acquisitions, Microsoft Planetary Computer Sentinel-1
RTC (gamma0, VV), ascending only (~19:08–19:16 EDT).

| Lot | Spaces | 2019 mean VV (dB) | 2020 | 2021 | 2026 | Recovery index 2026 (2019 = 100) |
|---|---|---|---|---|---|---|
| Oakville Main | 2,712 | −10.19 | −11.75 | −11.57 | −10.10 | 102 |
| Oakville South | 291 | −9.42 | −10.19 | −10.66 | −8.37 ⚠ | 127 ⚠ |
| Clarkson Main | 1,274 | −11.62 | −13.14 | −13.01 | −11.62 | 100 |
| Clarkson North | 627 | −9.68 | −11.68 | −11.79 | −9.35 | 108 |
| Bronte Main | 1,824 | −10.71 | −11.82 | −11.88 | −10.73 | 100 |
| Bronte South | 1,149 | −10.51 | −11.48 | −11.31 | −10.75 | 95 |

Story: flat 2018–2019, collapsed 2020–2021 (index 61–84), half back in
2022 (80–88), fully back 2023–2024, flat at ~2019 levels through
2025–2026 in 5 of 6 lots.

⚠ **Oakville South 2026 is excluded from any demand reading.** GO
construction started April 2026 with a south-side laydown/compound; the
lot was mostly closed in summer 2026, yet it is *brighter*, not darker —
construction trailers, equipment and containers reflect radar far more
strongly than cars. A Sep–Nov 2026 check (10 scenes) found it still
bright (−8.35 dB vs −9.42 in 2019), so it had not returned to normal by
2 Nov 2026. Oakville Main shows no detectable step from the Aug/Sep 2026
north-lot work (~100 of 2,712 spots closed), as expected — that series
stays usable, annotated. See
`quick-vv-check-2018-2026/vv-addendum-sep-nov-2026.md`.

Network inventory (2026-11-08, GO official station pages + OSM
cross-check): **71 rail stations, 57 with free parking, 14 with none;
69,338 spaces = 57,606 outdoor (83.1%) + 11,732 garage (16.9%)**, across
96 lots. Bloomington and Centennial are 100% garage — VV cannot measure
them. See `network-inventory/`.

## Repository layout

```
.
├── README.md
├── LICENSE                     # MIT
├── requirements.txt
├── lots-inventory.md           # Pilot 3-station lot inventory (GO official)
├── polygons/
│   ├── polygons-user.geojson   # Final AOI: 6 user-drawn lots (Clarkson North
│   │                           #   corrected to 627 spaces, 2026-11-08)
│   ├── polygons-draft.geojson  # Superseded first draft, kept for provenance
│   ├── validation-user-polygons.md
│   ├── polygons-edit.html      # Editable satellite map (Leaflet + Leaflet Draw)
│   └── polygons-final-review.html
├── sarpanel/                   # SARpanel configs (formal chain, not yet run)
│   ├── sarpanel-go-parking-2018-2026.yaml
│   └── sarpanel-go-parking-trial-2019-summer.yaml
├── quick-vv-check/             # First signal check: 3 summers, 52 scenes, 312 rows
│   ├── quick-vv-check.py / analyse-vv.py
│   ├── vv-by-lot-scene.csv / vv-summary.md / vv-time-series.png
│   └── run-log.txt
├── quick-vv-check-2018-2026/  # Expanded run: 9 summers, 114 scenes, 684 rows
│   ├── quick-vv-check-2018-2026.py / analyse-vv-2018-2026.py
│   ├── quick-vv-check-sep-nov-2026.py / make-per-scene-charts.py
│   ├── vv-by-lot-scene-2018-2026.csv / vv-annual-summary-2018-2026.csv
│   ├── vv-by-lot-scene-sep-nov-2026.csv   # Autumn check, 10 scenes, 60 rows
│   ├── vv-summary-2018-2026.md / vv-addendum-sep-nov-2026.md
│   ├── vv-time-series-2018-2026.png
│   └── vv-per-scene-*.png     # Per-scene line charts: 6 lots + 3 stations
└── network-inventory/
    ├── network-inventory.md / stations.csv (71) / lots.csv (107 rows)
    ├── inventory.py            # Reproduces stations.csv and lots.csv
    └── scripts/                # Intermediate scrape / parse / merge scripts
├── docs/
│   └── session-prompt-zh.md    # Portable Chinese project prompt (2026-11-10)
```

Folder names such as `quick-vv-check-2018-2026` are kept as originally
created, because the markdown summaries inside them cross-reference those
paths.

## Method

- **Polygons:** every outdoor lot is a separate polygon; indoor garages
  are excluded entirely (SAR cannot see inside), so VV measures
  outdoor-only demand, not total station demand. Polygons were drawn by
  hand on satellite imagery, validated closed, with no self-intersections
  and no overlaps. They include internal circulation aisles — a stall
  alone is ~12.5 m², plus aisle share the standard is ~25–30 m²/space,
  matching the 27–32 m²/space of 5 of the 6 lots. Internal asphalt is
  constant, so it dilutes measured change: observed drops are a
  conservative lower bound. **Clarkson North is the exception at
  52.3 m²/space — its boundary must be verified before any
  space-weighting or station totals.**
- **Quick check (preliminary chain):** Microsoft Planetary Computer STAC,
  collection `sentinel-1-rtc`, VV gamma0 in linear power, per-pixel
  `VV_dB = 10·log10(linear)`, clipped at 1e-6; ascending only; windowed
  COG reads; deduplicated by (date, orbit state, relative orbit,
  platform). Summers June–August only, to avoid snow/ice. All scenes are
  ascending, relative orbits 4 and 77, ~19:08–19:16 EDT.
- **Recovery index:** `100 × 10^((mean_year − mean_2019)/10)`, computed
  from linear power, 2019 = 100. It is a relative index, not a percentage
  of anything.
- **Autumn check:** Sep–Nov 2026 scenes are a separate file and are
  **not** part of the summer recovery index (different season, ~18:10
  EST, colder/wetter surface).
- **Formal chain (not yet run):** SARpanel
  ([ryjayne89/sarpanel](https://github.com/ryjayne89/sarpanel), pin/fork
  commit `a1c17c1`, last push 2026-11-04) — ASF Level-1 GRD processed
  through ESA SNAP/pyroSAR to sigma0, pixel-level Parquet, all seasons.
  SARpanel sigma0 and Planetary Computer RTC gamma0 are different
  products: **never merge their absolute dB values into one series**;
  only within-chain relative changes are comparable.

## Limits

1. **Evening residual, not peak occupancy.** Sentinel-1 land imaging
   over Oakville is ascending-only: ~19:10 in summer, ~18:10 in winter.
   What is measured is the evening residual at the tail of the return
   peak. Summer and winter snapshots cannot be compared directly, and
   only same-season comparisons are valid.
2. **Relative only, no calibration.** dB is a logarithmic relative index
   (1 dB ≈ 26% change in backscatter power). A 1.56 dB fall is a ~30%
   fall in backscatter power, **not** a 30% fall in cars, because cars are
   only part of the total return (asphalt background remains). No
   occupancy percentage can be quoted without ground-truth calibration
   (optical car counts or field counts at ~19:10).
3. **Outdoor only.** Garages are invisible to SAR. When bad weather
   pushes drivers into a garage, outdoor VV falls while total station
   demand may not have.
4. **Construction and lot changes contaminate the signal.** Any lot with
   construction, closure, expansion or resurfacing in 2018–2026 must be
   annotated on the time axis. Oakville South 2026 is the first confirmed
   case. Bronte South grew from ~175 spaces (2011) to ~375 (2016), before
   this series starts.
5. **Small lots are noisy.** Oakville South has only 82 pixels (SD
   ~1.4 dB); 18 network lots under 200 spaces should be aggregated to
   station level.
6. **2022 is thinnest** (8 scenes) after Sentinel-1B failed in Dec 2021;
   Sentinel-1D appears in 2026 with no systematic offset found in the
   large lots (≤0.31 dB).

## The business question

A recovery index alone merely retells the ridership-recovery story with
another dataset. The unique insight lives only in **divergence from
PRESTO**: parking = drive-access demand, PRESTO = total demand.
Ridership back but parking not → access-mode shift (feeder bus / bike /
drop-off), don't expand the lot; parking back but ridership not →
different user mix; neither back → demand itself hasn't returned. Land /
capital decisions (a parking structure costs ~$41M at Oakville,
~$47M at Pickering) and retrospective before/after evaluation from the
2018 archive are the other unique angles. The divergence table has not
yet been computed. The test for whether this work is worth taking to
leadership: *would any decision change without this data?*

## Reproduce

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Quick VV check (Planetary Computer, no credentials needed — it signs
public COGs itself):

```bash
cd quick-vv-check-2018-2026
python quick-vv-check-2018-2026.py   # summers 2018-2026, 6 lots
python analyse-vv-2018-2026.py       # annual means + recovery index
python make-per-scene-charts.py      # per-scene line charts
```

Network inventory (downloads ~1 GB of raw data; see below):

```bash
cd network-inventory
python inventory.py                  # reproduces stations.csv and lots.csv
```

SARpanel formal chain (not yet run): install SARpanel and ESA SNAP
separately, set your Earthdata token **only as a terminal environment
variable** (`EARTHDATA_TOKEN`) — never in chat, code or config — then
`doctor`, `plan`, `run` and `aggregate` using the configs in `sarpanel/`.
Start with the 2019-summer trial config before the full 2018–2026 run.

## Data sources

- Sentinel-1 RTC via Microsoft Planetary Computer (`sentinel-1-rtc`).
- GO Transit GTFS feed, version 20261104 (Metrolinx open data).
- GO station parking numbers: public station-details pages on
  gotransit.com, scraped 2026-11-08 (the GO public API endpoint is dead).
- OpenStreetMap: Geofabrik Ontario extract `ontario-261107.osm.pbf`
  (2026-11-07).
- SARpanel: https://github.com/ryjayne89/sarpanel (MIT).

## What is NOT in this repo

- `venv/` — recreate from `requirements.txt`.
- Raw downloads (~1 GB): the Ontario OSM PBF (979 MB), `GO-GTFS.zip` and
  the extracted GTFS tables, and the intermediate OSM JSON extracts.
  They are excluded because of size (GitHub's single-file limit is
  100 MB) and because they are regenerable: download the Geofabrik
  Ontario extract and the GO GTFS feed, then run `inventory.py` and the
  scripts in `network-inventory/scripts/`. The final CSVs are included.
- No credentials, tokens, API keys or personal data. The Earthdata token
  for SARpanel is never stored in this repo.

## Licence

MIT — see `LICENSE`.
