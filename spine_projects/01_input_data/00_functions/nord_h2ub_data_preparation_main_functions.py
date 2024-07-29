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

'''Define functions'''

def set_parameters(params):
    # Default values
    default_params = {
        'year': 2019,
        'area': 'DK1',
        'product': 'methanol',
        'scenario': 'Base',
        'frequency': '1h',
        'model_name': 'toy',
        'temporal_block': 'hourly',
        'stochastic_scenario': "realisation",
        'stochastic_structure': "deterministic",
        'report_name': 'Report',
        'reports': ['unit_flow', 'connection_flow', 'node_state', 'total_costs', 'unit_flow_op', 'node_slack_neg', 'node_slack_pos'],
        'electrolyzer_type': "Alkaline",
        'des_segments_electrolyzer': 1,
        'share_of_dh_price_cap': 0.5,
        'price_level_power': 1,
        'power_price_variance': 1,
        'roll_forward_use': True,
        'num_slices': 12
    }

    # Update default values with provided parameters
    default_params.update(params)

    # Extract parameters
    year = default_params['year']
    area = default_params['area']
    product = default_params['product']
    scenario = default_params['scenario']
    frequency = default_params['frequency']
    model_name = default_params['model_name']
    temporal_block = default_params['temporal_block']
    stochastic_scenario = default_params['stochastic_scenario']
    stochastic_structure = default_params['stochastic_structure']
    report_name = default_params['report_name']
    reports = default_params['reports']
    electrolyzer_type = default_params['electrolyzer_type']
    des_segments_electrolyzer = default_params['des_segments_electrolyzer']
    share_of_dh_price_cap = default_params['share_of_dh_price_cap']
    price_level_power = default_params['price_level_power']
    power_price_variance = default_params['power_price_variance']
    roll_forward_use = default_params['roll_forward_use']
    num_slices = default_params['num_slices']

    # Create time stamps
    start_date = pd.Timestamp(f'{year}-01-01 00:00:00')
    end_date = pd.Timestamp(f'{year}-12-31 23:00:00')

    # Create DatetimeIndex for the range of dates
    datetime_index = pd.date_range(start=start_date, end=end_date, freq=frequency)

    # Print warning message in red
    print("\033[91mWARNING:\033[0m Please control if all the parameters are set correctly")

    # Here you can add any additional processing or return the parameters
    # For demonstration, we return the parameters as a dictionary
    return {
        'start_date': start_date,
        'end_date': end_date,
        'area': area,
        'product': product,
        'scenario': scenario,
        'frequency': frequency,
        'model_name': model_name,
        'temporal_block': temporal_block,
        'stochastic_scenario': stochastic_scenario,
        'stochastic_structure': stochastic_structure,
        'report_name': report_name,
        'reports': reports,
        'electrolyzer_type': electrolyzer_type,
        'des_segments_electrolyzer': des_segments_electrolyzer,
        'share_of_dh_price_cap': share_of_dh_price_cap,
        'price_level_power': price_level_power,
        'power_price_variance': power_price_variance,
        'roll_forward_use': roll_forward_use,
        'num_slices': num_slices
        'start_date': start_date
        'end_date': end_date
        'datetime_index': datetime_index
    }