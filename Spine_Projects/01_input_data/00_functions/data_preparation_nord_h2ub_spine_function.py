def create_prepared_input_file(parameters:dict):

    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from datetime import timedelta
    import math
    import sys
    import os

    #set all the model variables
    #this is relevant for the input from the user drop down value definition
    (year, start_date, end_date, area, product, scenario, frequency, model_name,temporal_block, stochastic_scenario, stochastic_structure,
    report_name, reports, electrolyzer_type, des_segments_electrolyzer, share_of_dh_price_cap, price_level_power, power_price_variance,
    roll_forward_use, num_slices, datetime_index) = set_parameters(parameters)

    ## Methods 
    # Determine the current working directory
    current_working_dir = os.getcwd()
    
    # Set the module path (adjust the relative path if necessary)
    module_path = os.path.abspath(os.path.join(current_working_dir, '00_functions'))
    if module_path not in sys.path:
        sys.path.append(module_path)
    
    #load the functions and methods from the corresponding file
    from nord_h2ub_data_preparation_functions import *
    from nord_h2ub_data_preparation_main_functions import *

    #calculate the size of the roll-forward horizons
    roll_forward_size = calculate_opt_horizons(datetime_index, num_slices)

    #input data
    excel_file_path = get_excel_file_path() + '/01_input_raw/'
    #prepared input data
    output_file_path = get_excel_file_path() + '/02_input_prepared/'


    