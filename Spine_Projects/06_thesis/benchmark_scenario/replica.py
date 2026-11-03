"""SpineOpt → PyPSA replica of the power-to-methanol plant: run one case and print the benchmark.

Thin wrapper around benchmark.run_case.run_case (the model, constraints and cost accounting live in
the benchmark/ package; see CLAUDE.md for the SpineOpt conventions it reproduces). Same command and
environment variables as before:

    INPUT_XLSX, SPINE_OUTPUT_XLSX   relative paths resolve against this script's folder
    SOLVER                          gurobi (default) or highs
    MIPGAP                          overrides the relative MIP gap (quick development runs)
    N_WINDOWS                       e.g. 1 for a quick test; unset = all windows

Structured results (per_window.csv, investments.csv, flows.csv, blocks.csv, meta.json, network.nc)
are also written to results/<case>/ next to this script.
"""

from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from benchmark import Settings
from benchmark.charts import plot_case
from benchmark.run_case import run_case
from benchmark.settings import GAP_OPTION

HERE = Path(__file__).resolve().parent   # relative paths are resolved against the script's folder
INPUT_XLSX = HERE / os.environ.get("INPUT_XLSX", "paper_energy_2024_input_base_10op.xlsx")
SPINE_OUTPUT_XLSX = HERE / os.environ.get("SPINE_OUTPUT_XLSX", "Output_exported_paper_energy_2024_base_10op.xlsx")
SOLVER = os.environ.get("SOLVER", "gurobi")
N_WINDOWS = int(os.environ.get("N_WINDOWS", 0)) or None   # None = full year; e.g. 1 for a quick test
OUT_DIR = HERE / "results"


def main() -> None:
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    logging.getLogger("linopy").setLevel(logging.WARNING)
    warnings.filterwarnings("ignore", category=FutureWarning)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)

    settings = Settings(n_windows=N_WINDOWS, native_piecewise_check=True)
    opts = {GAP_OPTION[SOLVER]: float(os.environ["MIPGAP"])} if os.environ.get("MIPGAP") else None
    r = run_case(INPUT_XLSX, SPINE_OUTPUT_XLSX, solver=SOLVER, solver_options=opts, settings=settings,
                 out_dir=OUT_DIR, log=print)
    pw = r.per_window

    # PyPSA side of SpineOpt's objective terms per window
    terms = ["unit_investment", "storage_investment", "fom", "variable", "units_on", "slack", "total"]
    print(pw[[f"pypsa_{t}" for t in terms]].set_axis(terms, axis=1).round(0))

    cmp_cost = pd.DataFrame({"SpineOpt total_costs": pw.spine_total, "PyPSA total": pw.pypsa_total})
    cmp_cost["abs diff"] = cmp_cost["PyPSA total"] - cmp_cost["SpineOpt total_costs"]
    cmp_cost["rel diff [%]"] = 100 * cmp_cost["abs diff"] / cmp_cost["SpineOpt total_costs"].abs()
    s_sp, s_py = cmp_cost.iloc[:, 0].sum(), cmp_cost.iloc[:, 1].sum()
    cmp_cost.loc["sum"] = [s_sp, s_py, s_py - s_sp, 100 * (s_py - s_sp) / abs(s_sp)]
    print("Objective per window [EUR]")
    print(cmp_cost.round(3))

    cmp_inv = r.investments.rename(columns={"spine": "SpineOpt", "pypsa": "PyPSA"})
    print("Investments (fraction of candidate unit; storages cumulative)")
    print(cmp_inv.round(5))

    cmp_flow = r.flows.rename(columns={"direction": "dir", "spine_sum": "SpineOpt Σ", "pypsa_sum": "PyPSA Σ",
                                       "max_abs_hourly_diff": "max |hourly diff|", "hourly_corr": "hourly corr",
                                       "sum_rel_diff_pct": "Σ rel diff [%]"})
    print("Flows over the solved horizon (Σ = MWh, t or kg)")
    print(cmp_flow.round(4))

    for (bn, kind, obj, nd), g in r.blocks.groupby(["block_node", "kind", "object", "node"], sort=False):
        if kind == "delivery":
            print(f"{bn} block deliveries ({obj} from {nd}): max |diff| = {g['diff'].abs().max():.2e} "
                  f"over {len(g)} blocks")
        else:
            print(f"{obj} level at {bn} block ends: max |diff| = {g['diff'].abs().max():.2f}")

    plot_case(r)
    plt.show()

    if r.native_check is not None:
        print(r.native_check.round(3))

    print(f"Windows solved: {len(pw)}")
    print(f"Σ objective  SpineOpt {cmp_cost.loc['sum', 'SpineOpt total_costs']:,.2f} €   "
          f"PyPSA {cmp_cost.loc['sum', 'PyPSA total']:,.2f} €   "
          f"(diff {cmp_cost.loc['sum', 'abs diff']:,.2f} €, {cmp_cost.loc['sum', 'rel diff [%]']:.2e} %)")
    print(f"max |investment diff| = {cmp_inv['diff'].abs().max():.2e} (fraction of a unit)")
    exact = cmp_flow[(cmp_flow["max |hourly diff|"] < 1e-3)]
    print(f"{len(exact)}/{len(cmp_flow)} SpineOpt flow/state series reproduced hour-by-hour (|diff| < 1e-3); "
          "degenerate in-block delivery timing and the storage re-purchase artefact explain the others (CLAUDE.md).")
    exact_w = cmp_cost.index[:-1][cmp_cost["abs diff"].iloc[:-1].abs() < 0.01].tolist()
    print(f"windows whose objective matches SpineOpt to the cent: {exact_w}")
    print(f"results written to {r.out_dir}")


if __name__ == "__main__":
    main()
