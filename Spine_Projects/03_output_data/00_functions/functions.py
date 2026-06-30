import pandas as pd
import numpy as np
import ast


### LOAD FUNCTIONS ###

def load_emission_factors(
    path, 
    sheet_fossil = "Emmission_Factors_Fossils",
    sheet_grids = "Emmission_Factors_Power"
):
    """
    Load emission intensity data for fossil fuels and grid electricity.

    Parameters
    ----------
    path : str or Path
        Path to emission_factors_fossil_grid.xlsx.
    sheet_fossil : str
        Sheet with fossil-fuel CO2 intensities (upper/lower range per product) in kg CO2-eq / unit of product.
    sheet_power : str
        Sheet with grid electricity CO2 intensities in g CO2-eq / kWh.
        (rows = years, columns = zones / regions).

    Returns
    -------
    df_fossil_ef : pd.DataFrame
        Columns = ['Upper range', 'Lower range'], index = product names.
        Unit: kg CO2 / unit product.
    df_grid_ef : pd.DataFrame
        Index = year (int), columns = zones.
        Unit: g CO2 / kWh
    """

    df_fossil_ef = pd.read_excel(
        path, 
        sheet_name=sheet_fossil, 
        index_col=0,
        usecols = "A:C"
    )

    df_grid_ef = pd.read_excel(
        path, 
        sheet_name=sheet_grids, 
        index_col=0
    )

    return df_fossil_ef, df_grid_ef

def load_cost_factors(
    path,
    sheet_fossil = "Prices_Fossil_Alternatives",
    sheet_eua = "EUA_Prices",
):
    """
    Load fossil-fuel market prices and EUA (EU Allowance) prices from Excel.

    Parameters
    ----------
    path : str or Path
        Path to cost_factors_fossil_alternatives.xlsx
    sheet_fossil : str
        Sheet name with fossil prices (rows = years, cols = products).
    sheet_eua : str
        Sheet name with EUA prices (rows = years, col 'EUA').

    Returns
    -------
    fossil_prices : pd.DataFrame
        Index = year (int), columns = product names, values in € / unit product.
    eua_prices : dict
        Keys = year, values = prices in € / t CO2-eq.
    """

    fossil_prices = pd.read_excel(
        path, 
        sheet_name=sheet_fossil, 
        index_col=0,
        usecols = "A:H"
    )

    eua_prices = pd.read_excel(
        path, 
        sheet_name=sheet_eua, 
        index_col=0,
        usecols = "A:B"
    )['EUA'].to_dict()

    return fossil_prices, fossil_prices_currency, eua_prices

def load_results(
        path,
        sheet_results = "Results",
):
    """
    Load model results from Excel.

    Parameters
    ----------
    path : str or Path
        Path to results.xlsx
    sheet_results : str
        Sheet name with results (rows = years, cols = variables).

    Returns
    -------
    results : pd.DataFrame
        Index = year (int), columns = variables.
    """

    results = pd.read_excel(
        path, 
        sheet_name=sheet_results, 
        index_col=0
    )

    results = results.map(parse_dict_cell)
    
    return results








### HELPER FUNCTIONS ###

def safe_div(
        numer, 
        denom
    ):
    """
    Makes a safe division: 
    1) returns None if an error occurs, or numer or denom are None
    2) returns None if denom is 0
    
    """
    if numer is None or denom is None:
        return None
    try:
        denom_f = float(denom)
        if denom_f == 0:
            return None
        return numer / denom_f
    except Exception:
        return None
    

def gCO2_per_kwh_to_kgCO2_per_wh(value):
    """Convert g CO2 / kWh  →  kg CO2 / Wh  (divide by 1e6)."""
    if value is None:
        return None
    return float(value) / 1e6

def mwh_to_wh(value):
    """Convert MWh → Wh (multiply by 1e6)."""
    if value is None:
        return None
    return float(value) * 1e6

def kg_to_t(value):
    """Convert kg → t (devide by 1e3)."""
    if value is None:
        return None
    return float(value) / 1e3

def parse_dict_cell(cell):
    """
    Try to parse a cell value as a Python dict if it looks like one,
    otherwise return the value as-is.
    """
    if not isinstance(cell, str):
        return cell
    
    stripped = cell.strip()

    if not stripped.startswith("{"):
        return cell
    try:
        return ast.literal_eval(stripped)
    except (ValueError, SyntaxError):
        return cell






