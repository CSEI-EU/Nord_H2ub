"""Regression test: base_10op through run_case reproduces the validated SpineOpt result.

    pytest tests/test_base_10op.py                    # both solvers (env BENCH_SOLVERS=gurobi,highs)
    python tests/test_base_10op.py --solver highs     # without pytest

Asserted:
* per-window total cost within 0.01 € of SpineOpt for windows 1, 2, 3, 5, 8, 11, 12. Windows 4, 6, 7,
  9 and 10 depend on a degenerate storage path (CLAUDE.md artefact 2) and are not asserted.
* unit investments within 1e-6 of SpineOpt's exact values read from the output file, and within
  5e-6 (half a unit in the 5th decimal) of the 5-decimal reference values in CLAUDE.md. The reference
  values are rounded (e.g. steam_plant 0.0175757510 vs 0.01758), so 1e-6 against them is impossible.
* every window solved to optimality with the requested solver.

Each full run takes several minutes; the result is solved once per solver and reused.
"""

from __future__ import annotations

import argparse
import functools
import logging
import os
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from benchmark.run_case import run_case  # noqa: E402

INPUT = HERE / "paper_energy_2024_input_base_10op.xlsx"
OUTPUT = HERE / "Output_exported_paper_energy_2024_base_10op.xlsx"
ASSERTED_WINDOWS = [1, 2, 3, 5, 8, 11, 12]
NOT_ASSERTED_WINDOWS = [4, 6, 7, 9, 10]
COST_TOL = 0.01
REFERENCE_INVESTMENTS = {"electrolyzer": 0.82803, "co2_vaporizer": 0.06176, "dist_tower": 0.46896,
                         "ch3oh_reactor": 1.0, "steam_plant": 0.01758}
INV_TOL_EXACT = 1e-6
INV_TOL_REFERENCE = 5e-6
SOLVERS = [s for s in os.environ.get("BENCH_SOLVERS", "gurobi,highs").split(",") if s]


@functools.lru_cache(maxsize=None)
def result(solver: str):
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    logging.getLogger("linopy").setLevel(logging.WARNING)
    warnings.filterwarnings("ignore", category=FutureWarning)
    out = Path(os.environ.get("BENCH_TEST_OUT") or tempfile.mkdtemp(prefix="bench_")) / solver
    return run_case(INPUT, OUTPUT, solver=solver, out_dir=out)


def check_solved(r, solver):
    assert r.status == "ok", r.status
    assert r.meta["solver"]["used"] == solver, r.meta["solver"]
    assert r.meta["n_windows_solved"] == 12
    assert all(w["termination_condition"] == "optimal" for w in r.meta["windows"]), \
        [(w["window"], w["termination_condition"]) for w in r.meta["windows"]]


def check_window_costs(r):
    pw = r.per_window
    bad = {w: pw.loc[w, "diff_total"] for w in ASSERTED_WINDOWS if not abs(pw.loc[w, "diff_total"]) <= COST_TOL}
    assert not bad, f"windows outside ±{COST_TOL} €: {bad}"


def check_investments(r):
    inv = r.investments.set_index(["variable", "object"])
    errors = []
    for u, ref in REFERENCE_INVESTMENTS.items():
        row = inv.loc[("units_invested", u)]
        if not abs(row.pypsa - row.spine) <= INV_TOL_EXACT:
            errors.append(f"{u}: PyPSA {row.pypsa:.10f} vs SpineOpt {row.spine:.10f}")
        if not abs(row.pypsa - ref) <= INV_TOL_REFERENCE:
            errors.append(f"{u}: PyPSA {row.pypsa:.10f} vs reference {ref}")
    assert not errors, errors


try:
    import pytest

    @pytest.mark.parametrize("solver", SOLVERS)
    def test_solved(solver):
        check_solved(result(solver), solver)

    @pytest.mark.parametrize("solver", SOLVERS)
    def test_window_costs(solver):
        check_window_costs(result(solver))

    @pytest.mark.parametrize("solver", SOLVERS)
    def test_unit_investments(solver):
        check_investments(result(solver))
except ImportError:      # pytest not installed: use the __main__ entry point
    pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver", default="gurobi")
    a = ap.parse_args()
    r = result(a.solver)
    pw = r.per_window
    print(f"solver {a.solver}: results in {r.out_dir}")
    print(pw[["spine_total", "pypsa_total", "diff_total"]].round(4).to_string())
    print(r.investments.round(10).to_string())
    failed = 0
    for name, check in [("solved", lambda: check_solved(r, a.solver)), ("window costs", lambda: check_window_costs(r)),
                        ("unit investments", lambda: check_investments(r))]:
        try:
            check()
            print(f"PASS {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {name}: {e}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
