"""
Kassø PtX hub -- PyPSA model, build step 3
==========================================

Scope of this step (scenario S1):
  * everything from step 2: PV, shared grid connection, RFNBO and general
    buses, PEM, H2 tank (existing + extension), MSU, methanol target
  * NEW: biomass chain replacing the free CO2 stand-in
      digester (constant biogas, electricity and heat demand)
      -> biogas holder -> oxy-fuel CCPP -> CPU -> CO2 tank -> MSU
  * NEW: O2 from the PEM -> O2 compressor -> O2 tank -> CCPP (or vented)
  * NEW: electric boiler, so the digester heat can always be met
  * NOT YET (step 4): digester thermal mass, hot-water tank, the 24 h
    temperature-rate constraint, battery

Run:   python kasso_step3.py
Needs: pypsa >= 1.0, gurobipy + full licence (or highspy with SOLVER="highs")

Input files in data/ next to this script
----------------------------------------
    pv_cf.csv              PV capacity factor, 2019, UTC  (PVGIS 5.3, SARAH-3)
    price_dk1.csv          DK1 day-ahead price, 2019, UTC (Energinet)
    ccpp_coefficients.csv  CCPP per-tonne-biogas coefficients (Layer 1 model)
The CCPP file is the BASELINE: its values override anything in the tables.
"""

from pathlib import Path

import pandas as pd
import pypsa

HERE = Path(__file__).parent
DATA = HERE / "data"

SOLVER = "gurobi"
SOLVER_OPTIONS = {
    "gurobi": {"Method": 2, "Crossover": 0, "BarConvTol": 1e-6, "Threads": 4},
    "highs": {},
}[SOLVER]

# =====================================================================
# 1. Parameters
# =====================================================================
# --- CCPP coefficients from Layer 1 (baseline, full precision) ----------
ccpp = pd.read_csv(DATA / "ccpp_coefficients.csv", index_col=0)["value"]


def ccpp_value(prefix: str) -> float:
    """Pick a row of the CCPP file by the start of its label."""
    hits = [k for k in ccpp.index if k.startswith(prefix)]
    if len(hits) != 1:
        raise KeyError(f"'{prefix}' matches {hits} in ccpp_coefficients.csv")
    return float(ccpp[hits[0]])


P = dict(
    year=2019,
    # --- fixed plant --------------------------------------------------
    P_PV=304.0,          # MW
    P_PEM=52.5,          # MW electricity in
    P_MSU=4.8,           # t MeOH/h
    P_grid=304.0,        # MW
    E_H2_exist=3.3,      # t
    H2_cushion=0.0,      # t, set later
    M_tar=32_000.0,      # t MeOH/yr
    # --- digester -----------------------------------------------------
    eta_bg_AD=0.102,     # t biogas/t biomass
    eta_dig_AD=0.898,    # t digestate/t biomass
    theta_AD=0.028,      # MWh heat/t biomass
    e_AD=0.005,          # MWh el/t biomass
    # --- CCPP (per t biogas) -- from ccpp_coefficients.csv --------------
    eta_el_CC=ccpp_value("electricity"),       # 2.270 MWh/t
    eta_O2_CC=ccpp_value("O2 from PEM"),       # 1.481 t/t
    eta_CO2_CC=ccpp_value("new CO2"),          # 1.616 t/t
    eta_q_CC=ccpp_value("heat to digester"),   # 0.279 MWh/t
    LHV_bg=ccpp_value("fuel (LHV)"),           # 4.910 MWh/t (reporting only)
    # --- PEM (per MWh electricity) --------------------------------------
    eta_H2_PEM=0.0182,
    eta_O2_PEM=0.144,
    eta_q_PEM=0.20,
    # --- MSU (per t methanol) -------------------------------------------
    eta_H2_MSU=0.193,
    eta_CO2_MSU=1.416,
    e_MSU=0.15,
    # --- auxiliaries ----------------------------------------------------
    w_CPU=0.10,          # MWh/t CO2 compressed
    w_O2=0.10,           # MWh/t O2 into the tank (oxidant compression is inside the CCPP)
    eta_EB=0.99,
    # --- grid -----------------------------------------------------------
    tau_imp=11.70,
    tau_exp=0.0,
    # --- economics --------------------------------------------------------
    wacc=0.08,
    lifetime=20,
    c_bm=5.5,            # EUR/t biomass
    c_dig=10.05,         # EUR/t digestate
    C_fix=0.0,           # EUR/yr, existing PV, PEM, MSU, H2 tank, digester -- PLACEHOLDER
    # ================== PLACEHOLDER COSTS -- replace (DEA etc.) ==========
    # capex in EUR per unit of the component's capacity, fom as share of capex/yr
    capex_CC_per_MWel=1_500_000.0,  fom_CC=0.03,   # oxy-fuel CC, per MW_el
    capex_CPU=1_000_000.0,          fom_CPU=0.04,  # per t/h CO2
    capex_OXC=500_000.0,            fom_OXC=0.04,  # per t/h O2
    capex_EB=100_000.0,             fom_EB=0.02,   # per MW_el
    capex_bg_holder=80_000.0,       fom_bg=0.02,   # per t biogas (~830 m3)
    capex_O2_tank=100_000.0,        fom_O2t=0.02,  # per t O2
    capex_CO2_tank=50_000.0,        fom_CO2t=0.02, # per t CO2
    capex_H2_tank=500_000.0,        fom_H2t=0.02,  # per t H2
    c_var_CC_per_MWhel=0.0,  # EUR/MWh_el
    c_var_PEM=0.0,           # EUR/MWh_el in
    c_var_MSU=0.0,           # EUR/t MeOH
)

