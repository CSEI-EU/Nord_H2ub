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
    fossil_prices_currency = pd.read_excel(
        path, 
        sheet_name=sheet_fossil, 
        usecols = "I",
        nrows=1
    ).values[0][0].split('/')[0]

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

def load_exchange_rates(
        path,
        sheet_rates = "Exchange_Rates",
):
    """
    Load model results from Excel.

    Parameters
    ----------
    path : str or Path
        Path to exchange_rates.xlsx
    sheet_results : str
        Sheet name with exchange rates (rows = years, cols = currencies).

    Returns
    -------
    results : pd.DataFrame
        Index = year (int), columns = currencies.
    """

    rates = pd.read_excel(
        path, 
        sheet_name=sheet_rates,
        index_col=0
    )
    
    return rates





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

def exchange_rate(year, rates, from_curreny, to_currency):
    rate = rates.loc[year, f"{to_currency}/{from_curreny}"]
    return rate




### CALCULATION FUNCTIONS ###
def compute_electricity_breakdown(
        production_pv_mwh,
        production_wind_onshore_mwh,
        production_wind_offshore_mwh,
        pv_ppa_mwh,
        wind_ppa_mwh,
        grid_from_mwh,
):
    """
    Calculate the electricity breakdown. 
    Electricity can come from on-site or PPA RES (wind or PV), and the grid (from more than one country).


    Parameters
    ----------
    production_pv_mwh               : float  — on-site PV generation (MWh/a)
    production_wind_onshore_mwh     : float  — on-site onshore generation (MWh/a)
    production_wind_offshore_mwh    : float  — on-site offshore generation (MWh/a)
    pv_ppa_mwh                      : float  — electricity from PV PPA (MWh/a), default 0
    wind_ppa_mwh                    : float  — electricity from wind PPA (MWh/a), default 0
    grid_from_mwh                   : dict   — {zone_name: MWh, ...} multi-zone grid import

    

    Returns
    --------
    Returns dict with keys:
        total_elec_mwh                  : total electricity consumed in production (MWh/a)
        res_used_mwh                    : total on-site RES electricity used for production (MWh/a)
        pv_ppa_mwh                      : PV PPA electricity (MWh/a)
        wind_ppa_mwh                    : wind PPA electricity (MWh/a)
        ppa_total_mwh                   : total PPA electricity (MWh/a)
        grid_total_mwh                  : total grid electricity used in production (MWh/a)
        grid_zone_breakdown_mwh         : {zone: MWh, ...}

    """
    pv_produced = float(production_pv_mwh or 0.0)
    wind_on_produced = float(production_wind_onshore_mwh or 0.0)
    wind_off_produced = float(production_wind_offshore_mwh or 0.0)
    res_used = pv_produced + wind_on_produced + wind_off_produced


    wind_ppa = float(wind_ppa_mwh or 0.0)
    pv_ppa = float(pv_ppa_mwh or 0.0)
    ppa_total = wind_ppa + pv_ppa


    grid_zone = grid_from_mwh or {}
    grid_total = sum(v for v in grid_zone.values() if v is not None)

    el_used = res_used + ppa_total + grid_total

    return {
        "total_elec_mwh": el_used,
        "res_used_mwh": res_used,
        "pv_ppa_mwh": pv_ppa,
        "wind_ppa_mwh": wind_ppa,
        "ppa_total_mwh": ppa_total,
        "grid_total_mwh": grid_total,
        "grid_zone_breakdown": grid_zone,
    }

