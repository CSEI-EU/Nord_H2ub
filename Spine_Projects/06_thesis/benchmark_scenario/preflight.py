"""Preflight check of the paper_energy_2024 input workbooks (nothing is solved).

Every .xlsx in paper_energy_2024_inputs/ is parsed with the replica's own parser
(benchmark.spine_input, plus the unit -> port translation in benchmark.units) and its structure is
compared against paper_energy_2024_input_base_10op.xlsx, the only case the replica has been
validated on.

Output: preflight_report.csv (one row per file) next to this script, plus a printed summary of
the files that need special handling before replica.py can be run on them.

Run:  python preflight.py          (env var INPUT_DIR overrides the input folder)
"""

from __future__ import annotations

import calendar
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

from benchmark.spine_input import DATA_START_ROW as REPLICA_DATA_START
from benchmark.spine_input import SpineInput, parse_sheets, read_sheets, table
from benchmark.units import flow_coefficients, operating_segments

HERE = Path(__file__).resolve().parent
INPUT_DIR = Path(os.environ.get(
    "INPUT_DIR", HERE.parents[1] / "01_input_data" / "02_input_prepared" / "paper_energy_2024_inputs"))
BASE_FILE = "paper_energy_2024_input_base_10op.xlsx"
REPORT_CSV = HERE / "preflight_report.csv"
IDENTICAL_COL = "structurally identical to base (only values differ)"

# Names that the pre-refactor replica.py referenced literally (sections 3 and 8-10). The benchmark
# package no longer hardcodes them; the check is kept so the report stays comparable.
HARDCODED_CHECKS = {
    "node_block['ch3oh_demand'] (daily-block check)": lambda P: "ch3oh_demand" in P.node_block,
    "storage node ch3oh_st": lambda P: "ch3oh_st" in P.state_nodes,
    "flow pl_ch3oh_demand from ch3oh": lambda P: ("ch3oh", "from") in P.flows_of.get("pl_ch3oh_demand", []),
    "flow electrolyzer from power (chart)": lambda P: ("power", "from") in P.flows_of.get("electrolyzer", []),
    "flow pl_wholesale from power_wholesale (chart)":
        lambda P: ("power_wholesale", "from") in P.flows_of.get("pl_wholesale", []),
}


def unit_translation_errors(P: SpineInput) -> tuple[list[str], np.ndarray | None]:
    """benchmark.units translation without building a network. Returns (errors, marginal segment efficiencies)."""
    errors, seg_eff = [], None
    for u in P.units:
        if u == P.op_unit:
            continue
        try:
            flow_coefficients(P, u)
        except Exception as e:                      # noqa: BLE001 - report, don't stop
            errors.append(f"{type(e).__name__}: {e}")
    try:
        seg_eff = operating_segments(P).eff
    except Exception as e:                          # noqa: BLE001
        errors.append(f"{type(e).__name__}: {e}")
    return errors, seg_eff


# --------------------------------------------------------------------------------------------------
# Structure extraction
# --------------------------------------------------------------------------------------------------
def first_data_row(df: pd.DataFrame, sheet: str) -> int | None:
    for i, v in enumerate(df.iloc[:, 0]):
        if sheet in ("Operating_points", "Variable_Eff"):
            if re.fullmatch(r"\d+(\.0)?", str(v)):
                return i
        elif re.match(r"^\d{4}-\d{2}-\d{2}", str(v)):
            return i
    return None


def positional_layout(X: dict) -> dict:
    """Per positional sheet: data start row, column-0 labels above it, and column header tuples."""
    out = {}
    for sh in REPLICA_DATA_START:
        if sh not in X:
            continue
        df = X[sh]
        start = first_data_row(df, sh)
        hdr_rows = start if start is not None else min(len(df), 6)
        out[sh] = dict(
            start=start,
            labels=tuple(str(v) for v in df.iloc[:hdr_rows, 0]),
            columns={tuple(str(v) for v in df.iloc[:hdr_rows, c]) for c in range(1, df.shape[1])},
        )
    return out


