import numpy as np
import pandas as pd

INPUT_PATH = "C:/Users/kar.eco/Downloads/example_output.xlsx"

# ---------------------------------------------------------------------------
# Step 1: read all sheets needed for this part
# ---------------------------------------------------------------------------
inv_cost = pd.read_excel(INPUT_PATH, sheet_name="Inv_cost", header=None)
report_model = pd.read_excel(INPUT_PATH, sheet_name="report__model", header=None)
node_stochastic = pd.read_excel(INPUT_PATH, sheet_name="report__node__stochastic_scenar", header=None)
unit_stochastic = pd.read_excel(INPUT_PATH, sheet_name="report__unit__stochastic_scenar", header=None)

# ---------------------------------------------------------------------------
# Step 2: do the calculations
# ---------------------------------------------------------------------------

# --- Inv_cost: name / unit_cost / lifetime_years / om_rate, by row ---
inv_cost = inv_cost.dropna(subset=[0]).copy()
inv_cost["lifetime_years"] = (
    inv_cost[5].astype(str).str.extract(r"([\d.]+)").astype(float)[0] / 365
)
# columns: 0=name, 4=unit_cost (E), 7=om_rate (H), "lifetime_years" (derived from F)
inv_cost = inv_cost.set_index(inv_cost.index + 1)  # match original Excel row numbers

# --- number of rolling horizons = count of "total_costs" rows in report__model ---
n_horizons = (report_model[2] == "total_costs").sum()

# --- Storage Investment block ---
# "Total share of max" in the original sheet = SUM(...F26282:F26293), which is
# just the rows where report__node__stochastic_scenar's metric column == 'storages_invested'
storages_invested = node_stochastic[node_stochastic[2] == "storages_invested"]
node_headers = node_stochastic.iloc[0]  # e.g. "Report__ch3oh_st__realisation"

storage_investment = {}
for label, storage_name, unit_cost_name in [
    ("methanol", "ch3oh_st", "solar_plant"),  # unit_cost taken from 'solar_plant' in the original sheet - see note below
    ("hydrogen", "h2_st", "h2_st"),
    ("power", "power_st", "power_st"),
]:
    data_col = node_headers[node_headers == f"Report__{storage_name}__realisation"].index[0]
    inv_row = inv_cost.index[inv_cost[0] == storage_name][0]
    unit_cost_row = inv_cost.index[inv_cost[0] == unit_cost_name][0]

    total_share_of_max = storages_invested[data_col].sum()
    total_cost = (
        total_share_of_max
        * inv_cost.loc[unit_cost_row, 4]
        * n_horizons
        * inv_cost.loc[inv_row, "lifetime_years"]
    )
    om = total_cost * inv_cost.loc[inv_row, 7]
    storage_investment[label] = {
        "total_share_of_max": total_share_of_max,
        "total_cost": total_cost,
        "O&M": om,
    }
# NOTE: the original 'methanol' formula multiplies by 'solar_plant's unit cost instead
# of 'ch3oh_st's own cost - looks like a copy-paste bug in the source file, kept here
# on purpose to match the original output.

# --- Unit Investment block ---
# same idea: "Total" in the original sheet = SUM(...2:13), which is just the rows
# where report__unit__stochastic_scenar's metric column == 'units_invested'
units_invested = unit_stochastic[unit_stochastic[2] == "units_invested"]
unit_headers = unit_stochastic.iloc[0]  # e.g. "Report__electrolyzer__realisation"

# every unit present in report__unit__stochastic_scenar
unit_names = [
    name.replace("Report__", "").replace("__realisation", "")
    for name in unit_headers.dropna()
    if str(name).startswith("Report__")
]
# only these units had a total_cost/O&M formula in the original sheet
units_with_cost = {"co2_vaporizer", "dist_tower", "electrolyzer", "excess_heat_exchanger", "o2_liquefier", "steam_plant"}

unit_investment = {}
for name in unit_names:
    data_col = unit_headers[unit_headers == f"Report__{name}__realisation"].index[0]
    total = units_invested[data_col].sum()

    total_cost, om = np.nan, np.nan
    if name in units_with_cost:
        inv_row = inv_cost.index[inv_cost[0] == name][0]
        total_cost = total * inv_cost.loc[inv_row, 4] * n_horizons * inv_cost.loc[inv_row, "lifetime_years"]
        om = total_cost * inv_cost.loc[inv_row, 7]
    unit_investment[name] = {"total": total, "total_cost": total_cost, "O&M": om}

# ---------------------------------------------------------------------------
# Step 3: build the two result dataframes
# ---------------------------------------------------------------------------
storage_investment_df = pd.DataFrame(storage_investment).T
unit_investment_df = pd.DataFrame(unit_investment).T

print(storage_investment_df)
print()
print(unit_investment_df)