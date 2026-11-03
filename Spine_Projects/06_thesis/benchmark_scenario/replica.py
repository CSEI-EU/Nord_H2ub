# %% [markdown]
# # SpineOpt → PyPSA replica: power-to-methanol plant (`paper_energy_2024_base_10op`)
#
# This notebook rebuilds the SpineOpt model from its Excel input **as an exact replica** in PyPSA,
# solves it with the same rolling-horizon structure, and benchmarks every result against the
# exported SpineOpt output.
#
# **How SpineOpt concepts are mapped**
#
# | SpineOpt | PyPSA replica |
# |---|---|
# | `node` (`balance_type_node`) | `Bus` (+ optional ±slack generators at `node_slack_penalty`) |
# | `node` (`balance_type_none`) | `Bus` + free unbounded source/sink `Generator` |
# | `unit` with inputs | multi-port `Link`; `bus0` = main input, other ports from `fix_ratio_*_unit_flow` |
# | `unit` without inputs (solar) | `Generator` with `p_max_pu` = `unit_availability_factor` |
# | electrolyzer `operating_points` + `user_constraint` | one `Link` per segment (marginal efficiency), segment sizes tied to one capacity |
# | integer `online_variable_type` | `committable=True` (+ `min_down_time`, ramp / start-up / shut-down limits) |
# | `units_on_cost` (time series) | `stand_by_cost` (time series) |
# | `connection` (each direction) | `Link` with `efficiency` = `fix_ratio_out_in_connection_flow` |
# | `connection_flow_cost` | `marginal_cost` on that link |
# | `has_state` node | `Store` (exact transform for `frac_state_loss`, see below) |
# | node on `daily` temporal block | hourly `Load` + ±buffer `Store` forced to 0 at each daily block end |
# | `roll_forward = 730h` | 12 sequential `n.optimize(snapshots=window)` calls, investments carried over |
#
# **SpineOpt conventions confirmed from the output file** (see the checks at the end):
# * `unit_investment_cost` is charged per whole unit invested (fraction × cost), once, in the window it is made, no annuity.
# * `fom_cost` [€/MW/h] is charged on installed unit capacity for every hour of each window. `fom_cost` on connections is **not** applied by SpineOpt, so the replica ignores it too.
# * Daily blocks start at each window start, not at midnight (730 h = 30 full days + one 10 h block).
# * The segment coefficients are **marginal** efficiencies (full-load average 0.742 = 31.95/43.06 in the output).

# %%
from __future__ import annotations

import json
import logging
import os
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

logging.getLogger("pypsa").setLevel(logging.ERROR)
logging.getLogger("linopy").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", category=FutureWarning)
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

# %% [markdown]
# ## Settings

# %%
INPUT_XLSX = Path(os.environ.get("INPUT_XLSX", "paper_energy_2024_input_base_10op.xlsx"))
SPINE_OUTPUT_XLSX = Path(os.environ.get("SPINE_OUTPUT_XLSX", "Output_exported_paper_energy_2024_base_10op.xlsx"))

SOLVER = os.environ.get("SOLVER", "gurobi")
# Mirrors db_mip_solver_options in the SpineOpt input (mip_rel_gap 1e-10, time_limit 3000 s).
SOLVER_OPTIONS = {
    "gurobi": {"MIPGap": 1e-10, "TimeLimit": 3000, "OutputFlag": 0},
    "highs": {"mip_rel_gap": 1e-10, "time_limit": 3000.0, "presolve": "on", "output_flag": False},
}[SOLVER]
if os.environ.get("MIPGAP"):  # quick development runs
    SOLVER_OPTIONS["MIPGap" if SOLVER == "gurobi" else "mip_rel_gap"] = float(os.environ["MIPGAP"])

# The SpineOpt run also kept ch3oh_st >= 969.25 MWh (48 h of demand) at the last hour of window 12,
# although the exported Time_series_storage sheet stops at the end of window 11. True reproduces the run.
FINAL_WINDOW_STATE_MIN = True

INCLUDE_SLACKS = True     # SpineOpt adds node_slack_pos/neg at node_slack_penalty; they were all 0
N_WINDOWS = int(os.environ.get("N_WINDOWS", 0)) or None   # None = full year; e.g. 1 for a quick test
BIG = 1e6                 # size of "unbounded" sources/sinks (balance_type_none) and demand buffers

# %% [markdown]
# ## 1. Read the SpineOpt input workbook

# %%
X = pd.read_excel(INPUT_XLSX, sheet_name=None, header=None)


def table(sheet: str) -> pd.DataFrame:
    df = X[sheet]
    out = df.iloc[1:].copy()
    out.columns = df.iloc[0].tolist()
    return out.dropna(how="all").reset_index(drop=True)


def num(v, default=np.nan):
    return default if v is None or (isinstance(v, float) and np.isnan(v)) else v


defs = table("Definition")
UNITS = defs.loc[defs.Category == "unit", "Object_name"].tolist()
NODES = defs.loc[defs.Category == "node", "Object_name"].tolist()
CONNS = defs.loc[defs.Category == "connection", "Object_name"].tolist()

# object parameters: obj_par[name][param]
obj_par: dict[str, dict] = {o: {} for o in defs.Object_name}
for _, r in table("Definition_parameters").iterrows():
    obj_par[r.Object_name][r.Parameter] = r.Value
for _, r in table("Definition_parameters_duration").iterrows():
    obj_par[r.Object_name][r.Parameter] = pd.Timedelta(r.Value)

unit_inv = table("Unit_Inv_Parameters").set_index("Object_name")
conn_inv = table("Connection_Inv_Parameters").set_index("Object_name")
stor_inv = table("Storage_Inv_Parameters").set_index("Object_name")
nodes_df = table("Nodes").set_index("Object_name")

