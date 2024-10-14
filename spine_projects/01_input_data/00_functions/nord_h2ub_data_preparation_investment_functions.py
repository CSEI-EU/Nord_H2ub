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
        number_of_objects_column = 'initial_units_invested_available'
    elif 'storage' in parameter_name.lower():
        number_of_objects_column = 'initial_storages_invested'
    elif 'connection' in parameter_name.lower():
        number_of_objects_column = 'initial_connections_invested_available'
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
    new_units = merged_df['capacities_exisiting'] / merged_df['investment_limit'] 
    
    # Update only the matching rows in df_unit_investment
    df_object_investment.loc[mask, number_of_objects_column] = new_units[mask]

    return df_object_investment

# Function to update capacity in df_object__node based on investment_limit in df_investment_params
def update_object_capacity(df_investment_params, df_object__node, parameter_name):
    # Merge df_investment_params with df_object__node on 'Object_name', only bringing relevant columns from df_investment_params
    merged_df = pd.merge(df_object__node, 
                         df_investment_params[['Object_name', 'investment_limit']], 
                         on='Object_name', 
                         how='left', 
                         suffixes=('', '_new'))

    # Create a mask where 'investment_limit' is not NaN and 'Parameter' is the parameter_name
    mask = merged_df['investment_limit'].notna() & (merged_df['Parameter'] == parameter_name)
    
    # Update the 'Value' column in df_object__node with the 'investment_limit' where the mask is True
    df_object__node.loc[mask, 'Value'] = merged_df.loc[mask, 'investment_limit']

    return df_object__node

# Function to update storage capacity in df_nodes based on investment_limit in df_investment_params
def update_storage_capacity(df_investment_params, df_nodes, parameter_name):
    # Filter rows in df_investment_params that contain 'storage' in 'Object_name' and have a valid 'investment_limit'
    filtered_investment = df_investment_params[
        df_investment_params['Object_name'].str.contains('storage', case=False, na=False) & 
        df_investment_params['investment_limit'].notna()
    ][['Object_name', 'investment_limit']]
    
    # Merge df_nodes with filtered_investment on 'Object_name'
    merged_df = pd.merge(df_nodes, 
                         filtered_investment, 
                         on='Object_name', 
                         how='left', 
                         suffixes=('', '_new'))
    
    # Update the parameter_name column in df_nodes with the 'investment_limit' where it's available
    merged_df[parameter_name] = merged_df[parameter_name].where(merged_df['investment_limit'].isna(), merged_df['investment_limit'])
    
    # Drop the 'investment_limit' column that was added for merging purposes
    df_nodes = merged_df.drop(columns=['investment_limit'])

    return df_nodes



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
    Updates the 'initial_units_invested_available' column in the df_units_inv_parameters DataFrame.
    
    Parameters:
    df_units_inv_parameters (pd.DataFrame): The DataFrame containing inventory parameters.
    object_names (list): A list of object names to update.
    candidate_nonzero (bool): If True, update the 'number_of_units' for matching object names.
    
    Returns:
    pd.DataFrame: The updated DataFrame.
    """
    
    if candidate_nonzero:
        # Update the 'number_of_units' for the rows where 'Object_name' matches the given object names
        df_units_inv_parameters.loc[df_units_inv_parameters['Object_name'].isin(object_names), 'initial_units_invested_available'] = 1
    
    return df_units_inv_parameters

# Function to map dictionary keys to DataFrame object names and update a given column
#relevant to update the investment values based on the user interface
def update_res_parameter_in_invest(df, update_dict, column_name):
    # Create a mapping from the dictionary keys to the object names in the DataFrame
    mapping = {
        'Solar plant': 'Solar_Plant',
        'Wind onshore': 'Wind_onshore',
        'Wind offshore': 'Wind_offshore'
    }
    
    # Iterate over the dictionary and update the corresponding rows in the DataFrame
    for key, value in update_dict.items():
        # Get the corresponding Object_name from the mapping
        object_name = mapping.get(key)
        
        if object_name:
            # Check if the object exists in the DataFrame
            if object_name not in df['Object_name'].values:
                # If the object does not exist and the value is not NaN, create a new row
                if not pd.isna(value):
                    # Create a new row with NaN for all columns except Object_name
                    new_row = {col: np.nan for col in df.columns}
                    new_row['Object_name'] = object_name
                    # Concatenate the new row to the DataFrame
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Update the specified column where Object_name matches
            df.loc[df['Object_name'] == object_name, column_name] = value

    return df

#define function to update investment data in case of methanol production
#relevant to split the data for the methanol reactor and the Destilation tower
#as input data is for one complete unit (e.g. total investment cost)
def add_missing_investment_for_methanol(df, product_name):
    if product_name.lower() == "methanol":
        # Find the row with the object name 'Methanol Plant' (if exists)
        methanol_plant_row = df[df['Object_name'] == 'Methanol_Reactor']
        
        if not methanol_plant_row.empty:
            # Create a copy of the Methanol Plant row and modify the Object_name
            new_row = methanol_plant_row.copy()
            new_row['Object_name'] = 'Destilation_Tower'

            # Set the investment_cost to 1 for the new row
            #the cost avoid maximal investment up to the limit as cost would be 0
            new_row['investment_cost'] = 1
            
            # Append the new row to the original dataframe
            df = pd.concat([df, new_row], ignore_index=True)
    
    return df