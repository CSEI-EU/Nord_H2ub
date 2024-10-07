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

#function to filter the investment parameters for later use
def filter_investment_data(name_parameter, **kwargs):
    """
    This function takes an parameter column name and any number of parameters as named arguments.
    It filters out the ones that have no value (None) and returns a DataFrame with 
    the remaining parameters and their corresponding values.
    
    Args:
        name_parameter (str): The name for the column name.
        **kwargs: Any number of  parameters as named arguments.

    Returns:
        pd.DataFrame: A dataframe with 'Parameter' and the specified column.
    """
    # Filter out parameters that have a value (i.e., not None)
    filtered_data = {k: v for k, v in kwargs.items() if v is not None}

    # Convert the filtered data into a DataFrame
    df = pd.DataFrame(list(filtered_data.items()), columns=['object', name_parameter])
    return df   