# topology: unit / connection  x  node  x  direction
DIR = {"unit__from_node": "from", "unit__to_node": "to", "connection__from_node": "from", "connection__to_node": "to"}
topo = table("Object__to_from_node_definition")
flows_of: dict[str, list[tuple[str, str]]] = {}
for _, r in topo.iterrows():
    flows_of.setdefault(r.Object_name, []).append((r.Node, DIR[r.Relationship_class_name]))

# flow parameters: flow_par[(obj, node, dir)][param]
flow_par: dict[tuple, dict] = {}
for _, r in table("Object__to_from_node").iterrows():
    flow_par.setdefault((r.Object_name, r.Node, DIR[r.Relationship_class_name]), {})[r.Parameter] = r.Value
# relationships that only appear in the parameter sheet (e.g. pl_ch3oh_demand) exist in SpineOpt too
for (o, nd, d) in list(flow_par):
    if (nd, d) not in flows_of.setdefault(o, []):
        flows_of[o].append((nd, d))
for _, r in table("Boolean_relations").iterrows():
    flow_par.setdefault((r.Object_name, r.Node_name, DIR[r.Relationship_class_name]), {})[r.Parameter_name] = str(r.Value).lower() == "true"

# fixed ratios  f(n1) = R * f(n2)
RATIO_DIRS = {
    "fix_ratio_in_in_unit_flow": ("from", "from"),
    "fix_ratio_in_out_unit_flow": ("from", "to"),
    "fix_ratio_out_out_unit_flow": ("to", "to"),
    "fix_ratio_out_in_unit_flow": ("to", "from"),
    "fix_ratio_out_in_connection_flow": ("to", "from"),
}
ratios: dict[str, list] = {}
for _, r in table("Object__node_node").iterrows():
    d1, d2 = RATIO_DIRS[r.Parameter]
    ratios.setdefault(r.Object_name, []).append(((r.Node1, d1), (r.Node2, d2), float(r.Value)))

# operating points + user-constraint efficiency curve (Variable_Eff / Operating_points sheets)
op = X["Operating_points"]
OP_UNIT, OP_NODE = op.iloc[1, 1], op.iloc[2, 1]
OP_POINTS = op.iloc[4:, 1].astype(float).to_numpy()
ve = X["Variable_Eff"]
uc_coef: dict[tuple, np.ndarray] = {}
for col in range(1, ve.shape[1]):
    d = "from" if "from_node" in str(ve.iloc[0, col]) else "to"
    uc_coef[(ve.iloc[2, col], ve.iloc[3, col], d)] = pd.to_numeric(ve.iloc[5:, col], errors="coerce").to_numpy()
print(f"{len(UNITS)} units, {len(NODES)} nodes, {len(CONNS)} connections; "
      f"{len(OP_POINTS)} operating points on {OP_UNIT}/{OP_NODE}")

# %% [markdown]
# ### Model / temporal settings and time series

# %%
model_par = {(r.Object_name, r.Parameter): json.loads(r.Value) for _, r in table("Model").iterrows()}
T0 = pd.Timestamp(model_par[("Model", "model_start")]["data"])
T1 = pd.Timestamp(model_par[("Model", "model_end")]["data"])
RES = pd.Timedelta(model_par[("hourly", "resolution")]["data"])
ROLL = pd.Timedelta(model_par[("Model", "roll_forward")]["data"])
SNAPSHOTS = pd.date_range(T0, T1, freq=RES)
H = RES / pd.Timedelta("1h")                    # hours per snapshot
WIN = int(ROLL / RES)                           # snapshots per window
windows = [SNAPSHOTS[i:i + WIN] for i in range(0, len(SNAPSHOTS), WIN)][:N_WINDOWS]

# node -> coarser temporal block (here: ch3oh_demand -> daily)
node_block = {r.Node: pd.Timedelta(model_par[(r.Temporal_block, "resolution")]["data"])
              for _, r in table("Temporal_relations").iterrows()}

ts = X["Time_series"]
ts_unit = {(ts.iloc[0, c], ts.iloc[2, c]): pd.Series(ts.iloc[3:, c].astype(float).values,
                                                       index=pd.to_datetime(ts.iloc[3:, 0])).reindex(SNAPSHOTS)
           for c in range(1, ts.shape[1])}

ep = X["Energy_prices"]
flow_cost: dict[tuple, pd.Series] = {}
for c in range(1, ep.shape[1]):
    if pd.isna(ep.iloc[1, c]) or pd.isna(ep.iloc[2, c]):
        continue
    key = (ep.iloc[2, c], ep.iloc[3, c], DIR[ep.iloc[1, c]])
    s = pd.Series(ep.iloc[5:, c].astype(float).values, index=pd.to_datetime(ep.iloc[5:, 0])).reindex(SNAPSHOTS)
    flow_cost[key] = flow_cost.get(key, 0) + s

tss = X["Time_series_storage"]
storage_ts: dict[tuple, pd.Series] = {}
for c in range(1, tss.shape[1]):
    s = pd.Series(pd.to_numeric(tss.iloc[2:, c], errors="coerce").values, index=pd.to_datetime(tss.iloc[2:, 0]))
    storage_ts[(tss.iloc[0, c], tss.iloc[1, c])] = s.dropna()

print(f"{len(SNAPSHOTS)} snapshots, {len(windows)} windows of {WIN} h; daily-block nodes: {list(node_block)}")
print("connection_flow_cost keys:", list(flow_cost))

