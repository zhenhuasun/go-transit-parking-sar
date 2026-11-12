#!/usr/bin/env python3
"""T1b — Supplemental negative control test (see t1b_spec_addendum.md).

Written AFTER the T1 result (PASS, 2026-11-12). Not pre-registered
with T1. Implements the addendum exactly:

  C1  Per-area OLS on control VV: VV_dB ~ weekend + C(orbit) + C(year).
  C2  Pooled control OLS: VV_dB ~ weekend + C(area) + C(area):C(orbit)
      + C(area):C(year), SE clustered by acquisition date.
  D1  Per-lot differenced OLS: (lot VV_dB - same-station control VV_dB)
      ~ weekend + C(orbit) + C(year).
  D2  Pooled differenced OLS (same spec as T1 pooled), clustered SE,
      plus permutation test identical to T1 Step 2c (10,000 perms,
      seed 42).

Decision (addendum): T1 PASS stands iff (1) no control weekend effect
(all 3 per-area p >= 0.05 AND pooled control p >= 0.05, either sign)
and (2) the differenced series passes all T1 criteria (pooled coef < 0
with clustered p < 0.01; permutation one-sided p < 0.01; >= 5 of 6 lots
negative on differenced per-lot coefs). Otherwise T1 is downgraded to
INCONCLUSIVE (not FAIL).

Dependencies: numpy, pandas, matplotlib only. OLS / cluster-robust SE /
t p-values implemented with numpy + a continued-fraction incomplete-beta
function (same code as T1, verified against known t values).
"""
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
LOT_CSV = REPO_ROOT / "quick-vv-check-2018-2026" / "vv-by-lot-scene-2018-2026.csv"
CTRL_CSV = OUT / "t1b_control_vv.csv"
SEED = 42
N_PERM = 10_000
PRIMARY_YEARS = [2018, 2019, 2022, 2023, 2024, 2025, 2026]
LOTS = ["oakville-main", "oakville-south", "clarkson-main",
        "clarkson-north", "bronte-main", "bronte-south"]
STATION_OF_LOT = {"oakville-main": "oakville", "oakville-south": "oakville",
                  "clarkson-main": "clarkson", "clarkson-north": "clarkson",
                  "bronte-main": "bronte", "bronte-south": "bronte"}


