"""Classify each window's PyPSA − SpineOpt cost difference.

Rules, applied in this order; the first that matches gives the class (`rule` column):

R1 exact             |diff_total| <= 0.01 € and every compared hourly series within 1e-3 in the window.
R2 degenerate        |diff_total| <= 0.01 € but some hourly series differ by more than 1e-3
                     (equal cost, different schedule; e.g. in-block delivery timing, slack split).
R3 solver_tolerance  either (a) |diff_total| <= gap_tolerance, the MIP-gap-implied tolerance of the window:
                         gap_tolerance = (gap_spine + gap_pypsa) × max(|spine_total|, |pypsa_total|)
                     gap_pypsa = max(the relative gap option, the achieved gap of the window);
                     gap_spine = mip_rel_gap from the input's db_mip_solver_options (HiGHS.jl entry),
                     else the PyPSA option. Covers time-limited windows (achieved gap) automatically.
                     or (b) the difference is entirely in the slack term (|diff_ex_slack| <= 0.01 €) and
                     |diff_slack| <= slack_tolerance = max node_slack_penalty × FEAS_TOL × window hours,
                     i.e. slack at the solver's primal feasibility tolerance (FEAS_TOL = 1e-6 MWh, Gurobi's
                     FeasibilityTol default).
R4 artefact_storage  CLAUDE.md artefact 2 (storage capacity falls between windows in SpineOpt):
                     PyPSA cheaper (diff_total < 0); unit investment, FOM and slack terms equal within
                     max(0.01 €, gap_tolerance); |diff variable+units_on| <= 0.05 % of SpineOpt's
                     variable+units_on + gap_tolerance; and evidence in the window: SpineOpt re-buys
                     storage (spine − PyPSA storage investment > 0.01 €), or PyPSA stores more than
                     SpineOpt's window peak while that peak is below SpineOpt's cumulative purchases.
R4b artefact_storage_timing   [rule_origin "post-hoc (2020_10op)"; applied to windows not matched by R1..R4]
                     artefact 2 knock-on in which the same unit capacity is bought in different windows.
                     A sequence of windows a..b qualifies only if ALL of these hold:
                     (1) before the shift (some window w < a) SpineOpt's storage capacity differs from
                         PyPSA's: cumulative SpineOpt storage purchases exceed PyPSA's by > 0.01 €, or
                         PyPSA stores more than SpineOpt's fallen capacity (storage_peak_excess > 0);
                     (2) per unit, cumulative units invested are equal (within 1e-6) at the horizon end,
                         and the only per-window difference is a shift: non-zero (> 1e-6) differences in
                         exactly two windows a < b with δ_a = −δ_b (within 1e-6), and all shifted units
                         share the same (a, b);
                     (3) FOM differences in windows a..b are explained by the shift: |diff_fom_w −
                         Σ_u fom_u × capacity_u × δ_u × hours_w| <= 0.01 € for a <= w < b, |diff_fom_b| <= 0.01 €;
                     (4) Σ_{w=a..b} diff_total <= 0.01 €.
                     PyPSA's per-window unit investments are needed for (2). If run_case does not supply
                     them, they are reconstructed from the dispatch (installed units = running maximum of
                     capacity-flow utilisation) and accepted only if they reproduce PyPSA's per-window
                     unit investment € (within 0.01 €) and final units (within 1e-6); otherwise R4b is not
                     applied. `shift_detail` records unit, from-window, to-window and amount.
R5 artefact_units    artefact 2 for units (unverified: units_invested_available is not exported).
                     Case-level evidence: SpineOpt's cumulative units_invested exceeds PyPSA's for some
                     unit. Window: either SpineOpt re-buys units (spine − PyPSA unit investment > 0.01 €)
                     with PyPSA cheaper, or PyPSA dearer by at most the FOM SpineOpt can skip on that
                     excess capacity (Σ fom × capacity × excess units × hours) with investments equal.
R6 unexplained       anything else.

`rule_origin` is "design (pilot)" for R1..R6 and "post-hoc (2020_10op)" for R4b.
`also_consistent_with` lists the later rules (R3..R5) that the window also satisfies, so an overlap
such as "within solver tolerance and also consistent with artefact_units" stays visible.
`max_diff_series` names the hourly series with the largest difference in the window.

For cases with slack (SpineOpt node slacks or PyPSA slack generators non-zero) every comparison is
also reported without the slack penalty term (*_ex_slack), and `class_ex_slack` applies the same rules
to the ex-slack difference.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .spine_input import SpineInput
from .spine_output import SpineOutput
from .units import unit_counts

TOL_EUR = 0.01
FLOW_TOL = 1e-3
DISPATCH_REL_TOL = 5e-4
FEAS_TOL = 1e-6            # MWh, primal feasibility tolerance (Gurobi FeasibilityTol default)


def spine_mip_gap(inp: SpineInput) -> tuple[float | None, str]:
    v = inp.model_par.get((inp.model_name, "db_mip_solver_options"))
    if v is None:
        return None, "db_mip_solver_options not in input"
    data = v.get("data", v) if isinstance(v, dict) else v
    if isinstance(data, str):
        data = json.loads(data)
    for solver, opts in data:
        if solver.lower().startswith("highs"):
            for k, val in (opts.get("data", []) if isinstance(opts, dict) else opts):
                if k == "mip_rel_gap":
                    return float(val), "db_mip_solver_options HiGHS.jl mip_rel_gap"
    return None, "no HiGHS.jl mip_rel_gap in db_mip_solver_options"


def _window_flow_diff(spine: SpineOutput, hourly: dict, w) -> tuple[float, str]:
    m, name = 0.0, ""
    for var, key in (("unit_flow", "unit_flows"), ("connection_flow", "connection_flows")):
        frame = hourly[key]
        for (o, nd, d) in frame.columns:
            if not spine.has(var, o, f"{d}_node", nd):
                continue
            s = spine.series(var, o, f"{d}_node", nd).reindex(frame.index)
            if var == "connection_flow" and s.isna().any():
                s = s.ffill()
            v = float((frame[(o, nd, d)].loc[w] - s.loc[w]).abs().max())
            if v > m:
                m, name = v, f"{var}/{o}/{d}/{nd}"
    for nd in hourly["node_states"].columns:
        s = spine.object_series("node_state", nd)
        if s is not None:
            v = float((hourly["node_states"][nd].loc[w] - s.loc[w]).abs().max())
            if v > m:
                m, name = v, f"node_state/{nd}"
    return m, name


def classify_windows(inp: SpineInput, spine: SpineOutput, per_window: pd.DataFrame, hourly: dict,
                     win_meta: list[dict], solver_gap: float | None, units_invested: dict,
                     unit_fom: dict, windows: list, specs: dict | None = None, segs=None,
                     unit_inv_per_window: pd.DataFrame | None = None) -> tuple[pd.DataFrame, dict]:
    nW = len(windows)
    gap_sp, gap_sp_src = spine_mip_gap(inp)
    gap_opt = solver_gap or 0.0
    if gap_sp is None:
        gap_sp, gap_sp_src = gap_opt, gap_sp_src + "; using the PyPSA gap option"
    NS = hourly["node_states"]

    # storage peak evidence (artefact 2, storage)
    peak_excess = pd.Series(0.0, index=range(1, nW + 1))
    for nd in NS.columns:
        s, si = spine.object_series("node_state", nd), spine.object_series("storages_invested", nd)
        if s is None or si is None:
            continue
        cum = spine.per_window(si).iloc[:nW].cumsum() * float(inp.nodes_df.loc[nd].node_state_cap)
        for i, w in enumerate(windows, 1):
            excess = float(NS[nd].loc[w].max() - s.loc[w].max())
            if excess > 1e-6 and s.loc[w].max() < cum.loc[i] - 1e-6:
                peak_excess.loc[i] = max(peak_excess.loc[i], excess)

    # unit evidence (artefact 2, units): SpineOpt cumulative units_invested above PyPSA's
    unit_excess = {}
    for u in inp.units:
        s = spine.object_series("units_invested", u)
        if s is not None:
            ex = float(spine.per_window(s).iloc[:nW].sum()) - float(units_invested.get(u, 0.0))
            if ex > 1e-6:
                unit_excess[u] = ex
    fom_skip_per_h = sum(unit_fom[u][0] * unit_fom[u][1] * ex for u, ex in unit_excess.items() if u in unit_fom)

    max_pen = float(np.nan_to_num(pd.to_numeric(inp.nodes_df.get("node_slack_penalty"), errors="coerce")).max())         if "node_slack_penalty" in inp.nodes_df else 0.0
    has_slack = bool(np.nan_to_num(per_window.get("spine_slack", pd.Series(0.0))).any() or
                     (per_window.pypsa_slack.abs() > 0).any())
    rows = []
    for i, w in enumerate(windows, 1):
        x = per_window.loc[i]
        wm = win_meta[i - 1]
        gap_py = max(gap_opt, wm.get("achieved_gap") or 0.0)
        tol_gap = (gap_sp + gap_py) * max(abs(x.spine_total), abs(x.pypsa_total))
        tol = max(TOL_EUR, tol_gap)
        flow_diff, flow_name = _window_flow_diff(spine, hourly, w)
        slack_tol = max_pen * FEAS_TOL * x.hours
        rebuy_st = max(0.0, x.spine_storage_investment - x.pypsa_storage_investment)
        rebuy_u = max(0.0, x.spine_unit_investment - x.pypsa_unit_investment)
        fom_bound = fom_skip_per_h * x.hours
        diff_slack = 0.0 if pd.isna(x.diff_slack) else x.diff_slack
        ev = dict(diff_total=x.diff_total, diff_slack=diff_slack, flow_diff=flow_diff, tol_gap=tol_gap, tol=tol,
                  slack_tol=slack_tol,
                  rebuy_st=rebuy_st, rebuy_u=rebuy_u, peak_excess=peak_excess.loc[i], fom_bound=fom_bound, x=x)
        (cls, rule), also = _classify(x.diff_total, ev, unit_excess)
        row = dict(window=i, start=w[0], spine_total=x.spine_total, pypsa_total=x.pypsa_total, diff_total=x.diff_total,
                   gap_spine=gap_sp, gap_pypsa=gap_py, gap_tolerance=tol_gap, slack_tolerance=slack_tol,
                   max_hourly_series_diff=flow_diff, max_diff_series=flow_name,
                   spine_storage_rebuy=rebuy_st, spine_unit_rebuy=rebuy_u, storage_peak_excess_MWh=peak_excess.loc[i],
                   fom_skip_bound=fom_bound if unit_excess else 0.0, **{"class": cls, "rule": rule},
                   rule_origin=RULE_ORIGIN[rule], also_consistent_with=",".join(also), shift_detail="",
                   termination_condition=wm.get("termination_condition"), window_status=wm.get("status"))
        if has_slack:
            sp_ex = x.spine_total - np.nan_to_num(x.spine_slack)
            py_ex = x.pypsa_total - x.pypsa_slack
            d_ex = py_ex - sp_ex
            row.update(spine_total_ex_slack=sp_ex, pypsa_total_ex_slack=py_ex, diff_ex_slack=d_ex,
                       rel_diff_ex_slack_pct=100 * d_ex / abs(sp_ex) if sp_ex else np.nan,
                       diff_variable_units_on=x.diff_variable_units_on, diff_unit_investment=x.diff_unit_investment,
                       diff_storage_investment=x.diff_storage_investment, diff_fom=x.diff_fom, diff_slack=diff_slack)
            ev_ex = {**ev, "diff_total": d_ex, "diff_slack": 0.0}
            (row["class_ex_slack"], row["rule_ex_slack"]), _ = _classify(d_ex, ev_ex, unit_excess)
        rows.append(row)
    df = pd.DataFrame(rows)
    r4b = {"applied": False, "reason": "specs/segs not supplied"}
    if specs is not None and segs is not None:
        uinv, r4b = unit_investment_table(inp, spine, hourly["unit_flows"], specs, segs, per_window, nW,
                                          exact=unit_inv_per_window)
        if r4b.get("valid"):
            r4b.update(_apply_r4b(df, per_window, uinv, unit_fom, peak_excess))
    notes = {"r4b": r4b, "feasibility_tolerance_MWh": FEAS_TOL, "max_node_slack_penalty": max_pen, "gap_spine": gap_sp, "gap_spine_source": gap_sp_src, "gap_pypsa_option": gap_opt,
             "has_slack": has_slack, "unit_excess_spine_vs_pypsa": unit_excess,
             "rules": "see benchmark/classify.py docstring (R1..R6, R4b)"}
    return df, notes


def _classify(d: float, ev: dict, unit_excess: dict) -> tuple[tuple[str, str], list[str]]:
    """First matching rule, plus the later rules (R3..R5) the window also satisfies."""
    x, tol = ev["x"], ev["tol"]
    if abs(d) <= TOL_EUR:
        return (("exact", "R1") if ev["flow_diff"] <= FLOW_TOL else ("degenerate", "R2")), []
    hits = []
    if abs(d) <= ev["tol_gap"] or (abs(d - ev["diff_slack"]) <= TOL_EUR and abs(ev["diff_slack"]) <= ev["slack_tol"]):
        hits.append(("solver_tolerance", "R3"))
    var_ok = abs(x.diff_variable_units_on) <= DISPATCH_REL_TOL * abs(x.spine_variable_units_on) + ev["tol_gap"]
    same_units = abs(x.diff_unit_investment) <= tol and abs(x.diff_fom) <= tol
    if (d < 0 and same_units and abs(ev["diff_slack"]) <= tol and var_ok
            and (ev["rebuy_st"] > TOL_EUR or ev["peak_excess"] > 1e-6)):
        hits.append(("artefact_storage", "R4"))
    if unit_excess and ((d < 0 and ev["rebuy_u"] > TOL_EUR) or
                        (0 < d <= ev["fom_bound"] + tol and abs(x.diff_unit_investment) <= tol
                         and abs(x.diff_storage_investment) <= tol)):
        hits.append(("artefact_units", "R5"))
    if not hits:
        return ("unexplained", "R6"), []
    return hits[0], [f"{c} ({r})" for c, r in hits[1:]]


RULE_ORIGIN = {"R1": "design (pilot)", "R2": "design (pilot)", "R3": "design (pilot)", "R4": "design (pilot)",
               "R4b": "post-hoc (2020_10op)", "R5": "design (pilot)", "R6": "design (pilot)"}
UNIT_TOL = 1e-6


def unit_investment_table(inp: SpineInput, spine: SpineOutput, UF: pd.DataFrame, specs: dict, segs,
                          per_window: pd.DataFrame, nW: int, exact: pd.DataFrame | None = None
                          ) -> tuple[pd.DataFrame, dict]:
    """Units invested per window and unit, SpineOpt (from its output) and PyPSA.

    PyPSA: `exact` if supplied (columns window, unit, pypsa_units), else reconstructed from the dispatch
    as the running maximum of capacity-flow utilisation, and validated against PyPSA's per-window unit
    investment € and final units. Only investable, non-committable units are listed.
    """
    from .model import is_committable                      # local import: keeps module import light

    rows, const_w1 = [], 0.0
    for u in inp.units:
        exist, mx = unit_counts(inp, u)
        inv = float(inp.unit_inv.loc[u].unit_investment_cost) if u in inp.unit_inv.index else 0.0
        if is_committable(inp, u):
            const_w1 += inv * (mx - exist)
            continue
        if mx <= exist:
            continue
        if u == segs.unit:
            key, cap = (u, segs.in_node, "from"), segs.specs[0]["cap"]
        else:
            sp_ = specs.get(u)
            if sp_ is None or sp_["kind"] != "link":
                continue
            key, cap = (u, *sp_["ref"]), sp_["cap"]
        sp = spine.object_series("units_invested", u)
        sp_w = spine.per_window(sp).iloc[:nW].to_numpy() if sp is not None else np.full(nW, np.nan)
        if exact is not None:
            py_w = (exact[exact.unit == u].set_index("window").pypsa_units
                    .reindex(range(1, nW + 1)).fillna(0.0).to_numpy())
        else:
            installed, py_w = exist, []
            for w in range(1, nW + 1):
                start = per_window.loc[w, "start"]
                n_h = int(round(per_window.loc[w, "hours"] / inp.hours_per_snapshot))
                idx = UF.index[UF.index >= pd.Timestamp(start)][:n_h]
                util = float(UF[key].loc[idx].abs().max()) / cap if key in UF else 0.0
                new = max(installed, util)
                py_w.append(new - installed)
                installed = new
            py_w = np.array(py_w)
        for i in range(nW):
            rows.append(dict(window=i + 1, unit=u, inv_cost=inv, spine_units=float(sp_w[i]),
                             pypsa_units=float(py_w[i]), delta=float(py_w[i] - sp_w[i])))
    t = pd.DataFrame(rows)
    info = {"source": "exact (run_case records)" if exact is not None else "reconstructed from dispatch"}
    if t.empty:
        info.update(valid=False, reason="no investable non-committable units")
        return t, info
    cost = t.assign(c=t.inv_cost * t.pypsa_units).groupby("window").c.sum()
    cost.loc[1] += const_w1
    err_eur = float((cost.values - per_window.pypsa_unit_investment.iloc[:nW].values).__abs__().max())
    info["max_eur_mismatch"] = err_eur
    info["valid"] = err_eur <= TOL_EUR
    if not info["valid"]:
        info["reason"] = f"reconstruction does not reproduce PyPSA's unit investment € (max mismatch {err_eur:.4f})"
    return t, info


def _apply_r4b(df: pd.DataFrame, per_window: pd.DataFrame, uinv: pd.DataFrame, unit_fom: dict,
               peak_excess: pd.Series) -> dict:
    """R4b post-pass on windows still classified unexplained (see the module docstring, conditions 1-4)."""
    shifts, reject = {}, {}
    for u, g in uinv.groupby("unit"):
        g = g.set_index("window")
        nz = g.index[g.delta.abs() > UNIT_TOL].tolist()
        if not nz:
            continue
        cum_ok = abs(g.delta.sum()) <= UNIT_TOL
        if len(nz) == 2 and abs(g.delta.loc[nz[0]] + g.delta.loc[nz[1]]) <= UNIT_TOL and cum_ok:
            shifts[u] = (nz[0], nz[1], float(g.delta.loc[nz[0]]))
        else:
            reject[u] = (f"differences in windows {nz} (cumulative {g.delta.sum():.3g} units) "
                         "are not a single shift")
    out = {"shifts": {u: {"from_window": a, "to_window": b, "pypsa_minus_spine_units_at_from": d}
                      for u, (a, b, d) in shifts.items()}, "rejected_units": reject, "sequences": []}
    if reject or not shifts:
        out["reason"] = "condition (2) fails" if reject else "no unit investment shift"
        return out
    pairs = {(a, b) for a, b, _ in shifts.values()}
    if len(pairs) != 1:
        out["reason"] = f"condition (2): shifted units do not share one (a, b): {sorted(pairs)}"
        return out
    (a, b), = pairs
    pw = per_window
    st_gap = float((pw.spine_storage_investment - pw.pypsa_storage_investment).loc[: a - 1].sum())
    c1 = bool(st_gap > TOL_EUR or (peak_excess.loc[: a - 1] > 1e-6).any())
    fom_ok, fom_detail = True, {}
    for w in range(a, b + 1):
        expected = (sum(unit_fom[u][0] * unit_fom[u][1] * d for u, (_, _, d) in shifts.items()) * pw.loc[w, "hours"]
                    if w < b else 0.0)
        fom_detail[w] = {"diff_fom": float(pw.loc[w, "diff_fom"]), "expected_from_shift": float(expected)}
        fom_ok = fom_ok and abs(pw.loc[w, "diff_fom"] - expected) <= TOL_EUR
    total = float(pw.diff_total.loc[a:b].sum())
    c4 = total <= TOL_EUR
    out["sequences"].append({"windows": [a, b], "c1_storage_differs_before": c1,
                             "c1_storage_purchase_gap_before_eur": st_gap,
                             "c1_peak_excess_before": bool((peak_excess.loc[: a - 1] > 1e-6).any()),
                             "c2_single_shift": True, "c3_fom_explained": bool(fom_ok), "c3_detail": fom_detail,
                             "c4_sum_diff_total": total, "c4_ok": bool(c4)})
    if not (c1 and fom_ok and c4):
        out["reason"] = "conditions not all met"
        return out
    detail = "; ".join(f"{u}: {d:+.6f} units W{a}->W{b}" for u, (_, _, d) in sorted(shifts.items()))
    hit = df.window.between(a, b) & (df["class"] == "unexplained")
    df.loc[hit, ["class", "rule", "rule_origin"]] = ["artefact_storage_timing", "R4b", RULE_ORIGIN["R4b"]]
    df.loc[df.window.between(a, b), "shift_detail"] = detail
    out["reclassified_windows"] = df.loc[hit, "window"].tolist()
    return out
