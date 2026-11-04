"""Scan SpineOpt outputs (no solving) for negative storage states and non-zero node slacks.

    python -m benchmark.output_scan --cases cases.csv --out results/spine_output_scan.csv

One row per (case, storage node): minimum node_state and when it occurs (window, hours before the
first node_state_min timestamp), plus per case the total slack energy per node and direction.
Slack on nodes with a coarser temporal block is reported once per block as a rate and is weighted
by the block length (blocks restart at each window start).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .batch import load_cases
from .spine_input import SpineInput, read_input
from .spine_output import SpineOutput, read_output


def block_weights(inp: SpineInput, node: str, windows) -> pd.Series:
    """Hours represented by each output timestamp of `node` (1 h, or the block length at block starts)."""
    w_all = []
    for w in windows:
        wt = np.ones(len(w))
        if node in inp.node_block:
            step = int(inp.node_block[node] / inp.res)
            wt = np.zeros(len(w))
            for i in range(0, len(w), step):
                wt[i] = min(step, len(w) - i)
        w_all.append(pd.Series(wt * inp.hours_per_snapshot, index=w))
    return pd.concat(w_all)


def slack_energy(inp: SpineInput, sp: SpineOutput) -> dict[str, float]:
    out = {}
    for (v, o, d, nd) in sp.data.columns:
        if v not in ("node_slack_pos", "node_slack_neg"):
            continue
        wt = block_weights(inp, o, inp.windows)
        e = float((sp.data[(v, o, d, nd)].reindex(wt.index).fillna(0.0) * wt).sum())
        if abs(e) > 1e-9:
            out[f"{v.removeprefix('node_')}:{o}"] = e
    return out


def scan_case(case: str, inp: SpineInput, sp: SpineOutput) -> list[dict]:
    slack = slack_energy(inp, sp)
    first_min = {nd: s.index.min() for (nd, p), s in inp.storage_ts.items() if p == "node_state_min" and len(s)}
    win_of = pd.Series(np.concatenate([[i + 1] * len(w) for i, w in enumerate(inp.windows)]),
                       index=inp.snapshots[: sum(len(w) for w in inp.windows)])
    rows = []
    for nd in inp.state_nodes:
        st = sp.object_series("node_state", nd)
        if st is None:
            rows.append(dict(case=case, node=nd, in_output=False))
            continue
        st = st.reindex(win_of.index)
        neg = st[st < -1e-6]
        t_min = st.idxmin()
        fm = first_min.get(nd)
        rows.append(dict(
            case=case, node=nd, in_output=True, min_state=float(st.min()), min_state_time=t_min,
            min_state_window=int(win_of.loc[t_min]), negative_hours=len(neg),
            negative_windows=",".join(str(w) for w in sorted(set(win_of.loc[neg.index]))) if len(neg) else "",
            first_node_state_min=fm,
            negative_only_before_first_min=(bool((neg.index < fm).all()) if (len(neg) and fm is not None) else None),
            slack_total_MWh=sum(abs(v) for v in slack.values()),
            slack_by_node=";".join(f"{k}={v:.4f}" for k, v in sorted(slack.items())),
        ))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m benchmark.output_scan")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out", default="results/spine_output_scan.csv")
    a = ap.parse_args(argv)
    rows = []
    for _, r in load_cases(a.cases).iterrows():
        if not r.enabled:
            continue
        rows += scan_case(r.case, read_input(r.input), read_output(r.output))
        print(f"scanned {r.case}")
    df = pd.DataFrame(rows)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False)
    print(f"wrote {a.out}: {len(df)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
