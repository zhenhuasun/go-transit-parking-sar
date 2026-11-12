#!/usr/bin/env python3
"""T1b — EXPLORATORY sensitivity: single common control for all lots.

NOT part of the pre-specified T1b decision. The addendum fixes the
station mapping (each lot differenced against its own station's
control); this script re-runs the differenced models with ONE control
area applied to all 6 lots, to see how much the Oakville pooled
control's noise matters. Uses the exact same model code as
t1b_weekend_test.py (imported, not copied): per-lot OLS, pooled
clustered OLS, and the 10,000-permutation test, seed 42.

Run once per control area (Bronte / Clarkson / Oakville) and compare:
if only one choice passes, that is selection on the result, not a
robust finding.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t1b_weekend_test as T

LOT_CSV = T.LOT_CSV
CTRL_CSV = T.CTRL_CSV
PRIMARY_YEARS = T.PRIMARY_YEARS
LOTS = T.LOTS
STATION_OF_LOT = T.STATION_OF_LOT


def run_single_control(control_name):
    rng = np.random.default_rng(T.SEED)
    lot = pd.read_csv(LOT_CSV)
    ctrl = pd.read_csv(CTRL_CSV)
    lot = T.add_time_flags(lot)
    ctrl = T.add_time_flags(ctrl)
    lot_p = lot[lot["year"].isin(PRIMARY_YEARS)].copy()
    lot_p = lot_p[~((lot_p["lot_id"] == "oakville-south") & (lot_p["year"] == 2026))]
    ctrl_map = {(r["scene_id"]): r["mean_VV_dB"]
                for _, r in ctrl[ctrl["control_name"] == control_name].iterrows()}
    diff_rows = []
    for _, r in lot_p.iterrows():
        key = r["scene_id"]
        if key not in ctrl_map:
            continue
        diff_rows.append({**r.to_dict(), "diff_VV_dB": r["mean_VV_dB"] - ctrl_map[key]})
    diff = pd.DataFrame(diff_rows)
    d1 = T.fit_per_group(diff, "lot_id", value_col="diff_VV_dB")
    d2 = T.fit_pooled(diff, "lot_id", value_col="diff_VV_dB")
    d2_perm, _ = T.permutation_p(diff, "lot_id", d2["coef"], rng, value_col="diff_VV_dB")
    n_neg = sum(1 for r in d1.values() if r["coef"] < 0)
    crit2 = (d2["coef"] < 0 and d2["p"] < 0.01 and d2_perm < 0.01 and n_neg >= 5)
    print(f"\n=== single control: {control_name} ===")
    print(f"pooled differenced: coef={d2['coef']:.3f} dB, 95% CI [{d2['ci_lo']:.3f}, {d2['ci_hi']:.3f}], "
          f"clustered p={d2['p']:.4g}, perm p={d2_perm:.4g}, n={d2['n']}")
    for g in LOTS:
        r = d1[g]
        print(f"  {g:15s} {r['coef']:+.3f} dB  p={r['p']:.4g}  n={r['n']}")
    print(f"{n_neg}/6 lots negative; criterion-2-style pass: {crit2}")
    return {"control": control_name, "pooled_coef": d2["coef"], "pooled_p": d2["p"],
            "perm_p": d2_perm, "n_neg": n_neg, "crit2_pass": crit2,
            "per_lot": {g: (d1[g]["coef"], d1[g]["p"]) for g in LOTS}}


if __name__ == "__main__":
    rows = []
    for name in ["Bronte GO — Control", "Clarkson GO — Control", "Oakville GO — Control"]:
        rows.append(run_single_control(name))
    out = pd.DataFrame([{"control": r["control"], "pooled_coef_dB": r["pooled_coef"],
                         "pooled_p": r["pooled_p"], "perm_p": r["perm_p"],
                         "n_neg_lots": r["n_neg"], "crit2_style_pass": r["crit2_pass"]}
                        for r in rows])
    out.to_csv(Path(__file__).resolve().parent / "t1b_sensitivity_common_control.csv", index=False)
    print("\nwrote t1b_sensitivity_common_control.csv")
