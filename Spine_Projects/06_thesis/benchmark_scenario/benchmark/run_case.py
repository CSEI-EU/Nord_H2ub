"""Run one benchmark case: parse the SpineOpt input, build and solve the PyPSA replica with the same
rolling horizon, and compare it against the SpineOpt output.

    from benchmark.run_case import run_case
    result = run_case(input_xlsx, spine_output_xlsx, solver="gurobi", out_dir="results")

CLI:
    python -m benchmark.run_case --input <input.xlsx> --output <Output_exported.xlsx> --solver gurobi
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import platform
import time
import warnings
from dataclasses import replace
from importlib import metadata
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from .accounting import connection_flows, investments, node_states, solved_index, unit_flows, window_costs
from .compare import blocks_table, flows_table, investments_table, per_window_table
from .model import build_network, check_supported, make_extra_functionality, node_state_min
from .results import CaseResult
from .settings import GAP_OPTION, Settings
from .spine_input import read_input
from .spine_output import read_output
from .units import operating_segments, unit_specs

PACKAGES = ["pypsa", "linopy", "pandas", "numpy", "xarray", "gurobipy", "highspy"]


def case_name(input_xlsx: Path) -> str:
    stem = Path(input_xlsx).stem
    return stem.split("_input_", 1)[1] if "_input_" in stem else stem


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def package_versions() -> dict:
    out = {"python": platform.python_version()}
    for p in PACKAGES:
        try:
            out[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            out[p] = None
    return out


def model_size(m) -> dict:
    def count(v):
        try:
            return int(v.nvars)
        except Exception:                       # noqa: BLE001
            return None
    return {"variables": int(m.nvars), "constraints": int(m.ncons),
            "binaries": count(m.binaries), "integers": count(m.integers)}


def achieved_gap(m, solver: str) -> float | None:
    sm = getattr(m, "solver_model", None)
    try:
        if solver == "gurobi":
            return float(sm.MIPGap)
        if solver == "highs":
            return float(sm.getInfo().mip_gap)
    except Exception:                           # noqa: BLE001 - LP or solver without the attribute
        return None
    return None


def unit_ports_table(specs: dict, segs) -> pd.DataFrame:
    return pd.DataFrame(
        [(u, s["kind"], s.get("bus0", (s.get("bus"),))[0], [p[0] for p in s.get("ports", [])[1:]],
          np.round(s.get("eff", []), 5).tolist(), s.get("P0", s["cap"]), round(s.get("vom", 0), 4)) for u, s in specs.items()]
        + [(f"{segs.unit}[{k}]", "link", s["bus0"][0], [p[0] for p in s["ports"][1:]], np.round(s["eff"], 5).tolist(),
            segs.width[k] * s["P0"], round(s["vom"], 4)) for k, s in enumerate(segs.specs)],
        columns=["unit", "kind", "bus0", "other ports", "efficiencies", "max p0 [bus0 units]", "marginal €/unit p0"],
    )


def run_case(input_xlsx, spine_output_xlsx, solver: str = "gurobi", solver_options: dict | None = None,
             settings: Settings | None = None, out_dir="benchmark_results", case: str | None = None,
             log: Callable[[str], None] | None = None, write: bool = True) -> CaseResult:
    """Run one case. `solver_options` are merged over the settings' / default options.

    Raises UnsupportedStructure if the input uses a structure the replica cannot reproduce exactly.
    """
    import linopy

    settings = settings or Settings()
    if solver_options is not None:
        settings = replace(settings, solver_options={**(settings.solver_options or {}), **solver_options})
    opts = settings.resolved_solver_options(solver)
    if solver not in linopy.available_solvers:
        raise RuntimeError(f"solver {solver!r} is not available (linopy finds {linopy.available_solvers})")
    say = log or (lambda *_: None)
    t_case = time.time()

    input_xlsx, spine_output_xlsx = Path(input_xlsx), Path(spine_output_xlsx)
    case = case or case_name(input_xlsx)
    inp = read_input(input_xlsx)
    spine = read_output(spine_output_xlsx)

    # ----- translate and check
    segs = operating_segments(inp)
    specs = unit_specs(inp)
    support = check_supported(inp, specs, segs)
    windows = inp.windows[: settings.n_windows]
    smin, smin_notes = node_state_min(inp, settings)
    n, meta = build_network(inp, specs, segs, windows, settings)
    ef = make_extra_functionality(meta, segs.unit, segs.width, smin)
    ports = unit_ports_table(specs, segs)

    say(f"{len(inp.units)} units, {len(inp.nodes)} nodes, {len(inp.conns)} connections; "
        f"{len(inp.op_points)} operating points on {inp.op_unit}/{inp.op_node}")
    say(f"{len(inp.snapshots)} snapshots, {len(windows)} windows of {inp.win} h; "
        f"daily-block nodes: {list(inp.node_block)}")
    say(f"connection_flow_cost keys: {list(inp.flow_cost)}")
    say(str(ports))
    say(str(n))

    # ----- rolling-horizon solve
    # Each window is optimised with n.optimize(snapshots=window). PyPSA carries ramping and commitment
    # history from previous windows; store levels and installed capacity are carried by setting
    # e_initial and p_nom_min/e_nom_min before the next window (as in SpineOpt: investments are fixed
    # history, further increments are allowed and paid for in the window they are made).
    records, win_meta = [], []
    t_start = time.time()
    for w_i, sns in enumerate(windows):
        t = time.time()
        lk_before = n.links.p_nom_min.copy()
        st_before = n.stores.e_nom_min.copy()
        status, cond = n.optimize(sns, solver_name=solver, solver_options=opts,
                                  extra_functionality=ef,
                                  assign_all_duals=False, compute_infeasibilities=False, log_to_console=False,
                                  io_api="direct", progress=False, include_objective_constant=False)
        secs = time.time() - t
        info = {"window": w_i + 1, "start": sns[0], "snapshots": len(sns), "status": status,
                "termination_condition": str(cond), "solve_seconds": secs, "objective": float(n.objective),
                "achieved_gap": achieved_gap(n.model, solver), **model_size(n.model)}
        win_meta.append(info)
        if status != "ok":
            raise RuntimeError(f"{case}: window {w_i + 1} ({sns[0]}) ended with {status}/{cond}")
        # carry state & capacity into next window
        n.stores.e_initial = n.stores_t.e.loc[sns[-1]]
        ext_l = n.links.index[n.links.p_nom_extendable]
        ext_s = n.stores.index[n.stores.e_nom_extendable]
        n.links.loc[ext_l, "p_nom_min"] = n.links.loc[ext_l, "p_nom_opt"]
        n.stores.loc[ext_s, "e_nom_min"] = n.stores.loc[ext_s, "e_nom_opt"]
        records.append(dict(window=w_i + 1, start=sns[0], objective=n.objective,
                            lk_before=lk_before, lk_after=n.links.p_nom_opt.copy(),
                            st_before=st_before, st_after=n.stores.e_nom_opt.copy(), seconds=secs))
        say(f"window {w_i + 1:2d} {sns[0]:%Y-%m-%d %H:%M}  objective {n.objective:14,.0f}  ({secs:.1f}s)")
    say(f"total solve time {time.time() - t_start:.0f}s")

    # ----- SpineOpt cost terms, mapped results, comparisons
    H = inp.hours_per_snapshot
    costs = pd.DataFrame([window_costs(n, meta, r, w, H) for r, w in zip(records, windows)],
                         index=pd.Index([r["window"] for r in records], name="window"))
    idx = solved_index(inp.snapshots, windows)
    UF = unit_flows(n, specs, segs, idx)
    CF = connection_flows(n, meta, idx)
    NS = node_states(n, meta, idx)
    units_inv, stores_inv = investments(inp, meta, records[-1])

    per_window, pw_notes = per_window_table(costs, spine, inp, windows)
    inv_df, inv_skipped = investments_table(inp, meta, spine, len(windows), units_inv, stores_inv)
    flows_df, flow_skipped = flows_table(spine, UF, CF, NS)
    blocks_df, block_skipped = blocks_table(inp, windows, spine, CF, NS)

    native = None
    if settings.native_piecewise_check:
        from .native import native_piecewise_check
        native = native_piecewise_check(inp, specs, segs, windows, settings, solver, opts, smin,
                                        records, costs, per_window, UF, spine)

    none_nodes = {nd for nd in inp.nodes if inp.nodes_df.loc[nd].balance_type == "balance_type_none"}
    statuses = {w["status"] for w in win_meta}
    meta_out = {
        "case": case,
        "status": "ok" if statuses == {"ok"} else ",".join(sorted(statuses)),
        "solver": {"requested": solver, "used": n.model.solver_name if n.model is not None else solver,
                   "options": opts, "gap_option": GAP_OPTION.get(solver)},
        "windows": win_meta,
        "n_windows_solved": len(windows),
        "n_windows_in_input": len(inp.windows),
        "solve_seconds_total": float(sum(w["solve_seconds"] for w in win_meta)),
        "run_seconds_total": time.time() - t_case,
        "objective_sum": {"spine": float(per_window.spine_total.sum()), "pypsa": float(per_window.pypsa_total.sum()),
                          "diff": float(per_window.diff_total.sum())},
        "packages": package_versions(),
        "input": {"path": str(input_xlsx.resolve()), "sha256": sha256(input_xlsx)},
        "spine_output": {"path": str(spine_output_xlsx.resolve()), "sha256": sha256(spine_output_xlsx),
                         "sheet": spine.sheet_name, "run_timestamp": spine.run_timestamp},
        "settings": settings.to_dict(solver),
        "workarounds": meta["workarounds"] + [
            s + ("" if windows[-1][-1] == inp.snapshots[-1] else " - last snapshot not in the solved windows, so not binding")
            for s in smin_notes],
        "ignored_parameters": support["ignored_parameters"],
        "skipped_energy_price_columns": support["skipped_energy_price_columns"],
        "spine_cost_terms": pw_notes,
        "skipped_comparisons": inv_skipped + flow_skipped + block_skipped,
        "operating_point_unit": [segs.unit, segs.in_node],
        "external_supply_flows": [[c, nd] for c in inp.conns for nd, d in inp.flows_of.get(c, [])
                                  if d == "from" and nd in none_nodes],
        "units_invested": units_inv,
        "storages_invested": stores_inv,
    }
    result = CaseResult(case=case, per_window=per_window, investments=inv_df, flows=flows_df, blocks=blocks_df,
                        meta=meta_out, network=n, unit_ports=ports, spine=spine, native_check=native,
                        hourly={"unit_flows": UF, "connection_flows": CF, "node_states": NS})
    if write:
        result.write(Path(out_dir) / case)
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m benchmark.run_case", description=__doc__.split("\n\n")[0])
    ap.add_argument("--input", required=True, help="SpineOpt input workbook (.xlsx)")
    ap.add_argument("--output", required=True, help="SpineOpt exported output workbook (.xlsx)")
    ap.add_argument("--solver", default="gurobi")
    ap.add_argument("--out-dir", default="benchmark_results", help="results go to <out-dir>/<case>/")
    ap.add_argument("--case", default=None, help="case name (default: derived from the input file name)")
    ap.add_argument("--mip-gap", type=float, default=None)
    ap.add_argument("--n-windows", type=int, default=None)
    ap.add_argument("--no-final-window-state-min", action="store_true")
    ap.add_argument("--no-slacks", action="store_true")
    ap.add_argument("--big", type=float, default=Settings.big)
    ap.add_argument("--native-check", action="store_true", help="also run the native piecewise cross-check")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    logging.getLogger("pypsa").setLevel(logging.ERROR)
    logging.getLogger("linopy").setLevel(logging.WARNING)
    warnings.filterwarnings("ignore", category=FutureWarning)
    settings = Settings(final_window_state_min=not a.no_final_window_state_min, include_slacks=not a.no_slacks,
                        n_windows=a.n_windows, big=a.big, native_piecewise_check=a.native_check)
    opts = {GAP_OPTION[a.solver]: a.mip_gap} if a.mip_gap is not None else None
    r = run_case(a.input, a.output, solver=a.solver, solver_options=opts, settings=settings,
                 out_dir=a.out_dir, case=a.case, log=None if a.quiet else print)
    o = r.meta["objective_sum"]
    print(f"{r.case}: status {r.status}, Σ objective SpineOpt {o['spine']:,.2f} €  PyPSA {o['pypsa']:,.2f} €  "
          f"(diff {o['diff']:,.2f} €); results in {r.out_dir}")
    return 0 if r.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
