"""
Kassø PtX hub -- PyPSA model, build step 2
==========================================

Scope of this step (see model doc, scenario S1):
  * electricity side: PV, shared grid connection, RFNBO bus and general bus
  * PEM electrolyser, H2 tank (existing + extension), MSU, methanol target
  * PEM by-products (O2, low-temperature heat) are simply vented / dumped
  * CO2 is supplied by a FREE STAND-IN generator -- it will be replaced by
    the biogas -> CCPP -> CPU chain in step 3

Run:   python kasso_step2.py
Needs: pypsa >= 1.0, gurobipy + a full Gurobi licence
       (the pip package alone only has a size-limited licence, too small
       for 8760 hours). To fall back to HiGHS: pip install highspy and set
       SOLVER = "highs" below.

Time series
-----------
Put two CSV files next to this script (one column, 8760 rows, header line):
    data/pv_cf.csv        PV capacity factor  [-]      (renewables.ninja)
    data/price_dk1.csv    DK1 day-ahead price [EUR/MWh] (Energinet)
Both MUST be from the same weather/price year. If a file is missing, the
script falls back to a crude synthetic profile and says so loudly -- the
numbers are then only good for checking that the model works.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

# =====================================================================
# 1. Parameters  (symbols as in the model doc)
# =====================================================================
P = dict(
    year=2023,  # snapshot year; must match the time series
    # --- fixed plant ------------------------------------------------
    P_PV=304.0,  # MW
    P_PEM=52.5,  # MW electricity in
    P_MSU=4.8,  # t MeOH/h
    P_grid=304.0,  # MW, shared connection
    E_H2_exist=3.3,  # t
    H2_cushion=0.0,  # t that can never be withdrawn (MSU pressure); set later
    M_tar=32_000.0,  # t MeOH/yr
    # --- PEM (per MWh electricity) ------------------------------------
    eta_H2_PEM=0.0182,  # t H2/MWh
    eta_O2_PEM=0.144,  # t O2/MWh
    eta_q_PEM=0.20,  # MWh heat/MWh
    # --- MSU (per t methanol) ----------------------------------------
    eta_H2_MSU=0.193,  # t H2/t MeOH
    eta_CO2_MSU=1.416,  # t CO2/t MeOH
    e_MSU=0.15,  # MWh/t MeOH
    # --- grid ---------------------------------------------------------
    tau_imp=11.70,  # EUR/MWh
    tau_exp=0.0,  # EUR/MWh
    # --- economics ----------------------------------------------------
    wacc=0.08,
    lifetime=20,
    # PLACEHOLDERS -- replace with DEA / Giehl values
    capex_H2_tank=500_000.0,  # EUR per t H2 storage (~500 EUR/kg)
    fom_H2_tank=0.02,  # share of capex per year
    c_var_PEM=0.0,  # EUR/MWh electricity in
    c_var_MSU=0.0,  # EUR/t MeOH
)


SOLVER = "gurobi"
SOLVER_OPTIONS = {
    "gurobi": {
        "Method": 2,       # barrier: fastest for large LPs like this one
        "Crossover": 0,    # skip crossover; set to -1 if you need exact vertex solutions / clean duals
        "BarConvTol": 1e-6,
        "Threads": 4,
    },
    "highs": {},
}[SOLVER]


def crf(i: float, n: int) -> float:
    """Capital recovery factor, Eq. (crf)."""
    return i * (1 + i) ** n / ((1 + i) ** n - 1)


def annual_cost(capex: float, fom_share: float) -> float:
    """Annualised capex + fixed O&M per unit of capacity (EUR/unit/yr)."""
    return capex * (crf(P["wacc"], P["lifetime"]) + fom_share)


# =====================================================================
# 2. Time series
# =====================================================================
HERE = Path(__file__).parent
snapshots = pd.date_range(f"{P['year']}-01-01", periods=8760, freq="h")


def load_series(fname: str, synthetic) -> pd.Series:
    path = HERE / "data" / fname
    if path.exists():
        s = pd.read_csv(path).iloc[:, -1].to_numpy(dtype=float)
        if len(s) != 8760:
            raise ValueError(f"{fname}: expected 8760 rows, got {len(s)}")
        return pd.Series(s, index=snapshots)
    print(f"!! {path} not found -- using a SYNTHETIC profile for {fname}")
    return pd.Series(synthetic(), index=snapshots)


def synthetic_pv():
    h = snapshots.hour.to_numpy()
    doy = snapshots.dayofyear.to_numpy()
    day = np.clip(np.sin((h - 5) / 14 * np.pi), 0, None)
    season = 0.35 + 0.65 * np.sin((doy - 80) / 365 * 2 * np.pi) ** 2 * (
        (doy > 80) & (doy < 265)
    ) + 0.2
    cloud = np.random.default_rng(1).uniform(0.3, 1.0, 8760)
    return np.clip(0.8 * day * season * cloud, 0, 1)


def synthetic_price():
    rng = np.random.default_rng(2)
    h = snapshots.hour.to_numpy()
    base = 80 + 25 * np.cos((h - 19) / 24 * 2 * np.pi)  # evening peak
    solar_dip = -60 * np.clip(np.sin((h - 7) / 10 * np.pi), 0, None)
    return base + solar_dip + rng.normal(0, 25, 8760)


CF = load_series("pv_cf.csv", synthetic_pv)
price = load_series("price_dk1.csv", synthetic_price)
a_t = pd.Series(1.0, index=snapshots)  # S1: RFNBO import allowed in every hour

# =====================================================================
# 3. Network
# =====================================================================
n = pypsa.Network()
n.set_snapshots(snapshots)

for carrier in ["AC", "H2", "O2", "CO2", "heat", "methanol", "solar", "grid"]:
    n.add("Carrier", carrier)

# --- buses: one balance equation each --------------------------------
n.add("Bus", "grid", carrier="AC", unit="MW")  # point of connection
n.add("Bus", "elec_R", carrier="AC", unit="MW")  # Eq. (busR)
n.add("Bus", "elec_G", carrier="AC", unit="MW")  # Eq. (busG)
n.add("Bus", "H2", carrier="H2", unit="t/h")  # Eq. (h2)
n.add("Bus", "O2", carrier="O2", unit="t/h")  # Eq. (o2)
n.add("Bus", "heat", carrier="heat", unit="MW")  # Eq. (heat)
n.add("Bus", "CO2_hp", carrier="CO2", unit="t/h")  # Eq. (co2hp)
n.add("Bus", "methanol", carrier="methanol", unit="t/h")

# --- electricity -------------------------------------------------------
# PV on the RFNBO bus, Eq. (pv); curtailment allowed (p_min_pu = 0)
n.add("Generator", "PV", bus="elec_R", carrier="solar",
      p_nom=P["P_PV"], p_max_pu=CF)

# Grid: one bidirectional generator at the connection point.
#   p > 0  -> import, costs lambda_t
#   p < 0  -> export, earns lambda_t
# Its p_nom is the shared 304 MW connection, Eq. (grid).
n.add("Generator", "grid market", bus="grid", carrier="grid",
      p_nom=P["P_grid"], p_min_pu=-1.0, p_max_pu=1.0, marginal_cost=price)

# Import links carry the import tariff; the RFNBO one is gated by a_t, Eq. (rfnbo)
n.add("Link", "import RFNBO", bus0="grid", bus1="elec_R", carrier="grid",
      p_nom=P["P_grid"], p_max_pu=a_t, marginal_cost=P["tau_imp"])
n.add("Link", "import general", bus0="grid", bus1="elec_G", carrier="grid",
      p_nom=P["P_grid"], marginal_cost=P["tau_imp"])
n.add("Link", "export", bus0="elec_G", bus1="grid", carrier="grid",
      p_nom=P["P_grid"], marginal_cost=P["tau_exp"])

# Surplus PV from the RFNBO bus to the general bus (one direction only)
n.add("Link", "RFNBO to general", bus0="elec_R", bus1="elec_G", carrier="AC",
      p_nom=P["P_PV"])

# --- PEM: reference flow = MW electricity in --------------------------
n.add("Link", "PEM", bus0="elec_R", carrier="H2",
      bus1="H2", efficiency=P["eta_H2_PEM"],
      bus2="O2", efficiency2=P["eta_O2_PEM"],
      bus3="heat", efficiency3=P["eta_q_PEM"],
      p_nom=P["P_PEM"], marginal_cost=P["c_var_PEM"])

# --- H2 tank: existing part (free) + extension (sized), Eq. (h2tank) ----
n.add("Store", "H2 tank existing", bus="H2", carrier="H2",
      e_nom=P["E_H2_exist"], e_cyclic=True,
      e_min_pu=P["H2_cushion"] / P["E_H2_exist"])
n.add("Store", "H2 tank extension", bus="H2", carrier="H2",
      e_nom_extendable=True, e_cyclic=True,
      capital_cost=annual_cost(P["capex_H2_tank"], P["fom_H2_tank"]))

# --- MSU: reference flow = t H2/h in; all coefficients divided by 0.193 --
r = P["eta_H2_MSU"]
n.add("Link", "MSU", bus0="H2", carrier="methanol",
      bus1="methanol", efficiency=1 / r,
      bus2="CO2_hp", efficiency2=-P["eta_CO2_MSU"] / r,
      bus3="elec_G", efficiency3=-P["e_MSU"] / r,
      p_nom=P["P_MSU"] * r,
      marginal_cost=P["c_var_MSU"] / r)  # cost per t MeOH -> per t H2

# --- methanol target, Eq. (meoh): flat load + free cyclic buffer -------
n.add("Load", "methanol offtake", bus="methanol", carrier="methanol",
      p_set=P["M_tar"] / 8760)
n.add("Store", "methanol buffer", bus="methanol", carrier="methanol",
      e_nom=1e5, e_cyclic=True)

# --- STAND-IN for step 3: free CO2 -------------------------------------
n.add("Generator", "CO2 supply (stand-in)", bus="CO2_hp", carrier="CO2",
      p_nom=1e3)

# --- sinks for by-products (vent / dump), zero cost --------------------
for name, bus in [("O2 vent", "O2"), ("heat dump", "heat")]:
    n.add("Generator", name, bus=bus, carrier=n.buses.at[bus, "carrier"],
          p_nom=1e4, p_min_pu=-1.0, p_max_pu=0.0)

# =====================================================================
# 4. Solve
# =====================================================================
status, condition = n.optimize(solver_name=SOLVER, solver_options=SOLVER_OPTIONS)
print(f"\nSolver: {status} / {condition}")
if status != "ok":
    raise SystemExit("Model did not solve -- see solver log above.")

# =====================================================================
# 5. Checks against hand calculations
# =====================================================================
lp = n.links_t
gen = n.generators_t.p

meoh = -lp.p1["MSU"].sum()
h2_pem = -lp.p1["PEM"].sum()
el_pem = lp.p0["PEM"].sum()
co2_used = lp.p2["MSU"].sum()

expected = {
    "methanol [t]": P["M_tar"],
    "H2 from PEM [t]": P["M_tar"] * r,
    "PEM electricity [MWh]": P["M_tar"] * r / P["eta_H2_PEM"],
    "CO2 used [t]": P["M_tar"] * P["eta_CO2_MSU"],
}
actual = {
    "methanol [t]": meoh,
    "H2 from PEM [t]": h2_pem,
    "PEM electricity [MWh]": el_pem,
    "CO2 used [t]": co2_used,
}
print("\n--- mass/energy checks (model vs. hand calc) ---")
for k in expected:
    ok = abs(actual[k] - expected[k]) < 1e-3 * expected[k]
    print(f"{k:24s} {actual[k]:14,.1f} {expected[k]:14,.1f}  {'OK' if ok else '!! MISMATCH'}")

imp_R = lp.p0["import RFNBO"].sum()
imp_G = lp.p0["import general"].sum()
exp_ = lp.p0["export"].sum()
pv_used = gen["PV"].sum()
pv_avail = (CF * P["P_PV"]).sum()
print("\n--- electricity [GWh] ---")
print(f"PV available / used / curtailed : {pv_avail/1e3:8.1f} {pv_used/1e3:8.1f} {(pv_avail-pv_used)/1e3:8.1f}")
print(f"PEM from PV (approx.)           : {(el_pem - imp_R)/1e3:8.1f}")
print(f"grid import RFNBO / general     : {imp_R/1e3:8.1f} {imp_G/1e3:8.1f}")
print(f"export                          : {exp_/1e3:8.1f}")
print(f"PEM full-load hours             : {el_pem / P['P_PEM']:8.0f} h")

print("\n--- storage sizes ---")
print(f"H2 tank extension               : {n.stores.at['H2 tank extension', 'e_nom_opt']:8.2f} t")
print(f"methanol buffer peak            : {n.stores_t.e['methanol buffer'].max():8.0f} t (free, no cost)")

# Simultaneous import + export would be a modelling artefact; it should be ~0
both = ((lp.p0["import RFNBO"] + lp.p0["import general"] > 1e-3) & (lp.p0["export"] > 1e-3)).sum()
print(f"hours with import AND export    : {both:8d}  (should be 0)")

# =====================================================================
# 6. Cost (step 2 only: no CCPP, biomass, digestate or C_fix yet)
# =====================================================================
print("\n--- cost [M EUR/yr] ---")
print(f"objective (opex + new capex)    : {n.objective/1e6:8.2f}")
print(f"  of which grid import          : {((price + P['tau_imp']) * (lp.p0['import RFNBO'] + lp.p0['import general'])).sum()/1e6:8.2f}")
print(f"  of which export revenue       : {-(price * lp.p0['export']).sum()/1e6:8.2f}")
print(f"partial LCOM (excl. C_fix etc.) : {n.objective / P['M_tar']:8.1f} EUR/t")

out = HERE / "results"
out.mkdir(exist_ok=True)
n.export_to_netcdf(out / "step2_S1.nc")
print(f"\nNetwork with results saved to {out / 'step2_S1.nc'}")