'''
This is the Energy Hub Model of CSEI, an Open-source Tool
for Sector Coupling technologies. Developed at the Copenhagen School of
Energy Infrastructure at the Copenhagen Business School.
---------------------------------------
Functions File for Data Prep:
The functions include the logical prossecing, mathematical calculation
logic for the preparation of the input data file for the model runs.
SPDX-FileCopyrightText: Johannes Giehl <jfg.eco@cbs.dk>
SPDX-FileCopyrightText: Dana Hentschel <djh.eco@cbs.dk>
SPDX-License-Identifier: GNU GENERAL PUBLIC LICENSE GPL 3.0
'''

'''Import packages'''
import numpy as np
import pandas as pd
import os
from datetime import timedelta
import math

from nord_h2ub_data_preparation_functions import *

'''Define functions'''

def set_parameters(params):
    # Default values
    default_params = {
        'year': 2019,
        'starting_year': 2020,
        'lcoe_years': 25,
        'area': 'DK_1',
        'product': 'methanol',
        'demand': 180000,
        'demand_res': 'daily',
        'powers': {'Solar plant'},
        'powers_capacities': {304},
        'frequency': '1h',
        'model_name': 'model',
        'temporal_block': 'hourly',
        'stochastic_scenario': 'realisation',
        'stochastic_structure': 'deterministic',
        'run_name': 'base_case',
        'report_name': 'Report',
        'reports': ['unit_flow', 'connection_flow', 'node_state', 'total_costs', 'unit_flow_op', 'node_slack_neg', 'node_slack_pos'],
        'electrolyzer_type': 'Alkaline',
        'des_segments_electrolyzer': 3,
        'wacc': 0.08,
        'share_of_dh_price_cap': 0.5,
        'price_level_power': 1,
        'power_price_variance': 1,
        'roll_forward_use': True,
        'num_slices': 12,
        'candidate_nonzero': 1,
        'investment_period_default': '1Y',
        'inv_cost_ammonia_storage': None,
        'inv_cost_anaerobic': None,
        'inv_cost_asu': None,
        'inv_cost_biomethanation': None,
        'inv_cost_co2_removal': None,
        'inv_cost_diesel_storage': None,
        'inv_cost_egasoline_storage': None,
        'inv_cost_electrolyzer': None,
        'inv_cost_fischer': None,
        'inv_cost_haber': None,
        'inv_cost_hydrogen_storage': None,
        'inv_cost_jet_fuel_storage': None,
        'inv_cost_methane_storage': None,
        'inv_cost_methanol': None,
        'inv_cost_methanol_storage': None,
        'inv_cost_rwgs': None,
        'inv_cost_steam': None,
        'capacity_ammonia_storage': 0,
        'capacity_anaerobic': 0,
        'capacity_asu': 0,
        'capacity_biomethanation': 0,
        'capacity_co2_removal': 0,
        'capacity_distillation': 0,
        'capacity_egasoline_storage': 0,
        'capacity_electrolyzer': 0,
        'capacity_fischer': 0,
        'capacity_haber': 0,
        'capacity_hydrogen_storage': 0,
        'capacity_jet_fuel_storage': 0,
        'capacity_methane_storage': 0,        
        'capacity_methanol': 0,
        'capacity_methanol_storage': 0,
        'capacity_rwgs': 0,
        'capacity_steam': 0,
        'inv_limit_ammonia_storage': 1000,
        'inv_limit_anaerobic': 100,
        'inv_limit_asu': 100,
        'inv_limit_biomethanation': 100,
        'inv_limit_co2_removal': 100,
        'inv_limit_diesel_storage': 1000,
        'inv_limit_distillation': 100,
        'inv_limit_egasoline_storage': 1000,
        'inv_limit_electrolyzer': 100,
        'inv_limit_fischer': 100,
        'inv_limit_haber': 100,
        'inv_limit_hydrogen_storage': 1000,
        'inv_limit_jet_fuel_storage': 1000,
        'inv_limit_methane_storage': 1000,
        'inv_limit_methanol': 100,
        'inv_limit_methanol_storage': 1000,
        'inv_limit_rwgs': 100,
        'inv_limit_steam': 100,
        'investment_res': False,
        'investment_ps': False,
        'investment_ps_capacity': None
    }

    # Update default values with provided parameters}
    #params = {k: (v if pd.notna(v) or not '' else default_params.get(k, None)) for k, v in params.items()}
    params = {k: v for k, v in params.items()
        if v is not None and not (isinstance(v, str) and v.strip() == '') and not (isinstance(v, float) and math.isnan(v))
    }
    default_params.update(params)
    
    # Create time stamps
    start_date = pd.Timestamp(f'{default_params["year"]}-01-01 00:00:00')
    end_date = pd.Timestamp(f'{default_params["year"]}-12-31 23:00:00')

    # Create DatetimeIndex for the range of dates
    datetime_index = pd.date_range(start=start_date, end=end_date, freq=default_params["frequency"])
    
    # Create roll forward size (if used)
    roll_forward_size = calculate_opt_horizons(datetime_index, default_params["num_slices"])
    
    # Add to dictionary
    year = default_params['year']
    starting_year = default_params['starting_year']
    lcoe_years = default_params['lcoe_years']
    area = default_params['area']
    product = default_params['product']
    demand = default_params['demand']
    demand_res = default_params['demand_res']
    powers = default_params['powers']
    powers_capacities = default_params['powers_capacities']
    frequency = default_params['frequency']
    model_name = default_params['model_name']
    temporal_block = default_params['temporal_block']
    stochastic_scenario = default_params['stochastic_scenario']
    stochastic_structure = default_params['stochastic_structure']
    run_name = default_params['run_name']
    report_name = default_params['report_name']
    reports = default_params['reports']
    electrolyzer_type = default_params['electrolyzer_type']
    des_segments_electrolyzer = default_params['des_segments_electrolyzer']
    wacc = default_params['wacc']
    share_of_dh_price_cap = default_params['share_of_dh_price_cap']
    price_level_power = default_params['price_level_power']
    power_price_variance = default_params['power_price_variance']
    roll_forward_use = default_params['roll_forward_use']
    num_slices = default_params['num_slices']
    candidate_nonzero = default_params['candidate_nonzero']
    investment_period_default = default_params['investment_period_default']
    investment_res = default_params['investment_res']
    investment_ps = default_params['investment_ps']

    # Create the investment cost dictionary
    investment_cost_params = {
        'inv_cost_Ammonia_storage': default_params['inv_cost_ammonia_storage'],
        'inv_cost_Anaerobic': default_params['inv_cost_anaerobic'],
        'inv_cost_Air_separation_unit': default_params['inv_cost_asu'],
        'inv_cost_Biomethanation': default_params['inv_cost_biomethanation'],
        'inv_cost_CO2_Vaporizer': default_params['inv_cost_co2_removal'],
        'inv_cost_Diesel_storage': default_params['inv_cost_diesel_storage'],
        'inv_cost_Egasoline_storage': default_params['inv_cost_egasoline_storage'],
        'inv_cost_Electric_Steam_Boiler': default_params['inv_cost_steam'],
        'inv_cost_Electrolyzer': default_params['inv_cost_electrolyzer'],
        'inv_cost_Fischer_Tropsch_unit': default_params['inv_cost_fischer'],
        'inv_cost_Haber_Bosch_reactor': default_params['inv_cost_haber'],
        'inv_cost_Hydrogen_storage': default_params['inv_cost_hydrogen_storage'],
        'inv_cost_Jet_fuel_storage': default_params['inv_cost_jet_fuel_storage'],
        'inv_cost_Methane_storage': default_params['inv_cost_methane_storage'],
        'inv_cost_Methanol_Plant': default_params['inv_cost_methanol'],
        'inv_cost_Methanol_storage': default_params['inv_cost_methanol_storage'],
        'inv_cost_RWGS_unit': default_params['inv_cost_rwgs']
    }

    # Create the investment limits dictionary
    investment_limit_params = {
        'inv_limit_Ammonia_storage': default_params['inv_limit_ammonia_storage'],
        'inv_limit_Anaerobic': default_params['inv_limit_anaerobic'],
        'inv_limit_Air_separation_unit': default_params['inv_limit_asu'],
        'inv_limit_Biomethanation': default_params['inv_limit_biomethanation'],
        'inv_limit_CO2_Vaporizer': default_params['inv_limit_co2_removal'],
        'inv_limit_Diesel_storage': default_params['inv_limit_diesel_storage'],
        'inv_limit_Distillation_tower': default_params['inv_limit_methanol'],   #assumed to be the same as methanol
        'inv_limit_Egasoline_storage': default_params['inv_limit_egasoline_storage'],
        'inv_limit_Electric_Steam_Boiler': default_params['inv_limit_steam'],
        'inv_limit_Electrolyzer': default_params['inv_limit_electrolyzer'],
        'inv_limit_Fischer_Tropsch_unit': default_params['inv_limit_fischer'],
        'inv_limit_Haber_Bosch_reactor': default_params['inv_limit_haber'],
        'inv_limit_Hydrogen_storage': default_params['inv_limit_hydrogen_storage'],
        'inv_limit_Jet_Fuel_storage': default_params['inv_limit_jet_fuel_storage'],
        'inv_limit_Methane_storage': default_params['inv_limit_methane_storage'],
        'inv_limit_Methanol_Plant': default_params['inv_limit_methanol'],
        'inv_limit_Methanol_storage': default_params['inv_limit_methanol_storage'],
        'inv_limit_RWGS_unit': default_params['inv_limit_rwgs'],
        'investment_ps_capacity': default_params['investment_ps_capacity']
    }
    
    # Create the existing capacities  dictionary
    capacities_exisiting_params = {        
        'capacity_Ammonia_storage': default_params['capacity_ammonia_storage'],
        'capacity_Anaerobic': default_params['capacity_anaerobic'],
        'capacity_Air_separation_unit': default_params['capacity_asu'],
        'capacity_Biomethanation': default_params['capacity_biomethanation'],
        'capacity_CO2_Vaporizer': default_params['capacity_co2_removal'],
        'capacity_Diesel_storage': default_params['inv_cost_diesel_storage'],
        'capacity_Distillation_tower': default_params['capacity_methanol'],   #same as methanol
        'capacity_EGasoline_storage': default_params['capacity_egasoline_storage'],
        'capacity_Electric_Steam_Boiler': default_params['capacity_steam'],
        'capacity_Electrolyzer': default_params['capacity_electrolyzer'],
        'capacity_Fischer_Tropsch_Unit': default_params['capacity_fischer'],
        'capacity_Haber_Bosch_Reactor': default_params['capacity_haber'],
        'capacity_Hydrogen_storage': default_params['capacity_hydrogen_storage'],
        'capacity_Jet_Fuel_storage': default_params['capacity_jet_fuel_storage'],
        'capacity_Methane_storage': default_params['capacity_methane_storage'],
        'capacity_Methanol_Plant': default_params['capacity_methanol'],
        'capacity_Methanol_storage': default_params['capacity_methanol_storage'],
        'capacity_RWGS_unit': default_params['capacity_rwgs']
    }

    # Here you can add any additional processing or return the parameters
    return (year, starting_year, lcoe_years, start_date, end_date, area, product, demand, demand_res,
            powers, powers_capacities, frequency, 
            model_name, temporal_block, 
            stochastic_scenario, stochastic_structure, run_name, report_name, reports, 
            electrolyzer_type, des_segments_electrolyzer, 
            wacc, share_of_dh_price_cap, price_level_power, power_price_variance, 
            roll_forward_use, roll_forward_size, num_slices, datetime_index, 
            candidate_nonzero, 
            investment_period_default, investment_cost_params, investment_limit_params,
            capacities_exisiting_params, investment_res, investment_ps
           )