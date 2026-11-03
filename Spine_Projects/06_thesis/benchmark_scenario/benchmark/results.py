"""CaseResult: structured result of one benchmark case, and how it is written to disk."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [_jsonable(v) for v in (sorted(o) if isinstance(o, set) else o)]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return float(o) if math.isfinite(o) else None
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp, pd.Timedelta, Path)):
        return str(o)
    return o


@dataclass
class CaseResult:
    case: str
    per_window: pd.DataFrame      # both models' cost terms per window
    investments: pd.DataFrame
    flows: pd.DataFrame
    blocks: pd.DataFrame
    meta: dict
    network: object = field(repr=False)                     # pypsa.Network after the rolling-horizon solve
    unit_ports: pd.DataFrame = field(repr=False, default=None)
    hourly: dict = field(repr=False, default_factory=dict)  # PyPSA series mapped to SpineOpt variables
    spine: object = field(repr=False, default=None)         # SpineOutput
    native_check: pd.DataFrame | None = None
    out_dir: Path | None = None

    @property
    def status(self) -> str:
        return self.meta.get("status", "unknown")

    def write(self, case_dir: Path) -> Path:
        case_dir = Path(case_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        self.per_window.to_csv(case_dir / "per_window.csv")
        self.investments.to_csv(case_dir / "investments.csv", index=False)
        self.flows.to_csv(case_dir / "flows.csv", index=False)
        self.blocks.to_csv(case_dir / "blocks.csv", index=False)
        if self.native_check is not None:
            self.native_check.to_csv(case_dir / "native_piecewise_check.csv")
        (case_dir / "meta.json").write_text(json.dumps(_jsonable(self.meta), indent=2), encoding="utf-8")
        self.network.export_to_netcdf(case_dir / "network.nc")
        self.out_dir = case_dir
        return case_dir