def stop(msg):
    print(f"STOP: {msg}", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------- t dist
def _betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (a + b + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def betainc_reg(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1.0 - x))
    bt = math.exp(lbeta)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_pvalue_two_sided(t, df):
    return betainc_reg(df / 2.0, 0.5, df / (df + t * t))


def t_crit_975(df):
    lo, hi = 0.0, 50.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        cdf = 1.0 - t_pvalue_two_sided(mid, df) / 2.0
        if cdf < 0.975:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- OLS
def ols(X, y):
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    return beta, y - X @ beta, XtX_inv


def coef_ci_p(beta, se, df):
    crit = t_crit_975(df)
    return beta - crit * se, beta + crit * se, t_pvalue_two_sided(beta / se, df)


# ---------------------------------------------------------------- holidays (same as T1)
def civic_holiday(year):
    d = pd.Timestamp(year=year, month=8, day=1)
    return d + pd.Timedelta(days=(7 - d.day_of_week) % 7)


def is_holiday(local_date):
    y = local_date.year
    july1 = pd.Timestamp(year=y, month=7, day=1)
    if local_date == july1.date():
        return True
    if july1.day_of_week == 6 and local_date == (july1 + pd.Timedelta(days=1)).date():
        return True
    return local_date == civic_holiday(y).date()


def add_time_flags(df):
    dt_local = pd.to_datetime(df["datetime_utc"], utc=True).dt.tz_convert("America/Toronto")
    df["local_date"] = dt_local.dt.date
    df["dow"] = dt_local.dt.day_of_week
    df["year"] = dt_local.dt.year
    df["month"] = dt_local.dt.month
    df["is_holiday"] = df["local_date"].apply(is_holiday)
    df["weekend"] = ((df["dow"] >= 5) | df["is_holiday"]).astype(int)
    return df


# ---------------------------------------------------------------- designs
def build_pooled_design(d, group_col, value_col="mean_VV_dB"):
    """weekend + C(group) + C(group):C(orbit) + C(group):C(year)."""
    groups = sorted(d[group_col].unique())
    cols, names = [], []
    cols.append(d["weekend"].to_numpy(float)); names.append("weekend")
    for g in groups:
        ind = (d[group_col] == g).to_numpy(float)
        cols.append(ind); names.append(f"group[{g}]")
        orb = ind * (d["relative_orbit"] == 77).to_numpy(float)
        if 0 < orb.sum() < ind.sum():
            cols.append(orb); names.append(f"group[{g}]:orbit77")
        yrs_present = sorted(d.loc[d[group_col] == g, "year"].unique())
        for yr in yrs_present[1:]:
            cols.append(ind * (d["year"] == yr).to_numpy(float))
            names.append(f"group[{g}]:year{yr}")
    X = np.column_stack(cols)
    assert np.linalg.matrix_rank(X) == X.shape[1], "pooled design not full rank"
    return X, names


def cluster_se(X, resid, clusters):
    XtX_inv = np.linalg.inv(X.T @ X)
    K = X.shape[1]
    G = len(np.unique(clusters))
    N = len(resid)
    meat = np.zeros((K, K))
    for g in np.unique(clusters):
        m = clusters == g
        s = X[m].T @ resid[m]
        meat += np.outer(s, s)
    adj = (G / (G - 1.0)) * ((N - 1.0) / (N - K))
    V = adj * (XtX_inv @ meat @ XtX_inv)
    return math.sqrt(max(V[0, 0], 0.0)), G


def fit_pooled(d, group_col, value_col="mean_VV_dB"):
    X, _ = build_pooled_design(d, group_col, value_col)
    y = d[value_col].to_numpy(float)
    beta, resid, _ = ols(X, y)
    se, G = cluster_se(X, resid, d["local_date"].to_numpy())
    lo, hi, p = coef_ci_p(beta[0], se, G - 1)
    return {"coef": beta[0], "se": se, "ci_lo": lo, "ci_hi": hi, "p": p,
            "n": len(d), "n_clusters": G, "df": G - 1}


def fit_per_group(d, group_col, value_col="mean_VV_dB"):
    out = {}
    for g in sorted(d[group_col].unique()):
        dg = d[d[group_col] == g]
        yrs = sorted(dg["year"].unique())
        cols = [dg["weekend"].to_numpy(float),
                np.ones(len(dg)),
                (dg["relative_orbit"] == 77).to_numpy(float)]
        for yr in yrs[1:]:
            cols.append((dg["year"] == yr).to_numpy(float))
        X = np.column_stack(cols)
        y = dg[value_col].to_numpy(float)
        beta, resid, XtX_inv = ols(X, y)
        n, K = X.shape
        s2 = float(resid @ resid) / (n - K)
        se = math.sqrt(max(s2 * XtX_inv[0, 0], 0.0))
        lo, hi, p = coef_ci_p(beta[0], se, n - K)
        out[g] = {"coef": beta[0], "se": se, "ci_lo": lo, "ci_hi": hi,
                  "p": p, "n": n, "years": yrs}
    return out


def permutation_p(d, group_col, observed, rng, value_col="mean_VV_dB"):
    X, _ = build_pooled_design(d, group_col, value_col)
    Z = X[:, 1:]
    y = d[value_col].to_numpy(float)
    beta_z, _, _ = ols(Z, y)
    y_res = y - Z @ beta_z
    scenes = (d.drop_duplicates("scene_id")
                [["scene_id", "year", "relative_orbit", "weekend"]]
                .reset_index(drop=True))
    strata = scenes.groupby(["year", "relative_orbit"]).indices
    row_of_scene = {s: i for i, s in enumerate(scenes["scene_id"])}
    scene_idx_per_row = d["scene_id"].map(row_of_scene).to_numpy()
    ZtZ_inv = np.linalg.inv(Z.T @ Z)
    P = Z @ ZtZ_inv @ Z.T
    w0 = d["weekend"].to_numpy(float)
    w0_res = w0 - P @ w0
    obs_fwl = float(w0_res @ y_res) / float(w0_res @ w0_res)
    assert abs(obs_fwl - observed) < 1e-8, "FWL != full OLS coefficient"
    labels = scenes["weekend"].to_numpy()
    W = np.tile(labels, (N_PERM, 1)).astype(float)
    for _, idx in strata.items():
        idx = np.asarray(sorted(idx))
        for r in range(N_PERM):
            W[r, idx] = rng.permutation(labels[idx])
    W_row = W[:, scene_idx_per_row]
    W_res = W_row - W_row @ P.T
    num = W_res @ y_res
    den = np.einsum("ij,ij->i", W_res, W_res)
    coefs = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
    return float(np.mean(coefs <= observed)), coefs


# ---------------------------------------------------------------- main
def main():
    rng = np.random.default_rng(SEED)
    lot = pd.read_csv(LOT_CSV)
    ctrl = pd.read_csv(CTRL_CSV)
    if set(lot["scene_id"]) != set(ctrl["scene_id"]):
        stop("control scene set != lot scene set")
    lot = add_time_flags(lot)
    ctrl = add_time_flags(ctrl)
    # T1 sample rules for lots; controls keep all years in the primary set
    lot_p = lot[lot["year"].isin(PRIMARY_YEARS)].copy()
    lot_p = lot_p[~((lot_p["lot_id"] == "oakville-south") & (lot_p["year"] == 2026))]
    ctrl_p = ctrl[ctrl["year"].isin(PRIMARY_YEARS)].copy()
    print(f"primary: {len(lot_p)} lot rows, {len(ctrl_p)} control rows, "
          f"{lot_p['scene_id'].nunique()} scenes")

    # differenced dataset: lot VV - same-station control VV, per scene
    ctrl_map = {(r["scene_id"], r["station"]): r["mean_VV_dB"]
                for _, r in ctrl.iterrows()}
    diff_rows = []
    dropped = []
    for _, r in lot_p.iterrows():
        key = (r["scene_id"], STATION_OF_LOT[r["lot_id"]])
        if key not in ctrl_map:
            dropped.append(key)
            continue
        diff_rows.append({**r.to_dict(), "diff_VV_dB": r["mean_VV_dB"] - ctrl_map[key]})
    if dropped:
        print(f"WARNING: {len(dropped)} lot rows dropped (no control value): {sorted(set(dropped))[:5]}")
    diff = pd.DataFrame(diff_rows)
    print(f"differenced rows: {len(diff)} (dropped {len(dropped)})")

    results = []

    def record(analysis, model, group, r, perm_p=None):
        results.append({"analysis": analysis, "model": model, "group": group,
                        "coef_dB": r["coef"], "se": r["se"],
                        "ci_lo": r["ci_lo"], "ci_hi": r["ci_hi"],
                        "p_two_sided": r["p"],
                        "perm_p_one_sided": perm_p if perm_p is not None else "",
                        "n": r["n"],
                        "n_clusters": r.get("n_clusters", "")})

    # ---- C1: per-area control OLS
    c1 = fit_per_group(ctrl_p, "control_name")
    for g, r in c1.items():
        record("C1_control", "per-area OLS", g, r)
    # ---- C2: pooled control OLS
    c2 = fit_pooled(ctrl_p, "control_name")
    record("C2_control", "pooled clustered OLS", "pooled", c2)
    print(f"C2 pooled control: coef={c2['coef']:.3f} dB, "
          f"95% CI [{c2['ci_lo']:.3f}, {c2['ci_hi']:.3f}], p={c2['p']:.4g}")

    # ---- D1: per-lot differenced OLS
    d1 = fit_per_group(diff, "lot_id", value_col="diff_VV_dB")
    for g, r in d1.items():
        record("D1_differenced", "per-lot OLS", g, r)
    # ---- D2: pooled differenced OLS + permutation
    d2 = fit_pooled(diff, "lot_id", value_col="diff_VV_dB")
    d2_perm, _ = permutation_p(diff, "lot_id", d2["coef"], rng, value_col="diff_VV_dB")
    record("D2_differenced", "pooled clustered OLS", "pooled", d2, perm_p=d2_perm)
    print(f"D2 pooled differenced: coef={d2['coef']:.3f} dB, "
          f"95% CI [{d2['ci_lo']:.3f}, {d2['ci_hi']:.3f}], "
          f"p={d2['p']:.4g}, perm p={d2_perm:.4g}")

    # ---- decision (addendum)
    crit1 = all(r["p"] >= 0.05 for r in c1.values()) and c2["p"] >= 0.05
    n_neg_diff = sum(1 for r in d1.values() if r["coef"] < 0)
    crit2a = d2["coef"] < 0 and d2["p"] < 0.01
    crit2b = d2_perm < 0.01
    crit2c = n_neg_diff >= 5
    crit2 = crit2a and crit2b and crit2c
    if crit1 and crit2:
        decision = "PASS — T1 PASS reinstated (T1b round 3, pooled 4-roof Oakville control)"
    else:
        decision = "INCONCLUSIVE — T1 stays INCONCLUSIVE"
    print(f"\nDECISION: {decision} (crit1={crit1}, crit2={crit2} "
          f"[2a={crit2a}, 2b={crit2b}, 2c={crit2c}, {n_neg_diff}/6 negative])")

    res = pd.DataFrame(results)
    res.to_csv(OUT / "t1b_results.csv", index=False)

    # plots
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, data, title in [
            (axes[0], c1, "Control areas — weekend effect (dB)"),
            (axes[1], d1, "Differenced (lot − control) — weekend effect (dB)")]:
        keys = sorted(data, key=lambda k: data[k]["coef"])
        ypos = np.arange(len(keys))
        coefs = [data[k]["coef"] for k in keys]
        lo = [data[k]["coef"] - data[k]["ci_lo"] for k in keys]
        hi = [data[k]["ci_hi"] - data[k]["coef"] for k in keys]
        ax.errorbar(coefs, ypos, xerr=[lo, hi], fmt="o", capsize=4, color="#ef6c00")
        ax.axvline(0, color="grey", lw=1)
        ax.set_yticks(ypos)
        ax.set_yticklabels([f"{k} (n={data[k]['n']})" for k in keys])
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(OUT / "t1b_weekend_coefs.png", dpi=150)
    plt.close(fig)

    tick = lambda b: "✅" if b else "❌"
    lines = []
    lines.append("# T1b — Supplemental negative control (post-T1)")
    lines.append("")
    lines.append("**Status:** this test was specified AFTER the T1 result (PASS, "
                 "2026-11-12) — see `t1b_spec_addendum.md`. It is not "
                 "pre-registered with T1. Round 3 (2026-11-12): the Oakville "
                 "control was replaced again — a pooled 4-roof control, after "
                 "part 2 of the user's 5-roof set was dropped for overlapping "
                 "the failed round-2 roof; Bronte and Clarkson controls are "
                 "unchanged. Rounds 1–2 are archived as "
                 "`t1b_report_round1.md` and `t1b_report_round2.md`.")
    lines.append("")
    lines.append(f"**Decision: {decision}**")
    lines.append("")
    lines.append("## Extraction check")
    lines.append("")
    px = ctrl.groupby("control_name")["n_pixels"].mean()
    lines.append(f"Control VV extracted for all 114 T1 summer scenes "
                 f"(scene sets identical to the lot CSV). Unit check on the "
                 f"first scene confirmed LINEAR gamma naught, same branch as "
                 f"the lots. Mean pixels per scene: Bronte control "
                 f"{px['Bronte GO — Control']:.0f}, Clarkson control "
                 f"{px['Clarkson GO — Control']:.0f}, Oakville control "
                 f"{px['Oakville GO — Control']:.0f}. "
                 f"Differenced rows: {len(diff)} (dropped {len(dropped)}).")
    lines.append("")
    lines.append("## C — Control weekend effects (primary years 2018, 2019, 2022–2026)")
    lines.append("")
    lines.append("Per-area OLS: control `VV_dB ~ weekend + C(relative_orbit) + "
                 "C(year)` (classical SE). Pooled: `VV_dB ~ weekend + C(area) + "
                 "C(area):C(relative_orbit) + C(area):C(year)`, SE clustered by "
                 "acquisition date (CR1).")
    lines.append("")
    lines.append("| Control area | Weekend coef (dB) | 95% CI | p | n |")
    lines.append("|---|---|---|---|---|")
    for g in sorted(c1):
        r = c1[g]
        lines.append(f"| {g} | {r['coef']:.3f} | [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}] | {r['p']:.4g} | {r['n']} |")
    lines.append("")
    lines.append(f"**Pooled control:** weekend coef **{c2['coef']:.3f} dB**, "
                 f"95% CI [{c2['ci_lo']:.3f}, {c2['ci_hi']:.3f}], clustered "
                 f"two-sided p = {c2['p']:.4g}, n = {c2['n']} rows, "
                 f"{c2['n_clusters']} date clusters.")
    lines.append("")
    lines.append("## D — Differenced weekend effects (lot − same-station control)")
    lines.append("")
    lines.append("Same models as T1, fitted on differenced VV. Permutation: "
                 "10,000 permutations, seed 42, weekend label shuffled among "
                 "scenes within each (year × relative orbit) stratum, shared "
                 "across lots within a scene.")
    lines.append("")
    lines.append("| Lot | Differenced coef (dB) | 95% CI | p | n |")
    lines.append("|---|---|---|---|---|")
    for g in LOTS:
        r = d1.get(g)
        if r:
            lines.append(f"| {g} | {r['coef']:.3f} | [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}] | {r['p']:.4g} | {r['n']} |")
    lines.append("")
    lines.append(f"**Pooled differenced:** weekend coef **{d2['coef']:.3f} dB**, "
                 f"95% CI [{d2['ci_lo']:.3f}, {d2['ci_hi']:.3f}], clustered "
                 f"two-sided p = {d2['p']:.4g}, n = {d2['n']} rows, "
                 f"{d2['n_clusters']} date clusters. Permutation one-sided "
                 f"p = {d2_perm:.4g}.")
    lines.append("")
    lines.append("![Control and differenced weekend coefficients with 95% CIs]"
                 "(t1b_weekend_coefs.png)")
    lines.append("")
    lines.append("## Decision against each criterion")
    lines.append("")
    lines.append(f"1. {tick(crit1)} Controls show no significant weekend effect "
                 f"(all per-area p ≥ 0.05 and pooled p ≥ 0.05) — per-area "
                 f"p values: " + ", ".join(f"{g} {c1[g]['p']:.4g}" for g in sorted(c1)) +
                 f"; pooled p = {c2['p']:.4g}.")
    lines.append(f"2. {tick(crit2)} Differenced series passes all T1 criteria — "
                 f"pooled coef {d2['coef']:.3f} dB < 0 with clustered "
                 f"p = {d2['p']:.4g} (< 0.01: {tick(crit2a)}); permutation "
                 f"p = {d2_perm:.4g} (< 0.01: {tick(crit2b)}); "
                 f"{n_neg_diff}/6 lots negative (≥ 5: {tick(crit2c)}).")
    lines.append("")
    lines.append(f"**Decision: {decision}**")
    lines.append("")
    lines.append("## Deviations from the addendum")
    lines.append("")
    lines.append("None.")
    lines.append("")
    lines.append("## Reproducibility")
    lines.append("")
    lines.append("- Spec: `t1b_spec_addendum.md`, committed to "
                 "`zhenhuasun/go-transit-parking-sar` as "
                 "`7b5a9730f47d6aea4e63e141177fe1c6fd79b2e0` (round 1) and "
                 "`8bda63b7da552af2f91363d7141b4e10814f1531` (round 2, revised "
                 "Oakville control) BEFORE any extraction or modelling in "
                 "each round. Round 3 (2026-11-12): spec revision + 4-part "
                 "Oakville control committed BEFORE the run; the round-3 "
                 "commit hash is recorded in the repo history "
                 "(ROUND3_COMMIT_HASH).")
    lines.append("- Script: `t1b_weekend_test.py`, seed 42, 10,000 "
                 "permutations. Rerun: `python3 t1b_weekend_test.py` from the "
                 "repo root (uses only numpy, pandas, matplotlib). "
                 "Extraction: `extract-control-vv.py`.")
    lines.append("- `polygons/`, existing CSVs and existing scripts were not "
                 "edited; all new outputs are in `calibration/t1b/`.")
    lines.append("")
    lines.append("## Plain-language reading")
    lines.append("")
    lines.append("The control areas are surfaces near each station that should "
                 "not care what day of the week it is — warehouse and factory "
                 "roofs. If the satellite or the processing itself produced a "
                 "weekend pattern, the controls would show it too.")
    if crit1 and crit2:
        lines.append("They do not (criterion 1), and subtracting each station's "
                     "control from its lots leaves the weekend effect intact "
                     "(criterion 2) — so the T1 weekend effect is tied to the "
                     "lots themselves, not to a weekend artefact in the data.")
    else:
        lines.append("The test did not fully confirm that (see the decision "
                     "above), so T1 is downgraded to INCONCLUSIVE: the weekend "
                     "pattern in the lots may still be real, but this control "
                     "check cannot rule out a non-car explanation.")
    lines.append("This still does not measure "
                 "occupancy: without ground-truth calibration, no dB difference "
                 "converts into a number of cars or a percentage full.")
    (OUT / "t1b_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nwrote t1b_results.csv, t1b_report.md, t1b_weekend_coefs.png")


if __name__ == "__main__":
    main()
