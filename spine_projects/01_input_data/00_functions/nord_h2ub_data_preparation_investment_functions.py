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

#function to update the investment cost if defined by the user in the interface
def update_investment_cost(df_investment_params, df_unit_investment):
    # Merge the two DataFrames on 'Object_name' but keep all from df_unit_investment
    merged_df = pd.merge(df_unit_investment, 
                         df_investment_params[['Object_name', 'investment_limit', 'investment_cost']],
                         on='Object_name', 
                         how='left', 
                         suffixes=('', '_new'))

    # Calculate the new unit_investment_cost where applicable
    # Only update where investment_limit and investment_cost are not NaN
    mask = merged_df['investment_limit'].notna() & merged_df['investment_cost'].notna()
    new_costs = merged_df['investment_limit'] * merged_df['investment_cost']
    
    # Update only the matching rows in df_unit_investment
    df_unit_investment.loc[mask, 'unit_investment_cost'] = new_costs[mask]

    return df_unit_investment

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

#get information of investment objects and update informatio
def update_units_inv_parameters(df_units_inv_parameters, object_names, candidate_nonzero):
    """
    Updates the 'number_of_units' column in the df_units_inv_parameters DataFrame.
    
    Parameters:
    df_units_inv_parameters (pd.DataFrame): The DataFrame containing inventory parameters.
    object_names (list): A list of object names to update.
    candidate_nonzero (bool): If True, update the 'number_of_units' for matching object names.
    
    Returns:
    pd.DataFrame: The updated DataFrame.
    """
    
    if candidate_nonzero:
        # Update the 'number_of_units' for the rows where 'Object_name' matches the given object names
        df_units_inv_parameters.loc[df_units_inv_parameters['Object_name'].isin(object_names), 'number_of_units'] = 1
    
    return df_units_inv_parameters