def structure(X: dict, P: SpineInput) -> dict:
    """Value-free description of a parsed workbook: everything that must match for 'only values differ'."""
    S: dict = {}
    defs = P.defs
    objects = {f"{c}:{o}" for o, c in zip(defs.Object_name, defs.Category)}
    mc = table(X, "Model_components")
    objects |= {f"{c}:{o}" for c, o in zip(mc.iloc[:, 0], mc.iloc[:, 1])}
    ved = table(X, "Variable_Eff_Definition")
    objects |= {f"{c}:{o}" for c, o in zip(ved.iloc[:, 0], ved.iloc[:, 1])}
    S["objects"] = objects

    rel = {f"{o}|{nd}|{d}" for o, fl in P.flows_of.items() for nd, d in fl}
    rel |= {f"node_node:{o}|{k1[0]}|{k2[0]}" for o, lst in P.ratios.items() for k1, k2, _ in lst}
    rel |= {f"node__temporal_block:{nd}|{blk}" for nd, blk in P.node_block_name.items()}
    mr = table(X, "Model_relations")
    rel |= {f"{r.iloc[0]}:{r.iloc[3]}|{r.iloc[4]}" for _, r in mr.iterrows()}
    ve = X["Variable_Eff"]
    rel |= {f"{ve.iloc[0, c]}:{ve.iloc[1, c]}|{ve.iloc[2, c]}|{ve.iloc[3, c]}" for c in range(1, ve.shape[1])}
    S["relationships"] = rel

    pa: set[tuple[str, str]] = set()
    for sh in ("Definition_parameters", "Definition_parameters_duration"):
        pa |= {(r.Object_name, r.Parameter) for _, r in table(X, sh).iterrows()}
    for sh in ("Unit_Inv_Parameters", "Connection_Inv_Parameters", "Storage_Inv_Parameters", "Nodes"):
        t = table(X, sh)
        for _, r in t.iterrows():
            pa |= {(r.Object_name, col) for col in t.columns if col not in ("Object_name", "Category") and not pd.isna(r[col])}
    pa |= {(f"{o}|{nd}|{d}", p) for (o, nd, d), ps in P.flow_par.items() for p in ps}
    pa |= {(f"{r.Object_name}|{r.Node1}|{r.Node2}", r.Parameter) for _, r in table(X, "Object__node_node").iterrows()}
    pa |= {(o, p) for (o, p) in P.model_par}
    pa |= {(o, p) for (o, p) in P.ts_unit}
    pa |= {(f"{c}|{nd}|{d}", "connection_flow_cost") for (c, nd, d) in P.flow_cost}
    pa |= {(nd, p) for (nd, p) in P.storage_ts}
    pa |= {(f"{k[0]}|{k[1]}|{k[2]}", "unit_flow_coefficient") for k in P.uc_coef}
    pa.add((f"{P.op_unit}|{P.op_node}", "operating_points"))
    S["param_assign"] = {f"{o}.{p}" for o, p in pa}
    S["param_names"] = {p for _, p in pa}

    S["time"] = dict(model_start=str(P.t0), model_end=str(P.t1), resolution=str(P.res),
                     roll_forward=str(P.roll), n_hours=len(P.snapshots), n_windows=len(P.windows),
                     temporal_blocks=temporal_blocks(P), node_blocks=node_blocks(P))
    S["series_index"] = {k: (str(i.min()), str(i.max()), len(i)) for k, i in
                         (("Time_series", P.ts_index), ("Energy_prices", P.ep_index),
                          ("Time_series_storage", P.tss_index))}
    S["n_op"] = len(P.op_points)
    S["state_ts"] = {f"{nd}.{p}@{t:%Y-%m-%d %H:%M}" for (nd, p), s in P.storage_ts.items() for t in s.index}
    return S


def temporal_blocks(P: SpineInput) -> str:
    return "; ".join(f"{o}={v['data']}" for (o, p), v in P.model_par.items() if p == "resolution")


def node_blocks(P: SpineInput) -> str:
    return "; ".join(f"{nd}->{blk}" for nd, blk in P.node_block_name.items())


# --------------------------------------------------------------------------------------------------
# Reporting helpers
# --------------------------------------------------------------------------------------------------
def fmt_diff(a: set, base: set) -> str:
    return "; ".join([f"+{x}" for x in sorted(a - base)] + [f"-{x}" for x in sorted(base - a)])


def ranges(ints: list[int]) -> str:
    if not ints:
        return "none"
    out, start = [], ints[0]
    for prev, cur in zip(ints, ints[1:] + [None]):
        if cur != prev + 1:
            out.append(f"{start}" if start == prev else f"{start}-{prev}")
            start = cur
    return ",".join(out)