# %% [markdown]
# ## 2. Translate units into PyPSA ports
#
# For every unit, all flows are expressed as a multiple `a` of the flow that carries `unit_capacity`
# by walking the `fix_ratio_*` graph. The PyPSA `Link` then gets `bus0` = main input and
# `efficiency_k = ±a_k / a_bus0` (negative = additional input). For the electrolyzer each segment
# adds the edge `h2 = η_k · power` from the user constraint, so each segment link carries its own
# marginal efficiency.

# %%
def flow_coefficients(u: str, extra: list | None = None) -> dict[tuple, float]:
    edges = ratios.get(u, []) + (extra or [])
    cap_flows = [k for k in flows_of[u] if "unit_capacity" in flow_par.get((u, *k), {})]
    assert len(cap_flows) == 1, (u, cap_flows)
    a = {cap_flows[0]: 1.0}
    changed = True
    while changed:
        changed = False
        for k1, k2, R in edges:
            if k2 in a and k1 not in a:
                a[k1] = R * a[k2]; changed = True
            elif k1 in a and k2 not in a:
                a[k2] = a[k1] / R; changed = True
    missing = set(flows_of[u]) - set(a)
    assert not missing, (u, missing)
    return a


def unit_spec(u: str, extra=None) -> dict:
    a = flow_coefficients(u, extra)
    ins = [k for k in flows_of[u] if k[1] == "from"]
    cap_flow = next(k for k in a if a[k] == 1.0 and "unit_capacity" in flow_par.get((u, *k), {}))
    cap = float(flow_par[(u, *cap_flow)]["unit_capacity"])
    if not ins:
        return dict(kind="generator", bus=cap_flow[0], cap=cap, a=a, ref=cap_flow)
    bus0 = cap_flow if cap_flow[1] == "from" else ins[0]
    ports = [bus0] + [k for k in flows_of[u] if k != bus0]
    eff = [(+1 if k[1] == "to" else -1) * a[k] / a[bus0] for k in ports[1:]]
    vom = sum(float(flow_par.get((u, *k), {}).get("vom_cost", 0)) * a[k] / a[bus0] for k in ports)
    return dict(kind="link", ports=ports, eff=eff, cap=cap, P0=cap * a[bus0], vom=vom, a=a, ref=cap_flow, bus0=bus0)


def unit_counts(u: str):
    """(existing, maximum) number of units; SpineOpt: number_of_units + units_invested_available."""
    r = unit_inv.loc[u] if u in unit_inv.index else None
    n0 = num(r.number_of_units, 1) if r is not None else 1
    avail0 = num(r.initial_units_invested_available, 0) if r is not None else 0
    cand = num(r.candidate_units, 0) if r is not None else 0
    return n0 + avail0, n0 + max(cand, avail0)


SEG_UNIT = OP_UNIT
seg_width = np.diff(np.r_[0.0, OP_POINTS])
c_in = uc_coef[(SEG_UNIT, OP_NODE, "from")]
(h2_key, c_out), = [(k, v) for k, v in uc_coef.items() if k[0] == SEG_UNIT and k[2] == "to"]
seg_eff = c_in / -c_out[0]          # marginal efficiency per segment
SEGMENTS = [unit_spec(SEG_UNIT, extra=[((h2_key[1], "to"), (OP_NODE, "from"), e)]) for e in seg_eff]

specs = {u: unit_spec(u) for u in UNITS if u != SEG_UNIT}
pd.DataFrame(
    [(u, s["kind"], s.get("bus0", (s.get("bus"),))[0], [p[0] for p in s.get("ports", [])[1:]],
      np.round(s.get("eff", []), 5).tolist(), s.get("P0", s["cap"]), round(s.get("vom", 0), 4)) for u, s in specs.items()]
    + [(f"{SEG_UNIT}[{k}]", "link", s["bus0"][0], [p[0] for p in s["ports"][1:]], np.round(s["eff"], 5).tolist(),
        seg_width[k] * s["P0"], round(s["vom"], 4)) for k, s in enumerate(SEGMENTS)],
    columns=["unit", "kind", "bus0", "other ports", "efficiencies", "max p0 [bus0 units]", "marginal €/unit p0"],
)

# %% [markdown]
# ## 3. Build the network
#
# **Storage loss transform.** SpineOpt's balance is `s_t (1 + l) = s_{t-1} + net_inflow_t` (loss on the
# *end* state). PyPSA's store is `e_t = (1 − sl) e_{t-1} − p_t`. They are identical with
# `sl = l/(1+l)` and the store sitting behind a charge link (efficiency `1/(1+l)`) and a discharge
# link (efficiency `1+l`). For `l = 0` the store sits directly on the node bus.
#
# **Daily demand.** `ch3oh_demand` is solved on 24 h blocks in SpineOpt (Σ hourly deliveries over a
# block = 24 h × 20.19 MW). Here: an hourly `Load` plus a buffer `Store` with `e ∈ [−BIG, BIG]`
# that is forced to 0 at the end of every block, which enforces exactly that block balance.

# %%
def block_ends(block: pd.Timedelta) -> pd.DatetimeIndex:
    """Last snapshot of every temporal block; blocks restart at each window start (SpineOpt behaviour)."""
    step = int(block / RES)
    ends = []
    for w in windows:
        ends += [w[min(i + step, len(w)) - 1] for i in range(0, len(w), step)]
    return pd.DatetimeIndex(ends)


