"""Batch runner over cases.csv: one process per case, resumable, parallel, then tidy collection.

cases.csv columns:
    case, input, output             paths relative to the folder of cases.csv
    enabled                         False = excluded (kept in the file, never run)
    note

Layout under --out-dir (default results/):
    cases/<case>/...                run_case output (per_window.csv, ..., meta.json, network.nc)
    logs/<case>.log                 stdout/stderr of the case process
    batch_status.csv                one row per case of the last batch invocation (appended/updated)
    per_window.parquet, investments.parquet, flows.parquet, blocks.parquet,
    classified_windows.parquet, cases.parquet      tidy tables over all collected cases

Each case runs as `python -m benchmark.run_case ...` in its own process, so a crash or solver
failure is recorded and the batch continues. Cases whose meta.json has status ok / ok_time_limit
are skipped unless --force. Solver threads are split so that workers × threads <= CPU count, and
at most --max-gurobi-instances Gurobi processes run at the same time.

CLI:
    python -m benchmark.batch --cases cases.csv --dry-run
    python -m benchmark.batch --cases cases.csv --workers 3 --max-gurobi-instances 2
    python -m benchmark.batch --cases cases.csv --only base_1op,2050_10op --out-dir results/batch_test
    python -m benchmark.batch --cases cases.csv --collect-only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

DONE = {"ok", "ok_time_limit"}
TABLES = {"per_window": "per_window.csv", "investments": "investments.csv", "flows": "flows.csv",
          "blocks": "blocks.csv", "classified_windows": "classified_windows.csv"}
PACKAGE_ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------------------------------------ cases
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


def case_family(case: str) -> dict:
    """family (base_op / year / only_PV / sens), op points, year, sensitivity parameter and ±% from the name."""
    out = {"family": "other", "op_points": None, "year": None, "sens_parameter": None, "sens_pct": None}
    if m := re.fullmatch(r"base_(\d+)op", case):
        out.update(family="base_op", op_points=int(m[1]))
    elif m := re.fullmatch(r"(\d{4})_(\d+)op", case):
        out.update(family="year", year=int(m[1]), op_points=int(m[2]))
    elif m := re.fullmatch(r"only_PV_(\d+)op", case):
        out.update(family="only_PV", op_points=int(m[1]))
    elif m := re.fullmatch(r"sens_(\d+)op_([A-Za-z]+)_(\d+)p(up|down)(?:_.*)?", case):
        out.update(family="sens", op_points=int(m[1]), sens_parameter=m[2],
                   sens_pct=int(m[3]) * (1 if m[4] == "up" else -1))
    return out


# ------------------------------------------------------------------------------------------------ status
def case_status(case_dir: Path) -> str | None:
    meta = case_dir / "meta.json"
    if not meta.exists():
        return None
    try:
        return json.loads(meta.read_text(encoding="utf-8")).get("status")
    except (json.JSONDecodeError, OSError):
        return "unreadable_meta"


def thread_plan(workers: int, threads: int | None, cpus: int) -> int:
    t = threads if threads is not None else max(1, cpus // max(1, workers))
    if workers * t > cpus:
        raise SystemExit(f"workers × threads = {workers} × {t} = {workers * t} exceeds the {cpus} CPUs")
    return t


# ------------------------------------------------------------------------------------------------ run
def run_one(row, args, threads: int, gurobi_sem: threading.Semaphore | None) -> dict:
    case_root, log_dir = Path(args.out_dir) / "cases", Path(args.out_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / f"{row.case}.log"
    cmd = [sys.executable, "-m", "benchmark.run_case", "--input", row.input, "--output", row.output,
           "--case", row.case, "--out-dir", str(case_root.resolve()), "--solver", args.solver,
           "--threads", str(threads), "--quiet"]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg"}
    sem = gurobi_sem if args.solver == "gurobi" else None
    if sem:
        sem.acquire()
    t0 = time.time()
    try:
        with open(log, "w", encoding="utf-8") as fh:
            fh.write(f"# {' '.join(cmd)}\n# started {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            fh.flush()
            rc = subprocess.run(cmd, cwd=PACKAGE_ROOT, stdout=fh, stderr=subprocess.STDOUT, env=env).returncode
    finally:
        if sem:
            sem.release()
    secs = time.time() - t0
    status = case_status(case_root / row.case) if rc == 0 else "failed"
    tail = ""
    if rc != 0:
        tail = " | ".join(log.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-5:])
    return dict(case=row.case, status=status, returncode=rc, seconds=round(secs, 1), threads=threads,
                log=str(log), error_tail=tail, finished=time.strftime("%Y-%m-%d %H:%M:%S"))


def write_status(path: Path, rows: list[dict]) -> None:
    new = pd.DataFrame(rows)
    if path.exists():
        old = pd.read_csv(path, dtype=str, keep_default_na=False)
        new = pd.concat([old[~old.case.isin(new.case)], new.astype(str)], ignore_index=True)
    new.sort_values("case").to_csv(path, index=False)


# ------------------------------------------------------------------------------------------------ collect
def collect(cases: pd.DataFrame, out_dir: Path) -> dict[str, pd.DataFrame]:
    """Concatenate every case's tables (cases with a readable meta.json) into tidy parquet tables."""
    case_root = out_dir / "cases"
    frames = {k: [] for k in TABLES}
    rows = []
    for _, r in cases.iterrows():
        d = case_root / r.case
        fam = case_family(r.case)
        base = {"case": r.case, "enabled": r.enabled, **fam}
        st = case_status(d) if d.exists() else None
        if not r.enabled:                          # disabled cases stay out of the comparison tables
            rows.append({**base, "status": "excluded", "note": r.get("note", ""), "has_saved_results": st is not None})
            continue
        if st is None:
            rows.append({**base, "status": "not_run"})
            continue
        m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        rows.append({**base, "status": m["status"], "solver": m["solver"]["used"],
                     "n_windows": m["n_windows_solved"], "windows_at_time_limit": ",".join(map(str, m.get("windows_at_time_limit", []))),
                     "solve_seconds": m["solve_seconds_total"], "run_seconds": m["run_seconds_total"],
                     "objective_spine": m["objective_sum"]["spine"], "objective_pypsa": m["objective_sum"]["pypsa"],
                     "objective_diff": m["objective_sum"]["diff"],
                     "max_achieved_gap": max((w.get("achieved_gap") or 0) for w in m["windows"]),
                     "variables": m["windows"][0].get("variables"), "constraints": m["windows"][0].get("constraints"),
                     "binaries": m["windows"][0].get("binaries"),
                     "class_counts": json.dumps(m.get("classification", {}).get("counts", {})),
                     "input_sha256": m["input"]["sha256"], "spine_output_sha256": m["spine_output"]["sha256"],
                     "spine_run_timestamp": m["spine_output"]["run_timestamp"],
                     "packages": json.dumps(m["packages"]), "settings": json.dumps(m["settings"])})
        for k, f in TABLES.items():
            p = d / f
            if p.exists():
                t = pd.read_csv(p)
                frames[k].append(t.assign(**{c: v for c, v in base.items() if c != "enabled"})[
                    ["case", *[c for c in fam], *t.columns]])
    out = {k: pd.concat(v, ignore_index=True) if v else pd.DataFrame() for k, v in frames.items()}
    out["cases"] = pd.DataFrame(rows)
    for k, df in out.items():
        for c in df.columns:                      # mixed-type object columns -> string for parquet
            if df[c].dtype == object:
                df[c] = df[c].map(lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) else str(v))
        df.to_parquet(out_dir / f"{k}.parquet", index=False)
    return out


