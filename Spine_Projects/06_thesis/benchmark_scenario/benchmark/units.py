"""Translate SpineOpt units into PyPSA ports (no PyPSA dependency, side-effect free).

For every unit, all flows are expressed as a multiple `a` of the flow that carries `unit_capacity`
by walking the `fix_ratio_*` graph. The PyPSA `Link` then gets `bus0` = main input and
`efficiency_k = ±a_k / a_bus0` (negative = additional input). For the unit with operating points
each segment adds the edge `out = η_k · in` from the user constraint, so each segment link carries
its own marginal efficiency.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .errors import UnsupportedStructure
from .spine_input import SpineInput, num


def flow_coefficients(inp: SpineInput, u: str, extra: list | None = None) -> dict[tuple, float]:
    edges = inp.ratios.get(u, []) + (extra or [])
    if u not in inp.flows_of:
        raise UnsupportedStructure(f"{u}: unit has no flows")
    cap_flows = [k for k in inp.flows_of[u] if "unit_capacity" in inp.flow_par.get((u, *k), {})]
    if len(cap_flows) != 1:
        raise UnsupportedStructure(f"{u}: {len(cap_flows)} flows carry unit_capacity {cap_flows}; exactly one is supported")
    a = {cap_flows[0]: 1.0}
    changed = True
    while changed:
        changed = False
        for k1, k2, R in edges:
            if k2 in a and k1 not in a:
                a[k1] = R * a[k2]; changed = True
            elif k1 in a and k2 not in a:
                a[k2] = a[k1] / R; changed = True
    missing = set(inp.flows_of[u]) - set(a)
    if missing:
        raise UnsupportedStructure(f"{u}: flows {sorted(missing)} are not tied to the capacity flow by fix_ratio_* "
                                   "(free flows are not supported)")
    return a


def unit_spec(inp: SpineInput, u: str, extra=None) -> dict:
    a = flow_coefficients(inp, u, extra)
    ins = [k for k in inp.flows_of[u] if k[1] == "from"]
    cap_flow = next(k for k in a if a[k] == 1.0 and "unit_capacity" in inp.flow_par.get((u, *k), {}))
    cap = float(inp.flow_par[(u, *cap_flow)]["unit_capacity"])
    if not ins:
        return dict(kind="generator", bus=cap_flow[0], cap=cap, a=a, ref=cap_flow)
    bus0 = cap_flow if cap_flow[1] == "from" else ins[0]
    ports = [bus0] + [k for k in inp.flows_of[u] if k != bus0]
    eff = [(+1 if k[1] == "to" else -1) * a[k] / a[bus0] for k in ports[1:]]
    vom = sum(float(inp.flow_par.get((u, *k), {}).get("vom_cost", 0)) * a[k] / a[bus0] for k in ports)
    return dict(kind="link", ports=ports, eff=eff, cap=cap, P0=cap * a[bus0], vom=vom, a=a, ref=cap_flow, bus0=bus0)


def unit_counts(inp: SpineInput, u: str):
    """(existing, maximum) number of units; SpineOpt: number_of_units + units_invested_available."""
    r = inp.unit_inv.loc[u] if u in inp.unit_inv.index else None
    n0 = num(r.number_of_units, 1) if r is not None else 1
    avail0 = num(r.initial_units_invested_available, 0) if r is not None else 0
    cand = num(r.candidate_units, 0) if r is not None else 0
    return n0 + avail0, n0 + max(cand, avail0)


@dataclass
class Segments:
    """Operating-point segments of the unit named in the Operating_points sheet."""
    unit: str
    in_node: str              # node whose flow defines the load (operating points)
    out_node: str             # node whose flow follows the efficiency curve
    op_points: np.ndarray
    width: np.ndarray         # Δop_k
    eff: np.ndarray           # marginal efficiency per segment
    specs: list[dict]         # one unit_spec per segment


def operating_segments(inp: SpineInput) -> Segments:
    u, node = inp.op_unit, inp.op_node
    if (u, node, "from") not in inp.uc_coef:
        raise UnsupportedStructure(f"Variable_Eff has no 'from' coefficient for {u}/{node} (the Operating_points flow)")
    c_in = inp.uc_coef[(u, node, "from")]
    others = [k for k in inp.uc_coef if k[0] != u]
    if others:
        raise UnsupportedStructure(f"user-constraint coefficients on objects other than {u} are not supported: {others}")
    extra_in = [k for k in inp.uc_coef if k[2] == "from" and k != (u, node, "from")]
    if extra_in:
        raise UnsupportedStructure(f"{u}: more than one 'from' user-constraint coefficient {extra_in}")
    outs = [(k, v) for k, v in inp.uc_coef.items() if k[0] == u and k[2] == "to"]
    if len(outs) != 1:
        raise UnsupportedStructure(f"{u}: {len(outs)} 'to' user-constraint coefficients; exactly one is supported")
    (out_key, c_out), = outs
    if len(c_in) != len(inp.op_points):
        raise UnsupportedStructure(f"{u}: {len(c_in)} unit_flow_coefficients vs {len(inp.op_points)} operating points")
    if np.isnan(c_in).any() or np.isnan(c_out[0]):
        raise UnsupportedStructure(f"{u}: NaN in unit_flow_coefficient")
    if np.isfinite(c_out[1:]).any():
        raise UnsupportedStructure(f"{u}: segment-dependent coefficient on the 'to' flow is not supported")
    width = np.diff(np.r_[0.0, inp.op_points])
    eff = c_in / -c_out[0]          # marginal efficiency per segment
    specs = [unit_spec(inp, u, extra=[((out_key[1], "to"), (node, "from"), e)]) for e in eff]
    return Segments(unit=u, in_node=node, out_node=out_key[1], op_points=inp.op_points, width=width, eff=eff, specs=specs)


def unit_specs(inp: SpineInput) -> dict[str, dict]:
    """unit_spec for every unit except the operating-point unit."""
    return {u: unit_spec(inp, u) for u in inp.units if u != inp.op_unit}