# --- biomass feed derived from the CO2 balance (zero margin, see thesis text)
P["m_bm"] = P["M_tar"] * P["eta_CO2_MSU"] / (P["eta_CO2_CC"] * P["eta_bg_AD"] * 8760)
m_bm = P["m_bm"]                      # t biomass/h
bg_rate = P["eta_bg_AD"] * m_bm       # t biogas/h


def crf(i: float, n: int) -> float:
    return i * (1 + i) ** n / ((1 + i) ** n - 1)


def ann(capex: float, fom: float) -> float:
    """Annualised capex + fixed O&M per unit capacity (EUR/unit/yr)."""
    return capex * (crf(P["wacc"], P["lifetime"]) + fom)


# =====================================================================
# 2. Time series
# =====================================================================
snapshots = pd.date_range(f"{P['year']}-01-01", periods=8760, freq="h")


def load_series(fname: str) -> pd.Series:
    df = pd.read_csv(DATA / fname)
    if len(df) != 8760:
        raise ValueError(f"{fname}: expected 8760 rows, got {len(df)}")
    t = pd.to_datetime(df.iloc[:, 0], errors="coerce")
    if t.notna().all() and not (t.dt.year == P["year"]).all():
        raise ValueError(f"{fname}: timestamps are not all in {P['year']}")
    return pd.Series(df.iloc[:, -1].to_numpy(dtype=float), index=snapshots)


CF = load_series("pv_cf.csv")
price = load_series("price_dk1.csv")
a_t = pd.Series(1.0, index=snapshots)  # S1

# =====================================================================
# 3. Network
# =====================================================================
n = pypsa.Network()
n.set_snapshots(snapshots)

for c in ["AC", "H2", "O2", "CO2", "heat", "methanol", "biogas", "solar", "grid"]:
    n.add("Carrier", c)

buses = {
    "grid": "AC", "elec_R": "AC", "elec_G": "AC",
    "H2": "H2", "methanol": "methanol", "biogas": "biogas",
    "O2": "O2",          # low-pressure O2 header: PEM out, CCPP in, vent
    "O2_tank": "O2",     # inside the O2 tank (after the O2 compressor)
    "CO2_lp": "CO2",     # CCPP outlet, Eq. (co2lp)
    "CO2_hp": "CO2",     # after the CPU, Eq. (co2hp)
    "heat": "heat",
}
for b, c in buses.items():
    n.add("Bus", b, carrier=c)

