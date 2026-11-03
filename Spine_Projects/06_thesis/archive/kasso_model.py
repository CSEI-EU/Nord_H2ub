"""
Kassø PtX hub with biomass battery -- PyPSA implementation of Layer 2
=====================================================================

Implements kasso_S1_model.tex (version with simplified auxiliaries):
  * no electricity for storage compressors, CPU or digester; compressor costs
    are part of the tank costs; CO2 compression to synthesis pressure is in e_MSU
  * heat dumping limited to PEM + CCPP waste heat, Eq. (dump)
  * cyclic time-index convention for every lagged term, Eq. (wrap)
  * operational sensitivity cases as switches:
        OP_MSU = True  -> S1-MSU: MSU minimum load + ramp limits, Eq. (msumin, msuramp)
        OP_CC  = True  -> S1-CC : linearised CCPP unit commitment, Eq. (ccon ... ccnst)
        both           -> S1-OP

Run:   python kasso_model.py
Needs: pypsa >= 1.0, gurobipy + full licence (or highspy with SOLVER = "highs")

Input files in data/ next to this script
    pv_cf.csv              PV capacity factor, 2019, UTC  (PVGIS 5.3, SARAH-3)
    price_dk1.csv          DK1 day-ahead price, 2019, UTC (Energinet)
    ccpp_coefficients.csv  CCPP coefficients per t biogas (Layer 1) -- BASELINE
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

HERE = Path(__file__).parent
DATA = HERE / "data"

# =====================================================================
# 0. Run settings
# =====================================================================
SCENARIO = "S1"          # "S1" | "S2" | "S3"
OP_MSU = False           # sensitivity S1-MSU
OP_CC = False            # sensitivity S1-CC
RFNBO_PRICE_LIMIT = 20.0 # EUR/MWh, S2/S3 -- check against Delegated Act 2023/1184

SOLVER = "gurobi"
SOLVER_OPTIONS = {
    "gurobi": {"Method": 2, "Crossover": 0, "BarConvTol": 1e-6, "Threads": 4},
    "highs": {"solver": "ipm", "run_crossover": "off"},
}[SOLVER]

case = SCENARIO + ("-OP" if OP_MSU and OP_CC else "-MSU" if OP_MSU else "-CC" if OP_CC else "")

# =====================================================================
# 1. Parameters
# =====================================================================
ccpp = pd.read_csv(DATA / "ccpp_coefficients.csv", index_col=0)["value"]


def ccpp_value(prefix: str) -> float:
    hits = [k for k in ccpp.index if k.startswith(prefix)]
    if len(hits) != 1:
        raise KeyError(f"'{prefix}' matches {hits} in ccpp_coefficients.csv")
    return float(ccpp[hits[0]])


P = dict(
    year=2019,
    # --- fixed plant -----------------------------------------------------
    P_PV=304.0, P_PEM=52.5, P_MSU=4.8, P_grid=304.0,
    E_H2_exist=3.3, H2_cushion=0.0, M_tar=32_000.0,
    # --- digester ----------------------------------------------------------
    eta_bg_AD=0.102, eta_dig_AD=0.898, theta_AD=0.028,
    # --- CCPP (per t biogas) -- baseline file ------------------------------
    eta_el_CC=ccpp_value("electricity"),       # net, oxidant compressor included
    eta_O2_CC=ccpp_value("O2 from PEM"),
    eta_CO2_CC=ccpp_value("new CO2"),
    eta_q_CC=ccpp_value("heat to digester"),
    # --- PEM (per MWh el) -----------------------------------------------------
    eta_H2_PEM=0.0182, eta_O2_PEM=0.144, eta_q_PEM=0.20,
    # --- MSU (per t MeOH) -----------------------------------------------------
    eta_H2_MSU=0.193, eta_CO2_MSU=1.416, e_MSU=0.15,  # e_MSU incl. CO2 compression
    # --- electric boiler -------------------------------------------------------
    eta_EB=0.99,
    # --- grid -------------------------------------------------------------------
    tau_imp=11.70, tau_exp=0.0,
    # --- digester thermal mass ---------------------------------------------------
    m_AD=18_800.0, cp_bm=3.46, dT=1.0, r_T=0.5,
    # --- hot-water tank (PLACEHOLDER performance) ---------------------------------
    h_q=10.0, sigma_qtank=0.002, eta_qtank=0.98,
    # --- battery, S2/S3 (PLACEHOLDER performance) ---------------------------------
    eta_bat=0.95, sigma_bat=0.0,
    # --- operational sensitivity cases ---------------------------------------------
    mu_MSU=0.3,      # MSU minimum load, fraction of P_MSU (sweep 0.2-0.5)
    rho_MSU=0.5,     # MSU ramp limit per hour, fraction of P_MSU (Giehl)
    mu_CC=0.4,       # CCPP minimum load, fraction of online capacity (0.3-0.5)
    beta_CC=0.1,     # CCPP part-load penalty
    UT_CC=4,         # h, minimum up time
    c_su_CC=100.0,   # EUR per t/h biogas started -- PLACEHOLDER (~45 EUR/MW_el)
    N_st_CC=200,     # max full starts per year; None = no limit
    # --- economics ------------------------------------------------------------------
    wacc=0.08, lifetime=20, c_bm=5.5, c_dig=10.05,
    C_fix=0.0,       # EUR/yr existing PV, PEM, MSU, H2 tank, digester -- PLACEHOLDER
    # =============== PLACEHOLDER COSTS -- replace (DEA, Akbari, Giehl) ==========
    # capex per unit capacity, fom as share of capex per year
    capex_CC_per_MWel=1_500_000.0, fom_CC=0.03,
    capex_EB=100_000.0,            fom_EB=0.02,     # per MW_el
    capex_bg_holder=80_000.0,      fom_bg=0.02,     # per t biogas
    capex_O2_tank=100_000.0,       fom_O2t=0.02,    # per t O2, compressor included
    capex_CO2_tank=50_000.0,       fom_CO2t=0.02,   # per t CO2, compressor included
    capex_H2_tank=500_000.0,       fom_H2t=0.02,    # per t H2, compressor included
    capex_qtank=3_000.0,           fom_qtank=0.01,  # per MWh heat
    capex_bat_E=150_000.0,         fom_bat=0.02,    # per MWh
    capex_bat_P=100_000.0,                          # per MW
    c_var_CC_per_MWhel=0.0, c_var_PEM=0.0, c_var_MSU=0.0,
    # =============== END OF PLACEHOLDERS =========================================
)

# Biomass feed derived from the CO2 balance (zero margin)
m_bm = P["M_tar"] * P["eta_CO2_MSU"] / (P["eta_CO2_CC"] * P["eta_bg_AD"] * 8760)
bg_rate = P["eta_bg_AD"] * m_bm

# Digester thermal mass in MWh: MJ/(t K) * t * K / 3600
kAD = P["m_AD"] * P["cp_bm"] / 3600          # MWh per K
E_qAD = 2 * P["dT"] * kAD                    # 36.1 MWh, Eq. (qad)
dE_qAD_24h = P["r_T"] * kAD                  #  9.0 MWh, Eq. (qadrate)


def crf(i, n):
    return i * (1 + i) ** n / ((1 + i) ** n - 1)


def ann(capex, fom):
    return capex * (crf(P["wacc"], P["lifetime"]) + fom)


# =====================================================================
# 2. Time series and scenario
# =====================================================================
snapshots = pd.date_range(f"{P['year']}-01-01", periods=8760, freq="h")


def load_series(fname):
    df = pd.read_csv(DATA / fname)
    if len(df) != 8760:
        raise ValueError(f"{fname}: expected 8760 rows, got {len(df)}")
    t = pd.to_datetime(df.iloc[:, 0], errors="coerce")
    if t.notna().all() and not (t.dt.year == P["year"]).all():
        raise ValueError(f"{fname}: timestamps are not all in {P['year']}")
    return pd.Series(df.iloc[:, -1].to_numpy(dtype=float), index=snapshots)


CF = load_series("pv_cf.csv")
price = load_series("price_dk1.csv")

if SCENARIO == "S1":
    a_t, BATTERY = pd.Series(1.0, index=snapshots), False
elif SCENARIO in ("S2", "S3"):          # S2 and S3 still identical -- define the difference
    a_t, BATTERY = (price <= RFNBO_PRICE_LIMIT).astype(float), True
else:
    raise ValueError(SCENARIO)
print(f"Case {case}: RFNBO import allowed in {int(a_t.sum())} h, "
      f"battery {'on' if BATTERY else 'off'}")

# =====================================================================
# 3. Network
# =====================================================================
n = pypsa.Network()
n.set_snapshots(snapshots)

buses = {"grid": "AC", "elec_R": "AC", "elec_G": "AC", "H2": "H2",
         "methanol": "methanol", "biogas": "biogas", "O2": "O2",
         "CO2": "CO2", "heat": "heat"}
for c in set(buses.values()) | {"solar", "grid"}:
    n.add("Carrier", c)
for b, c in buses.items():
    n.add("Bus", b, carrier=c)

# --- electricity: Eq. (busR), (busG), (pv), (rfnbo), (grid) ---------------
n.add("Generator", "PV", bus="elec_R", carrier="solar", p_nom=P["P_PV"], p_max_pu=CF)
n.add("Generator", "grid market", bus="grid", carrier="grid", p_nom=P["P_grid"],
      p_min_pu=-1.0, p_max_pu=1.0, marginal_cost=price)
n.add("Link", "import RFNBO", bus0="grid", bus1="elec_R", carrier="grid",
      p_nom=P["P_grid"], p_max_pu=a_t, marginal_cost=P["tau_imp"])
n.add("Link", "import general", bus0="grid", bus1="elec_G", carrier="grid",
      p_nom=P["P_grid"], marginal_cost=P["tau_imp"])
n.add("Link", "export", bus0="elec_G", bus1="grid", carrier="grid",
      p_nom=P["P_grid"], marginal_cost=P["tau_exp"])
n.add("Link", "RFNBO to general", bus0="elec_R", bus1="elec_G", carrier="AC",
      p_nom=P["P_PV"])

# --- PEM -----------------------------------------------------------------------
n.add("Link", "PEM", bus0="elec_R", carrier="H2",
      bus1="H2", efficiency=P["eta_H2_PEM"],
      bus2="O2", efficiency2=P["eta_O2_PEM"],
      bus3="heat", efficiency3=P["eta_q_PEM"],
      p_nom=P["P_PEM"], marginal_cost=P["c_var_PEM"])

# --- H2 tank, Eq. (h2tank) ----------------------------------------------------------
n.add("Store", "H2 tank existing", bus="H2", carrier="H2", e_nom=P["E_H2_exist"],
      e_cyclic=True, e_min_pu=P["H2_cushion"] / P["E_H2_exist"])
n.add("Store", "H2 tank extension", bus="H2", carrier="H2", e_nom_extendable=True,
      e_cyclic=True, capital_cost=ann(P["capex_H2_tank"], P["fom_H2t"]))

# --- MSU (reference flow t H2/h) -------------------------------------------------------
r = P["eta_H2_MSU"]
n.add("Link", "MSU", bus0="H2", carrier="methanol",
      bus1="methanol", efficiency=1 / r,
      bus2="CO2", efficiency2=-P["eta_CO2_MSU"] / r,
      bus3="elec_G", efficiency3=-P["e_MSU"] / r,
      p_nom=P["P_MSU"] * r, marginal_cost=P["c_var_MSU"] / r,
      p_min_pu=P["mu_MSU"] if OP_MSU else 0.0)              # Eq. (msumin)

# --- methanol target, Eq. (meoh) --------------------------------------------------------
n.add("Load", "methanol offtake", bus="methanol", carrier="methanol",
      p_set=P["M_tar"] / 8760)
n.add("Store", "methanol buffer", bus="methanol", carrier="methanol",
      e_nom=1e5, e_cyclic=True)

# --- digester: constant biogas and heat demand --------------------------------------------
n.add("Generator", "digester biogas", bus="biogas", carrier="biogas",
      p_nom=bg_rate, p_min_pu=1.0, p_max_pu=1.0)
n.add("Load", "digester heat", bus="heat", carrier="heat", p_set=P["theta_AD"] * m_bm)

n.add("Store", "biogas holder", bus="biogas", carrier="biogas", e_nom_extendable=True,
      e_cyclic=True, capital_cost=ann(P["capex_bg_holder"], P["fom_bg"]))

# --- CCPP (reference flow t biogas/h) ------------------------------------------------------
# In S1-CC the electricity efficiency is (1+beta) eta and a part-load loss
# eta*beta*k_t is withdrawn separately, Eq. (ccpl).
eta_el_link = P["eta_el_CC"] * ((1 + P["beta_CC"]) if OP_CC else 1.0)
n.add("Link", "CCPP", bus0="biogas", carrier="biogas",
      bus1="elec_G", efficiency=eta_el_link,
      bus2="CO2", efficiency2=P["eta_CO2_CC"],
      bus3="heat", efficiency3=P["eta_q_CC"],
      bus4="O2", efficiency4=-P["eta_O2_CC"],
      p_nom_extendable=True,
      capital_cost=ann(P["capex_CC_per_MWel"], P["fom_CC"]) * P["eta_el_CC"],
      marginal_cost=P["c_var_CC_per_MWhel"] * P["eta_el_CC"])
if OP_CC:
    n.add("Bus", "CC part-load loss", carrier="AC")
    n.add("Link", "CCPP part-load loss", bus0="elec_G", bus1="CC part-load loss",
          carrier="AC", p_nom=1e3)
    n.add("Generator", "CC loss sink", bus="CC part-load loss", carrier="AC",
          p_nom=1e3, p_min_pu=-1.0, p_max_pu=0.0)

# --- O2 and CO2 tanks (compressor cost inside the tank cost) ---------------------------------
n.add("Store", "O2 tank", bus="O2", carrier="O2", e_nom_extendable=True, e_cyclic=True,
      capital_cost=ann(P["capex_O2_tank"], P["fom_O2t"]))
n.add("Store", "CO2 tank", bus="CO2", carrier="CO2", e_nom_extendable=True, e_cyclic=True,
      capital_cost=ann(P["capex_CO2_tank"], P["fom_CO2t"]))

# --- electric boiler -------------------------------------------------------------------------
n.add("Link", "electric boiler", bus0="elec_G", bus1="heat", carrier="heat",
      efficiency=P["eta_EB"], p_nom_extendable=True,
      capital_cost=ann(P["capex_EB"], P["fom_EB"]))

# --- heat stores, Eq. (qad), (qtank) -------------------------------------------------------------
n.add("Store", "digester thermal mass", bus="heat", carrier="heat",
      e_nom=E_qAD, e_cyclic=True)
n.add("StorageUnit", "hot-water tank", bus="heat", carrier="heat",
      p_nom_extendable=True, max_hours=P["h_q"], cyclic_state_of_charge=True,
      efficiency_store=P["eta_qtank"], efficiency_dispatch=P["eta_qtank"],
      standing_loss=P["sigma_qtank"],
      capital_cost=ann(P["capex_qtank"], P["fom_qtank"]) * P["h_q"])

# --- battery (S2/S3) on the RFNBO bus -----------------------------------------------------------
if BATTERY:
    n.add("Bus", "battery", carrier="AC")
    n.add("Store", "battery", bus="battery", carrier="AC", e_nom_extendable=True,
          e_cyclic=True, standing_loss=P["sigma_bat"],
          capital_cost=ann(P["capex_bat_E"], P["fom_bat"]))
    n.add("Link", "battery charger", bus0="elec_R", bus1="battery", carrier="AC",
          efficiency=P["eta_bat"], p_nom_extendable=True,
          capital_cost=ann(P["capex_bat_P"], P["fom_bat"]))
    n.add("Link", "battery discharger", bus0="battery", bus1="elec_R", carrier="AC",
          efficiency=P["eta_bat"], p_nom_extendable=True)

# --- free sinks ------------------------------------------------------------------------------------
for name, bus in [("O2 vent", "O2"), ("CO2 vent", "CO2"), ("heat dump", "heat")]:
    n.add("Generator", name, bus=bus, carrier=buses[bus],
          p_nom=1e4, p_min_pu=-1.0, p_max_pu=0.0)


# =====================================================================
# 4. Custom constraints
# =====================================================================
def lag(x, k):
    """x_{t-k} with the cyclic convention of Eq. (wrap)."""
    return x.roll(snapshot=k)


def extra_constraints(n, sns):
    m = n.model
    lp = m["Link-p"]

    # Eq. (qadrate): digester temperature rate, cyclic
    e = m["Store-e"].sel(name="digester thermal mass", drop=True)
    d24 = e - lag(e, 24)
    m.add_constraints(d24 <= dE_qAD_24h, name="digester-rate-up")
    m.add_constraints(d24 >= -dE_qAD_24h, name="digester-rate-down")

    # Eq. (dump): only PEM and CCPP waste heat may be dumped (dump p <= 0)
    dump = -m["Generator-p"].sel(name="heat dump", drop=True)
    waste = P["eta_q_PEM"] * lp.sel(name="PEM", drop=True) + P["eta_q_CC"] * lp.sel(name="CCPP", drop=True)
    m.add_constraints(dump - waste <= 0, name="heat-dump-limit")

    if BATTERY:
        pn = m["Link-p_nom"]
        m.add_constraints(pn.sel(name="battery charger", drop=True) == pn.sel(name="battery discharger", drop=True),
                          name="battery-inverter")

    # S1-MSU: Eq. (msuramp), cyclic; min load is p_min_pu on the MSU link
    if OP_MSU:
        p = lp.sel(name="MSU", drop=True)
        ramp = P["rho_MSU"] * P["P_MSU"] * r          # in t H2/h
        m.add_constraints(p - lag(p, 1) <= ramp, name="msu-ramp-up")
        m.add_constraints(p - lag(p, 1) >= -ramp, name="msu-ramp-down")

    # S1-CC: linearised unit commitment, Eq. (ccon)-(ccnst)
    if OP_CC:
        p = lp.sel(name="CCPP", drop=True)
        Pbar = m["Link-p_nom"].sel(name="CCPP", drop=True)
        k = m.add_variables(lower=0, coords=[sns], name="CC-online")
        su = m.add_variables(lower=0, coords=[sns], name="CC-startup")
        m.add_constraints(p - k <= 0, name="cc-online-p")                 # (ccon)
        m.add_constraints(k - Pbar <= 0, name="cc-online-cap")             # (ccon)
        m.add_constraints(p - P["mu_CC"] * k >= 0, name="cc-minload")      # (ccmin)
        m.add_constraints(lp.sel(name="CCPP part-load loss", drop=True)               # (ccpl)
                          - P["eta_el_CC"] * P["beta_CC"] * k == 0, name="cc-partload")
        m.add_constraints(su - k + lag(k, 1) >= 0, name="cc-startup")      # (ccsu)
        recent = sum(lag(su, j) for j in range(P["UT_CC"]))
        m.add_constraints(k - recent >= 0, name="cc-min-uptime")           # (ccut)
        if P["N_st_CC"] is not None:
            m.add_constraints(su.sum() - P["N_st_CC"] * Pbar <= 0, name="cc-start-limit")
        m.objective = m.objective + P["c_su_CC"] * su.sum()                # (ccsucost)


# =====================================================================
# 5. Solve
# =====================================================================
status, condition = n.optimize(solver_name=SOLVER, solver_options=SOLVER_OPTIONS,
                               extra_functionality=extra_constraints)
print(f"\nSolver: {status} / {condition}")
if status != "ok":
    raise SystemExit("Model did not solve -- see solver log above.")

# =====================================================================
# 6. Results and checks
# =====================================================================
lp, gen, st = n.links_t, n.generators_t.p, n.stores_t.e
H = 8760
bg_burned = lp.p0["CCPP"].sum()

print(f"\nbiomass feed m_bm (derived)     : {m_bm:10.4f} t/h  = {m_bm*H/1e3:8.1f} kt/yr")
checks = {
    "methanol [t]": (-lp.p1["MSU"].sum(), P["M_tar"]),
    "PEM electricity [MWh]": (lp.p0["PEM"].sum(), P["M_tar"] * r / P["eta_H2_PEM"]),
    "biogas burned [t]": (bg_burned, bg_rate * H),
    "CO2 from CCPP [t]": (-lp.p2["CCPP"].sum(), bg_rate * H * P["eta_CO2_CC"]),
    "CO2 used by MSU [t]": (lp.p2["MSU"].sum(), P["M_tar"] * P["eta_CO2_MSU"]),
    "O2 used by CCPP [t]": (lp.p4["CCPP"].sum(), bg_rate * H * P["eta_O2_CC"]),
}
print("\n--- mass/energy checks (model vs. hand calc) ---")
for key, (a, e_) in checks.items():
    print(f"{key:24s} {a:14,.1f} {e_:14,.1f}  {'OK' if abs(a-e_) < 1e-3*e_ else '!! MISMATCH'}")
print(f"{'CO2 vented [t]':24s} {max(0.0, -gen['CO2 vent'].sum()):14,.1f}")
print(f"{'O2 from PEM / vented [t]':24s} {-lp.p2['PEM'].sum():14,.1f} {-gen['O2 vent'].sum():14,.1f}")

cc = n.links.at["CCPP", "p_nom_opt"]
qt = n.storage_units.at["hot-water tank", "p_nom_opt"]
print("\n--- optimal sizes ---")
rows = [
    ("CCPP", f"{cc:8.3f} t/h biogas = {cc*P['eta_el_CC']:6.2f} MW_el (flat = {bg_rate:.3f} t/h)"),
    ("electric boiler", f"{n.links.at['electric boiler', 'p_nom_opt']:8.3f} MW_el"),
    ("biogas holder", f"{n.stores.at['biogas holder', 'e_nom_opt']:8.2f} t "
                      f"(= {n.stores.at['biogas holder', 'e_nom_opt']/bg_rate:.1f} h of production)"),
    ("O2 tank", f"{n.stores.at['O2 tank', 'e_nom_opt']:8.2f} t"),
    ("CO2 tank", f"{n.stores.at['CO2 tank', 'e_nom_opt']:8.2f} t"),
    ("H2 tank extension", f"{n.stores.at['H2 tank extension', 'e_nom_opt']:8.2f} t"),
    ("hot-water tank", f"{qt*P['h_q']:8.2f} MWh ({qt:.2f} MW)"),
]
if BATTERY:
    rows.append(("battery", f"{n.stores.at['battery', 'e_nom_opt']:8.2f} MWh, "
                            f"{n.links.at['battery charger', 'p_nom_opt']:.2f} MW"))
for k_, v in rows:
    print(f"{k_:18s}: {v}")
e_buf = st["methanol buffer"]
print(f"{'methanol buffer':18s}: {e_buf.max()-e_buf.min():8.0f} t swing (free, no cost)")

# --- digester and heat -----------------------------------------------------------------
e_ad = st["digester thermal mass"].to_numpy()
T_ad = 42.0 + (e_ad - E_qAD / 2) / kAD
dT24 = np.abs(e_ad - np.roll(e_ad, 24)).max() / kAD
q_dump = -gen["heat dump"]
waste = P["eta_q_PEM"] * lp.p0["PEM"] + P["eta_q_CC"] * lp.p0["CCPP"]
print(f"{'digester temp.':18s}: {T_ad.min():6.2f} to {T_ad.max():6.2f} C, "
      f"max change {dT24:.2f} K/24 h (limit {P['r_T']})")
print(f"{'heat dumped':18s}: {q_dump.sum()/1e3:8.1f} GWh/yr "
      f"(max excess over waste heat {(q_dump - waste).max():.2e} MW, should be <= 0)")

# --- CCPP operation, Eq. (flh) ----------------------------------------------------------------
pcc = lp.p0["CCPP"].to_numpy()
print("\n--- CCPP operation ---")
if cc > 1e-6:
    print(f"full-load hours                 : {pcc.sum()/cc:8.0f} h")
    if OP_CC:
        k_on = n.model["CC-online"].solution.to_numpy()
        su_v = n.model["CC-startup"].solution.to_numpy()
        print(f"equivalent full starts          : {su_v.sum()/cc:8.1f}")
        print(f"start-up cost                   : {P['c_su_CC']*su_v.sum()/1e6:8.3f} M EUR")
        loss = P["eta_el_CC"] * P["beta_CC"] * (k_on - pcc).clip(min=0)   # Eq. (ccpl): lost vs. full load
        print(f"part-load electricity loss      : {loss.sum()/1e3:8.2f} GWh")
        print(f"load factor when online (min)   : "
              f"{(pcc[k_on > 1e-6] / k_on[k_on > 1e-6]).min():8.2f}")
    else:
        su_ind = np.maximum(0, pcc - np.roll(pcc, 1))
        print(f"equivalent full starts (indic.) : {su_ind.sum()/cc:8.1f}")
w = lp.p0["CCPP"] * P["eta_el_CC"]
if w.sum() > 0:
    print(f"price earned by CCPP power      : {(w*price).sum()/w.sum():8.1f} EUR/MWh "
          f"(year average {price.mean():.1f})")
if OP_MSU:
    pm = -lp.p1["MSU"]
    print(f"MSU load range                  : {pm.min():.2f} to {pm.max():.2f} t/h "
          f"(min {P['mu_MSU']*P['P_MSU']:.2f})")

# --- electricity --------------------------------------------------------------------------------
imp = lp.p0["import RFNBO"] + lp.p0["import general"]
print("\n--- electricity [GWh] ---")
print(f"PV used / curtailed             : {gen['PV'].sum()/1e3:8.1f} {((CF*P['P_PV']).sum()-gen['PV'].sum())/1e3:8.1f}")
print(f"CCPP output                     : {-lp.p1['CCPP'].sum()/1e3:8.1f}")
print(f"grid import RFNBO / general     : {lp.p0['import RFNBO'].sum()/1e3:8.1f} {lp.p0['import general'].sum()/1e3:8.1f}")
print(f"export                          : {lp.p0['export'].sum()/1e3:8.1f}")

# --- reported indicators, Eq. (neg) ----------------------------------------------------------------
neg = price < 0
R_neg = ((-price) * imp)[neg].sum()
E_EB_neg = lp.p0["electric boiler"][neg].sum()
print(f"R_neg (paid to import at < 0)   : {R_neg/1e3:8.1f} k EUR")
print(f"E_EB,neg (boiler at < 0)        : {E_EB_neg:8.1f} MWh")

# =====================================================================
# 7. Cost and LCOM
# =====================================================================
C_bm = P["c_bm"] * m_bm * H
R_dig = P["c_dig"] * P["eta_dig_AD"] * m_bm * H
C_total = n.objective + P["C_fix"] + C_bm - R_dig
print("\n--- cost [M EUR/yr] ---")
print(f"objective (new capex + opex)    : {n.objective/1e6:8.2f}")
print(f"C_fix (PLACEHOLDER)             : {P['C_fix']/1e6:8.2f}")
print(f"biomass cost / digestate revenue: {C_bm/1e6:8.2f} {-R_dig/1e6:8.2f}")
print(f"total                           : {C_total/1e6:8.2f}")
print(f"LCOM                            : {C_total/P['M_tar']:8.1f} EUR/t (placeholders inside!)")
print(f"LCOM without R_neg              : {(C_total + R_neg)/P['M_tar']:8.1f} EUR/t")

out = HERE / "results"
out.mkdir(exist_ok=True)
result_file = out / f"model_{case}.nc"
n.export_to_netcdf(result_file)
print(f"\nSaved to {result_file}")
