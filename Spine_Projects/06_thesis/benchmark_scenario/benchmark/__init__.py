"""SpineOpt -> PyPSA benchmark package.

Importing this package (or any module in it) never reads files or solves anything.

    from benchmark.run_case import run_case
    result = run_case("input.xlsx", "Output_exported.xlsx", solver="gurobi")

CLI:  python -m benchmark.run_case --input ... --output ... --solver gurobi
"""

from .errors import UnsupportedStructure
from .settings import DEFAULT_SOLVER_OPTIONS, Settings

__all__ = ["DEFAULT_SOLVER_OPTIONS", "Settings", "UnsupportedStructure"]