### CALCULATION FUNCTIONS ###
def compute_electricity_breakdown(scenario):
    """
    Calculate the electricity breakdown. 
    Electricity can come from on-site or PPA RES (wind or PV), and the grid (from more than one country).


    Parameters
    ----------
    Expected keys in `scenario`:
        (option 1)
        production_pv_mwh               : float  — on-site PV generation (MWh/a)
        production_wind_onshore_mwh     : float  — on-site onshore generation (MWh/a)
        production_wind_offshore_mwh    : float  — on-site offshore generation (MWh/a)
        el_from_grid_mwh                : float  — electricity imported from the grid (MWh/a)
        el_to_grid_mwh                  : float  — electricity exported to the grid (MWh/a)

        (option 2)
        pv_ppa_mwh                      : float  — electricity from PV PPA (MWh/a), default 0
        wind_ppa_mwh                    : float  — electricity from wind PPA (MWh/a), default 0
        grid_from_mwh                   : dict   — {zone_name: MWh, ...} multi-zone grid import

    

    Returns
    --------
    Returns dict with keys:
        el_used_total_mwh               : total electricity consumed in production (MWh/a)
        res_used_mwh                    : total on-site RES electricity used for production (MWh/a)
        pv_ppa_mwh                      : PV PPA electricity (MWh/a)
        wind_ppa_mwh                    : wind PPA electricity (MWh/a)
        ppa_total_mwh                   : total PPA electricity (MWh/a)
        grid_total_mwh                  : total grid electricity used in production (MWh/a)
        grid_zone_breakdown_mwh         : {zone: MWh, ...}

    """
    pv_produced = float(scenario.get("production_pv_mwh") or 0.0)
    wind_on_produced = float(scenario.get("production_wind_onshore_mwh") or 0.0)
    wind_off_produced = float(scenario.get("production_wind_offshore_mwh") or 0.0)
    el_from_grid = float(scenario.get("el_from_grid_mwh") or 0.0)
    el_to_grid = float(scenario.get("el_to_grid_mwh") or 0.0)

    wind_ppa = float(scenario.get("wind_ppa_mwh") or 0.0)
    pv_ppa = float(scenario.get("pv_ppa_mwh") or 0.0)
    ppa_total = wind_ppa + pv_ppa


    # If 'grid_from' is provided, then there isn't a need to calculate the amount of electricity from the grid
    grid_zone = scenario.get("grid_from_mwh") or {}

    if isinstance(grid_zone, dict) and grid_zone:

        grid_total = sum(v for v in grid_zone.values() if v is not None)
        res_used = 0
        
    else: # Single-source grid:
        grid_zone = {}
        
        res_produced = pv_produced + wind_on_produced + wind_off_produced
        el_used = res_produced + el_from_grid - el_to_grid
        res_used = res_produced - el_to_grid
        res_used_rel = safe_div(res_used, el_used) if el_used > 0 else None
        
        grid_total = el_from_grid * (1.0 - (res_used_rel or 0.0))


    el_used = res_used + ppa_total + grid_total

    return {
        "el_used_total_mwh": el_used,
        "res_used_mwh": res_used,
        "pv_ppa_mwh": pv_ppa,
        "wind_ppa_mwh": wind_ppa,
        "ppa_total_mwh": ppa_total,
        "grid_total_mwh": grid_total,
        "grid_zone_breakdown": grid_zone,
    }

def compute_hub_emissions(
        el_breakdown,
        df_grid_ef,
        year,
        ppa_emission_factor_gkwh,
        primary_zone = "DK1",
):
    """
    Compute the CO2 emissions from hub's electricity (grid) consumption.

    Parameters
    ----------
    el_breakdown                : dict from compute_electricity_breakdown()
    df_grid_ef                  : pandas.DataFrame with grid emission factors (g CO2/kWh), index=year, columns=zone
    year                        : int — the year for which to look up the grid emission factor
    ppa_emission_factor_gkwh    : float — CO2 intensity of PPA electricity (g CO2/kWh)
    primary_zone                : str — which column of df_grid_ef to use when no zone breakdown

    Returns dict with keys
    ----------------------
    hub_emissions_tco2        : total annual hub CO2 emissions (t CO2/a)
    emissions_by_source       : {source: tCO2, ...}
    """

    # Calculate emissions from grid
    sources: dict[str, float | None] = {}

    zone_breakdown = el_breakdown.get("grid_zone_breakdown") or {}
    if zone_breakdown:
        for zone, mwh in zone_breakdown.items():
            # look up emission factor for the zone (column) and year
            ef_zone = None
            if zone in df_grid_ef.columns and year in df_grid_ef.index:
                ef_zone = gCO2_per_kwh_to_kgCO2_per_wh(df_grid_ef.at[year, zone])
            sources[f"grid_{zone}"] = kg_to_t(mwh_to_wh(mwh) * ef_zone)
    else:
        grid_mwh = el_breakdown.get("grid_total_mwh") or 0.0
        ef_primary = None
        if primary_zone in df_grid_ef.columns and year in df_grid_ef.index:
            ef_primary = gCO2_per_kwh_to_kgCO2_per_wh(df_grid_ef.at[year, primary_zone])
        sources[f"grid_{primary_zone}"] = kg_to_t(mwh_to_wh(grid_mwh) * ef_primary)


    # Calculate emissions from PPA
    ef_ppa = gCO2_per_kwh_to_kgCO2_per_wh(ppa_emission_factor_gkwh)


    # PPA sources (wind + PV via PPA)
    wind_ppa_mwh = el_breakdown.get("wind_ppa_mwh")
    sources["wind_ppa"] = kg_to_t(mwh_to_wh(wind_ppa_mwh) * ef_ppa)
    pv_ppa_mwh = el_breakdown.get("pv_ppa_mwh")
    sources["pv_ppa"] = kg_to_t(mwh_to_wh(wind_ppa_mwh) * ef_ppa)

    

    total = sum(v for v in sources.values() if v is not None) 

    return {
        "hub_emissions_tco2": total,
        "emissions_by_source": sources,
    }