def build_network() -> tuple[pypsa.Network, dict]:
    n = pypsa.Network()
    n.set_snapshots(SNAPSHOTS)
    meta = {"ext_units": {}, "fixed_units": {}, "stores": {}, "const_inv_first_window": 0.0}

    for nd in NODES:
        n.add("Bus", nd)
        row = nodes_df.loc[nd]
        if row.balance_type == "balance_type_none":
            n.add("Generator", f"free {nd}", bus=nd, p_nom=BIG, p_min_pu=-1, p_max_pu=1)
        elif INCLUDE_SLACKS and not pd.isna(row.node_slack_penalty):
            pen = float(row.node_slack_penalty)
            n.add("Generator", f"slack_pos {nd}", bus=nd, p_nom=BIG, marginal_cost=pen)
            n.add("Generator", f"slack_neg {nd}", bus=nd, p_nom=BIG, p_min_pu=-1, p_max_pu=0, marginal_cost=-pen)

        if not pd.isna(row.demand):
            n.add("Load", f"demand {nd}", bus=nd, p_set=float(row.demand))
            if nd in node_block:
                ends = block_ends(node_block[nd])
                pu = pd.Series(1.0, SNAPSHOTS); pu[ends] = 0.0
                n.add("Store", f"block buffer {nd}", bus=nd, e_nom=BIG, e_min_pu=-pu, e_max_pu=pu)

        if str(row.has_state).lower() == "true":
            loss = float(num(row.frac_state_loss, 0.0))
            cap = float(row.node_state_cap)
            si = stor_inv.loc[nd]
            s_exist = num(si.number_of_storages, 0) + num(si.initial_storages_invested, 0)
            s_max = num(si.number_of_storages, 0) + num(si.candidate_storages, 0)
            e_init = float(storage_ts.get((nd, "fix_node_state"), pd.Series([0.0])).iloc[0])
            sbus = nd
            if loss > 0:
                sbus = f"{nd} store"
                n.add("Bus", sbus)
                n.add("Link", f"{nd} loss-charge", bus0=nd, bus1=sbus, efficiency=1 / (1 + loss), p_nom=BIG)
                n.add("Link", f"{nd} loss-discharge", bus0=sbus, bus1=nd, efficiency=1 + loss, p_nom=BIG)
            n.add("Store", nd, bus=sbus, e_nom_extendable=s_max > s_exist, e_nom=cap * s_exist,
                  e_nom_min=cap * s_exist, e_nom_max=cap * s_max, standing_loss=loss / (1 + loss),
                  capital_cost=float(si.storage_investment_cost) / cap, e_initial=e_init)
            meta["stores"][nd] = dict(cap=cap, inv=float(si.storage_investment_cost))

    # ----- units
    for u, s in specs.items():
        exist, mx = unit_counts(u)
        fom = float(obj_par[u].get("fom_cost", 0))
        committable = obj_par[u].get("online_variable_type") == "unit_online_variable_type_integer"
        if s["kind"] == "generator":
            avail = ts_unit.get((u, "unit_availability_factor"))
            n.add("Generator", u, bus=s["bus"], p_nom=s["cap"] * exist,
                  p_max_pu=avail if avail is not None else 1.0)
            meta["fixed_units"][u] = dict(units=exist, cap=s["cap"], fom=fom, inv=0.0)
            continue
        kw = {f"bus{i}": p[0] for i, p in enumerate(s["ports"])}
        kw.update({("efficiency" if i == 0 else f"efficiency{i + 1}"): e for i, e in enumerate(s["eff"])})
        inv = float(unit_inv.loc[u].unit_investment_cost) if u in unit_inv.index else 0.0
        if committable:
            # integer units_on <= units available forces a full unit in SpineOpt -> fixed at max size
            ref = flow_par[(u, *s["ref"])]
            uon = ts_unit.get((u, "units_on_cost"))
            n.add("Link", u, **kw, p_nom=s["P0"] * mx, marginal_cost=s["vom"], committable=True,
                  min_down_time=int(obj_par[u].get("min_down_time", pd.Timedelta(0)) / RES),
                  up_time_before=1 if num(obj_par[u].get("initial_units_on"), 0) >= 1 else 0,
                  down_time_before=0 if num(obj_par[u].get("initial_units_on"), 0) >= 1 else 1,
                  ramp_limit_up=num(ref.get("ramp_up_limit")), ramp_limit_down=num(ref.get("ramp_down_limit")),
                  ramp_limit_start_up=num(ref.get("start_up_limit")), ramp_limit_shut_down=num(ref.get("shut_down_limit")),
                  stand_by_cost=uon if uon is not None else 0.0)
            meta["fixed_units"][u] = dict(units=mx, cap=s["cap"], fom=fom, inv=inv)
            meta["const_inv_first_window"] += inv * (mx - exist)
        else:
            ext = mx > exist
            n.add("Link", u, **kw, p_nom_extendable=ext, p_nom=s["P0"] * exist, p_nom_min=s["P0"] * exist,
                  p_nom_max=s["P0"] * mx, marginal_cost=s["vom"],
                  capital_cost=(inv + fom * s["cap"] * WIN * H) / s["P0"])
            (meta["ext_units"] if ext else meta["fixed_units"])[u] = dict(units=exist, cap=s["cap"], fom=fom, inv=inv, P0=s["P0"])

    # ----- electrolyzer segments
    u = SEG_UNIT
    exist, mx = unit_counts(u)
    fom = float(obj_par[u].get("fom_cost", 0))
    inv = float(unit_inv.loc[u].unit_investment_cost)
    for k, s in enumerate(SEGMENTS):
        kw = {f"bus{i}": p[0] for i, p in enumerate(s["ports"])}
        kw.update({("efficiency" if i == 0 else f"efficiency{i + 1}"): e for i, e in enumerate(s["eff"])})
        n.add("Link", f"{u}[{k}]", **kw, p_nom_extendable=mx > exist, p_nom=seg_width[k] * s["P0"] * exist,
              p_nom_min=seg_width[k] * s["P0"] * exist, p_nom_max=seg_width[k] * s["P0"] * mx,
              marginal_cost=s["vom"], capital_cost=(inv + fom * s["cap"] * WIN * H) / s["P0"])
    meta["ext_units"][u] = dict(units=exist, cap=SEGMENTS[0]["cap"], fom=fom, inv=inv, P0=SEGMENTS[0]["P0"],
                                segments=[f"{u}[{k}]" for k in range(len(SEGMENTS))])

    # ----- connections: one Link per direction
    for c in CONNS:
        frm = [nd for nd, d in flows_of[c] if d == "from"]
        to = [nd for nd, d in flows_of[c] if d == "to"]
        for (k_to, k_from, R) in ratios.get(c, []):
            n1, n2 = k_from[0], k_to[0]
            if n1 not in frm or n2 not in to:
                continue
            cap_from = float(flow_par.get((c, n1, "from"), {}).get("connection_capacity", np.inf))
            cap_to = float(flow_par.get((c, n2, "to"), {}).get("connection_capacity", np.inf))
            mc = flow_cost.get((c, n1, "from"), 0) + R * flow_cost.get((c, n2, "to"), 0)
            n.add("Link", f"{c} {n1}->{n2}", bus0=n1, bus1=n2, efficiency=R,
                  p_nom=min(cap_from, cap_to / R), marginal_cost=mc)
    return n, meta


