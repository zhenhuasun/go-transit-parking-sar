#!/usr/bin/env python3
"""Analyse quick-vv-check/vv-by-lot-scene.csv -> vv-summary.md + vv-time-series.png."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

BASE = Path(__file__).resolve().parent
df = pd.read_csv(BASE / "vv-by-lot-scene.csv", parse_dates=["date"])
df["period"] = np.where(
    df["date"].dt.year == 2020,
    np.where(df["date"].dt.month <= 5, "2020-Apr-May", "2020-Jun-Aug"),
    df["date"].dt.year.astype(str) + "-summer",
)
ORDER = ["2019-summer", "2020-Apr-May", "2020-Jun-Aug", "2024-summer"]
LOTS = ["oakville-main", "oakville-south", "clarkson-main",
        "clarkson-north", "bronte-main", "bronte-south"]

# ---- summary table: pooled ascending, and per relative orbit ----
rows = []
for lot in LOTS:
    sub = df[df["lot_id"] == lot]
    r = {"lot_id": lot, "spaces": int(sub["spaces"].iloc[0]),
         "n_pixels": int(sub["n_pixels"].iloc[0])}
    for per in ORDER:
        s = sub[sub["period"] == per]["mean_VV_dB"]
        r[f"{per}_mean"] = round(float(s.mean()), 2)
        r[f"{per}_sd"] = round(float(s.std()), 2)
        r[f"{per}_n"] = int(len(s))
    r["drop_19_to_20AM"] = round(r["2020-Apr-May_mean"] - r["2019-summer_mean"], 2)
    r["drop_19_to_20JA"] = round(r["2020-Jun-Aug_mean"] - r["2019-summer_mean"], 2)
    r["recov_20JA_to_24"] = round(r["2024-summer_mean"] - r["2020-Jun-Aug_mean"], 2)
    r["net_19_to_24"] = round(r["2024-summer_mean"] - r["2019-summer_mean"], 2)
    rows.append(r)
summ = pd.DataFrame(rows)
summ.to_csv(BASE / "vv-summary-table.csv", index=False)

# per relative orbit, for the within-track check
track = (df.groupby(["lot_id", "period", "relative_orbit"])["mean_VV_dB"]
         .agg(["mean", "std", "count"]).reset_index())
track.to_csv(BASE / "vv-by-lot-period-track.csv", index=False)

# ---- chart: faceted, one panel per lot, colour = relative orbit ----
fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True, sharey=True)
colors = {4: "#1565c0", 77: "#ef6c00"}
for ax, lot in zip(axes.flat, LOTS):
    sub = df[df["lot_id"] == lot]
    for rel, c in colors.items():
        s = sub[sub["relative_orbit"] == rel].sort_values("date")
        ax.plot(s["date"], s["mean_VV_dB"], "o-", color=c, ms=4, lw=1,
                label=f"rel orbit {rel}")
    # period means (pooled ascending) as dashed lines
    for per in ORDER:
        s = sub[sub["period"] == per]
        if len(s):
            ax.axhline(s["mean_VV_dB"].mean(), color="grey", ls="--", lw=0.8, alpha=0.6)
    ax.set_title(f"{lot}  ({int(sub['spaces'].iloc[0])} spaces, "
                 f"{int(sub['n_pixels'].iloc[0])} px)", fontsize=11)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")
    for lbl in ax.get_xticklabels():
        lbl.set_rotation(30)
axes[1, 0].set_ylabel("mean VV (dB)")
fig.suptitle("GO parking lots — mean VV backscatter (Sentinel-1 RTC, ascending only, ~19:10 EDT)\n"
             "Dashed grey = period mean (ascending, both relative orbits pooled)",
             fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(BASE / "vv-time-series.png", dpi=150)
print(summ.to_string(index=False))
print("\nWrote vv-summary-table.csv, vv-by-lot-period-track.csv, vv-time-series.png")
