"""Recompute SpineOpt's objective terms per window and map PyPSA results back to SpineOpt variables."""

from __future__ import annotations

import pandas as pd
import pypsa

from .units import Segments, unit_counts

COST_TERMS = ["unit_investment", "storage_investment", "fom", "variable", "units_on", "slack"]


def window_costs(n: pypsa.Network, meta: dict, rec: dict, sns, H: float) -> dict:
    """SpineOpt cost terms of one window, with SpineOpt's conventions (see CLAUDE.md)."""
    lkb, lka, stb, sta = rec["lk_before"], rec["lk_after"], rec["st_before"], rec["st_after"]
    inv_u = fom = 0.0
    for u, d in meta["ext_units"].items():
        names = d.get("segments", [u])
        P0_after = lka[names].sum()
        P0_before = lkb[names].sum()
        inv_u += d["inv"] * (P0_after - P0_before) / d["P0"]
        fom += d["fom"] * d["cap"] * (P0_after / d["P0"]) * len(sns) * H
    for u, d in meta["fixed_units"].items():
        fom += d["fom"] * d["cap"] * d["units"] * len(sns) * H
    if rec["window"] == 1:
        inv_u += meta["const_inv_first_window"]
    inv_s = sum(d["inv"] * (sta[nd] - stb[nd]) / d["cap"] for nd, d in meta["stores"].items())

    def mc(df_static, df_t, name):
        return df_t.marginal_cost[name].loc[sns] if name in df_t.marginal_cost else df_static.marginal_cost[name]

    var = 0.0
    for name in n.links.index:
        var += (mc(n.links, n.links_t, name) * n.links_t.p0[name].loc[sns]).sum()
    slack = 0.0
    slack_names = set(meta["slack_generators"])
    for name in n.generators.index:
        c = (mc(n.generators, n.generators_t, name) * n.generators_t.p[name].loc[sns]).sum()
        if name in slack_names:
            slack += c
        else:
            var += c
    uon = 0.0
    for name in n.links.index[n.links.committable]:
        sb = n.links_t.stand_by_cost[name].loc[sns] if name in n.links_t.stand_by_cost else n.links.stand_by_cost[name]
        uon += (sb * n.links_t.status[name].loc[sns]).sum()
    return dict(unit_investment=inv_u, storage_investment=inv_s, fom=fom, variable=var,
                units_on=uon, slack=slack, total=inv_u + inv_s + fom + var + uon + slack)


def solved_index(snapshots: pd.DatetimeIndex, windows: list) -> pd.DatetimeIndex:
    return snapshots[: sum(len(w) for w in windows)]


def unit_flows(n: pypsa.Network, specs: dict, segs: Segments, index: pd.DatetimeIndex) -> pd.DataFrame:
    """Hourly SpineOpt unit_flow per (unit, node, direction)."""
    out = {}
    for u, s in specs.items():
        if s["kind"] == "generator":
            out[(u, s["bus"], "to")] = n.generators_t.p[u]
            continue
        p0 = n.links_t.p0[u]
        for k in s["ports"]:
            out[(u, *k)] = p0 * s["a"][k] / s["a"][s["bus0"]]
    for k_seg, s in enumerate(segs.specs):
        p0 = n.links_t.p0[f"{segs.unit}[{k_seg}]"]
        for k in s["ports"]:
            out[(segs.unit, *k)] = out.get((segs.unit, *k), 0) + p0 * s["a"][k] / s["a"][s["bus0"]]
    return pd.DataFrame(out).loc[index]


def connection_flows(n: pypsa.Network, meta: dict, index: pd.DatetimeIndex) -> pd.DataFrame:
    """Hourly SpineOpt connection_flow per (connection, node, direction)."""
    out = {}
    for name, (c, n1, n2) in meta["connection_links"].items():
        out[(c, n1, "from")] = out.get((c, n1, "from"), 0) + n.links_t.p0[name]
        out[(c, n2, "to")] = out.get((c, n2, "to"), 0) - n.links_t.p1[name]
    return pd.DataFrame(out).loc[index]


def node_states(n: pypsa.Network, meta: dict, index: pd.DatetimeIndex) -> pd.DataFrame:
    return n.stores_t.e[[nd for nd in meta["stores"]]].loc[index]


def investments(inp, meta: dict, last_record: dict) -> tuple[dict, dict]:
    """(units_invested, cumulative storages_invested) at the end of the horizon."""
    units_invested = {}
    for u, d in meta["ext_units"].items():
        names = d.get("segments", [u])
        units_invested[u] = last_record["lk_after"][names].sum() / d["P0"] - d["units"]
    for u, d in meta["fixed_units"].items():
        units_invested[u] = d["units"] - unit_counts(inp, u)[0]
    storages_invested = {nd: last_record["st_after"][nd] / d["cap"] for nd, d in meta["stores"].items()}
    return units_invested, storages_invested