# --- electricity (as step 2) -------------------------------------------
n.add("Generator", "PV", bus="elec_R", carrier="solar", p_nom=P["P_PV"], p_max_pu=CF)
n.add("Generator", "grid market", bus="grid", carrier="grid",
      p_nom=P["P_grid"], p_min_pu=-1.0, p_max_pu=1.0, marginal_cost=price)
n.add("Link", "import RFNBO", bus0="grid", bus1="elec_R", carrier="grid",
      p_nom=P["P_grid"], p_max_pu=a_t, marginal_cost=P["tau_imp"])
n.add("Link", "import general", bus0="grid", bus1="elec_G", carrier="grid",
      p_nom=P["P_grid"], marginal_cost=P["tau_imp"])
n.add("Link", "export", bus0="elec_G", bus1="grid", carrier="grid",
      p_nom=P["P_grid"], marginal_cost=P["tau_exp"])
n.add("Link", "RFNBO to general", bus0="elec_R", bus1="elec_G", carrier="AC",
      p_nom=P["P_PV"])

# --- PEM ----------------------------------------------------------------
n.add("Link", "PEM", bus0="elec_R", carrier="H2",
      bus1="H2", efficiency=P["eta_H2_PEM"],
      bus2="O2", efficiency2=P["eta_O2_PEM"],
      bus3="heat", efficiency3=P["eta_q_PEM"],
      p_nom=P["P_PEM"], marginal_cost=P["c_var_PEM"])

# --- H2 tank -------------------------------------------------------------
n.add("Store", "H2 tank existing", bus="H2", carrier="H2",
      e_nom=P["E_H2_exist"], e_cyclic=True,
      e_min_pu=P["H2_cushion"] / P["E_H2_exist"])
n.add("Store", "H2 tank extension", bus="H2", carrier="H2",
      e_nom_extendable=True, e_cyclic=True,
      capital_cost=ann(P["capex_H2_tank"], P["fom_H2t"]))

# --- MSU (reference flow: t H2/h in) ---------------------------------------
r = P["eta_H2_MSU"]
n.add("Link", "MSU", bus0="H2", carrier="methanol",
      bus1="methanol", efficiency=1 / r,
      bus2="CO2_hp", efficiency2=-P["eta_CO2_MSU"] / r,
      bus3="elec_G", efficiency3=-P["e_MSU"] / r,
      p_nom=P["P_MSU"] * r, marginal_cost=P["c_var_MSU"] / r)

n.add("Load", "methanol offtake", bus="methanol", carrier="methanol",
      p_set=P["M_tar"] / 8760)
n.add("Store", "methanol buffer", bus="methanol", carrier="methanol",
      e_nom=1e5, e_cyclic=True)

# --- digester: constant biogas output and constant loads ------------------
n.add("Generator", "digester biogas", bus="biogas", carrier="biogas",
      p_nom=bg_rate, p_min_pu=1.0, p_max_pu=1.0)            # Eq. (bg), production term
n.add("Load", "digester electricity", bus="elec_G", carrier="AC",
      p_set=P["e_AD"] * m_bm)
n.add("Load", "digester heat", bus="heat", carrier="heat",
      p_set=P["theta_AD"] * m_bm)

# --- biogas holder ----------------------------------------------------------
n.add("Store", "biogas holder", bus="biogas", carrier="biogas",
      e_nom_extendable=True, e_cyclic=True,
      capital_cost=ann(P["capex_bg_holder"], P["fom_bg"]))

# --- CCPP (reference flow: t biogas/h in) -----------------------------------
# Capacity is in t/h biogas; a DEA cost per MW_el is converted with eta_el_CC.
n.add("Link", "CCPP", bus0="biogas", carrier="biogas",
      bus1="elec_G", efficiency=P["eta_el_CC"],
      bus2="CO2_lp", efficiency2=P["eta_CO2_CC"],
      bus3="heat", efficiency3=P["eta_q_CC"],
      bus4="O2", efficiency4=-P["eta_O2_CC"],               # consumes O2
      p_nom_extendable=True,
      capital_cost=ann(P["capex_CC_per_MWel"], P["fom_CC"]) * P["eta_el_CC"],
      marginal_cost=P["c_var_CC_per_MWhel"] * P["eta_el_CC"])

