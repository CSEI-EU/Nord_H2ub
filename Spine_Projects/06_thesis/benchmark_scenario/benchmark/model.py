"""Build the PyPSA replica network and its custom constraints from a parsed SpineInput.

Storage loss transform. SpineOpt's balance is `s_t (1 + l) = s_{t-1} + net_inflow_t` (loss on the
end state). PyPSA's store is `e_t = (1 − sl) e_{t-1} − p_t`. They are identical with
`sl = l/(1+l)` and the store sitting behind a charge link (efficiency `1/(1+l)`) and a discharge
link (efficiency `1+l`). For `l = 0` the store sits directly on the node bus.

Coarser temporal blocks on demand nodes (e.g. daily). SpineOpt balances such a node per block
(Σ hourly deliveries over a block = block length × demand). Here: an hourly `Load` plus a buffer
`Store` with `e ∈ [−BIG, BIG]` that is forced to 0 at the end of every block, which enforces
exactly that block balance. Blocks restart at each window start (SpineOpt behaviour).

Segments. One `Link` per operating-point segment with its marginal efficiency; the segment sizes
are tied to one capacity by `p_nom[k] = Δop_k / Δop_0 · p_nom[0]`. Because the marginal
efficiencies are non-increasing (checked), the LP fills the bands in order by itself, so SpineOpt's
`ordered_unit_flow_op` binaries are not needed.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd
import pypsa

from .errors import UnsupportedStructure
from .settings import Settings
from .spine_input import RATIO_DIRS, SpineInput, num, table
from .units import Segments, unit_counts

COMMITTABLE = "unit_online_variable_type_integer"
ONLINE_TYPES_OK = {COMMITTABLE, "unit_online_variable_type_none"}

HANDLED_PARAMETERS = {
    # objects
    "fom_cost", "online_variable_type", "initial_units_on", "min_down_time",
    # unit / storage investment
    "number_of_units", "initial_units_invested_available", "candidate_units", "unit_investment_cost",
    "unit_investment_variable_type", "initial_storages_invested", "number_of_storages", "candidate_storages",
    "storage_investment_cost", "storage_investment_variable_type",
    # nodes
    "balance_type", "has_state", "node_state_cap", "frac_state_loss", "demand", "node_slack_penalty",
    # flows
    "unit_capacity", "vom_cost", "ramp_up_limit", "ramp_down_limit", "start_up_limit", "shut_down_limit",
    "connection_capacity", *RATIO_DIRS,
    # model / temporal
    "model_start", "model_end", "resolution", "roll_forward",
    # time series
    "unit_availability_factor", "units_on_cost", "connection_flow_cost", "fix_node_state", "node_state_min",
    # operating points
    "unit_flow_coefficient", "operating_points",
}
_CONN_FIXED = "connections are modelled with fixed capacity (connection_investment_cost must be 0, checked)"
IGNORED_PARAMETERS = {
    "unit_investment_tech_lifetime": "SpineOpt charges investment cost once, no annuity (CLAUDE.md conventions)",
    "unit_investment_econ_lifetime": "SpineOpt charges investment cost once, no annuity (CLAUDE.md conventions)",
    "storage_investment_tech_lifetime": "SpineOpt charges investment cost once, no annuity (CLAUDE.md conventions)",
    "storage_investment_econ_lifetime": "SpineOpt charges investment cost once, no annuity (CLAUDE.md conventions)",
    "minimum_operating_point": "only allowed on units without an online variable, where SpineOpt's "
                               "flow >= mop·units_on constraint is not binding (checked)",
    "ordered_unit_flow_op": "segment links fill in order because marginal efficiencies are non-increasing (checked)",
    "db_mip_solver_options": "solver options come from Settings",
    "connection_type": "each direction is modelled as a separate link (normal / lossless_bidirectional only, checked)",
    "connection_investment_variable_type": _CONN_FIXED,
    "initial_connections_invested_available": _CONN_FIXED,
    "number_of_connections": _CONN_FIXED,
    "candidate_connections": _CONN_FIXED,
    "connection_investment_cost": _CONN_FIXED,
    "connection_investment_tech_lifetime": _CONN_FIXED,
    "connection_investment_econ_lifetime": _CONN_FIXED,
}
CONNECTION_TYPES_OK = {"connection_type_normal", "connection_type_lossless_bidirectional"}


def is_committable(inp: SpineInput, u: str) -> bool:
    return inp.obj_par.get(u, {}).get("online_variable_type") == COMMITTABLE


def parameter_owners(inp: SpineInput) -> dict[str, set[str]]:
    owners: dict[str, set[str]] = defaultdict(set)
    for o, ps in inp.obj_par.items():
        for p in ps:
            owners[p].add(o)
    for t in (inp.unit_inv, inp.conn_inv, inp.stor_inv, inp.nodes_df):
        for o, r in t.iterrows():
            for col in t.columns:
                if col != "Category" and not pd.isna(r[col]):
                    owners[col].add(o)
    for (o, nd, d), ps in inp.flow_par.items():
        for p in ps:
            owners[p].add(f"{o}|{nd}|{d}")
    for o, p in inp.ratio_params:
        owners[p].add(o)
    for o, p in inp.model_par:
        owners[p].add(o)
    for o, p in inp.ts_unit:
        owners[p].add(o)
    for k in inp.flow_cost:
        owners["connection_flow_cost"].add("|".join(k))
    for nd, p in inp.storage_ts:
        owners[p].add(nd)
    for k in inp.uc_coef:
        owners["unit_flow_coefficient"].add("|".join(k))
    owners["operating_points"].add(f"{inp.op_unit}|{inp.op_node}")
    return owners


def check_supported(inp: SpineInput, specs: dict, segs: Segments) -> dict:
    """Raise UnsupportedStructure for anything the replica would not reproduce exactly.

    Returns notes on parameters that are present but deliberately ignored, for the run metadata.
    """
    problems: list[str] = []
    ignored: dict[str, dict] = {}
    units, conns = set(inp.units), set(inp.conns)

    for p, owners in sorted(parameter_owners(inp).items()):
        if p == "fom_cost" and owners & conns:
            ignored["fom_cost (connections)"] = {"reason": "SpineOpt does not apply fom_cost on connections",
                                                "owners": sorted(owners & conns)}
            owners = owners - conns
            if not owners:
                continue
        if p in IGNORED_PARAMETERS:
            ignored[p] = {"reason": IGNORED_PARAMETERS[p], "owners": sorted(owners)}
        elif p not in HANDLED_PARAMETERS:
            problems.append(f"parameter {p!r} (on {sorted(owners)}) is not handled by the replica")

    # all flows end on known nodes
    for o, fl in inp.flows_of.items():
        for nd, _ in fl:
            if nd not in inp.nodes:
                problems.append(f"{o}: flow to/from unknown node {nd!r}")
        if o not in units and o not in conns:
            problems.append(f"{o!r} has flows but is neither a unit nor a connection")

    # nodes
    for nd in inp.nodes:
        if nd not in inp.nodes_df.index:
            problems.append(f"node {nd} missing from the Nodes sheet")
            continue
        bt = inp.nodes_df.loc[nd].balance_type
        if bt not in ("balance_type_node", "balance_type_none"):
            problems.append(f"node {nd}: balance_type {bt!r} not supported")
    for nd in inp.state_nodes:
        if nd not in inp.stor_inv.index:
            problems.append(f"storage node {nd} has no Storage_Inv_Parameters row")
        if pd.isna(inp.nodes_df.loc[nd].node_state_cap):
            problems.append(f"storage node {nd} has no node_state_cap")
    for t, col in ((inp.unit_inv, "unit_investment_variable_type"), (inp.stor_inv, "storage_investment_variable_type")):
        if col in t:
            for o, v in t[col].items():
                if not pd.isna(v) and "continuous" not in str(v):
                    problems.append(f"{o}: {col} = {v!r}; only continuous investment is supported")
    for (nd, p), s in inp.storage_ts.items():
        if nd not in inp.state_nodes:
            problems.append(f"{p} on {nd}, which has no state")
        if p == "fix_node_state" and (len(s) > 1 or (len(s) and s.index[0] > inp.t0)):
            problems.append(f"fix_node_state on {nd} at {list(s.index)}: only a single initial value "
                            "(at or before model_start) is supported")

    # temporal blocks
    mr = table(inp.sheets, "Model_relations")
    inv_blocks = set(mr.loc[mr.iloc[:, 0] == "model__default_investment_temporal_block", mr.columns[4]])
    horizon = inp.t1 - inp.t0 + inp.res
    for (o, p), v in inp.model_par.items():
        if p != "resolution" or o == inp.default_block or o in inp.node_block_name.values():
            continue
        if o not in inv_blocks or pd.Timedelta(v["data"]) < horizon:
            problems.append(f"temporal block {o} ({v['data']}) is neither the default block, a node block, nor an "
                            "investment block covering the whole horizon")
    for nd, blk in inp.node_block.items():
        if nd not in inp.nodes_df.index or pd.isna(inp.nodes_df.loc[nd].demand):
            problems.append(f"node {nd} is on temporal block {inp.node_block_name[nd]} but has no demand; "
                            "only demand nodes on coarser blocks are supported")
        if blk % inp.res != pd.Timedelta(0) or blk < inp.res:
            problems.append(f"block {inp.node_block_name[nd]} ({blk}) is not a multiple of the resolution {inp.res}")

    # time series must cover every snapshot
    for k, s in inp.ts_unit.items():
        if s.isna().any():
            problems.append(f"Time_series {k}: {int(s.isna().sum())} snapshots without a value")
    for k, s in inp.flow_cost.items():
        if s.isna().any():
            problems.append(f"Energy_prices {k}: {int(s.isna().sum())} snapshots without a value")
        if k[0] not in conns or (k[1], k[2]) not in inp.flows_of.get(k[0], []):
            problems.append(f"connection_flow_cost on {k}: only costs on existing connection flows are supported")

    # units
    for u in inp.units:
        op = inp.obj_par.get(u, {})
        ot = op.get("online_variable_type")
        if ot is not None and ot not in ONLINE_TYPES_OK:
            problems.append(f"{u}: online_variable_type {ot!r} not supported")
        commit = is_committable(inp, u)
        flows = inp.flows_of.get(u, [])
        fpar = {k: inp.flow_par.get((u, *k), {}) for k in flows}
        if not commit:
            for p in ("initial_units_on", "min_down_time"):
                if p in op:
                    problems.append(f"{u}: {p} without an integer online variable is not supported")
            for k, ps in fpar.items():
                for p in ("ramp_up_limit", "ramp_down_limit", "start_up_limit", "shut_down_limit"):
                    if p in ps:
                        problems.append(f"{u}: {p} on {k} without an integer online variable is not supported")
            if (u, "units_on_cost") in inp.ts_unit:
                problems.append(f"{u}: units_on_cost without an integer online variable is not supported")
        else:
            if u == segs.unit:
                problems.append(f"{u}: operating-point segments on a committable unit are not supported")
            for k, ps in fpar.items():
                if "minimum_operating_point" in ps:
                    problems.append(f"{u}: minimum_operating_point on a committable unit is not supported")
                if k != specs.get(u, {}).get("ref"):
                    for p in ("ramp_up_limit", "ramp_down_limit", "start_up_limit", "shut_down_limit"):
                        if p in ps:
                            problems.append(f"{u}: {p} on {k}, which is not the capacity flow, is not supported")
        for k, ps in fpar.items():
            if "connection_capacity" in ps:
                problems.append(f"{u}: connection_capacity on a unit flow {k}")
        for o, p in inp.ratio_params:
            if o == u and p == "fix_ratio_out_in_connection_flow":
                problems.append(f"{u}: connection ratio on a unit")
        s = specs.get(u)
        if s is not None and s["kind"] == "generator":
            exist, mx = unit_counts(inp, u)
            if mx > exist:
                problems.append(f"{u}: investment in a unit without inputs (generator) is not supported")
            if any("vom_cost" in ps for ps in fpar.values()):
                problems.append(f"{u}: vom_cost on a unit without inputs (generator) is not supported")
        elif (u, "unit_availability_factor") in inp.ts_unit:
            problems.append(f"{u}: unit_availability_factor on a unit with inputs is not supported")
    if segs.unit not in inp.unit_inv.index:
        problems.append(f"{segs.unit}: operating-point unit has no Unit_Inv_Parameters row")

    # operating-point segments
    if len(inp.uc_names) != 1:
        problems.append(f"exactly one user constraint is supported, found {inp.uc_names}")
    if not (len(segs.op_points) and np.all(segs.width > 0) and np.isclose(segs.op_points[-1], 1.0)):
        problems.append(f"{segs.unit}: operating points {list(segs.op_points)} must increase strictly and end at 1")
    inc = [k for k in range(1, len(segs.eff)) if segs.eff[k] > segs.eff[k - 1] + 1e-12]
    if inc:
        problems.append(f"{segs.unit}: marginal efficiency increases at segment(s) {inc}; the LP segment formulation "
                        "is only exact for non-increasing efficiencies (ordered-segment binaries would be needed)")

    # connections
    for c in inp.conns:
        frm = {nd for nd, d in inp.flows_of.get(c, []) if d == "from"}
        to = {nd for nd, d in inp.flows_of.get(c, []) if d == "to"}
        seen_from, seen_to = set(), set()
        for (k_to, k_from, R) in inp.ratios.get(c, []):
            if k_to[1] != "to" or k_from[1] != "from" or k_from[0] not in frm or k_to[0] not in to:
                problems.append(f"{c}: ratio {k_to}->{k_from} does not match the connection's from/to flows")
            seen_from.add(k_from[0]); seen_to.add(k_to[0])
        if frm - seen_from or to - seen_to:
            problems.append(f"{c}: flows {sorted((frm - seen_from) | (to - seen_to))} have no fix_ratio_out_in_connection_flow")
        for k in [(c, nd, d) for nd, d in inp.flows_of.get(c, [])]:
            for p in ("vom_cost", "unit_capacity"):
                if p in inp.flow_par.get(k, {}):
                    problems.append(f"{c}: {p} on a connection flow is not supported")
        if c in inp.conn_inv.index:
            r = inp.conn_inv.loc[c]
            if num(r.get("connection_investment_cost"), 0) != 0:
                problems.append(f"{c}: connection investment (cost {r.connection_investment_cost}) is not supported")
            if r.get("connection_type") is not None and not pd.isna(r.get("connection_type")) \
                    and r.connection_type not in CONNECTION_TYPES_OK:
                problems.append(f"{c}: connection_type {r.connection_type!r} not supported")
            avail = sum(num(r.get(p), 0) for p in ("number_of_connections", "initial_connections_invested_available",
                                                     "candidate_connections"))
            if avail <= 0:
                problems.append(f"{c}: connection has no existing or candidate capacity")

    if problems:
        raise UnsupportedStructure("input not supported by the replica:\n  - " + "\n  - ".join(problems))
    return {"ignored_parameters": ignored, "skipped_energy_price_columns": inp.ep_skipped_columns}


def block_ends(windows: list[pd.DatetimeIndex], res: pd.Timedelta, block: pd.Timedelta) -> pd.DatetimeIndex:
    """Last snapshot of every temporal block; blocks restart at each window start (SpineOpt behaviour)."""
    step = int(block / res)
    ends = []
    for w in windows:
        ends += [w[min(i + step, len(w)) - 1] for i in range(0, len(w), step)]
    return pd.DatetimeIndex(ends)


def build_network(inp: SpineInput, specs: dict, segs: Segments, windows: list[pd.DatetimeIndex],
                  settings: Settings) -> tuple[pypsa.Network, dict]:
    BIG = settings.big
    H = inp.hours_per_snapshot
    WIN = inp.win
    n = pypsa.Network()
    n.set_snapshots(inp.snapshots)
    meta = {"ext_units": {}, "fixed_units": {}, "stores": {}, "const_inv_first_window": 0.0,
            "connection_links": {}, "slack_generators": [], "workarounds": []}
    wk = meta["workarounds"]

    for nd in inp.nodes:
        n.add("Bus", nd)
        row = inp.nodes_df.loc[nd]
        if row.balance_type == "balance_type_none":
            n.add("Generator", f"free {nd}", bus=nd, p_nom=BIG, p_min_pu=-1, p_max_pu=1)
            wk.append(f"{nd}: balance_type_none modelled as a free source/sink of ±{BIG:g}")
        elif settings.include_slacks and not pd.isna(row.node_slack_penalty):
            pen = float(row.node_slack_penalty)
            n.add("Generator", f"slack_pos {nd}", bus=nd, p_nom=BIG, marginal_cost=pen)
            n.add("Generator", f"slack_neg {nd}", bus=nd, p_nom=BIG, p_min_pu=-1, p_max_pu=0, marginal_cost=-pen)
            meta["slack_generators"] += [f"slack_pos {nd}", f"slack_neg {nd}"]

        if not pd.isna(row.demand):
            n.add("Load", f"demand {nd}", bus=nd, p_set=float(row.demand))
            if nd in inp.node_block:
                ends = block_ends(windows, inp.res, inp.node_block[nd])
                pu = pd.Series(1.0, inp.snapshots); pu[ends] = 0.0
                n.add("Store", f"block buffer {nd}", bus=nd, e_nom=BIG, e_min_pu=-pu, e_max_pu=pu)
                wk.append(f"{nd}: {inp.node_block_name[nd]} block balance via hourly Load + buffer Store "
                          f"(±{BIG:g}, zero at {len(ends)} block ends, blocks restart at each window)")

        if str(row.has_state).lower() == "true":
            loss = float(num(row.frac_state_loss, 0.0))
            cap = float(row.node_state_cap)
            si = inp.stor_inv.loc[nd]
            s_exist = num(si.number_of_storages, 0) + num(si.initial_storages_invested, 0)
            s_max = num(si.number_of_storages, 0) + num(si.candidate_storages, 0)
            e_init = float(inp.storage_ts.get((nd, "fix_node_state"), pd.Series([0.0])).iloc[0])
            sbus = nd
            if loss > 0:
                sbus = f"{nd} store"
                n.add("Bus", sbus)
                n.add("Link", f"{nd} loss-charge", bus0=nd, bus1=sbus, efficiency=1 / (1 + loss), p_nom=BIG)
                n.add("Link", f"{nd} loss-discharge", bus0=sbus, bus1=nd, efficiency=1 + loss, p_nom=BIG)
                wk.append(f"{nd}: frac_state_loss {loss:g} via exact transform (standing_loss l/(1+l), "
                          "charge/discharge links 1/(1+l) and 1+l)")
            n.add("Store", nd, bus=sbus, e_nom_extendable=s_max > s_exist, e_nom=cap * s_exist,
                  e_nom_min=cap * s_exist, e_nom_max=cap * s_max, standing_loss=loss / (1 + loss),
                  capital_cost=float(si.storage_investment_cost) / cap, e_initial=e_init)
            meta["stores"][nd] = dict(cap=cap, inv=float(si.storage_investment_cost))

    # ----- units
    for u, s in specs.items():
        exist, mx = unit_counts(inp, u)
        fom = float(inp.obj_par[u].get("fom_cost", 0))
        committable = is_committable(inp, u)
        if s["kind"] == "generator":
            avail = inp.ts_unit.get((u, "unit_availability_factor"))
            n.add("Generator", u, bus=s["bus"], p_nom=s["cap"] * exist,
                  p_max_pu=avail if avail is not None else 1.0)
            meta["fixed_units"][u] = dict(units=exist, cap=s["cap"], fom=fom, inv=0.0)
            continue
        kw = {f"bus{i}": p[0] for i, p in enumerate(s["ports"])}
        kw.update({("efficiency" if i == 0 else f"efficiency{i + 1}"): e for i, e in enumerate(s["eff"])})
        inv = float(inp.unit_inv.loc[u].unit_investment_cost) if u in inp.unit_inv.index else 0.0
        if committable:
            # integer units_on <= units available forces a full unit in SpineOpt -> fixed at max size
            ref = inp.flow_par[(u, *s["ref"])]
            uon = inp.ts_unit.get((u, "units_on_cost"))
            n.add("Link", u, **kw, p_nom=s["P0"] * mx, marginal_cost=s["vom"], committable=True,
                  min_down_time=int(inp.obj_par[u].get("min_down_time", pd.Timedelta(0)) / inp.res),
                  up_time_before=1 if num(inp.obj_par[u].get("initial_units_on"), 0) >= 1 else 0,
                  down_time_before=0 if num(inp.obj_par[u].get("initial_units_on"), 0) >= 1 else 1,
                  ramp_limit_up=num(ref.get("ramp_up_limit")), ramp_limit_down=num(ref.get("ramp_down_limit")),
                  ramp_limit_start_up=num(ref.get("start_up_limit")), ramp_limit_shut_down=num(ref.get("shut_down_limit")),
                  stand_by_cost=uon if uon is not None else 0.0)
            meta["fixed_units"][u] = dict(units=mx, cap=s["cap"], fom=fom, inv=inv)
            meta["const_inv_first_window"] += inv * (mx - exist)
            wk.append(f"{u}: committable unit fixed at its maximum of {mx:g} unit(s) ({s['P0'] * mx:g} on bus0); "
                      f"investment {inv * (mx - exist):g} charged as a constant in window 1")
        else:
            ext = mx > exist
            n.add("Link", u, **kw, p_nom_extendable=ext, p_nom=s["P0"] * exist, p_nom_min=s["P0"] * exist,
                  p_nom_max=s["P0"] * mx, marginal_cost=s["vom"],
                  capital_cost=(inv + fom * s["cap"] * WIN * H) / s["P0"])
            (meta["ext_units"] if ext else meta["fixed_units"])[u] = dict(units=exist, cap=s["cap"], fom=fom, inv=inv, P0=s["P0"])

    # ----- operating-point segments
    u = segs.unit
    exist, mx = unit_counts(inp, u)
    fom = float(inp.obj_par[u].get("fom_cost", 0))
    inv = float(inp.unit_inv.loc[u].unit_investment_cost)
    for k, s in enumerate(segs.specs):
        kw = {f"bus{i}": p[0] for i, p in enumerate(s["ports"])}
        kw.update({("efficiency" if i == 0 else f"efficiency{i + 1}"): e for i, e in enumerate(s["eff"])})
        n.add("Link", f"{u}[{k}]", **kw, p_nom_extendable=mx > exist, p_nom=segs.width[k] * s["P0"] * exist,
              p_nom_min=segs.width[k] * s["P0"] * exist, p_nom_max=segs.width[k] * s["P0"] * mx,
              marginal_cost=s["vom"], capital_cost=(inv + fom * s["cap"] * WIN * H) / s["P0"])
    meta["ext_units"][u] = dict(units=exist, cap=segs.specs[0]["cap"], fom=fom, inv=inv, P0=segs.specs[0]["P0"],
                                segments=[f"{u}[{k}]" for k in range(len(segs.specs))])
    wk.append(f"{u}: {len(segs.specs)} operating-point segments as separate links with marginal efficiencies, "
              "capacities tied by p_nom ratio constraints")

    # ----- connections: one Link per direction
    for c in inp.conns:
        frm = [nd for nd, d in inp.flows_of[c] if d == "from"]
        to = [nd for nd, d in inp.flows_of[c] if d == "to"]
        for (k_to, k_from, R) in inp.ratios.get(c, []):
            n1, n2 = k_from[0], k_to[0]
            if n1 not in frm or n2 not in to:
                continue
            cap_from = float(inp.flow_par.get((c, n1, "from"), {}).get("connection_capacity", np.inf))
            cap_to = float(inp.flow_par.get((c, n2, "to"), {}).get("connection_capacity", np.inf))
            mc = inp.flow_cost.get((c, n1, "from"), 0) + R * inp.flow_cost.get((c, n2, "to"), 0)
            name = f"{c} {n1}->{n2}"
            n.add("Link", name, bus0=n1, bus1=n2, efficiency=R, p_nom=min(cap_from, cap_to / R), marginal_cost=mc)
            meta["connection_links"][name] = (c, n1, n2)
    if meta["stores"]:
        wk.append("storage capacity is cumulative across windows (SpineOpt lets it fall between windows and "
                  "re-invests; CLAUDE.md artefact 2)")
    return n, meta


def node_state_min(inp: SpineInput, settings: Settings) -> tuple[dict[str, pd.Series], list[str]]:
    """node_state_min per state node, forward-filled onto the snapshots, plus workaround notes."""
    smin = {nd: s.reindex(inp.snapshots.union(s.index)).ffill().reindex(inp.snapshots).fillna(0.0)
            for (nd, p), s in inp.storage_ts.items() if p == "node_state_min"}
    notes = []
    if settings.final_window_state_min:
        for nd, s in smin.items():
            had = float(s.iloc[-1])
            s.iloc[-1] = s.max()
            notes.append(f"{nd}: FINAL_WINDOW_STATE_MIN sets node_state_min = {s.iloc[-1]:g} at the last snapshot "
                         f"{inp.snapshots[-1]} (input value there: {had:g})")
    return smin, notes


def make_extra_functionality(meta: dict, seg_unit: str, seg_width: np.ndarray, smin: dict[str, pd.Series]):
    def extra_functionality(n: pypsa.Network, sns: pd.Index) -> None:
        m = n.model
        segs = [g for g in meta["ext_units"].get(seg_unit, {}).get("segments", []) if g in n.links.index[n.links.p_nom_extendable]]
        p_nom = m["Link-p_nom"] if segs else None
        for k in range(1, len(segs)):
            lhs = p_nom.loc[[segs[k]]].assign_coords(name=[segs[0]]) - seg_width[k] / seg_width[0] * p_nom.loc[[segs[0]]]
            m.add_constraints(lhs == 0, name=f"segment_ratio_{k}")
        if not smin:
            return
        e = m["Store-e"]
        for nd, s in smin.items():
            req = s.loc[sns]
            req = req[req > 0]
            if len(req):
                m.add_constraints(e.sel(name=nd, snapshot=req.index) >= req.values, name=f"state_min_{nd}")
    return extra_functionality