n, META = build_network()
n

# %% [markdown]
# ## 4. Custom constraints (`extra_functionality`)
#
# 1. **Electrolyzer segments scale together:** `p_nom[k] = Δop_k / Δop_0 · p_nom[0]` (one capacity,
#    marginal efficiency per load band). Efficiencies fall with load, so the LP fills the bands in
#    order by itself; SpineOpt's `ordered_unit_flow_op` binaries are therefore not binding.
# 2. **Methanol stock at window end:** `e(ch3oh_st) ≥ node_state_min` on the snapshots where SpineOpt
#    sets it (the last hour of windows 1–11).

# %%
NODE_STATE_MIN = {nd: s.reindex(SNAPSHOTS.union(s.index)).ffill().reindex(SNAPSHOTS).fillna(0.0)
                  for (nd, p), s in storage_ts.items() if p == "node_state_min"}
if FINAL_WINDOW_STATE_MIN:
    for nd, smin in NODE_STATE_MIN.items():
        smin.iloc[-1] = smin.max()


def extra_functionality(n: pypsa.Network, sns: pd.Index) -> None:
    m = n.model
    segs = [g for g in META["ext_units"].get(SEG_UNIT, {}).get("segments", []) if g in n.links.index[n.links.p_nom_extendable]]
    p_nom = m["Link-p_nom"] if segs else None
    for k in range(1, len(segs)):
        lhs = p_nom.loc[[segs[k]]].assign_coords(name=[segs[0]]) - seg_width[k] / seg_width[0] * p_nom.loc[[segs[0]]]
        m.add_constraints(lhs == 0, name=f"segment_ratio_{k}")
    e = m["Store-e"]
    for nd, smin in NODE_STATE_MIN.items():
        req = smin.loc[sns]
        req = req[req > 0]
        if len(req):
            m.add_constraints(e.sel(name=nd, snapshot=req.index) >= req.values, name=f"state_min_{nd}")

# %% [markdown]
# ## 5. Rolling-horizon solve
#
# Each window is optimised with `n.optimize(snapshots=window)`. PyPSA carries ramping and
# commitment history from previous windows; store levels and installed capacity are carried by
# setting `e_initial` and `p_nom_min`/`e_nom_min` before the next window (same as SpineOpt:
# investments are fixed history, further increments are allowed and paid for in the window made).

# %%
def capacities(n):
    lk = n.links.p_nom_opt.copy()
    st = n.stores.e_nom_opt.copy()
    return lk, st


records = []
t_start = time.time()
for w_i, sns in enumerate(windows):
    t = time.time()
    lk_before = n.links.p_nom_min.copy()
    st_before = n.stores.e_nom_min.copy()
    status, cond = n.optimize(sns, solver_name=SOLVER, solver_options=SOLVER_OPTIONS,
                              extra_functionality=extra_functionality,
                              assign_all_duals=False, compute_infeasibilities=False, log_to_console=False,
                              io_api="direct", progress=False, include_objective_constant=False)
    assert status == "ok", (w_i, status, cond)
    # carry state & capacity into next window
    n.stores.e_initial = n.stores_t.e.loc[sns[-1]]
    ext_l = n.links.index[n.links.p_nom_extendable]
    ext_s = n.stores.index[n.stores.e_nom_extendable]
    n.links.loc[ext_l, "p_nom_min"] = n.links.loc[ext_l, "p_nom_opt"]
    n.stores.loc[ext_s, "e_nom_min"] = n.stores.loc[ext_s, "e_nom_opt"]
    records.append(dict(window=w_i + 1, start=sns[0], objective=n.objective,
                        lk_before=lk_before, lk_after=n.links.p_nom_opt.copy(),
                        st_before=st_before, st_after=n.stores.e_nom_opt.copy(),
                        seconds=time.time() - t))
    print(f"window {w_i + 1:2d} {sns[0]:%Y-%m-%d %H:%M}  objective {n.objective:14,.0f}  ({time.time() - t:.1f}s)")
print(f"total solve time {time.time() - t_start:.0f}s")

# %% [markdown]
# ## 6. Recompute SpineOpt's objective terms per window

