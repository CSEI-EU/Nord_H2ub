"""Read a SpineOpt exported output workbook (Spine Toolbox exporter layout). Side-effect free.

Layout: one sheet named 'Run SpineOpt@<timestamp>'; four header rows (variable, object, direction,
node-or-scenario) and a datetime index in column 0. Rolling-window outputs (total_costs,
objective_*, units_invested, ...) have one value per window.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

NA = "nan"   # how empty header cells read after str()


@dataclass
class SpineOutput:
    path: Path
    sheet_name: str
    run_timestamp: str | None
    data: pd.DataFrame = field(repr=False)   # columns: MultiIndex (variable, object, direction, node)

    def has(self, var: str, obj: str, direction: str = NA, node: str = NA) -> bool:
        return (var, obj, direction, node) in self.data.columns

    def series(self, var: str, obj: str, direction: str = NA, node: str = NA) -> pd.Series:
        return self.data[(var, obj, direction, node)]

    def variables(self) -> list[str]:
        return sorted(set(self.data.columns.get_level_values(0)))

    def entries(self, var: str) -> list[tuple[str, str, str]]:
        """(object, direction, node) of every column of `var`."""
        return [c[1:] for c in self.data.columns if c[0] == var]

    def object_series(self, var: str, obj: str) -> pd.Series | None:
        """The single column of an object-level variable (node level = stochastic scenario), or None."""
        cols = [c for c in self.data.columns if c[0] == var and c[1] == obj and c[2] == NA]
        if len(cols) > 1:
            raise ValueError(f"{var}/{obj}: {len(cols)} columns (several stochastic scenarios?) {cols}")
        return self.data[cols[0]] if cols else None

    def per_window(self, s: pd.Series) -> pd.Series:
        """Values of a once-per-window output, indexed 1..n."""
        return s.dropna().reset_index(drop=True).set_axis(range(1, s.notna().sum() + 1))


def run_timestamp_from_sheet(name: str) -> str | None:
    m = re.search(r"@(\d{4}-\d{2}-\d{2})T(\d{2})(\d{2})(\d{2})", name)
    return f"{m.group(1)}T{m.group(2)}:{m.group(3)}:{m.group(4)}" if m else None


def read_output(path: str | Path) -> SpineOutput:
    path = Path(path)
    sheets = pd.ExcelFile(path).sheet_names
    if len(sheets) != 1:
        raise ValueError(f"{path.name}: expected one output sheet, found {sheets}")
    raw = pd.read_excel(path, sheet_name=sheets[0], header=None)
    hdr = raw.iloc[:4, 1:].T.map(str).apply(tuple, axis=1).tolist()
    sp = raw.iloc[4:, 1:].apply(pd.to_numeric, errors="coerce")
    sp.index = pd.to_datetime(raw.iloc[4:, 0])
    sp.columns = pd.MultiIndex.from_tuples(hdr, names=["variable", "object", "direction", "node"])
    return SpineOutput(path=path, sheet_name=sheets[0], run_timestamp=run_timestamp_from_sheet(sheets[0]), data=sp)
