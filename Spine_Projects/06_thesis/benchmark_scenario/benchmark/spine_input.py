"""Parse a SpineOpt Excel input workbook (the 'input_prepared' layout). Side-effect free.

    sheets = read_sheets(path)          # dict of raw sheets (header=None)
    inp = parse_sheets(sheets, path)    # SpineInput
    inp = read_input(path)              # both in one go

The positional sheets (Operating_points, Variable_Eff, Time_series, Time_series_storage,
Energy_prices) are read at fixed row offsets, see DATA_START_ROW; preflight.py checks every input
file against these offsets.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .errors import UnsupportedStructure

# Row at which data starts in the sheets that are read by position.
DATA_START_ROW = {"Operating_points": 4, "Variable_Eff": 5, "Time_series": 3,
                  "Time_series_storage": 2, "Energy_prices": 5}

DIR = {"unit__from_node": "from", "unit__to_node": "to", "connection__from_node": "from", "connection__to_node": "to"}

# fixed ratios  f(n1) = R * f(n2)
RATIO_DIRS = {
    "fix_ratio_in_in_unit_flow": ("from", "from"),
    "fix_ratio_in_out_unit_flow": ("from", "to"),
    "fix_ratio_out_out_unit_flow": ("to", "to"),
    "fix_ratio_out_in_unit_flow": ("to", "from"),
    "fix_ratio_out_in_connection_flow": ("to", "from"),
}


def table(X: dict, sheet: str) -> pd.DataFrame:
    df = X[sheet]
    out = df.iloc[1:].copy()
    out.columns = df.iloc[0].tolist()
    return out.dropna(how="all").reset_index(drop=True)


def num(v, default=np.nan):
    return default if v is None or (isinstance(v, float) and np.isnan(v)) else v


def _dir(rel_class: str, where: str) -> str:
    if rel_class not in DIR:
        raise UnsupportedStructure(f"{where}: relationship class {rel_class!r} is not supported (expected one of {list(DIR)})")
    return DIR[rel_class]


@dataclass
class SpineInput:
    path: Path | None
    sheets: dict = field(repr=False)
    defs: pd.DataFrame = field(repr=False)
    units: list[str]
    nodes: list[str]
    conns: list[str]
    obj_par: dict[str, dict]
    unit_inv: pd.DataFrame = field(repr=False)
    conn_inv: pd.DataFrame = field(repr=False)
    stor_inv: pd.DataFrame = field(repr=False)
    nodes_df: pd.DataFrame = field(repr=False)
    state_nodes: list[str]
    flows_of: dict[str, list[tuple[str, str]]]          # object -> [(node, "from"/"to")]
    flow_par: dict[tuple, dict]                          # (object, node, dir) -> {param: value}
    ratios: dict[str, list]                              # object -> [((n1, d1), (n2, d2), R)]
    ratio_params: set[tuple[str, str]]                   # (object, fix_ratio_* parameter)
    op_unit: str
    op_node: str
    op_points: np.ndarray
    uc_coef: dict[tuple, np.ndarray]                     # (object, node, dir) -> coefficient per op point
    uc_names: list[str]
    model_name: str
    model_par: dict[tuple, dict]                         # (object, parameter) -> parsed JSON value
    default_block: str
    t0: pd.Timestamp
    t1: pd.Timestamp
    res: pd.Timedelta
    roll: pd.Timedelta
    snapshots: pd.DatetimeIndex = field(repr=False)
    win: int                                             # snapshots per rolling window
    windows: list[pd.DatetimeIndex] = field(repr=False)  # all rolling windows
    node_block: dict[str, pd.Timedelta]                  # node -> resolution of its coarser temporal block
    node_block_name: dict[str, str]
    ts_index: pd.Series = field(repr=False)
    ts_unit: dict[tuple, pd.Series] = field(repr=False)
    ep_index: pd.Series = field(repr=False)
    flow_cost: dict[tuple, pd.Series] = field(repr=False)
    ep_skipped_columns: list[str]
    tss_index: pd.Series = field(repr=False)
    storage_ts: dict[tuple, pd.Series] = field(repr=False)

    @property
    def hours_per_snapshot(self) -> float:
        return self.res / pd.Timedelta("1h")


def read_sheets(path: str | Path) -> dict:
    return pd.read_excel(path, sheet_name=None, header=None)


def read_input(path: str | Path) -> SpineInput:
    return parse_sheets(read_sheets(path), Path(path))


def parse_sheets(X: dict, path: Path | None = None) -> SpineInput:
    defs = table(X, "Definition")
    units = defs.loc[defs.Category == "unit", "Object_name"].tolist()
    nodes = defs.loc[defs.Category == "node", "Object_name"].tolist()
    conns = defs.loc[defs.Category == "connection", "Object_name"].tolist()

    # object parameters: obj_par[name][param]
    obj_par: dict[str, dict] = {o: {} for o in defs.Object_name}
    for _, r in table(X, "Definition_parameters").iterrows():
        obj_par[r.Object_name][r.Parameter] = r.Value
    for _, r in table(X, "Definition_parameters_duration").iterrows():
        obj_par[r.Object_name][r.Parameter] = pd.Timedelta(r.Value)

    unit_inv = table(X, "Unit_Inv_Parameters").set_index("Object_name")
    conn_inv = table(X, "Connection_Inv_Parameters").set_index("Object_name")
    stor_inv = table(X, "Storage_Inv_Parameters").set_index("Object_name")
    nodes_df = table(X, "Nodes").set_index("Object_name")
    state_nodes = [nd for nd in nodes_df.index if str(nodes_df.loc[nd].get("has_state")).lower() == "true"]

    # topology: unit / connection  x  node  x  direction
    flows_of: dict[str, list[tuple[str, str]]] = {}
    for _, r in table(X, "Object__to_from_node_definition").iterrows():
        flows_of.setdefault(r.Object_name, []).append((r.Node, _dir(r.Relationship_class_name, "Object__to_from_node_definition")))

    # flow parameters: flow_par[(obj, node, dir)][param]
    flow_par: dict[tuple, dict] = {}
    for _, r in table(X, "Object__to_from_node").iterrows():
        key = (r.Object_name, r.Node, _dir(r.Relationship_class_name, "Object__to_from_node"))
        flow_par.setdefault(key, {})[r.Parameter] = r.Value
    # relationships that only appear in the parameter sheet (e.g. a demand connection) exist in SpineOpt too
    for (o, nd, d) in list(flow_par):
        if (nd, d) not in flows_of.setdefault(o, []):
            flows_of[o].append((nd, d))
    for _, r in table(X, "Boolean_relations").iterrows():
        key = (r.Object_name, r.Node_name, _dir(r.Relationship_class_name, "Boolean_relations"))
        flow_par.setdefault(key, {})[r.Parameter_name] = str(r.Value).lower() == "true"

    ratios: dict[str, list] = {}
    ratio_params: set[tuple[str, str]] = set()
    for _, r in table(X, "Object__node_node").iterrows():
        if r.Parameter not in RATIO_DIRS:
            raise UnsupportedStructure(f"Object__node_node: parameter {r.Parameter!r} on {r.Object_name} is not supported "
                                       f"(expected one of {list(RATIO_DIRS)})")
        d1, d2 = RATIO_DIRS[r.Parameter]
        ratios.setdefault(r.Object_name, []).append(((r.Node1, d1), (r.Node2, d2), float(r.Value)))
        ratio_params.add((r.Object_name, r.Parameter))

    # operating points + user-constraint efficiency curve (Variable_Eff / Operating_points sheets)
    op = X["Operating_points"]
    if op.shape[1] != 2:
        raise UnsupportedStructure(f"Operating_points has {op.shape[1] - 1} value columns; exactly one unit/node is supported")
    op_unit, op_node = op.iloc[1, 1], op.iloc[2, 1]
    op_points = op.iloc[DATA_START_ROW["Operating_points"]:, 1].astype(float).to_numpy()
    ve = X["Variable_Eff"]
    r0 = DATA_START_ROW["Variable_Eff"]
    uc_coef: dict[tuple, np.ndarray] = {}
    for col in range(1, ve.shape[1]):
        d = "from" if "from_node" in str(ve.iloc[0, col]) else "to"
        key = (ve.iloc[2, col], ve.iloc[3, col], d)
        if key in uc_coef:
            raise UnsupportedStructure(f"Variable_Eff: duplicate coefficient column for {key}")
        uc_coef[key] = pd.to_numeric(ve.iloc[r0:, col], errors="coerce").to_numpy()
    uc_names = sorted({str(ve.iloc[1, col]) for col in range(1, ve.shape[1])})

    # model / temporal settings
    model_tab = table(X, "Model")
    model_par = {(r.Object_name, r.Parameter): json.loads(r.Value) for _, r in model_tab.iterrows()}
    model_names = sorted(set(model_tab.loc[model_tab.Object_class_name == "model", "Object_name"]))
    if len(model_names) != 1:
        raise UnsupportedStructure(f"Model sheet defines {len(model_names)} model objects {model_names}; exactly one is supported")
    model_name = model_names[0]
    mr = table(X, "Model_relations")
    default_blocks = mr.loc[mr.iloc[:, 0] == "model__default_temporal_block", mr.columns[4]].tolist()
    if len(default_blocks) != 1:
        raise UnsupportedStructure(f"expected exactly one model__default_temporal_block, found {default_blocks}")
    default_block = default_blocks[0]

    t0 = pd.Timestamp(model_par[(model_name, "model_start")]["data"])
    t1 = pd.Timestamp(model_par[(model_name, "model_end")]["data"])
    res = pd.Timedelta(model_par[(default_block, "resolution")]["data"])
    roll = pd.Timedelta(model_par[(model_name, "roll_forward")]["data"])
    snapshots = pd.date_range(t0, t1, freq=res)
    win = int(roll / res)
    windows = [snapshots[i:i + win] for i in range(0, len(snapshots), win)]

    # node -> coarser temporal block (e.g. a demand node on a daily block)
    node_block, node_block_name = {}, {}
    for _, r in table(X, "Temporal_relations").iterrows():
        node_block[r.Node] = pd.Timedelta(model_par[(r.Temporal_block, "resolution")]["data"])
        node_block_name[r.Node] = r.Temporal_block

    # time series
    ts = X["Time_series"]
    r0 = DATA_START_ROW["Time_series"]
    ts_index = pd.to_datetime(ts.iloc[r0:, 0])
    ts_unit = {(ts.iloc[0, c], ts.iloc[2, c]): pd.Series(ts.iloc[r0:, c].astype(float).values,
                                                       index=ts_index).reindex(snapshots)
               for c in range(1, ts.shape[1])}

    ep = X["Energy_prices"]
    r0 = DATA_START_ROW["Energy_prices"]
    ep_index = pd.to_datetime(ep.iloc[r0:, 0])
    flow_cost: dict[tuple, pd.Series] = {}
    ep_skipped: list[str] = []
    for c in range(1, ep.shape[1]):
        if pd.isna(ep.iloc[1, c]) or pd.isna(ep.iloc[2, c]):
            ep_skipped.append(str(ep.iloc[0, c]))
            continue
        key = (ep.iloc[2, c], ep.iloc[3, c], _dir(ep.iloc[1, c], "Energy_prices"))
        s = pd.Series(ep.iloc[r0:, c].astype(float).values, index=ep_index).reindex(snapshots)
        flow_cost[key] = flow_cost.get(key, 0) + s

    tss = X["Time_series_storage"]
    r0 = DATA_START_ROW["Time_series_storage"]
    tss_index = pd.to_datetime(tss.iloc[r0:, 0])
    storage_ts: dict[tuple, pd.Series] = {}
    for c in range(1, tss.shape[1]):
        s = pd.Series(pd.to_numeric(tss.iloc[r0:, c], errors="coerce").values, index=tss_index)
        storage_ts[(tss.iloc[0, c], tss.iloc[1, c])] = s.dropna()

    return SpineInput(
        path=path, sheets=X, defs=defs, units=units, nodes=nodes, conns=conns, obj_par=obj_par,
        unit_inv=unit_inv, conn_inv=conn_inv, stor_inv=stor_inv, nodes_df=nodes_df, state_nodes=state_nodes,
        flows_of=flows_of, flow_par=flow_par, ratios=ratios, ratio_params=ratio_params,
        op_unit=op_unit, op_node=op_node, op_points=op_points, uc_coef=uc_coef, uc_names=uc_names,
        model_name=model_name, model_par=model_par, default_block=default_block,
        t0=t0, t1=t1, res=res, roll=roll, snapshots=snapshots, win=win, windows=windows,
        node_block=node_block, node_block_name=node_block_name,
        ts_index=ts_index, ts_unit=ts_unit, ep_index=ep_index, flow_cost=flow_cost, ep_skipped_columns=ep_skipped,
        tss_index=tss_index, storage_ts=storage_ts,
    )