def state_report(P: SpineInput) -> tuple[str, str, bool | None]:
    """node_state_min / fix_node_state timestamps, mapped onto rolling-window ends."""
    ends = {w[-1]: i + 1 for i, w in enumerate(P.windows)}
    final = P.snapshots[-1]
    smin_parts, fix_parts, final_hit = [], [], None
    for (nd, p), s in P.storage_ts.items():
        if p == "node_state_min":
            nz = s[s != 0]
            at_end = sorted(ends[t] for t in nz.index if t in ends)
            other = [f"{t:%m-%d %H:%M}" for t in nz.index if t not in ends]
            vals = sorted({round(float(v), 4) for v in nz.values})
            final_hit = bool(final in nz.index) if final_hit is None else (final_hit or final in nz.index)
            smin_parts.append(f"{nd}: {len(nz)} nonzero {vals}, at ends of windows {ranges(at_end)}"
                              + (f", other times {other}" if other else "")
                              + f"; reset to 0 at {len(s) - len(nz)} timestamps")
        elif p == "fix_node_state":
            fix_parts.append(", ".join(f"{nd}@{t:%Y-%m-%d %H:%M}={v:g}" + (" (before model_start)" if t < P.t0 else "")
                                       for t, v in s.items()))
    return " | ".join(smin_parts) or "none", " | ".join(fix_parts) or "none", final_hit


