"""Data-driven comparison of the PyPSA replica against the SpineOpt output.

Everything iterates over the objects present in the network / parsed input and in the SpineOpt
output; anything missing on either side is skipped and listed in the returned notes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .accounting import COST_TERMS
from .model import block_ends
from .spine_input import SpineInput
from .spine_output import SpineOutput

# SpineOpt objective_* outputs that make up each cost term (summed over the ones present).
SPINE_OBJECTIVE_TERMS = {
    "unit_investment": ["objective_unit_investment_costs"],
    "storage_investment": ["objective_storage_investment_costs"],
    "connection_investment": ["objective_connection_investment_costs"],
    "fom": ["objective_fixed_om_costs"],
    "variable": ["objective_variable_om_costs", "objective_fuel_costs", "objective_connection_flow_costs",
                 "objective_taxes"],
    "units_on": ["objective_units_on_costs"],
    "slack": ["objective_objective_penalties"],
}
INVESTMENT_TERMS = ["unit_investment", "storage_investment", "connection_investment"]


def _corr(s: pd.Series, p: pd.Series) -> float:
    return np.corrcoef(s, p)[0, 1] if s.std() > 1e-9 and p.std() > 1e-9 else np.nan


def spine_fom(spine: SpineOutput, unit_fom: dict, nW: int, hours: pd.Series) -> tuple[pd.Series, list]:
    """SpineOpt FOM per window from SpineOpt's own installed capacity, with the replica's formula:
    fom_cost × unit_capacity × (existing units + cumulative units_invested) × hours."""
    total = pd.Series(0.0, index=range(1, nW + 1))
    missing = []
    for u, (fom, cap, exist) in unit_fom.items():
        if fom == 0:
            continue
        s = spine.object_series("units_invested", u)
        if s is None:
            missing.append(u)
            continue
        installed = exist + spine.per_window(s).iloc[:nW].cumsum()
        total += fom * cap * installed.values * hours.values
    return (total if not missing else pd.Series(np.nan, index=total.index)), missing


def spine_slack(spine: SpineOutput, inp: SpineInput, windows: list) -> pd.Series | None:
    """Σ node_slack_penalty × (node_slack_pos + node_slack_neg) × hours per window, or None if not reported."""
    cols = [(v, o, d, nd) for (v, o, d, nd) in spine.data.columns if v in ("node_slack_pos", "node_slack_neg")]
    if not cols:
        return None
    H = inp.hours_per_snapshot
    out = []
    for w in windows:
        c = 0.0
        for col in cols:
            nd = col[1]
            pen = float(np.nan_to_num(inp.nodes_df.loc[nd].node_slack_penalty)) if nd in inp.nodes_df.index else 0.0
            v = spine.data[col].reindex(w).fillna(0.0).to_numpy()
            if nd in inp.node_block:
                # coarser block: one rate per block, reported at the block start (blocks restart each window)
                step = int(inp.node_block[nd] / inp.res)
                weight = np.zeros(len(w))
                for i in range(0, len(w), step):
                    weight[i] = min(step, len(w) - i)
            else:
                weight = np.ones(len(w))
            c += pen * float((v * weight).sum()) * H
        out.append(c)
    return pd.Series(out, index=range(1, len(windows) + 1))


def per_window_table(costs: pd.DataFrame, spine: SpineOutput, inp: SpineInput, windows: list,
                     unit_fom: dict | None = None) -> tuple[pd.DataFrame, dict]:
    nW = len(windows)
    df = pd.DataFrame({"window": range(1, nW + 1), "start": [w[0] for w in windows],
                       "hours": [len(w) * inp.hours_per_snapshot for w in windows]}).set_index("window")
    for t in COST_TERMS:
        df[f"pypsa_{t}"] = costs[t].values
    df["pypsa_connection_investment"] = 0.0
    df["pypsa_total"] = costs["total"].values
    df["pypsa_operating"] = df[[f"pypsa_{t}" for t in ("fom", "variable", "units_on", "slack")]].sum(axis=1)

    found, missing = {}, {}
    for t, names in SPINE_OBJECTIVE_TERMS.items():
        parts = [(v, spine.object_series(v, inp.model_name)) for v in names]
        parts = [(v, s) for v, s in parts if s is not None]
        if parts:
            df[f"spine_{t}"] = sum(spine.per_window(s).iloc[:nW].values for _, s in parts)
            found[t] = [v for v, _ in parts]
        else:
            df[f"spine_{t}"] = np.nan
            missing[t] = names
    tot = spine.object_series("total_costs", inp.model_name)
    df["spine_total"] = spine.per_window(tot).iloc[:nW].values if tot is not None else np.nan
    inv = [f"spine_{t}" for t in INVESTMENT_TERMS if t in found]
    df["spine_operating"] = df["spine_total"] - df[inv].sum(axis=1)

    derived = {}
    if "fom" not in found and unit_fom is not None:
        fom, fom_missing = spine_fom(spine, unit_fom, nW, df["hours"])
        df["spine_fom"] = fom.values
        derived["fom"] = ("fom_cost × unit_capacity × (existing + cumulative SpineOpt units_invested) × hours"
                          + (f"; NaN: units_invested missing for {fom_missing}" if fom_missing else ""))
    if "slack" not in found:
        sl = spine_slack(spine, inp, windows)
        if sl is not None:
            df["spine_slack"] = sl.values
            derived["slack"] = "node_slack_penalty × (node_slack_pos + node_slack_neg) × hours"
    rest = df["spine_operating"] - df["spine_fom"] - df["spine_slack"].fillna(0.0)
    df["spine_variable_units_on"] = (df["spine_variable"] + df["spine_units_on"]
                                     if {"variable", "units_on"} <= set(found) else rest)
    df["pypsa_variable_units_on"] = df["pypsa_variable"] + df["pypsa_units_on"]
    derived["variable_units_on"] = "spine_total − investment terms − spine_fom − spine_slack (slack 0 if not reported)"
    for t in ["unit_investment", "storage_investment", "fom", "variable_units_on", "slack"]:
        df[f"diff_{t}"] = df[f"pypsa_{t}"] - df[f"spine_{t}"]
    df["diff_total"] = df["pypsa_total"] - df["spine_total"]
    df["rel_diff_total_pct"] = 100 * df["diff_total"] / df["spine_total"].abs()
    mapped = {v for vs in SPINE_OBJECTIVE_TERMS.values() for v in vs}
    unmapped = [v for v in spine.variables() if v.startswith("objective_") and v not in mapped]
    notes = {"spine_objective_terms_found": found, "spine_objective_terms_missing": missing,
             "spine_objective_terms_unmapped": unmapped, "spine_terms_derived": derived,
             "spine_operating": "spine_total minus the investment terms found (fom + variable + units_on + slack)",
             "total_costs_present": tot is not None}
    return df, notes


def investments_table(inp: SpineInput, meta: dict, spine: SpineOutput, nW: int,
                      units_invested: dict, storages_invested: dict) -> tuple[pd.DataFrame, list]:
    rows, skipped = [], []
    for u in inp.units:
        s = spine.object_series("units_invested", u)
        if s is None:
            skipped.append(f"units_invested/{u}: not in SpineOpt output")
            continue
        rows.append(("units_invested", u, spine.per_window(s).iloc[:nW].sum(), units_invested.get(u, 0.0)))
    for nd in meta["stores"]:
        s = spine.object_series("storages_invested", nd)
        if s is None:
            skipped.append(f"storages_invested/{nd}: not in SpineOpt output")
            continue
        rows.append(("storages_invested (cum.)", nd, spine.per_window(s).iloc[:nW].sum(), storages_invested[nd]))
    df = pd.DataFrame(rows, columns=["variable", "object", "spine", "pypsa"])
    df["diff"] = df.pypsa - df.spine
    return df, skipped


def flows_table(spine: SpineOutput, UF: pd.DataFrame, CF: pd.DataFrame, NS: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    idx = UF.index
    rows, skipped = [], []
    for var, frame in (("unit_flow", UF), ("connection_flow", CF)):
        for (o, nd, d) in frame.columns:
            if not spine.has(var, o, f"{d}_node", nd):
                skipped.append(f"{var}/{o}/{d}_node/{nd}: not in SpineOpt output")
                continue
            s = spine.series(var, o, f"{d}_node", nd).loc[idx]
            p = frame[(o, nd, d)]
            if var == "connection_flow" and s.isna().any():   # coarser-block variable: forward-fill block values
                s = s.ffill()
            rows.append((var, o, nd, d, s.sum(), p.sum(), (p - s).abs().max(), _corr(s, p)))
    for nd in NS.columns:
        s = spine.object_series("node_state", nd)
        if s is None:
            skipped.append(f"node_state/{nd}: not in SpineOpt output")
            continue
        s, p = s.loc[idx], NS[nd]
        rows.append(("node_state", nd, "", "", s.sum(), p.sum(), (p - s).abs().max(), _corr(s, p)))
    for var in ("unit_flow", "connection_flow"):
        for (o, d, nd) in spine.entries(var):
            frame = UF if var == "unit_flow" else CF
            if (o, nd, d.removesuffix("_node")) not in frame.columns:
                skipped.append(f"{var}/{o}/{d}/{nd}: in SpineOpt output but not in the network")
    df = pd.DataFrame(rows, columns=["variable", "object", "node", "direction", "spine_sum", "pypsa_sum",
                                     "max_abs_hourly_diff", "hourly_corr"])
    base = df.spine_sum.abs().where(df.spine_sum.abs() > 1e-6)
    df["sum_rel_diff_pct"] = 100 * (df.pypsa_sum - df.spine_sum) / base
    return df, skipped


def blocks_table(inp: SpineInput, windows: list, spine: SpineOutput, CF: pd.DataFrame,
                 NS: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """Per coarser temporal block: deliveries into the block node and storage levels at block ends."""
    idx = CF.index
    rows, skipped = [], []
    for B, blk in inp.node_block.items():
        ends = block_ends(windows, inp.res, blk)
        ends = ends[ends <= idx[-1]]
        grp = np.searchsorted(ends.values, idx.values)          # block id per hour
        for c in inp.conns:
            if (B, "to") not in inp.flows_of.get(c, []):
                continue
            for f, d in inp.flows_of[c]:
                if d != "from" or f == B:
                    continue
                if (c, f, "from") not in CF.columns or not spine.has("connection_flow", c, "from_node", f):
                    skipped.append(f"block deliveries {c}/{f}: missing in network or SpineOpt output")
                    continue
                sp = spine.series("connection_flow", c, "from_node", f).loc[idx].groupby(grp).sum()
                py = CF[(c, f, "from")].groupby(grp).sum()
                for i, t in enumerate(ends):
                    rows.append((B, i + 1, t, "delivery", c, f, sp.iloc[i], py.iloc[i]))
        for nd in NS.columns:
            s = spine.object_series("node_state", nd)
            if s is None:
                continue
            for i, t in enumerate(ends):
                rows.append((B, i + 1, t, "node_state", nd, "", s.loc[t], NS[nd].loc[t]))
    df = pd.DataFrame(rows, columns=["block_node", "block", "block_end", "kind", "object", "node", "spine", "pypsa"])
    df["diff"] = df.pypsa - df.spine
    return df, skipped
