"""Re-classify saved case results (no solving) and re-collect the tidy tables.

    python -m benchmark.reclassify --cases cases.csv --out-dir results [--only a,b]

For every case with a meta.json under <out-dir>/cases/<case>/: rebuild the hourly PyPSA series from
network.nc with the package's own mapping, re-run benchmark.classify on the saved per_window.csv,
overwrite classified_windows.csv and the meta.json "classification" entry, then collect the parquet
tables exactly as benchmark.batch does.
"""

from __future__ import annotations

import argparse
import json
import logging
import warnings
from pathlib import Path

import pandas as pd

from .batch import collect, load_cases


def reclassify_case(case_dir: Path) -> dict:
    import pypsa

    from .accounting import connection_flows, node_states, solved_index, unit_flows
    from .classify import classify_windows
    from .results import _jsonable
    from .settings import GAP_OPTION
    from .spine_input import read_input
    from .spine_output import read_output
    from .units import operating_segments, unit_counts, unit_specs

    m = json.loads((case_dir / "meta.json").read_text(encoding="utf-8"))
    inp, sp = read_input(m["input"]["path"]), read_output(m["spine_output"]["path"])
    n = pypsa.Network(str(case_dir / "network.nc"))
    segs, specs = operating_segments(inp), unit_specs(inp)
    windows = inp.windows[: m["n_windows_solved"]]
    idx = solved_index(inp.snapshots, windows)
    links = {nm: (nm.split(" ", 1)[0], *nm.split(" ", 1)[1].split("->")) for nm in n.links.index if "->" in nm}
    meta = {"connection_links": links, "stores": {nd: None for nd in inp.state_nodes}}
    hourly = {"unit_flows": unit_flows(n, specs, segs, idx), "connection_flows": connection_flows(n, meta, idx),
              "node_states": node_states(n, meta, idx)}
    unit_fom = {u: (float(inp.obj_par[u].get("fom_cost", 0)), (segs.specs[0] if u == segs.unit else specs[u])["cap"],
                    unit_counts(inp, u)[0]) for u in inp.units}
    pw = pd.read_csv(case_dir / "per_window.csv", index_col="window", parse_dates=["start"])
    solver = m["solver"]["requested"]
    cl, notes = classify_windows(inp, sp, pw, hourly, m["windows"], m["solver"]["options"].get(GAP_OPTION.get(solver)),
                                 m["units_invested"], unit_fom, windows, specs=specs, segs=segs)
    notes["counts"] = cl["class"].value_counts().to_dict()
    cl.to_csv(case_dir / "classified_windows.csv", index=False)
    m["classification"] = notes
    (case_dir / "meta.json").write_text(json.dumps(_jsonable(m), indent=2), encoding="utf-8")
    return notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m benchmark.reclassify")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--only", default=None)
    a = ap.parse_args(argv)
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore", category=FutureWarning)
    out_dir = Path(a.out_dir).resolve()
    cases = load_cases(a.cases)
    names = [c.strip() for c in a.only.split(",")] if a.only else list(cases.case)
    for c in names:
        d = out_dir / "cases" / c
        if not (d / "meta.json").exists():
            continue
        notes = reclassify_case(d)
        print(f"{c}: {notes['counts']}  R4b: {notes['r4b'].get('reclassified_windows', notes['r4b'].get('reason'))}",
              flush=True)
    t = collect(cases, out_dir)
    print("collected:", {k: len(v) for k, v in t.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
