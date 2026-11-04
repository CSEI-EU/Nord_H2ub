"""Run several cases from a cases.csv, one after another in one process.

cases.csv columns:
    case, input, output             paths relative to the folder of cases.csv
    enabled                         False = excluded (kept in the file, never run)
    note

CLI:
    python -m benchmark.batch --cases cases.csv --only base_1op,base_20op --solver gurobi --out-dir results
"""

from __future__ import annotations

import argparse
import logging
import traceback
import warnings
from pathlib import Path

import pandas as pd

from .errors import UnsupportedStructure
from .settings import Settings


def _bool(v) -> bool | None:
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "":
        return None
    s = str(v).strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no"):
        return False
    raise ValueError(f"cannot read {v!r} as a boolean")


def load_cases(path: str | Path) -> pd.DataFrame:
    path = Path(path).resolve()
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = {"case", "input", "output", "enabled"} - set(df.columns)
    if missing:
        raise ValueError(f"{path.name}: missing columns {sorted(missing)}")
    df["enabled"] = df["enabled"].map(lambda v: bool(_bool(v)))
    for col in ("input", "output"):
        df[col] = df[col].map(lambda p: str((path.parent / p).resolve()) if p else "")
    if df.case.duplicated().any():
        raise ValueError(f"{path.name}: duplicate case names {df.case[df.case.duplicated()].tolist()}")
    return df


def main(argv=None) -> int:
    from .run_case import run_case

    ap = argparse.ArgumentParser(prog="python -m benchmark.batch")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--only", default=None, help="comma-separated case names (default: all enabled)")
    ap.add_argument("--solver", default="gurobi")
    ap.add_argument("--out-dir", default="results")
    a = ap.parse_args(argv)
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    logging.getLogger("linopy").setLevel(logging.WARNING)
    warnings.filterwarnings("ignore", category=FutureWarning)

    cases = load_cases(a.cases)
    if a.only:
        want = [c.strip() for c in a.only.split(",") if c.strip()]
        unknown = set(want) - set(cases.case)
        if unknown:
            raise SystemExit(f"unknown cases: {sorted(unknown)}")
        cases = cases.set_index("case").loc[want].reset_index()
    failed = 0
    for _, row in cases.iterrows():
        if not row.enabled:
            print(f"{row.case}: excluded ({row.get('note', '')})")
            continue
        try:
            r = run_case(row.input, row.output, solver=a.solver, settings=Settings(),
                         out_dir=a.out_dir, case=row.case)
            o = r.meta["objective_sum"]
            print(f"{row.case}: {r.status}; Σ SpineOpt {o['spine']:,.2f} €  PyPSA {o['pypsa']:,.2f} €  "
                  f"diff {o['diff']:,.2f} €; solve {r.meta['solve_seconds_total']:.0f} s")
        except UnsupportedStructure as e:
            failed += 1
            print(f"{row.case}: UNSUPPORTED\n{e}")
        except Exception:                       # noqa: BLE001 - keep going with the next case
            failed += 1
            print(f"{row.case}: ERROR\n{traceback.format_exc()}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
