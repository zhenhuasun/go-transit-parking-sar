#!/usr/bin/env python3
"""T1b round-4 per-roof DIAGNOSTIC (not part of the decision).

Fits the same per-area OLS as C1 (VV_dB ~ weekend + C(orbit) + C(year),
classical SE) to each of the 3 Bronte roofs separately, using
t1b_control_vv_r4_parts.csv, and appends the table to t1b_report.md.

Purpose: confirm no single roof carries a weekend effect hidden inside
the pooled control. Diagnostic only — it cannot change either criterion.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t1b_weekend_test import (PRIMARY_YEARS, add_time_flags,  # noqa: E402
                              fit_per_group)

OUT = Path(__file__).resolve().parent
PARTS_CSV = OUT / "t1b_control_vv_r4_parts.csv"
REPORT = OUT / "t1b_report.md"


def main():
    parts = pd.read_csv(PARTS_CSV)
    parts = add_time_flags(parts)
    parts_p = parts[parts["year"].isin(PRIMARY_YEARS)].copy()
    print(f"per-roof diagnostic: {len(parts_p)} rows, "
          f"{parts_p['scene_id'].nunique()} scenes")
    res = fit_per_group(parts_p, "control_name")
    lines = []
    lines.append("")
    lines.append("## Per-roof diagnostic (NOT part of the decision)")
    lines.append("")
    lines.append("Each roof fitted separately with the C1 model "
                 "(`VV_dB ~ weekend + C(relative_orbit) + C(year)`, "
                 "classical SE; primary years 2018, 2019, 2022–2026). A "
                 "roof with a significant weekend effect here would mean "
                 "the pooled control hides a bad roof — the diagnostic is "
                 "reported so that can be seen, but it does not affect "
                 "either criterion.")
    lines.append("")
    lines.append("| Roof | Weekend coef (dB) | 95% CI | p | n |")
    lines.append("|---|---|---|---|---|")
    for g in sorted(res):
        r = res[g]
        lines.append(f"| {g} | {r['coef']:.3f} | [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}] | {r['p']:.4g} | {r['n']} |")
    lines.append("")
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))
    for g in sorted(res):
        r = res[g]
        print(f"{g}: coef={r['coef']:.3f} dB, p={r['p']:.4g}, n={r['n']}")
    print("appended per-roof diagnostic to t1b_report.md")


if __name__ == "__main__":
    main()