# --- CO2: vent at the CCPP outlet, CPU, CO2 tank ------------------------------
n.add("Link", "CPU", bus0="CO2_lp", carrier="CO2",
      bus1="CO2_hp", efficiency=1.0,
      bus2="elec_G", efficiency2=-P["w_CPU"],
      p_nom_extendable=True,
      capital_cost=ann(P["capex_CPU"], P["fom_CPU"]))
n.add("Store", "CO2 tank", bus="CO2_hp", carrier="CO2",
      e_nom_extendable=True, e_cyclic=True,
      capital_cost=ann(P["capex_CO2_tank"], P["fom_CO2t"]))

# --- O2: compressor into the tank, free discharge back --------------------------
n.add("Link", "O2 compressor", bus0="O2", carrier="O2",
      bus1="O2_tank", efficiency=1.0,
      bus2="elec_G", efficiency2=-P["w_O2"],
      p_nom_extendable=True,
      capital_cost=ann(P["capex_OXC"], P["fom_OXC"]))
n.add("Link", "O2 tank discharge", bus0="O2_tank", bus1="O2", carrier="O2",
      p_nom=1e3)
n.add("Store", "O2 tank", bus="O2_tank", carrier="O2",
      e_nom_extendable=True, e_cyclic=True,
      capital_cost=ann(P["capex_O2_tank"], P["fom_O2t"]))

# --- electric boiler ------------------------------------------------------------
n.add("Link", "electric boiler", bus0="elec_G", bus1="heat", carrier="heat",
      efficiency=P["eta_EB"], p_nom_extendable=True,
      capital_cost=ann(P["capex_EB"], P["fom_EB"]))

# --- free sinks: O2 vent, CO2 vent, heat dump --------------------------------------
for name, bus in [("O2 vent", "O2"), ("CO2 vent", "CO2_lp"), ("heat dump", "heat")]:
    n.add("Generator", name, bus=bus, carrier=buses[bus],
          p_nom=1e4, p_min_pu=-1.0, p_max_pu=0.0)

# =====================================================================
# 4. Solve
# =====================================================================
status, condition = n.optimize(solver_name=SOLVER, solver_options=SOLVER_OPTIONS)
print(f"\nSolver: {status} / {condition}")
if status != "ok":
    raise SystemExit("Model did not solve -- see solver log above.")

# =====================================================================
# 5. Checks
# =====================================================================
lp, gen, st = n.links_t, n.generators_t.p, n.stores_t.e
H = 8760

bg_burned = lp.p0["CCPP"].sum()
co2_made = -lp.p2["CCPP"].sum()
co2_vent = -gen["CO2 vent"].sum()
o2_pem = -lp.p2["PEM"].sum()
o2_cc = lp.p4["CCPP"].sum()
o2_vent = -gen["O2 vent"].sum()

print(f"\nbiomass feed m_bm (derived)     : {m_bm:10.4f} t/h  = {m_bm*H/1e3:8.1f} kt/yr")

checks = {
    "methanol [t]": (-lp.p1["MSU"].sum(), P["M_tar"]),
    "PEM electricity [MWh]": (lp.p0["PEM"].sum(), P["M_tar"] * r / P["eta_H2_PEM"]),
    "biogas burned [t]": (bg_burned, bg_rate * H),
    "CO2 from CCPP [t]": (co2_made, bg_rate * H * P["eta_CO2_CC"]),
    "CO2 used by MSU [t]": (lp.p2["MSU"].sum(), P["M_tar"] * P["eta_CO2_MSU"]),
    "O2 used by CCPP [t]": (o2_cc, bg_rate * H * P["eta_O2_CC"]),
}
print("\n--- mass/energy checks (model vs. hand calc) ---")
for k, (a, e) in checks.items():
    ok = abs(a - e) < 1e-3 * e
    print(f"{k:24s} {a:14,.1f} {e:14,.1f}  {'OK' if ok else '!! MISMATCH'}")