def compute_fossil_emissions(
        product,
        demand,
        df_fossil_ef,
):
    """
    Compute annual CO2 emissions from the fossil-fuel alternative.

    Parameters
    ----------
    product         : str — e.g. 'Methanol', 'Hydrogen', 'Ammonia'
    demand          : float — annual demand in tonnes of product
    df_fossil_ef    : DataFrame with 'Upper range' and 'Lower range' columns,
                      index = product names (kg CO2 / kg product)

    Returns dict with keys
    ----------------------
    fossil_emissions_tco2_low  : t CO2/a using lower EF
    fossil_emissions_tco2_high : t CO2/a using upper EF
    """
    ef_low = ef_high = 0

    if product in df_fossil_ef.index:
        ef_low = df_fossil_ef.loc[product, "Lower range"]
        ef_high = df_fossil_ef.loc[product, "Upper range"]
    else:
        print(f"Product '{product}' not found in fossil emission factors sheet.")
        return None, None

    fossil_emissions_tco2_low = demand * ef_low
    fossil_emissions_tco2_high = demand * ef_high


    return fossil_emissions_tco2_low, fossil_emissions_tco2_high

def compute_carbon_price(
        ptx_annual_cost_eur,
        fossil_annual_cost_eur,
        hub_emissions_tco2,
        fossil_fuel_alternative_emissions_tco2,
):
    delta_costs = ptx_annual_cost_eur - fossil_annual_cost_eur
    delta_emissions = fossil_fuel_alternative_emissions_tco2 - hub_emissions_tco2

    carbon_price = delta_costs / delta_emissions

    return carbon_price

def compute_hub_costs(
        scenario, 
        demand
):
    """
    Aggregate all cost and revenue components for a scenario.

    Expected keys in `scenario`
    ---------------------------
    lcoe_eur_per_t              : float  — Levelized Cost of Energy (€/t)
    investment_cost_eur_per_t   : float  
    variable_cost_eur_per_t     : float  
    side_product_revenues       : dict   — {name: €/a}  e.g. {'oxygen': ..., 'district_heating': ...}
    res_sale_revenues_eur_pa    : float  — revenue from selling surplus RES electricity (€/a) 

    Returns dict with keys
    ----------------------
    lcoe_eur_per_t                  : levelised cost of product (€)
    total_costs_eur_pa              : total annual cost (€/a)  = lcom × demand
    investment_cost_eur_pa          : annualised CAPEX (€/a)
    variable_cost_eur_pa            : annual OPEX (€/a)
    revenue_side_products_eur_pa    : total side-product revenue (€/a)
    revenue_res_sale_eur_pa         : RES electricity sale revenue (€/a)
    net_costs_eur_pa                : total costs minus all revenues (€/a)
    """

    lcom = scenario.get("lcom_eur_per_t")
    total_costs = (lcom * demand) if lcom is not None else None

    inv_cost_per_t = scenario.get("investment_cost_eur_per_t")
    investment_cost = (inv_cost_per_t * demand) if inv_cost_per_t is not None else None


    var_cost_per_t = scenario.get("variable_cost_eur_per_t")
    variable_cost = (var_cost_per_t * demand) if var_cost_per_t is not None else None


    side_products = scenario.get("side_product_revenues") or {}
    revenue_side_products = sum(v for v in side_products.values() if v is not None) if side_products else 0.0

    revenue_res = float(scenario.get("res_sale_revenues_eur_pa") or 0.0)

    revenue = revenue_side_products + revenue_res

    costs_net_after_revenues = (total_costs - revenue) if total_costs is not None else None

    return {
        "hub_costs": total_costs,
        "investment_costs": investment_cost,
        "variable_costs": variable_cost,
        "revenue_side_products": revenue_side_products,
        "revenue_res": revenue_res,
        "revenue": revenue,
        "costs_net_after_revenues": costs_net_after_revenues,
    }