# ------------------------------------------------------------------------------------------------ main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m benchmark.batch", description="batch runner over cases.csv")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--only", default=None, help="comma-separated case names (default: all enabled)")
    ap.add_argument("--solver", default="gurobi")
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--threads", type=int, default=None, help="solver threads per case (default: CPUs // workers)")
    ap.add_argument("--max-gurobi-instances", type=int, default=None,
                    help="max concurrent Gurobi processes (default: workers)")
    ap.add_argument("--force", action="store_true", help="re-run cases that already have status ok")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--collect-only", action="store_true")
    a = ap.parse_args(argv)

    out_dir = Path(a.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = load_cases(a.cases)
    if a.only:
        want = [c.strip() for c in a.only.split(",") if c.strip()]
        unknown = set(want) - set(cases.case)
        if unknown:
            raise SystemExit(f"unknown cases: {sorted(unknown)}")
        cases = cases.set_index("case").loc[want].reset_index()
    if a.collect_only:
        t = collect(cases, out_dir)
        print({k: len(v) for k, v in t.items()})
        return 0

    cpus = os.cpu_count() or 1
    threads = thread_plan(a.workers, a.threads, cpus)
    gmax = a.max_gurobi_instances or a.workers
    plan = []
    for _, r in cases.iterrows():
        st = case_status(out_dir / "cases" / r.case)
        action = "excluded" if not r.enabled else ("skip (done)" if st in DONE and not a.force else "run")
        plan.append((r, action, st))
    n_run = sum(1 for _, act, _ in plan if act == "run")
    print(f"CPUs {cpus}; workers {a.workers} × {threads} solver threads = {a.workers * threads}; "
          f"solver {a.solver}" + (f"; max Gurobi instances {gmax} (effective parallel cases {min(a.workers, gmax)})"
                                  if a.solver == "gurobi" else ""))
    print(f"{len(plan)} cases: {n_run} to run, {sum(1 for _, x, _ in plan if x.startswith('skip'))} skipped, "
          f"{sum(1 for _, x, _ in plan if x == 'excluded')} excluded; out-dir {out_dir}")
    for r, act, st in plan:
        f = case_family(r.case)
        print(f"  {r.case:32} {act:12} previous status {st or '-':14} family {f['family']}"
              + (f" {f['sens_parameter']} {f['sens_pct']:+d}%" if f["family"] == "sens" else ""))
    if a.dry_run:
        return 0

    sem = threading.Semaphore(gmax) if a.solver == "gurobi" else None
    results = [dict(case=r.case, status="excluded", returncode="", seconds="", threads="", log="",
                    error_tail=r.get("note", ""), finished="") for r, act, _ in plan if act == "excluded"]
    todo = [r for r, act, _ in plan if act == "run"]
    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as ex:
        futs = {ex.submit(run_one, r, a, threads, sem): r.case for r in todo}
        for f in as_completed(futs):
            res = f.result()
            results.append(res)
            write_status(out_dir / "batch_status.csv", [res])
            print(f"{res['case']}: {res['status']} ({res['seconds']} s)" + (f"  {res['error_tail']}" if res["error_tail"] else ""),
                  flush=True)
    write_status(out_dir / "batch_status.csv", results)
    t = collect(cases, out_dir)
    print("collected:", {k: len(v) for k, v in t.items()})
    return 1 if any(r["status"] == "failed" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