# %%
def window_costs(rec: dict, sns) -> dict:
    lkb, lka, stb, sta = rec["lk_before"], rec["lk_after"], rec["st_before"], rec["st_after"]
    inv_u = fom = 0.0
    for u, d in META["ext_units"].items():
        names = d.get("segments", [u])
        P0_after = lka[names].sum()
        P0_before = lkb[names].sum()
        inv_u += d["inv"] * (P0_after - P0_before) / d["P0"]
        fom += d["fom"] * d["cap"] * (P0_after / d["P0"]) * len(sns) * H
    for u, d in META["fixed_units"].items():
        fom += d["fom"] * d["cap"] * d["units"] * len(sns) * H
    if rec["window"] == 1:
        inv_u += META["const_inv_first_window"]
    inv_s = sum(d["inv"] * (sta[nd] - stb[nd]) / d["cap"] for nd, d in META["stores"].items())

    def mc(df_static, df_t, name):
        v = df_t.marginal_cost[name].loc[sns] if name in df_t.marginal_cost else df_static.marginal_cost[name]
        return v

    var = 0.0
    for name in n.links.index:
        var += (mc(n.links, n.links_t, name) * n.links_t.p0[name].loc[sns]).sum()
    slack = 0.0
    for name in n.generators.index:
        c = (mc(n.generators, n.generators_t, name) * n.generators_t.p[name].loc[sns]).sum()
        if name.startswith("slack"):
            slack += c
        else:
            var += c
    uon = 0.0
    for name in n.links.index[n.links.committable]:
        sb = n.links_t.stand_by_cost[name].loc[sns] if name in n.links_t.stand_by_cost else n.links.stand_by_cost[name]
        uon += (sb * n.links_t.status[name].loc[sns]).sum()
    return dict(unit_investment=inv_u, storage_investment=inv_s, fom=fom, variable=var,
                units_on=uon, slack=slack, total=inv_u + inv_s + fom + var + uon + slack)


costs = pd.DataFrame([window_costs(r, w) for r, w in zip(records, windows)],
                     index=pd.Index([r["window"] for r in records], name="window"))
# consistency check: our decomposition reproduces PyPSA's objective up to the constant
# (investment cost of capacity existing before the window, which PyPSA re-prices via capital_cost)
costs.round(0)

# %% [markdown]
# ## 7. Map results back to SpineOpt variables

# %%
def unit_flows() -> pd.DataFrame:
    out = {}
    for u, s in specs.items():
        if s["kind"] == "generator":
            out[(u, s["bus"], "to")] = n.generators_t.p[u]
            continue
        p0 = n.links_t.p0[u]
        for k in s["ports"]:
            out[(u, *k)] = p0 * s["a"][k] / s["a"][s["bus0"]]
    for k_seg, s in enumerate(SEGMENTS):
        p0 = n.links_t.p0[f"{SEG_UNIT}[{k_seg}]"]
        for k in s["ports"]:
            out[(SEG_UNIT, *k)] = out.get((SEG_UNIT, *k), 0) + p0 * s["a"][k] / s["a"][s["bus0"]]
    return pd.DataFrame(out).loc[SNAPSHOTS[: sum(len(w) for w in windows)]]


def connection_flows() -> pd.DataFrame:
    out = {}
    for name in n.links.index:
        if "->" not in name:
            continue
        c, pair = name.split(" ", 1)
        n1, n2 = pair.split("->")
        out[(c, n1, "from")] = out.get((c, n1, "from"), 0) + n.links_t.p0[name]
        out[(c, n2, "to")] = out.get((c, n2, "to"), 0) - n.links_t.p1[name]
    return pd.DataFrame(out).loc[SNAPSHOTS[: sum(len(w) for w in windows)]]


UF = unit_flows()
CF = connection_flows()
NS = n.stores_t.e[[nd for nd in META["stores"]]].loc[UF.index]

units_invested = {}
for u, d in META["ext_units"].items():
    names = d.get("segments", [u])
    units_invested[u] = records[-1]["lk_after"][names].sum() / d["P0"] - d["units"]
for u, d in META["fixed_units"].items():
    units_invested[u] = d["units"] - unit_counts(u)[0]
storages_invested = {nd: (records[-1]["st_after"][nd]) / d["cap"] for nd, d in META["stores"].items()}

# %% [markdown]
# ## 8. Benchmark against the SpineOpt output

# %%
raw = pd.read_excel(SPINE_OUTPUT_XLSX, header=None)
hdr = raw.iloc[:4, 1:].T.map(str).apply(tuple, axis=1).tolist()
sp = raw.iloc[4:, 1:].apply(pd.to_numeric, errors="coerce")
sp.index = pd.to_datetime(raw.iloc[4:, 0])
sp.columns = pd.MultiIndex.from_tuples(hdr, names=["variable", "object", "direction", "node"])


def spine(var, obj, direction="nan", node="nan") -> pd.Series:
    return sp[(var, obj, direction, node)]


per_window = lambda s: s.dropna().reset_index(drop=True).set_axis(range(1, s.notna().sum() + 1))

nW = len(windows)
cmp_cost = pd.DataFrame({
    "SpineOpt total_costs": per_window(spine("total_costs", "Model")).iloc[:nW],
    "PyPSA total": costs.total.values,
})
cmp_cost["abs diff"] = cmp_cost["PyPSA total"] - cmp_cost["SpineOpt total_costs"]
cmp_cost["rel diff [%]"] = 100 * cmp_cost["abs diff"] / cmp_cost["SpineOpt total_costs"].abs()
cmp_cost.loc["sum"] = [cmp_cost.iloc[:, 0].sum(), cmp_cost.iloc[:, 1].sum(),
                       cmp_cost.iloc[:, 1].sum() - cmp_cost.iloc[:, 0].sum(),
                       100 * (cmp_cost.iloc[:, 1].sum() - cmp_cost.iloc[:, 0].sum()) / abs(cmp_cost.iloc[:, 0].sum())]
print("Objective per window [EUR]")
cmp_cost.round(3)

# %%
inv_rows = []
for u in UNITS:
    s = per_window(spine("units_invested", u, "nan", "realization")).iloc[:nW].sum()
    inv_rows.append(("units_invested", u, s, units_invested.get(u, 0.0)))
