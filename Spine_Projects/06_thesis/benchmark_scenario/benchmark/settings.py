"""Run settings. The defaults are the values the replica was validated with on base_10op."""

from __future__ import annotations

from dataclasses import asdict, dataclass

# Mirrors db_mip_solver_options in the SpineOpt input (mip_rel_gap 1e-10, time_limit 3000 s).
DEFAULT_SOLVER_OPTIONS: dict[str, dict] = {
    "gurobi": {"MIPGap": 1e-10, "TimeLimit": 3000, "OutputFlag": 0},
    "highs": {"mip_rel_gap": 1e-10, "time_limit": 3000.0, "presolve": "on", "output_flag": False},
}
GAP_OPTION = {"gurobi": "MIPGap", "highs": "mip_rel_gap"}


@dataclass(frozen=True)
class Settings:
    # SpineOpt's base_10op run kept the final node_state_min also at the last hour of the horizon,
    # although the input only sets it at the ends of windows 1..n-1. True reproduces that run.
    # Whether other runs did the same must be decided per case from their output (CLAUDE.md).
    final_window_state_min: bool = True
    # SpineOpt adds node_slack_pos/neg at node_slack_penalty on balance_type_node nodes.
    include_slacks: bool = True
    # None = all rolling windows; e.g. 1 for a quick test.
    n_windows: int | None = None
    # Size of "unbounded" sources/sinks (balance_type_none), demand buffers and loss links.
    big: float = 1e6
    # Solver options merged over DEFAULT_SOLVER_OPTIONS[solver]; None = defaults only.
    solver_options: dict | None = None
    # Re-solve window 1 with PyPSA's native piecewise efficiency as a check of the segment links.
    native_piecewise_check: bool = False

    def resolved_solver_options(self, solver: str) -> dict:
        return {**DEFAULT_SOLVER_OPTIONS.get(solver, {}), **(self.solver_options or {})}

    def to_dict(self, solver: str) -> dict:
        d = asdict(self)
        d["resolved_solver_options"] = self.resolved_solver_options(solver)
        return d