def compute_hub_emissions(
        year,
        pv_ppa_mwh,
        wind_ppa_mwh,
        grid_from_mwh,
        df_grid_ef,
        ppa_emission_factor_gkwh,
        primary_zone = "DK1",
):
    """
    Compute the CO2 emissions from hub's electricity (grid) consumption.

    Parameters
    ----------
    year                        : int — the year for which to look up the grid emission factor
    pv_ppa_mwh                  : float  — electricity from PV PPA (MWh/a), default 0
    wind_ppa_mwh                : float  — electricity from wind PPA (MWh/a), default 0
    ppa_emission_factor_gkwh    : float — CO2 intensity of PPA electricity (g CO2/kWh)
    grid_from_mwh               : dict   — {zone_name: MWh, ...} multi-zone grid import
    df_grid_ef                  : pandas.DataFrame with grid emission factors (g CO2/kWh), index=year, columns=zone
    primary_zone                : str — which column of df_grid_ef to use when no zone breakdown

    Returns dict with keys
    ----------------------
    total           : total annual hub CO2 emissions (t CO2/a)
    sources         : {source: tCO2, ...}
    """

    # Calculate emissions from grid
    sources: dict[str, float | None] = {}

    zone_breakdown = grid_from_mwh or {"DK1": 0}
    if zone_breakdown:
        for zone, mwh in zone_breakdown.items():
            # look up emission factor for the zone (column) and year
            ef_zone = None
            if zone in df_grid_ef.columns and year in df_grid_ef.index:
                ef_zone = gCO2_per_kwh_to_kgCO2_per_wh(df_grid_ef.at[year, zone])
            sources[f"grid_{zone}"] = kg_to_t(mwh_to_wh(mwh) * ef_zone)


    # Calculate emissions from PPA
    ef_ppa = gCO2_per_kwh_to_kgCO2_per_wh(ppa_emission_factor_gkwh)

    # PPA sources (wind + PV via PPA)
    wind_ppa_mwh = wind_ppa_mwh or 0.0
    sources["wind_ppa"] = kg_to_t(mwh_to_wh(wind_ppa_mwh) * ef_ppa)
    pv_ppa_mwh = pv_ppa_mwh or 0.0
    sources["pv_ppa"] = kg_to_t(mwh_to_wh(pv_ppa_mwh) * ef_ppa)

    
    total = sum(v for v in sources.values() if v is not None) 

    return total, sources

def compute_fossil_emissions(
        product,
        demand,
        df_fossil_ef
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

def compute_industrial_costs(
        year,
        product,
        demand,
        df_fossil_prices,
        exchange_rates,
        fossil_prices_currency = "€"
):
    """
    Compute annual CO2 emissions from the fossil-fuel alternative.

    Parameters
    ----------
    year                    : int — the year for which to look up the price of fossil fuel alternative
    product                 : str — e.g. 'Methanol', 'Hydrogen', 'Ammonia'
    demand                  : float — annual demand in tonnes of product
    df_fossil_prices        : DataFrame with prices of the fossil fuel alternatives,
                            Index = year (int), columns = product names
    exchange_rates          : DataFrame with exchnage rates pf currency, by year,
                            Index = year (int), columns = currencies
    fossil_prices_currency  : Curreny of the prices in df_fossil_prices

    Returns float
    ----------------------
    industrial_cost     : cost of using the fossil fuel alternative (€ / t)
    """

    if product in df_fossil_prices.columns:
        price = df_fossil_prices.loc[year, product] if fossil_prices_currency == "€" else df_fossil_prices.loc[year, product] * exchange_rate(year, exchange_rates, fossil_prices_currency, "€")
    else:
        print(f"Product '{product}' not found in fossil prices sheet.")
        return None
    industrial_cost = price * demand 

    return industrial_cost

def compute_hub_costs(
        hub_costs_eur_t, 
        side_product_revenues_eur,
        res_sale_revenues_eur,
        demand
):
    """
    Aggregate all cost and revenue components for a scenario.

    
    Parameters
    ----------
    hub_costs_eur_t             : float  - hub costs in € / t
    side_product_revenues_eur   : dict   — {name: €/a}  e.g. {'oxygen': ..., 'district_heating': ...}
    res_sale_revenues_eur       : float  — revenue from selling surplus RES electricity (€/a)
    

    Returns
    -------
    hub_costs_eur                   : total annual hub costs (€/a)
    revenue_side_products_eur       : total side-product revenue (€/a)
    revenue_res_sale_eur            : RES electricity sale revenue (€/a)
    revenue_eur                     : total revenue (€/a)
    net_costs_eur                   : total costs minus all revenues (€/a)
    """

    hub_costs_eur_t = hub_costs_eur_t
    total_costs = (hub_costs_eur_t * demand) if hub_costs_eur_t is not None else None

    side_products = side_product_revenues_eur or {}
    revenue_side_products = sum(v for v in side_products.values() if v is not None) if side_products else 0.0

    revenue_res = float(res_sale_revenues_eur or 0.0)

    revenue = revenue_side_products + revenue_res

    costs_net_after_revenues = (total_costs - revenue) if total_costs is not None else None

    return total_costs, revenue_side_products, revenue_res, revenue, costs_net_after_revenues,


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