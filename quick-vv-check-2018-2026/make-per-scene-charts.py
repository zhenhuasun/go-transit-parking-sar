#!/usr/bin/env python3
"""Per-scene line charts for GO parking VV, summers 2018-2026 + Sep-Nov 2026 autumn check.

Inputs: vv-by-lot-scene-2018-2026.csv (684 rows, Jun-Aug 2018-2026),
        vv-by-lot-scene-sep-nov-2026.csv (60 rows, Sep 1-Nov 10 2026).
Outputs: 6 per-lot PNGs (vv-per-scene-<lot>.png) and 3 per-station PNGs
         (vv-per-scene-station-<station>.png).
Rules: summer and autumn are plotted as SEPARATE series (no line connecting
Aug 2026 to Sep 2026); autumn band shaded and labelled; autumn values are
NOT part of the summer recovery index. Horizontal dashed line = lot's 2019
summer mean. Oakville South construction Apr-Sep 2026 shaded/annotated.
Station aggregate (if shown) = space-weighted mean of LINEAR power,
converted back to dB; Clarkson North weight is provisional (boundary unverified).
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOTS = ["oakville-main", "oakville-south", "clarkson-main",
        "clarkson-north", "bronte-main", "bronte-south"]
SPACES = {"oakville-main": 2712, "oakville-south": 291, "clarkson-main": 1274,
          "clarkson-north": 627, "bronte-main": 1824, "bronte-south": 1149}
NPIX = {"oakville-main": 739, "oakville-south": 82, "clarkson-main": 360,
        "clarkson-north": 325, "bronte-main": 575, "bronte-south": 319}
STATIONS = {"oakville": ["oakville-main", "oakville-south"],
            "clarkson": ["clarkson-main", "clarkson-north"],
            "bronte": ["bronte-main", "bronte-south"]}
COLOURS = {"oakville-main": "#1f77b4", "oakville-south": "#d62728",
           "clarkson-main": "#2ca02c", "clarkson-north": "#ff7f0e",
           "bronte-main": "#9467bd", "bronte-south": "#8c564b"}

summ = pd.read_csv(BASE / "vv-by-lot-scene-2018-2026.csv", parse_dates=["date"])
aut = pd.read_csv(BASE / "vv-by-lot-scene-sep-nov-2026.csv", parse_dates=["date"])
# verification: summer means must match annual CSV
ann = pd.read_csv(BASE / "vv-annual-summary-2018-2026.csv")
for lot in LOTS:
    for y in (2019, 2020, 2024):
        m = summ[(summ["lot_id"] == lot) & (summ["date"].dt.year == y)]["mean_VV_dB"].mean()
        ref = float(ann[ann["lot_id"] == lot][f"{y}_mean_dB"].iloc[0])
        assert abs(m - ref) < 0.005, (lot, y, m, ref)
print("Verified: summer 2019/2020/2024 means match annual CSV for all 6 lots.")

AUT_START = pd.Timestamp("2026-09-01")
AUT_END = pd.Timestamp("2026-11-10")
CONSTR_START = pd.Timestamp("2026-04-01")
CONSTR_END = pd.Timestamp("2026-09-30")


def base_style(ax):
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=(1, 7)))
    ax.tick_params(axis="x", rotation=0)


def plot_series(ax, lot, label=None):
    """Plot summer (connected) and autumn (separate markers) for one lot."""
    s = summ[summ["lot_id"] == lot].sort_values("date")
    a = aut[aut["lot_id"] == lot].sort_values("date")
    ax.plot(s["date"], s["mean_VV_dB"], "o-", ms=3.5, lw=1.2,
            color=COLOURS[lot], label=label or f"{lot} (summer, Jun-Aug)")
    ax.plot(a["date"], a["mean_VV_dB"], "s--", ms=5, lw=1.0,
            color=COLOURS[lot], markerfacecolor="white", markeredgewidth=1.5,
            label=f"{lot} (autumn Sep-Nov 2026)")
    return s, a


def finish(ax, title, subtitle, ylim):
    ax.axvspan(AUT_START, AUT_END, color="orange", alpha=0.12)
    ax.text(AUT_START + pd.Timedelta(days=2), ylim[0] + 0.15,
            "Autumn check\nSep-Nov 2026", fontsize=8, color="#8a5a00", va="bottom")
    ax.set_ylim(*ylim)
    ax.set_title(title, fontsize=12)
    ax.set_ylabel("per-scene mean VV (dB)")
    base_style(ax)
    ax.legend(fontsize=8, loc="lower left", framealpha=0.9)
    plt.tight_layout()
    return ax


def ylim_for(frames):
    vals = np.concatenate([f["mean_VV_dB"].values for f in frames if len(f)])
    return float(vals.min()) - 0.9, float(vals.max()) + 0.9


# ---- (a) per-lot charts ----
for lot in LOTS:
    fig, ax = plt.subplots(figsize=(12, 5))
    s, a = plot_series(ax, lot)
    base19 = float(summ[(summ["lot_id"] == lot) & (summ["date"].dt.year == 2019)]["mean_VV_dB"].mean())
    ax.axhline(base19, color="grey", ls="--", lw=1.0, alpha=0.7,
               label=f"2019 summer mean ({base19:.2f} dB)")
    if lot == "oakville-south":
        ax.axvspan(CONSTR_START, CONSTR_END, color="red", alpha=0.10)
        ax.text(pd.Timestamp("2026-05-15"), ylim_for([s, a])[1] - 0.3,
                "Construction compound\nApr-Sep 2026 (south lot closed)", fontsize=8,
                color="#a00000", ha="center", va="top")
    ylim = ylim_for([s, a])
    finish(ax, f"{lot} — per-scene mean VV, every acquisition 2018-2026  "
               f"({SPACES[lot]} spaces, {NPIX[lot]} px)",
           "", ylim)
    fig.text(0.5, -0.01,
             "Summer points (Jun-Aug, circles) connected in date order. Autumn squares Sep-Nov 2026 are a separate "
             "check, not connected to summer and not in the summer recovery index. Dashed grey = 2019 summer mean.",
             ha="center", fontsize=8, color="#555555")
    out = BASE / f"vv-per-scene-{lot}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out.name)


def space_weighted_agg(lots, df):
    """Space-weighted mean of linear power per date, back to dB."""
    out = []
    for d, g in df.groupby("date"):
        lin = 0.0
        wsum = 0
        for lot in lots:
            row = g[g["lot_id"] == lot]
            if len(row):
                w = SPACES[lot]
                lin += w * 10 ** (float(row["mean_VV_dB"].iloc[0]) / 10)
                wsum += w
        out.append({"date": d, "mean_VV_dB": 10 * np.log10(lin / wsum) if wsum else np.nan})
    return pd.DataFrame(out)


# ---- (b) per-station charts ----
for station, lots in STATIONS.items():
    fig, ax = plt.subplots(figsize=(12, 6))
    frames = []
    for lot in lots:
        s, a = plot_series(ax, lot)
        frames += [s, a]
        base19 = float(summ[(summ["lot_id"] == lot) & (summ["date"].dt.year == 2019)]["mean_VV_dB"].mean())
        ax.axhline(base19, color=COLOURS[lot], ls=":", lw=0.9, alpha=0.5)
    # space-weighted station aggregate (dashed black), summer and autumn separately
    agg_s = space_weighted_agg(lots, summ)
    agg_a = space_weighted_agg(lots, aut)
    ax.plot(agg_s["date"], agg_s["mean_VV_dB"], "k--", lw=1.4,
            label="Station aggregate, space-weighted (summer)")
    ax.plot(agg_a["date"], agg_a["mean_VV_dB"], "ks--", ms=4, lw=1.0,
            markerfacecolor="white", label="Station aggregate (autumn)")
    frames += [agg_s, agg_a]
    note = "Clarkson North weight provisional (boundary unverified)." if station == "clarkson" else ""
    ylim = ylim_for(frames)
    finish(ax, f"{station.capitalize()} GO — per-scene mean VV, every acquisition 2018-2026",
           "", ylim)
    ax.legend(fontsize=8, loc="lower left", framealpha=0.9, ncol=2)
    fig.text(0.5, -0.01,
             "One line per lot (per-scene values). Black dashed = space-weighted station aggregate "
             "(linear-power mean, weights = spaces). Dotted lines = each lot's 2019 summer mean. "
             f"Autumn squares are a separate check. {note}",
             ha="center", fontsize=8, color="#555555")
    out = BASE / f"vv-per-scene-station-{station}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out.name)

print("Done: 6 per-lot + 3 per-station per-scene charts.")