print(f"{'CO2 vented [t]':24s} {co2_vent:14,.1f} {'~0 (zero margin)':>14s}")
print(f"{'O2 from PEM / vented [t]':24s} {o2_pem:14,.1f} {o2_vent:14,.1f}")

print("\n--- optimal sizes ---")
cc = n.links.at["CCPP", "p_nom_opt"]
sizes = [
    ("CCPP", f"{cc:8.3f} t/h biogas = {cc*P['eta_el_CC']:6.2f} MW_el "
             f"(flat would be {bg_rate:.3f} t/h)"),
    ("CPU", f"{n.links.at['CPU', 'p_nom_opt']:8.3f} t/h CO2  "
            f"(1.616 x CCPP = {cc*P['eta_CO2_CC']:.3f})"),
    ("O2 compressor", f"{n.links.at['O2 compressor', 'p_nom_opt']:8.3f} t/h O2"),
    ("electric boiler", f"{n.links.at['electric boiler', 'p_nom_opt']:8.3f} MW_el"),
    ("biogas holder", f"{n.stores.at['biogas holder', 'e_nom_opt']:8.2f} t  "
                      f"(= {n.stores.at['biogas holder', 'e_nom_opt']/bg_rate:5.1f} h of production)"),
    ("O2 tank", f"{n.stores.at['O2 tank', 'e_nom_opt']:8.2f} t"),
    ("CO2 tank", f"{n.stores.at['CO2 tank', 'e_nom_opt']:8.2f} t"),
    ("H2 tank extension", f"{n.stores.at['H2 tank extension', 'e_nom_opt']:8.2f} t"),
]
for k, v in sizes:
    print(f"{k:18s}: {v}")
e_buf = st["methanol buffer"]
print(f"{'methanol buffer':18s}: {e_buf.max() - e_buf.min():8.0f} t swing (free, no cost)")
print(f"CCPP full-load hours: {bg_burned / cc:6.0f} h" if cc > 1e-6 else "CCPP not built")

# --- electricity ---------------------------------------------------------------
imp_R, imp_G = lp.p0["import RFNBO"].sum(), lp.p0["import general"].sum()
print("\n--- electricity [GWh] ---")
print(f"PV used / curtailed             : {gen['PV'].sum()/1e3:8.1f} {((CF*P['P_PV']).sum()-gen['PV'].sum())/1e3:8.1f}")
print(f"CCPP output                     : {-lp.p1['CCPP'].sum()/1e3:8.1f}")
print(f"grid import RFNBO / general     : {imp_R/1e3:8.1f} {imp_G/1e3:8.1f}")
print(f"export                          : {lp.p0['export'].sum()/1e3:8.1f}")
w = lp.p0["CCPP"] * P["eta_el_CC"]
if w.sum() > 0:
    print(f"price earned by CCPP power      : {(w*price).sum()/w.sum():8.1f} EUR/MWh "
          f"(year average {price.mean():.1f})")

# =====================================================================
# 6. Cost and LCOM
# =====================================================================
C_bm = P["c_bm"] * m_bm * H
R_dig = P["c_dig"] * P["eta_dig_AD"] * m_bm * H
C_total = n.objective + P["C_fix"] + C_bm - R_dig
print("\n--- cost [M EUR/yr] ---")
print(f"objective (new capex + opex)    : {n.objective/1e6:8.2f}")
print(f"C_fix (PLACEHOLDER)             : {P['C_fix']/1e6:8.2f}")
print(f"biomass cost                    : {C_bm/1e6:8.2f}")
print(f"digestate revenue               : {-R_dig/1e6:8.2f}")
print(f"total                           : {C_total/1e6:8.2f}")
print(f"LCOM                            : {C_total/P['M_tar']:8.1f} EUR/t  (placeholders inside!)")

out = HERE / "results"
out.mkdir(exist_ok=True)
n.export_to_netcdf(out / "step3_S1.nc")
print(f"\nSaved to {out / 'step3_S1.nc'}")
