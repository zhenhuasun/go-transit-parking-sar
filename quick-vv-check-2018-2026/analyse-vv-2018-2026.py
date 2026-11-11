#!/usr/bin/env python3
"""Analyse quick-vv-check-2018-2026/vv-by-lot-scene-2018-2026.csv.

Outputs:
  vv-annual-summary-2018-2026.csv  (per lot per year: n, mean, SD, recovery index 2019=100)
  vv-by-lot-year-track-2018-2026.csv (per lot per year per relative orbit)
  vv-time-series-2018-2026.png     (annual mean VV_dB per lot vs summer year, SD error bars)
Prints the annual table and recovery-index table for the summary markdown.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent
df = pd.read_csv(BASE / "vv-by-lot-scene-2018-2026.csv", parse_dates=["date"])
df["year"] = df["date"].dt.year
YEARS = list(range(2018, 2027))
LOTS = ["oakville-main", "oakville-south", "clarkson-main",
        "clarkson-north", "bronte-main", "bronte-south"]

# ---- annual summary ----
rows = []
for lot in LOTS:
    sub = df[df["lot_id"] == lot]
    base = sub[sub["year"] == 2019]["mean_VV_dB"]
    base_mean = float(base.mean())
    r = {"lot_id": lot, "spaces": int(sub["spaces"].iloc[0]),
         "n_pixels": int(sub["n_pixels"].iloc[0]), "base_2019_mean_dB": round(base_mean, 2)}
    for y in YEARS:
        s = sub[sub["year"] == y]["mean_VV_dB"]
        r[f"{y}_n"] = int(len(s))
        r[f"{y}_mean_dB"] = round(float(s.mean()), 2) if len(s) else None
        r[f"{y}_sd_dB"] = round(float(s.std()), 2) if len(s) > 1 else None
        # recovery index from LINEAR power: 100 * 10^((mean_y - mean_2019)/10)
        r[f"{y}_index2019"] = (round(100 * 10 ** ((float(s.mean()) - base_mean) / 10), 1)
                               if len(s) else None)
    rows.append(r)
summ = pd.DataFrame(rows)
summ.to_csv(BASE / "vv-annual-summary-2018-2026.csv", index=False)

# per relative orbit per year
track = (df.groupby(["lot_id", "year", "relative_orbit"])["mean_VV_dB"]
         .agg(["mean", "std", "count"]).reset_index())
track.to_csv(BASE / "vv-by-lot-year-track-2018-2026.csv", index=False)

# ---- chart: annual means, one panel per lot, SD error bars ----
fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True, sharey=True)
for ax, lot in zip(axes.flat, LOTS):
    sub = df[df["lot_id"] == lot]
    xs, ys, es = [], [], []
    for y in YEARS:
        s = sub[sub["year"] == y]["mean_VV_dB"]
        if len(s):
            xs.append(y); ys.append(s.mean()); es.append(s.std())
    ax.errorbar(xs, ys, yerr=es, fmt="o-", capsize=4, lw=1.5, ms=5)
    ax.axhline(ys[xs.index(2019)] if 2019 in xs else np.nan, color="grey",
               ls="--", lw=0.8, alpha=0.6)
    ax.set_title(f"{lot}  ({int(sub['spaces'].iloc[0])} spaces, "
                 f"{int(sub['n_pixels'].iloc[0])} px)", fontsize=11)
    ax.set_xticks(YEARS); ax.set_xticklabels([str(y) for y in YEARS], rotation=30)
    ax.grid(alpha=0.3)
# one common y-range for all panels (sharey): global annual mean +/- SD, with margin,
# so no point or error bar is clipped (oakville-south 2026 is the top, clarkson-main 2020 the bottom)
_all = df.groupby(["lot_id", "year"])["mean_VV_dB"].agg(["mean", "std"])
_lo = float((_all["mean"] - _all["std"]).min()) - 0.7
_hi = float((_all["mean"] + _all["std"]).max()) + 0.7
for _ax in axes.flat:
    _ax.set_ylim(_lo, _hi)
axes[1, 0].set_ylabel("summer mean VV (dB)")
fig.suptitle("GO parking lots — summer mean VV backscatter by year (Sentinel-1 RTC, ascending only, ~19:10 EDT)\n"
             "Error bars = SD across scenes within the summer; dashed grey = 2019 (pre-COVID baseline)",
             fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(BASE / "vv-time-series-2018-2026.png", dpi=150)

pd.set_option("display.width", 250)
print("ANNUAL MEANS (dB)")
print(summ[["lot_id"] + [f"{y}_mean_dB" for y in YEARS]].to_string(index=False))
print("\nRECOVERY INDEX (2019 = 100, from linear power)")
print(summ[["lot_id"] + [f"{y}_index2019" for y in YEARS]].to_string(index=False))
print("\nSCENE COUNTS")
print(summ[["lot_id"] + [f"{y}_n" for y in YEARS]].to_string(index=False))
print("\nWrote vv-annual-summary-2018-2026.csv, vv-by-lot-year-track-2018-2026.csv, vv-time-series-2018-2026.png")
