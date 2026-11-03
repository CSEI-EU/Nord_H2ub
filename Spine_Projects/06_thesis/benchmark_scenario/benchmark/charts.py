"""Charts for a CaseResult. Data-driven: only series present in both models are drawn."""

from __future__ import annotations

import numpy as np
import pandas as pd

C_SPINE, C_PYPSA = "#2a78d6", "#eb6834"   # categorical slots 1-2 of the validated reference palette


def week_series(result) -> list[tuple[str, pd.Series, pd.Series]]:
    """Operating-point unit's load flow, plus every connection flow out of a balance_type_none node."""
    sp, UF, CF = result.spine, result.hourly["unit_flows"], result.hourly["connection_flows"]
    seg_unit, seg_node = result.meta["operating_point_unit"]
    out = []
    if (seg_unit, seg_node, "from") in UF and sp.has("unit_flow", seg_unit, "from_node", seg_node):
        out.append((f"{seg_unit} input from {seg_node}", sp.series("unit_flow", seg_unit, "from_node", seg_node),
                    UF[(seg_unit, seg_node, "from")]))
    for c, nd in result.meta["external_supply_flows"]:
        if (c, nd, "from") in CF and sp.has("connection_flow", c, "from_node", nd):
            out.append((f"{c} flow from {nd}", sp.series("connection_flow", c, "from_node", nd), CF[(c, nd, "from")]))
    return out


def plot_case(result) -> list:
    import matplotlib.pyplot as plt

    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                         "grid.color": "#e6e5e0", "grid.linewidth": 0.6, "axes.axisbelow": True,
                         "axes.edgecolor": "#8a8984", "font.size": 10})
    figs = []
    pw = result.per_window
    nW = len(pw)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    x = np.arange(nW)
    w = 0.38
    ax.bar(x - w / 2 - 0.01, pw.spine_total / 1e6, w, color=C_SPINE, label="SpineOpt")
    ax.bar(x + w / 2 + 0.01, pw.pypsa_total / 1e6, w, color=C_PYPSA, label="PyPSA replica")
    ax.axhline(0, color="#8a8984", lw=0.8)
    ax.set_xticks(x, [f"W{i}\n{t:%b %d}" for i, t in zip(pw.index, pw.start)])
    ax.set_ylabel("Window objective [M€]")
    ax.set_title(f"Objective per {pw.hours.iloc[0]:g} h window", loc="left")
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    figs.append(fig)

    series = week_series(result)
    if series:
        idx = result.hourly["unit_flows"].index
        step = idx[1] - idx[0] if len(idx) > 1 else pd.Timedelta("1h")
        a, b = int(pd.Timedelta("14D") / step), int(pd.Timedelta("21D") / step)
        wk = idx[a:b] if len(idx) >= b else idx
        fig, axes = plt.subplots(len(series), 1, figsize=(9, 2.6 * len(series)), sharex=True, squeeze=False)
        for ax, (title, s_sp, s_py) in zip(axes[:, 0], series):
            ax.plot(wk, s_sp.loc[wk], color=C_SPINE, lw=2, label="SpineOpt")
            ax.plot(wk, s_py.loc[wk], color=C_PYPSA, lw=2, ls=(0, (3, 2)), label="PyPSA replica")
            ax.set_title(title, loc="left")
        axes[0, 0].legend(frameon=False, loc="lower right", ncol=2)
        fig.autofmt_xdate()
        fig.tight_layout()
        figs.append(fig)
    return figs