for nd in META["stores"]:
    s = per_window(spine("storages_invested", nd, "nan", "realization")).iloc[:nW].sum()
    inv_rows.append(("storages_invested (cum.)", nd, s, storages_invested[nd]))
cmp_inv = pd.DataFrame(inv_rows, columns=["variable", "object", "SpineOpt", "PyPSA"])
cmp_inv["diff"] = cmp_inv.PyPSA - cmp_inv.SpineOpt
print("Investments (fraction of candidate unit; storages cumulative)")
cmp_inv.round(5)

# %%
idx = UF.index
rows = []
for (u, nd, d) in UF.columns:
    s = spine("unit_flow", u, f"{d}_node", nd).loc[idx]
    p = UF[(u, nd, d)]
    rows.append(("unit_flow", u, nd, d, s.sum(), p.sum(), (p - s).abs().max(), np.corrcoef(s, p)[0, 1] if s.std() > 1e-9 and p.std() > 1e-9 else np.nan))
for (c, nd, d) in CF.columns:
    s = spine("connection_flow", c, f"{d}_node", nd).loc[idx]
    p = CF[(c, nd, d)]
    if s.isna().any():  # daily-resolution variable: compare block averages
        s = s.ffill()
    rows.append(("connection_flow", c, nd, d, s.sum(), p.sum(), (p - s).abs().max(), np.corrcoef(s, p)[0, 1] if s.std() > 1e-9 and p.std() > 1e-9 else np.nan))
for nd in NS.columns:
    s = spine("node_state", nd, "nan", "realization").loc[idx]
    p = NS[nd]
    rows.append(("node_state", nd, "", "", s.sum(), p.sum(), (p - s).abs().max(), np.corrcoef(s, p)[0, 1] if s.std() > 1e-9 and p.std() > 1e-9 else np.nan))
cmp_flow = pd.DataFrame(rows, columns=["variable", "object", "node", "dir", "SpineOpt Σ", "PyPSA Σ", "max |hourly diff|", "hourly corr"])
base = cmp_flow["SpineOpt Σ"].abs().where(cmp_flow["SpineOpt Σ"].abs() > 1e-6)
cmp_flow["Σ rel diff [%]"] = 100 * (cmp_flow["PyPSA Σ"] - cmp_flow["SpineOpt Σ"]) / base
print("Flows over the solved horizon (Σ = MWh, t or kg)")
cmp_flow.round(4)

# %% [markdown]
# **Reading the benchmark.**
# * *Degenerate methanol timing.* Delivery timing within a daily block and the matching `ch3oh_st`
#   charge/discharge are degenerate: any split of a day's delivery across its hours costs the same, so
#   the solvers may pick different but equally optimal schedules. Compare those on block totals.
# * *Storage capacity between windows (SpineOpt artefact).* In the SpineOpt run the `ch3oh_st`
#   capacity entering a window is sometimes **lower** than what was bought earlier (e.g. 1,508.6 MWh
#   bought in window 1, yet 102 MWh re-bought in window 6 whose peak is 1,116 MWh). SpineOpt lets
#   `storages_invested_available` fall between rolling windows at no cost and then pays again to
#   re-invest. The replica keeps capacity cumulative (it never disappears), so from window 4 on it
#   saves those re-purchases (about €320 over the year). Because the storage capacity then differs,
#   hourly dispatch in those windows can also differ. Unit investments are unaffected.

# %%
blocks = block_ends(node_block["ch3oh_demand"])
blocks = blocks[blocks <= UF.index[-1]]
grp = np.searchsorted(blocks.values, UF.index.values)          # block id per hour
deliv_sp = spine("connection_flow", "pl_ch3oh_demand", "from_node", "ch3oh").loc[UF.index].groupby(grp).sum()
deliv_py = CF[("pl_ch3oh_demand", "ch3oh", "from")].groupby(grp).sum()
state_end_sp = spine("node_state", "ch3oh_st", "nan", "realization").loc[blocks]
state_end_py = NS["ch3oh_st"].loc[blocks]
print(f"daily-block deliveries: max |diff| = {np.abs(deliv_sp.values - deliv_py.values).max():.2e} MWh over {len(blocks)} blocks")
print(f"ch3oh_st level at block ends: max |diff| = {np.abs(state_end_sp.values - state_end_py.values).max():.2f} MWh")

# %% [markdown]
# ## 9. Charts

# %%
import matplotlib.pyplot as plt

C_SPINE, C_PYPSA = "#2a78d6", "#eb6834"   # categorical slots 1-2 of the validated reference palette
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e6e5e0", "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "axes.edgecolor": "#8a8984", "font.size": 10})

fig, ax = plt.subplots(figsize=(9, 3.6))
x = np.arange(nW)
w = 0.38
ax.bar(x - w / 2 - 0.01, cmp_cost["SpineOpt total_costs"].iloc[:nW] / 1e6, w, color=C_SPINE, label="SpineOpt")
ax.bar(x + w / 2 + 0.01, cmp_cost["PyPSA total"].iloc[:nW] / 1e6, w, color=C_PYPSA, label="PyPSA replica")
ax.axhline(0, color="#8a8984", lw=0.8)
ax.set_xticks(x, [f"W{i + 1}\n{windows[i][0]:%b %d}" for i in range(nW)])
ax.set_ylabel("Window objective [M€]")
ax.set_title("Objective per 730 h window", loc="left")
ax.legend(frameon=False, loc="upper right")
plt.tight_layout(); plt.show()

