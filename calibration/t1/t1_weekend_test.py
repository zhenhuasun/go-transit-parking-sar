#!/usr/bin/env python3
"""
T1 — Pre-registered weekend-effect test (GO Transit parking, Sentinel-1 SAR).

Hypothesis (H1): mean VV is lower on weekends/holidays than on weekdays
within the same lot (fewer cars at ~19:10). Direction pre-specified:
weekend effect < 0.

Spec (verbatim, fixed before seeing results):
  Step 0  Inspect only: schema, local times ~19:00-19:20, holiday flags,
          scene counts (no VV means).
  Step 1  Months Jun-Aug only. Exclude Oakville South 2026 (construction).
          PRIMARY sample: years 2018, 2019, 2022-2026 (drop 2020-2021).
          Model on per-scene lot mean VV in dB.
  Step 2  a) Per lot OLS: VV_dB ~ weekend + C(relative_orbit) + C(year).
          b) Pooled: VV_dB ~ weekend + C(lot) + C(lot):C(relative_orbit)
             + C(lot):C(year); SE clustered by acquisition date.
          c) Permutation: shuffle weekend label among scenes within each
             (year x relative_orbit) stratum, label shared across lots
             within a scene; 10,000 permutations, seed 42; one-sided p
             (fraction <= observed).
  Step 3  S1 all years 2018-2026; S2 Tue-Thu vs Sunday+holidays only
          (drop Mon, Fri, Sat); S3 drop Clarkson North; S4 leave-one-lot-out
          pooled; S5 control areas (only if polygons/control-areas.geojson
          exists -- it does not, so S5 is skipped).
  Step 4  PASS iff ALL: (1) pooled coef < 0 with clustered two-sided
          p < 0.01; (2) permutation one-sided p < 0.01; (3) >= 5 of 6 lots
          have a negative weekend coefficient (Oakville South 2018-2025
          only); (4) if S5 ran, no control area shows a negative weekend
          effect with p < 0.05. Exception: if S2 passes but the primary
          fails, report "INCONCLUSIVE - weekend contrast too weak at 19:10"
          and do not call it a PASS.

Outputs (this directory): t1_results.csv, t1_report.md,
t1_per_lot_weekend_coefs.png. This script is the single reproducible
artifact; fixed seed 42. Dependencies: numpy, pandas, matplotlib only
(matching repo requirements.txt). OLS / cluster-robust SE / t p-values
are implemented with numpy + a continued-fraction incomplete-beta
function (no statsmodels/scipy needed).

Note on the outcome variable: the input CSV's mean_VV_dB is the mean of
per-pixel dB values for the scene (see quick-vv-check-2018-2026.py).
No cross-scene averaging of VV is performed anywhere in this test
(the regression uses per-scene values; the report shows coefficients
only), so the spec's "average in linear power, then convert to dB"
rule for averages does not apply to any number in this test.
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
CSV = REPO_ROOT / "quick-vv-check-2018-2026" / "vv-by-lot-scene-2018-2026.csv"
CONTROL = REPO_ROOT / "polygons" / "control-areas.geojson"
SEED = 42
N_PERM = 10_000
PRIMARY_YEARS = [2018, 2019, 2022, 2023, 2024, 2025, 2026]
LOTS = ["oakville-main", "oakville-south", "clarkson-main",
        "clarkson-north", "bronte-main", "bronte-south"]


def stop(msg):
    print(f"STOP: {msg}", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------- t dist
def _betacf(a, b, x):
    """Continued fraction for the incomplete beta function (NR betacf)."""
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
    """Regularized incomplete beta I_x(a, b)."""
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
    x = df / (df + t * t)
    return betainc_reg(df / 2.0, 0.5, x)


def t_crit_975(df):
    lo, hi = 0.0, 50.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        # CDF(mid) = 1 - p_two_sided(mid)/2 ; want 0.975
        cdf = 1.0 - t_pvalue_two_sided(mid, df) / 2.0
        if cdf < 0.975:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- OLS
def ols(X, y):
    """Return beta, residuals, rank, (X'X)^-1."""
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta
    return beta, resid, XtX_inv


def coef_ci_p(beta, se, df):
    crit = t_crit_975(df)
    p = t_pvalue_two_sided(beta / se, df)
    return beta - crit * se, beta + crit * se, p


def df_to_md(df):
    """Render a DataFrame as a GitHub-flavoured markdown table (no tabulate)."""
    cols = [""] + [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |",
             "|" + "---|" * len(cols)]
    for idx, row in df.iterrows():
        label = " / ".join(str(v) for v in idx) if isinstance(idx, tuple) else str(idx)
        vals = [label] + [str(v) for v in row]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------- holidays
def civic_holiday(year):
    """First Monday of August (Ontario Civic Holiday)."""
    d = pd.Timestamp(year=year, month=8, day=1)
    return d + pd.Timedelta(days=(7 - d.day_of_week) % 7)


def is_holiday(local_date):
    y = local_date.year
    july1 = pd.Timestamp(year=y, month=7, day=1)
    if local_date == july1.date():
        return True
    if july1.day_of_week == 6 and local_date == (july1 + pd.Timedelta(days=1)).date():
        return True  # Canada Day observed (Jul 1 was a Sunday)
    return local_date == civic_holiday(y).date()


# ---------------------------------------------------------------- step 0
def step0(df):
    print("=== STEP 0: schema ===")
    print("columns:", list(df.columns))
    print(df.head(5).to_string(index=False))
    required = {"datetime_utc": "acquisition datetime", "lot_id": "lot id",
                "mean_VV_dB": "VV", "relative_orbit": "relative orbit",
                "platform": "platform"}
    for col, label in required.items():
        if col not in df.columns:
            stop(f"missing required column: {col} ({label})")
    print("VV column: mean_VV_dB (dB — mean of per-pixel dB values)")
    print("relative_orbit values:", sorted(df["relative_orbit"].unique()))
    print("platform values:", sorted(df["platform"].unique()))

    dt_utc = pd.to_datetime(df["datetime_utc"], utc=True)
    dt_local = dt_utc.dt.tz_convert("America/Toronto")
    df["local_date"] = dt_local.dt.date
    df["local_time"] = dt_local.dt.strftime("%H:%M:%S")
    df["dow"] = dt_local.dt.day_of_week  # Mon=0 ... Sun=6
    df["year"] = dt_local.dt.year
    df["month"] = dt_local.dt.month
    times = dt_local.dt.hour * 60 + dt_local.dt.minute
    print(f"local time range: {df['local_time'].min()} - {df['local_time'].max()}")
    if not ((times >= 19 * 60) & (times <= 19 * 60 + 20)).all():
        stop("not all summer acquisition times fall in 19:00-19:20 local")
    print("all summer times within 19:00-19:20 local: OK")
    if not df["month"].isin([6, 7, 8]).all():
        stop("months outside Jun-Aug present")
    print("months: Jun-Aug only: OK")

    df["is_holiday"] = df["local_date"].apply(is_holiday)
    df["weekend"] = ((df["dow"] >= 5) | df["is_holiday"]).astype(int)
    df["weekend_label"] = np.where(df["weekend"] == 1, "weekend/holiday", "weekday")
    df["scene_id_check"] = df["scene_id"]
    n_scenes = df["scene_id"].nunique()
    print(f"rows: {len(df)}, unique scenes: {n_scenes}, "
          f"rows per scene: {len(df) / n_scenes:.1f}")

    counts = (df.drop_duplicates("scene_id")
                .groupby(["year", "weekend_label"]).size().unstack(fill_value=0))
    print("\nscenes per year x weekday/weekend (all lots share the same scenes):")
    print(counts.to_string())
    per_lot = (df.groupby(["lot_id", "year", "weekend_label"]).size()
                 .unstack(fill_value=0))
    print("\nscenes per lot x year x weekday/weekend:")
    print(per_lot.to_string())
    per_orbit = df.drop_duplicates("scene_id").groupby("relative_orbit").size()
    print("\nscenes per relative orbit:")
    print(per_orbit.to_string())
    per_orbit_year = (df.drop_duplicates("scene_id")
                        .groupby(["relative_orbit", "year"]).size().unstack(fill_value=0))
    print("\nscenes per relative orbit x year:")
    print(per_orbit_year.to_string())
    return df


# ---------------------------------------------------------------- design
def build_pooled_design(d, years):
    """weekend + C(lot) + C(lot):C(orbit) + C(lot):C(year)."""
    lots = sorted(d["lot_id"].unique())
    n = len(d)
    cols, names = [], []
    w = d["weekend"].to_numpy(float)
    cols.append(w); names.append("weekend")
    for lot in lots:
        ind = (d["lot_id"] == lot).to_numpy(float)
        cols.append(ind); names.append(f"lot[{lot}]")
        orb = ind * (d["relative_orbit"] == 77).to_numpy(float)
        if 0 < orb.sum() < ind.sum():
            cols.append(orb); names.append(f"lot[{lot}]:orbit77")
        yrs_present = sorted(d.loc[d["lot_id"] == lot, "year"].unique())
        for yr in yrs_present[1:]:
            cols.append(ind * (d["year"] == yr).to_numpy(float))
            names.append(f"lot[{lot}]:year{yr}")
    X = np.column_stack(cols)
    assert np.linalg.matrix_rank(X) == X.shape[1], "pooled design not full rank"
    return X, names


def cluster_se(X, resid, clusters):
    """CR1 cluster-robust variance for the first coefficient (weekend)."""
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


def fit_pooled(d, years):
    """Pooled model; returns dict with coef, cluster SE, CI, p, n, clusters."""
    X, _ = build_pooled_design(d, years)
    y = d["mean_VV_dB"].to_numpy(float)
    beta, resid, _ = ols(X, y)
    se, G = cluster_se(X, resid, d["local_date"].to_numpy())
    lo, hi, p = coef_ci_p(beta[0], se, G - 1)
    return {"coef": beta[0], "se": se, "ci_lo": lo, "ci_hi": hi, "p": p,
            "n": len(d), "n_clusters": G, "df": G - 1}


def fit_per_lot(d, years):
    """Per-lot OLS: VV_dB ~ weekend + C(orbit) + C(year), classical SE."""
    out = {}
    for lot in LOTS:
        dl = d[d["lot_id"] == lot]
        if len(dl) == 0:
            continue
        yrs = sorted(dl["year"].unique())
        cols = [dl["weekend"].to_numpy(float),
                np.ones(len(dl)),
                (dl["relative_orbit"] == 77).to_numpy(float)]
        for yr in yrs[1:]:
            cols.append((dl["year"] == yr).to_numpy(float))
        X = np.column_stack(cols)
        y = dl["mean_VV_dB"].to_numpy(float)
        beta, resid, XtX_inv = ols(X, y)
        n, K = X.shape
        s2 = float(resid @ resid) / (n - K)
        se = math.sqrt(max(s2 * XtX_inv[0, 0], 0.0))
        lo, hi, p = coef_ci_p(beta[0], se, n - K)
        out[lot] = {"coef": beta[0], "se": se, "ci_lo": lo, "ci_hi": hi,
                    "p": p, "n": n, "years": yrs}
    return out


def permutation_p(d, years, observed, rng):
    """Shuffle weekend label among scenes within (year x orbit) strata."""
    X, _ = build_pooled_design(d, years)
    Z = X[:, 1:]  # controls (everything except weekend)
    y = d["mean_VV_dB"].to_numpy(float)
    # FWL: residualize y on controls once
    beta_z, _, _ = ols(Z, y)
    y_res = y - Z @ beta_z
    # scene table: one row per scene_id
    scenes = (d.drop_duplicates("scene_id")
                [["scene_id", "year", "relative_orbit", "weekend"]]
                .reset_index(drop=True))
    strata = scenes.groupby(["year", "relative_orbit"]).indices
    row_of_scene = {s: i for i, s in enumerate(scenes["scene_id"])}
    scene_idx_per_row = d["scene_id"].map(row_of_scene).to_numpy()
    # residual maker applied via projection: w_res = w - Z (Z'Z)^-1 Z' w
    ZtZ_inv = np.linalg.inv(Z.T @ Z)
    P = Z @ ZtZ_inv @ Z.T  # n x n projection (n ~ 513, fine)
    w0 = d["weekend"].to_numpy(float)
    w0_res = w0 - P @ w0
    denom0 = float(w0_res @ w0_res)
    obs_fwl = float(w0_res @ y_res) / denom0
    assert abs(obs_fwl - observed) < 1e-8, "FWL != full OLS coefficient"
    labels = scenes["weekend"].to_numpy()
    n_scenes = len(scenes)
    W = np.tile(labels, (N_PERM, 1)).astype(float)
    for _, idx in strata.items():
        idx = np.asarray(sorted(idx))
        for r in range(N_PERM):
            W[r, idx] = rng.permutation(labels[idx])
    W_row = W[:, scene_idx_per_row]          # (n_perm, n_rows)
    W_res = W_row - W_row @ P.T              # residualize each permuted label
    num = W_res @ y_res
    den = np.einsum("ij,ij->i", W_res, W_res)
    coefs = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
    p_one = float(np.mean(coefs <= observed))
    return p_one, coefs


# ---------------------------------------------------------------- main
def main():
    rng = np.random.default_rng(SEED)
    df = pd.read_csv(CSV)
    df = step0(df)

    # Step 1 rules
    base = df[df["month"].isin([6, 7, 8])].copy()
    base = base[~((base["lot_id"] == "oakville-south") & (base["year"] == 2026))]
    primary = base[base["year"].isin(PRIMARY_YEARS)].copy()
    print(f"\nprimary sample: {len(primary)} rows, "
          f"{primary['scene_id'].nunique()} scenes, "
          f"weekend rows: {int(primary['weekend'].sum())}")

    results = []

    def record(analysis, model, lot, r, perm_p=None, note=""):
        results.append({"analysis": analysis, "model": model, "lot": lot,
                        "coef_dB": r["coef"], "se": r["se"],
                        "ci_lo": r["ci_lo"], "ci_hi": r["ci_hi"],
                        "p_two_sided": r["p"],
                        "perm_p_one_sided": perm_p if perm_p is not None else "",
                        "n": r["n"],
                        "n_clusters": r.get("n_clusters", ""),
                        "note": note})

    # ---- Step 2: primary
    per_lot = fit_per_lot(primary, PRIMARY_YEARS)
    for lot, r in per_lot.items():
        record("primary", "per-lot OLS", lot, r)
    pooled = fit_pooled(primary, PRIMARY_YEARS)
    perm_p, _ = permutation_p(primary, PRIMARY_YEARS, pooled["coef"], rng)
    record("primary", "pooled clustered OLS", "pooled", pooled, perm_p=perm_p)
    print(f"\nPRIMARY pooled: coef={pooled['coef']:.3f} dB, "
          f"95% CI [{pooled['ci_lo']:.3f}, {pooled['ci_hi']:.3f}], "
          f"p={pooled['p']:.4g}, perm p={perm_p:.4g}, n={pooled['n']}")

    # ---- Step 3 sensitivities
    # S1: all years
    s1 = base.copy()
    s1_years = sorted(s1["year"].unique())
    for lot, r in fit_per_lot(s1, s1_years).items():
        record("S1_all_years", "per-lot OLS", lot, r)
    s1p = fit_pooled(s1, s1_years)
    s1_perm, _ = permutation_p(s1, s1_years, s1p["coef"], rng)
    record("S1_all_years", "pooled clustered OLS", "pooled", s1p, perm_p=s1_perm)

    # S2: Tue-Thu vs Sunday + holidays only
    s2 = primary[((primary["dow"] >= 1) & (primary["dow"] <= 3))
                 | ((primary["dow"] == 6) | primary["is_holiday"])].copy()
    for lot, r in fit_per_lot(s2, PRIMARY_YEARS).items():
        record("S2_tue-thu_vs_sun-hol", "per-lot OLS", lot, r)
    s2p = fit_pooled(s2, PRIMARY_YEARS)
    s2_perm, _ = permutation_p(s2, PRIMARY_YEARS, s2p["coef"], rng)
    record("S2_tue-thu_vs_sun-hol", "pooled clustered OLS", "pooled", s2p,
           perm_p=s2_perm)

    # S3: drop Clarkson North
    s3 = primary[primary["lot_id"] != "clarkson-north"].copy()
    for lot, r in fit_per_lot(s3, PRIMARY_YEARS).items():
        record("S3_drop_clarkson_north", "per-lot OLS", lot, r)
    s3p = fit_pooled(s3, PRIMARY_YEARS)
    s3_perm, _ = permutation_p(s3, PRIMARY_YEARS, s3p["coef"], rng)
    record("S3_drop_clarkson_north", "pooled clustered OLS", "pooled", s3p,
           perm_p=s3_perm)

    # S4: leave-one-lot-out pooled
    for lot in LOTS:
        s4 = primary[primary["lot_id"] != lot].copy()
        r = fit_pooled(s4, PRIMARY_YEARS)
        record("S4_lolo", "pooled clustered OLS", f"drop {lot}", r)

    # S5: control areas
    s5_ran = CONTROL.exists()
    print(f"\nS5 control areas: {'exists' if s5_ran else 'ABSENT — skipped'}")

    # ---- Step 4: decision
    n_neg = sum(1 for r in per_lot.values() if r["coef"] < 0)
    crit1 = pooled["coef"] < 0 and pooled["p"] < 0.01
    crit2 = perm_p < 0.01
    crit3 = n_neg >= 5
    crit4 = True if not s5_ran else None  # S5 not run: criterion vacuous
    passed = bool(crit1 and crit2 and crit3 and (crit4 is not False))
    s2_passes = bool(s2p["coef"] < 0 and s2p["p"] < 0.01 and s2_perm < 0.01)
    if passed:
        decision = "PASS"
    elif (not passed) and s2_passes:
        decision = "INCONCLUSIVE – weekend contrast too weak at 19:10"
    else:
        decision = "FAIL"
    print(f"\nDECISION: {decision} (crit1={crit1}, crit2={crit2}, "
          f"crit3={crit3} [{n_neg}/6 negative], crit4={'n/a (S5 not run)'}, "
          f"S2 passes={s2_passes})")

    # ---- outputs
    res = pd.DataFrame(results)
    res.to_csv(OUT / "t1_results.csv", index=False)

    # plot: per-lot weekend coefficients, primary per-lot models
    fig, ax = plt.subplots(figsize=(8, 4.6))
    lots_sorted = sorted(per_lot, key=lambda l: per_lot[l]["coef"])
    ypos = np.arange(len(lots_sorted))
    coefs = [per_lot[l]["coef"] for l in lots_sorted]
    lo = [per_lot[l]["coef"] - per_lot[l]["ci_lo"] for l in lots_sorted]
    hi = [per_lot[l]["ci_hi"] - per_lot[l]["coef"] for l in lots_sorted]
    ax.errorbar(coefs, ypos, xerr=[lo, hi], fmt="o", capsize=4,
                color="#1f77b4")
    ax.axvline(0, color="grey", lw=1)
    ax.set_yticks(ypos)
    ax.set_yticklabels([f"{l} (n={per_lot[l]['n']})" for l in lots_sorted])
    ax.set_xlabel("Weekend coefficient (dB), primary per-lot OLS")
    ax.set_title("Weekend effect on VV (dB), 2018–2019 + 2022–2026 summers")
    fig.tight_layout()
    fig.savefig(OUT / "t1_per_lot_weekend_coefs.png", dpi=150)
    plt.close(fig)

    # report
    counts_tbl = (df.drop_duplicates("scene_id")
                    .groupby(["year", "weekend_label"]).size()
                    .unstack(fill_value=0))
    per_lot_tbl = (df.groupby(["lot_id", "year", "weekend_label"]).size()
                     .unstack(fill_value=0))
    per_orbit_tbl = (df.drop_duplicates("scene_id")
                       .groupby(["relative_orbit", "year"]).size()
                       .unstack(fill_value=0))
    tick = lambda b: "✅" if b else "❌"
    lines = []
    lines.append("# T1 — Weekend-effect test (pre-registered)")
    lines.append("")
    lines.append("**Hypothesis (H1):** mean VV is lower on weekends/holidays than on "
                 "weekdays within the same lot (fewer cars at ~19:10). "
                 "Direction pre-specified: weekend effect < 0.")
    lines.append("")
    lines.append(f"**Decision: {decision}**")
    lines.append("")
    lines.append("## Step 0 — Inspection (no modelling)")
    lines.append("")
    lines.append(f"Input: `quick-vv-check-2018-2026/vv-by-lot-scene-2018-2026.csv` — "
                 f"{len(df)} rows, {df['scene_id'].nunique()} scenes, "
                 "6 lots, Jun–Aug 2018–2026.")
    lines.append("")
    lines.append("Columns: `lot_id, lot_name, spaces, scene_id, date, datetime_utc, "
                 "orbit_state, relative_orbit, platform, n_pixels, mean_VV_dB, "
                 "median_VV_dB, std_VV_dB`. All required columns present: "
                 "acquisition datetime (`datetime_utc`), lot id (`lot_id`), "
                 "VV (`mean_VV_dB`, in dB), relative orbit (`relative_orbit`), "
                 "platform (`platform`).")
    lines.append("")
    lines.append(f"All acquisition times fall {df['local_time'].min()}–"
                 f"{df['local_time'].max()} local (America/Toronto) — within "
                 "19:00–19:20 as specified.")
    lines.append("")
    lines.append("Holiday flag: Canada Day (Jul 1; if Sunday, also Jul 2 "
                 "observed) and Civic Holiday (first Monday of August), treated "
                 "as weekend. Weekend = Saturday, Sunday, or holiday.")
    lines.append("")
    lines.append("Scenes per year × weekday/weekend (all lots share the same scenes):")
    lines.append("")
    lines.append(df_to_md(counts_tbl))
    lines.append("")
    lines.append("Scenes per lot × year × weekday/weekend:")
    lines.append("")
    lines.append(df_to_md(per_lot_tbl))
    lines.append("")
    lines.append("Scenes per relative orbit × year:")
    lines.append("")
    lines.append(df_to_md(per_orbit_tbl))
    lines.append("")
    lines.append("No VV means are reported in this section, per spec.")
    lines.append("")
    lines.append("## Primary results (years 2018, 2019, 2022–2026; "
                 "Oakville South 2026 excluded)")
    lines.append("")
    lines.append("Per-lot OLS: `VV_dB ~ weekend + C(relative_orbit) + C(year)` "
                 "(classical SE). Pooled: `VV_dB ~ weekend + C(lot) + "
                 "C(lot):C(relative_orbit) + C(lot):C(year)`, SE clustered by "
                 "acquisition date (CR1, t with G−1 df). Permutation: 10,000 "
                 "permutations, seed 42, weekend label shuffled among scenes "
                 "within each (year × relative orbit) stratum, shared across "
                 "lots within a scene.")
    lines.append("")
    lines.append("| Lot | Weekend coef (dB) | 95% CI | p | n |")
    lines.append("|---|---|---|---|---|")
    for lot in LOTS:
        r = per_lot.get(lot)
        if r:
            lines.append(f"| {lot} | {r['coef']:.3f} | "
                         f"[{r['ci_lo']:.3f}, {r['ci_hi']:.3f}] | {r['p']:.4g} | {r['n']} |")
    lines.append("")
    lines.append(f"**Pooled:** weekend coef **{pooled['coef']:.3f} dB**, "
                 f"95% CI [{pooled['ci_lo']:.3f}, {pooled['ci_hi']:.3f}], "
                 f"clustered two-sided p = {pooled['p']:.4g}, "
                 f"n = {pooled['n']} rows, {pooled['n_clusters']} date clusters. "
                 f"Permutation one-sided p = {perm_p:.4g}.")
    lines.append("")
    lines.append("![Per-lot weekend coefficients with 95% CIs]"
                 "(t1_per_lot_weekend_coefs.png)")
    lines.append("")
    lines.append("## Sensitivity")
    lines.append("")
    lines.append("| Analysis | Pooled coef (dB) | 95% CI | Clustered p | Perm p | n |")
    lines.append("|---|---|---|---|---|---|")
    for label, r, pp in [("S1 — all years 2018–2026", s1p, s1_perm),
                         ("S2 — Tue–Thu vs Sun+holidays", s2p, s2_perm),
                         ("S3 — drop Clarkson North", s3p, s3_perm)]:
        lines.append(f"| {label} | {r['coef']:.3f} | "
                     f"[{r['ci_lo']:.3f}, {r['ci_hi']:.3f}] | {r['p']:.4g} | "
                     f"{pp:.4g} | {r['n']} |")
    lines.append("")
    lines.append("S4 — leave-one-lot-out pooled estimates:")
    lines.append("")
    lines.append("| Dropped lot | Pooled coef (dB) | 95% CI | Clustered p | n |")
    lines.append("|---|---|---|---|---|")
    for row in res[(res["analysis"] == "S4_lolo")].itertuples():
        lines.append(f"| {row.lot.replace('drop ', '')} | {row.coef_dB:.3f} | "
                     f"[{row.ci_lo:.3f}, {row.ci_hi:.3f}] | "
                     f"{row.p_two_sided:.4g} | {row.n} |")
    lines.append("")
    lines.append("S5 — **not run**: `polygons/control-areas.geojson` does not "
                 "exist, so the negative control was skipped as specified.")
    lines.append("")
    lines.append("Full per-model coefficients (including per-lot results for "
                 "S1–S3) are in `t1_results.csv`.")
    lines.append("")
    lines.append("## Decision against each criterion")
    lines.append("")
    lines.append(f"1. {tick(crit1)} Pooled weekend coefficient < 0 with clustered "
                 f"two-sided p < 0.01 — coef {pooled['coef']:.3f} dB, "
                 f"p = {pooled['p']:.4g}.")
    lines.append(f"2. {tick(crit2)} Permutation one-sided p < 0.01 — p = {perm_p:.4g}.")
    lines.append(f"3. {tick(crit3)} ≥ 5 of 6 lots have a negative weekend "
                 f"coefficient — {n_neg}/6 negative "
                 f"(Oakville South uses 2018–2025 only).")
    lines.append(f"4. {tick(True)} S5 not run (no control file), so criterion 4 "
                 "is vacuous — no control area could show an effect.")
    lines.append("")
    lines.append(f"**Decision: {decision}**")
    if decision.startswith("INCONCLUSIVE"):
        lines.append("")
        lines.append("S2 passed (pooled coef < 0, clustered p < 0.01, "
                     "permutation p < 0.01) while the primary did not, so per "
                     "the pre-registered exception the result is INCONCLUSIVE "
                     "rather than a FAIL.")
    lines.append("")
    lines.append("## Deviations from the spec")
    lines.append("")
    lines.append("None. Two interpretation notes (not deviations):")
    lines.append("")
    lines.append("- The spec's S2 exception does not define what 'S2 passes' "
                 "means; it was operationalised as criteria 1–2 applied to the "
                 "S2 sample (pooled coef < 0, clustered two-sided p < 0.01, "
                 "permutation one-sided p < 0.01).")
    lines.append("- The spec's linear-averaging rule applies 'where averages are "
                 "needed'; this test performs no cross-scene averaging of VV "
                 "(the regression uses per-scene `mean_VV_dB` as supplied, and "
                 "the report shows coefficients only), so the rule does not "
                 "bite. Per-lot OLS uses classical (homoskedastic) SE, the "
                 "standard default, as the spec does not specify a robust SE "
                 "for the per-lot models.")
    lines.append("")
    lines.append("## Reproducibility")
    lines.append("")
    lines.append("- Script: `t1_weekend_test.py` (this file), seed 42, "
                 "10,000 permutations. Rerun: "
                 "`python3 t1_weekend_test.py` from the repo root "
                 "(uses only numpy, pandas, matplotlib).")
    lines.append("- Local working copy is not a git checkout. Remote HEAD of "
                 "`zhenhuasun/go-transit-parking-sar` at run time: "
                 "`7025234d93cc14fece51b8a4b31ecba844390097` "
                 "(verified: that commit touched only `docs/session-prompt.md`). "
                 "`polygons/` was last modified in commit "
                 "`eccc1fcb062b05b9659ea91f3f3f34cb1fd996de` "
                 "(English-only cleanup) and is unchanged since.")
    lines.append("- `polygons/`, existing CSVs and existing scripts were not edited; "
                 "all new outputs are in `calibration/t1/`.")
    lines.append("")
    lines.append("## Plain-language reading")
    lines.append("")
    lines.append("This test asks whether the radar brightness of a parking lot at "
                 "about 19:10 is systematically lower on weekends and holidays "
                 "than on weekdays, after accounting for which orbit the satellite "
                 "was on and which year it was. A lower weekend value would be "
                 "consistent with fewer cars in the evening, but it is a test of "
                 "sensitivity to evening car presence, not a measurement of "
                 "occupancy: without ground-truth calibration, no dB difference "
                 "can be converted into a number of cars or a percentage full.")
    (OUT / "t1_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nwrote t1_results.csv, t1_report.md, "
          "t1_per_lot_weekend_coefs.png")


if __name__ == "__main__":
    main()