def check_file(path: Path, base: dict | None) -> tuple[dict, dict | None]:
    case = path.stem.replace("paper_energy_2024_input_", "")
    row: dict = {"file": path.name, "case": case, "flag_OLD": "_OLD" in path.stem}
    reasons: list[str] = []
    if row["flag_OLD"]:
        reasons.append("stale _OLD duplicate: exclude from runs")

    X = read_sheets(path)
    layout = positional_layout(X)
    row["sheets_diff"] = fmt_diff(set(X), base["sheets"]) if base else ""
    row["data_start_rows"] = "; ".join(f"{sh}={v['start']}" for sh, v in layout.items())
    for sh, expect in REPLICA_DATA_START.items():
        got = layout.get(sh, {}).get("start", "missing sheet")
        if got != expect:
            reasons.append(f"row offset: {sh} data starts at row {got}, replica.py reads from row {expect}")
    if base:
        lay = []
        for sh in REPLICA_DATA_START:
            a, b = layout.get(sh), base["layout"].get(sh)
            if a is None or b is None:
                lay.append(f"{sh}: {'missing' if a is None else 'new'}")
                continue
            if a["start"] != b["start"]:
                lay.append(f"{sh}: data start {b['start']}->{a['start']}")
            if a["labels"] != b["labels"]:
                lay.append(f"{sh}: column-0 header labels {b['labels']}->{a['labels']}")
            cd = fmt_diff({" / ".join(c) for c in a["columns"]}, {" / ".join(c) for c in b["columns"]})
            if cd:
                lay.append(f"{sh} columns: {cd}")
        row["header_layout_diff"] = " | ".join(lay)
        if row["sheets_diff"]:
            reasons.append(f"sheets differ ({row['sheets_diff']})")
        if any(" columns: " not in s for s in lay):
            reasons.append("header layout differs from base (see header_layout_diff)")
        col_diffs = [s for s in lay if " columns: " in s]
        if col_diffs:
            reasons.append("time-series/price columns differ from base: " + " | ".join(col_diffs))

    try:
        P = parse_sheets(X, path)
    except Exception as e:                          # noqa: BLE001
        row["parse_error"] = f"{type(e).__name__}: {e}"
        reasons.append(f"replica.py parsing fails: {row['parse_error']}")
        row[IDENTICAL_COL] = False
        row["needs_special_handling"] = True
        row["reasons"] = " | ".join(reasons)
        return row, None
    row["parse_error"] = ""
    S = structure(X, P)
    S["sheets"], S["layout"] = set(X), layout

    # --- topology and parameters
    if base:
        row["objects_diff"] = fmt_diff(S["objects"], base["objects"])
        row["relationships_diff"] = fmt_diff(S["relationships"], base["relationships"])
        row["param_names_diff"] = fmt_diff(S["param_names"], base["param_names"])
        row["param_assignments_diff"] = fmt_diff(S["param_assign"], base["param_assign"])
        if row["objects_diff"] or row["relationships_diff"]:
            reasons.append("topology differs from base (objects/relationships)")
        added = sorted(S["param_names"] - base["param_names"])
        if added:
            reasons.append(f"new parameter names not seen in base (replica may ignore them): {added}")
        if base["param_names"] - S["param_names"]:
            reasons.append(f"parameter names removed: {sorted(base['param_names'] - S['param_names'])}")
        elif row["param_assignments_diff"]:
            reasons.append("parameters assigned to different objects than in base")

    # --- time
    T0, T1, SN, WIN = P.t0, P.t1, P.snapshots, P.win
    years = sorted({T0.year, T1.year})
    leap = any(calendar.isleap(y) for y in years)
    has_feb29 = bool(((SN.month == 2) & (SN.day == 29)).any())
    last_h = len(P.windows[-1]) * P.res / pd.Timedelta("1h")
    row.update(model_start=str(T0), model_end=str(T1), n_hours=len(SN), leap_year=leap or has_feb29,
               roll_forward=f"{P.roll / pd.Timedelta('1h'):g}h", n_windows=len(P.windows), last_window_h=last_h,
               short_final_window=bool(len(P.windows[-1]) < WIN),
               temporal_blocks=S["time"]["temporal_blocks"], node_blocks=S["time"]["node_blocks"],
               series_years=",".join(str(y) for y in sorted(set(P.ts_index.dt.year) | set(P.ep_index.dt.year))))
    m = re.search(r"(?<!\d)(20\d\d)(?!\d)", case)
    row["case_year_vs_data_year"] = (f"case {m.group(1)} but timestamps {row['series_years']}"
                                     if m and m.group(1) not in row["series_years"].split(",") else "")
    if row["leap_year"]:
        reasons.append(f"leap year in model horizon ({years}, {len(SN)} h)")
    elif len(SN) != 8760:
        reasons.append(f"{len(SN)} hours instead of 8760")
    if row["short_final_window"]:
        reasons.append(f"final window is {last_h:g} h < {WIN} h")
    if base and S["time"] != base["time"]:
        reasons.append("model/temporal settings differ: " + ", ".join(
            f"{k} {base['time'][k]}->{v}" for k, v in S["time"].items() if base["time"][k] != v))

    gaps = [f"{k[0]}.{k[1]}: {int(s.isna().sum())} NaN" for k, s in P.ts_unit.items() if s.isna().any()]
    gaps += [f"{'|'.join(k)}.connection_flow_cost: {int(s.isna().sum())} NaN" for k, s in P.flow_cost.items()
             if isinstance(s, pd.Series) and s.isna().any()]
    row["series_coverage_issues"] = "; ".join(gaps)
    if gaps:
        reasons.append("time series do not cover all snapshots (NaN after reindex)")
    if base and S["series_index"] != base["series_index"]:
        reasons.append("time-series index differs from base: " + str(S["series_index"]))

    # --- electrolyzer operating points
    op = P.op_points
    errors, seg_eff = unit_translation_errors(P)
    row["n_op_points"] = len(op)
    row["op_points"] = ", ".join(f"{v:.4f}" for v in op)
    row["op_points_ok"] = bool(len(op) and np.all(np.diff(np.r_[0.0, op]) > 0) and np.isclose(op[-1], 1.0))
    if not row["op_points_ok"]:
        reasons.append("operating points not strictly increasing in (0, 1] or not ending at 1")
    if seg_eff is not None:
        row["marginal_eff"] = ", ".join(f"{v:.5f}" for v in seg_eff)
        inc = [k for k in range(1, len(seg_eff)) if seg_eff[k] > seg_eff[k - 1] + 1e-12]
        row["marginal_eff_non_increasing"] = not inc
        if inc:
            reasons.append(f"electrolyzer marginal efficiency increases at segment(s) {inc}: "
                           "LP segment formulation is not exact (needs ordered-segment binaries)")
    else:
        row["marginal_eff"], row["marginal_eff_non_increasing"] = "", None
    row["unit_translation_errors"] = " | ".join(errors)
    if errors:
        reasons.append("replica unit->port translation fails: " + " | ".join(errors))

    # --- assumptions in replica.py that are value-dependent
    for t, col in ((P.unit_inv, "unit_investment_variable_type"), (P.stor_inv, "storage_investment_variable_type")):
        bad = [o for o, v in t[col].items() if not pd.isna(v) and "continuous" not in str(v)] if col in t else []
        if bad:
            reasons.append(f"non-continuous {col} for {bad} (replica assumes continuous investment)")
    missing = [name for name, ok in HARDCODED_CHECKS.items() if not ok(P)]
    row["hardcoded_names_missing"] = "; ".join(missing)
    if missing:
        reasons.append(f"names hard-coded in replica.py are absent: {missing}")

    # --- storage state timestamps
    row["node_state_min"], row["fix_node_state"], final_hit = state_report(P)
    row["node_state_min_at_final_hour"] = final_hit
    if final_hit:
        reasons.append("node_state_min already set at the final hour: check FINAL_WINDOW_STATE_MIN")
    if base and S["state_ts"] != base["state_ts"]:
        reasons.append("node_state_min / fix_node_state timestamps differ from base: "
                       + fmt_diff(S["state_ts"], base["state_ts"]))

    # --- identity
    if base:
        identical = (not row["sheets_diff"] and not row["header_layout_diff"] and not row["objects_diff"]
                     and not row["relationships_diff"] and not row["param_assignments_diff"]
                     and S["time"] == base["time"] and S["series_index"] == base["series_index"]
                     and S["n_op"] == base["n_op"] and S["state_ts"] == base["state_ts"])
        row[IDENTICAL_COL] = identical
    else:
        row[IDENTICAL_COL] = True
    row["needs_special_handling"] = bool(reasons)
    row["reasons"] = " | ".join(reasons)
    return row, S


