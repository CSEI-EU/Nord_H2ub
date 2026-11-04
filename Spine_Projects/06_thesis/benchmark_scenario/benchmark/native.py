"""Cross-check of the segment formulation against PyPSA's native piecewise efficiency (PyPSA >= 1.3).

Native piecewise efficiencies need a fixed `p_nom`, so they cannot size the unit. Window 1 is
re-solved with every capacity fixed at the replica's window-1 result and the segment links replaced
by one link whose output efficiencies are piecewise curves. PyPSA's curve is the realised
efficiency at each load point, so the marginal SpineOpt coefficients are integrated first:
`η_real(op_k) = Σ_{j≤k} η_j Δop_j / op_k`. The operating cost must equal the replica's.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .model import build_network, make_extra_functionality


def native_piecewise_check(inp, specs, segs, windows, settings, solver, solver_options, smin, free_before,
                           records, costs: pd.DataFrame, per_window: pd.DataFrame, UF: pd.DataFrame, spine) -> pd.DataFrame:
    n2, meta2 = build_network(inp, specs, segs, windows, settings)
    r1 = records[0]
    for name in n2.links.index[n2.links.p_nom_extendable]:
        n2.links.loc[name, ["p_nom", "p_nom_extendable"]] = [r1["lk_after"][name], False]
    for name in n2.stores.index[n2.stores.e_nom_extendable]:
        n2.stores.loc[name, ["e_nom", "e_nom_extendable"]] = [r1["st_after"][name], False]
    seg_names = meta2["ext_units"][segs.unit]["segments"]
    P = n2.links.loc[seg_names, "p_nom"].sum()
    s0 = segs.specs[0]
    ports = s0["ports"]
    real = np.cumsum(segs.eff * segs.width) / segs.op_points        # realised efficiency at each op point
    out_i = ports.index((segs.out_node, "to"))
    co_scale = {i: s0["eff"][i - 1] / s0["eff"][out_i - 1] for i in range(1, len(ports))
                if i != out_i and ports[i][1] == "to"}
    kw = {f"bus{i}": p[0] for i, p in enumerate(ports)}
    for i in range(1, len(ports)):
        key = "efficiency" if i == 1 else f"efficiency{i}"
        if i == out_i:
            kw[key] = {0.0: 0.0, **dict(zip(segs.op_points, real))}
        elif i in co_scale:
            kw[key] = {0.0: 0.0, **dict(zip(segs.op_points, real * co_scale[i]))}
        else:
            kw[key] = s0["eff"][i - 1]          # other inputs: constant per unit of bus0 flow
    n2.remove("Link", seg_names)
    n2.add("Link", segs.unit, **kw, p_nom=P, marginal_cost=s0["vom"])
    ef = make_extra_functionality(meta2, segs.unit, segs.width, smin, free_before)
    status, _ = n2.optimize(windows[0], solver_name=solver, solver_options=solver_options,
                            extra_functionality=ef, log_to_console=False,
                            io_api="direct", include_objective_constant=False)
    if status != "ok":
        raise RuntimeError(f"native piecewise check: solve status {status}")
    replica_opex = costs.loc[1, ["variable", "units_on", "slack"]].sum()
    w1 = per_window.loc[1]
    sp_opex = w1.spine_total - np.nansum([w1.spine_unit_investment, w1.spine_storage_investment]) - costs.loc[1, "fom"]
    out_native = -n2.links_t[f"p{out_i}"][segs.unit].loc[windows[0]].sum()
    sp_out = (spine.series("unit_flow", segs.unit, "to_node", segs.out_node).loc[windows[0]].sum()
              if spine.has("unit_flow", segs.unit, "to_node", segs.out_node) else np.nan)
    return pd.DataFrame({
        "operating cost window 1 [€]": [sp_opex, replica_opex, n2.objective],
        f"{segs.unit} {segs.out_node} window 1": [sp_out, UF[(segs.unit, segs.out_node, "to")].loc[windows[0]].sum(),
                                                  out_native],
    }, index=["SpineOpt (segments + binaries)", "PyPSA replica (segment links)", "PyPSA native piecewise"])
