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

from nord_h2ub_data_preparation_functions import *

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
        'stochastic_scenario': 'realisation',
        'stochastic_structure': 'deterministic',
        'report_name': 'Report',
        'reports': ['unit_flow', 'connection_flow', 'node_state', 'total_costs', 'unit_flow_op', 'node_slack_neg', 'node_slack_pos'],
        'electrolyzer_type': 'Alkaline',
        'des_segments_electrolyzer': 1,
        'share_of_dh_price_cap': 0.5,
        'price_level_power': 1,
        'power_price_variance': 1,
        'roll_forward_use': True,
        'num_slices': 12,
        'candidate_nonzero': 1,
        'investment_period_default': '1Y'
    }

    # Update default values with provided parameters
    default_params.update(params)

    # Create time stamps
    start_date = pd.Timestamp(f'{default_params["year"]}-01-01 00:00:00')
    end_date = pd.Timestamp(f'{default_params["year"]}-12-31 23:00:00')

    # Create DatetimeIndex for the range of dates
    datetime_index = pd.date_range(start=start_date, end=end_date, freq=default_params["frequency"])
    
    # Create roll forward size (if used)
    roll_forward_size = calculate_opt_horizons(datetime_index, default_params["num_slices"])
    
    # Add to dictionary
    default_params['start_date'] = start_date
    default_params['end_date'] = end_date
    default_params['roll_forward_size'] = roll_forward_size
    default_params['datetime_index'] = datetime_index
    
    # Print warning message in red
    print("\033[91mWARNING:\033[0m Please control if all the parameters are set correctly")
    
    # Here you can add any additional processing or return the parameters
    return (default_params['year'], start_date, end_date, default_params['area'],
            default_params['product'], default_params['scenario'], default_params['frequency'],
            default_params['model_name'], default_params['temporal_block'], 
            default_params['stochastic_scenario'], default_params['stochastic_structure'],
            default_params['report_name'], default_params['reports'], 
            default_params['electrolyzer_type'], default_params['des_segments_electrolyzer'],
            default_params['share_of_dh_price_cap'], default_params['price_level_power'],
            default_params['power_price_variance'], default_params['roll_forward_use'], 
            roll_forward_size, default_params['num_slices'], datetime_index, 
            default_params['candidate_nonzero'], default_params['investment_period_default']
           )