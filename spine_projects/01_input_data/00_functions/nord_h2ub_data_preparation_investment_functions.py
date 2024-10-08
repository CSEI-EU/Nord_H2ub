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
def update_investment_cost(df_investment_params, df_object_investment, parameter_name):
    # Determine the column name to update based on the parameter_name string
    if 'unit' in parameter_name.lower():
        investment_cost_column = 'unit_investment_cost'
    elif 'storage' in parameter_name.lower():
        investment_cost_column = 'storage_investment_cost'
    elif 'connection' in parameter_name.lower():
        investment_cost_column = 'connection_investment_cost'
    else:
        raise ValueError("The parameter_name does not contain 'unit', 'storage', or 'connection'. Unable to determine the correct column.")

    # Merge the two DataFrames on 'Object_name' but keep all from df_object_investment
    merged_df = pd.merge(df_object_investment, 
                         df_investment_params[['Object_name', 'investment_limit', 'investment_cost']],
                         on='Object_name', 
                         how='left', 
                         suffixes=('', '_new'))

    # Calculate the new cost where applicable
    # Only update where investment_limit and investment_cost are not NaN
    mask = merged_df['investment_limit'].notna() & merged_df['investment_cost'].notna()
    new_costs = merged_df['investment_limit'] * merged_df['investment_cost']
    
    # Update only the matching rows in df_object_investment
    df_object_investment.loc[mask, investment_cost_column] = new_costs[mask]

    return df_object_investment


# Function to update the number_of_units if capacities_exisiting is defined by the user in the interface
def update_number_of_objects(df_investment_params, df_object_investment, parameter_name):
    # Determine the column name to update based on the parameter_name string
    if 'unit' in parameter_name.lower():
        number_of_objects_column = 'number_of_units'
    elif 'storage' in parameter_name.lower():
        number_of_objects_column = 'number_of_storages'
    elif 'connection' in parameter_name.lower():
        number_of_objects_column = 'number_of_connections'
    else:
        raise ValueError("The parameter_name does not contain 'unit', 'storage', or 'connection'. Unable to determine the correct column.")

    # Merge the two DataFrames on 'Object_name' but keep all from df_unit_investment
    merged_df = pd.merge(df_object_investment, 
                         df_investment_params[['Object_name', 'investment_limit', 'capacities_exisiting']],
                         on='Object_name', 
                         how='left', 
                         suffixes=('', '_new'))

    # Calculate the new number_of_units where applicable
    # Only update where investment_limit and capacities_exisiting are not NaN
    mask = merged_df['investment_limit'].notna() & merged_df['capacities_exisiting'].notna()
    new_units = merged_df['investment_limit'] / merged_df['capacities_exisiting']
    
    # Update only the matching rows in df_unit_investment
    df_object_investment.loc[mask, number_of_objects_column] = new_units[mask]

    return df_object_investment

# Function to update unit_capacity in df_object__node based on investment_limit in df_investment_params
def update_unit_capacity(df_investment_params, df_object__node):
    # Merge df_investment_params with df_object__node on 'Object_name', only bringing relevant columns from df_investment_params
    merged_df = pd.merge(df_object__node, 
                         df_investment_params[['Object_name', 'investment_limit']], 
                         on='Object_name', 
                         how='left', 
                         suffixes=('', '_new'))

    # Create a mask where 'investment_limit' is not NaN and 'Parameter' is 'unit_capacity'
    mask = merged_df['investment_limit'].notna() & (merged_df['Parameter'] == 'unit_capacity')
    
    # Update the 'Value' column in df_object__node with the 'investment_limit' where the mask is True
    df_object__node.loc[mask, 'Value'] = merged_df.loc[mask, 'investment_limit']

    return df_object__node


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