# %%
wk = UF.index[24 * 14: 24 * 21] if len(UF) >= 24 * 21 else UF.index
fig, axes = plt.subplots(2, 1, figsize=(9, 5.2), sharex=True)
for ax, (title, s_sp, s_py) in zip(axes, [
    ("Electrolyzer power input [MW]", spine("unit_flow", "electrolyzer", "from_node", "power"), UF[("electrolyzer", "power", "from")]),
    ("Grid import [MW]", spine("connection_flow", "pl_wholesale", "from_node", "power_wholesale"), CF[("pl_wholesale", "power_wholesale", "from")]),
]):
    ax.plot(wk, s_sp.loc[wk], color=C_SPINE, lw=2, label="SpineOpt")
    ax.plot(wk, s_py.loc[wk], color=C_PYPSA, lw=2, ls=(0, (3, 2)), label="PyPSA replica")
    ax.set_title(title, loc="left")
axes[0].legend(frameon=False, loc="lower right", ncol=2)
fig.autofmt_xdate()
plt.tight_layout(); plt.show()

# %% [markdown]
# ## 10. Cross-check: PyPSA's native piecewise efficiency (PyPSA ≥ 1.3)
#
# Native piecewise efficiencies need a **fixed** `p_nom`, so they cannot size the electrolyzer.
# As a check of the segment formulation, window 1 is re-solved with every capacity fixed at the
# replica's window-1 result and the 10 segment links replaced by **one** link whose `efficiency`
# (H₂) and `efficiency2` (heat) are piecewise curves. PyPSA's curve is the *realised* efficiency at
# each load point, so the marginal SpineOpt coefficients are integrated first:
# `η_real(op_k) = Σ_{j≤k} η_j Δop_j / op_k`. The operating cost must equal the replica's.

# %%
def native_piecewise_check() -> pd.DataFrame:
    n2, _ = build_network()
    r1 = records[0]
    for name in n2.links.index[n2.links.p_nom_extendable]:
        n2.links.loc[name, ["p_nom", "p_nom_extendable"]] = [r1["lk_after"][name], False]
    for name in n2.stores.index[n2.stores.e_nom_extendable]:
        n2.stores.loc[name, ["e_nom", "e_nom_extendable"]] = [r1["st_after"][name], False]
    segs = META["ext_units"][SEG_UNIT]["segments"]
    P = n2.links.loc[segs, "p_nom"].sum()
    s0 = SEGMENTS[0]
    ports = s0["ports"]
    real = np.cumsum(seg_eff * seg_width) / OP_POINTS            # realised H2 efficiency at each op point
    h2_i = ports.index((h2_key[1], "to"))
    heat_scale = {i: s0["eff"][i - 1] / s0["eff"][h2_i - 1] for i in range(1, len(ports)) if i != h2_i and ports[i][1] == "to"}
    kw = {f"bus{i}": p[0] for i, p in enumerate(ports)}
    for i in range(1, len(ports)):
        key = "efficiency" if i == 1 else f"efficiency{i}"
        if i == h2_i:
            kw[key] = {0.0: 0.0, **dict(zip(OP_POINTS, real))}
        elif i in heat_scale:
            kw[key] = {0.0: 0.0, **dict(zip(OP_POINTS, real * heat_scale[i]))}
        else:
            kw[key] = s0["eff"][i - 1]          # water: constant per MW of power
    n2.remove("Link", segs)
    n2.add("Link", SEG_UNIT, **kw, p_nom=P, marginal_cost=s0["vom"])
    status, _ = n2.optimize(windows[0], solver_name=SOLVER, solver_options=SOLVER_OPTIONS,
                            extra_functionality=extra_functionality, log_to_console=False,
                            io_api="direct", include_objective_constant=False)
    assert status == "ok"
    replica_opex = costs.loc[1, ["variable", "units_on", "slack"]].sum()
    sp_opex = cmp_cost.loc[1, "SpineOpt total_costs"] - per_window(spine("objective_unit_investment_costs", "Model")).iloc[0] \
        - per_window(spine("objective_storage_investment_costs", "Model")).iloc[0] - costs.loc[1, "fom"]
    h2_native = -n2.links_t[f"p{h2_i}"][SEG_UNIT].loc[windows[0]].sum()
    return pd.DataFrame({
        "operating cost window 1 [€]": [sp_opex, replica_opex, n2.objective],
        "electrolyzer H2 window 1 [MWh]": [spine("unit_flow", SEG_UNIT, "to_node", h2_key[1]).loc[windows[0]].sum(),
                                           UF[(SEG_UNIT, h2_key[1], "to")].loc[windows[0]].sum(), h2_native],
    }, index=["SpineOpt (segments + binaries)", "PyPSA replica (segment links)", "PyPSA native piecewise"])


pw_check = native_piecewise_check()
pw_check.round(3)

# %% [markdown]
# ## 11. Summary

# %%
print(f"Windows solved: {nW}")
print(f"Σ objective  SpineOpt {cmp_cost.loc['sum', 'SpineOpt total_costs']:,.2f} €   "
      f"PyPSA {cmp_cost.loc['sum', 'PyPSA total']:,.2f} €   "
      f"(diff {cmp_cost.loc['sum', 'abs diff']:,.2f} €, {cmp_cost.loc['sum', 'rel diff [%]']:.2e} %)")
print(f"max |investment diff| = {cmp_inv['diff'].abs().max():.2e} (fraction of a unit)")
exact = cmp_flow[(cmp_flow["max |hourly diff|"] < 1e-3)]
print(f"{len(exact)}/{len(cmp_flow)} SpineOpt flow/state series reproduced hour-by-hour (|diff| < 1e-3); "
      "see section 8 for why the others differ.")
exact_w = cmp_cost.index[:-1][cmp_cost["abs diff"].iloc[:-1].abs() < 0.01].tolist()
print(f"windows whose objective matches SpineOpt to the cent: {exact_w}")