def main() -> None:
    files = sorted(INPUT_DIR.glob("*.xlsx"))
    files = [f for f in files if not f.name.startswith("~$")]
    base_path = INPUT_DIR / BASE_FILE
    assert base_path in files, f"{BASE_FILE} not found in {INPUT_DIR}"
    print(f"preflight: {len(files)} workbooks in {INPUT_DIR}")

    base_row, base = check_file(base_path, None)
    assert base is not None, f"base file does not parse: {base_row['parse_error']}"
    rows = []
    for f in files:
        row, _ = check_file(f, base)
        rows.append(row)
        print(f"  {row['case']:<32} identical={str(row[IDENTICAL_COL]):<5}  special={row['needs_special_handling']}")

    cols = ["file", "case", "flag_OLD", IDENTICAL_COL, "needs_special_handling", "reasons", "parse_error",
            "sheets_diff", "header_layout_diff", "data_start_rows", "objects_diff", "relationships_diff",
            "param_names_diff", "param_assignments_diff", "model_start", "model_end", "n_hours", "leap_year",
            "roll_forward", "n_windows", "last_window_h", "short_final_window", "temporal_blocks", "node_blocks",
            "series_years", "case_year_vs_data_year", "series_coverage_issues", "n_op_points", "op_points",
            "op_points_ok", "marginal_eff", "marginal_eff_non_increasing", "unit_translation_errors",
            "hardcoded_names_missing", "node_state_min", "node_state_min_at_final_hour", "fix_node_state"]
    report = pd.DataFrame(rows).reindex(columns=cols)
    report.to_csv(REPORT_CSV, index=False, encoding="utf-8-sig")

    # ------------------------------------------------------------------ summary
    print(f"\nreport written to {REPORT_CSV}")
    ident = report[report[IDENTICAL_COL] == True]               # noqa: E712
    print(f"\n{len(ident)}/{len(report)} files are structurally identical to base_10op (only values differ).")
    diff_ok = report[(report[IDENTICAL_COL] != True) & ~report.needs_special_handling]   # noqa: E712
    if len(diff_ok):
        print("\nStructurally different but no special handling needed (replica handles these generically):")
        for _, r in diff_ok.iterrows():
            what = [f"{r.n_op_points} operating points" if r.n_op_points != base["n_op"] else "",
                    "header rows" if r.header_layout_diff else ""]
            print(f"  {r.case}: {', '.join(w for w in what if w) or 'see report'}")
    special = report[report.needs_special_handling]
    print(f"\n{len(special)} files need special handling:")
    for _, r in special.iterrows():
        print(f"  {r.case}{'  [OLD]' if r.flag_OLD else ''}")
        for reason in r.reasons.split(" | "):
            print(f"      - {reason}")
    years = report[report.case_year_vs_data_year.fillna("") != ""]
    if len(years):
        print("\nNote: year cases whose timestamps are not in the case year (prices/profiles mapped onto "
              "another calendar):")
        for _, r in years.iterrows():
            print(f"  {r.case}: {r.case_year_vs_data_year}")


if __name__ == "__main__":
    main()
