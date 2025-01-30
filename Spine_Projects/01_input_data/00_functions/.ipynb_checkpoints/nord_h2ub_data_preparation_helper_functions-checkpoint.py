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

#the first function is potentially outdated and not necessary anymore
# Function to map Object_name to Parameter with priority for pipelines (specific types), storage (specific types), then the rest
def map_parameters_by_similarity(df1, df2, prefix):
    # Initialize a new column in df2 to store the matched Object_name
    df2['Object_name'] = None

    # Use the provided mapping dictionary, incorporating the prefix
    mapping_dict = {
        f"{prefix}Ammonia_storage": 'ammonia_storage',
        f"{prefix}Anaerobic": 'Anaerobic',
        f"{prefix}Air_separation_unit": 'air_separation_unit',
        f"{prefix}Biomethanation": 'Biomethanation',
        f"{prefix}CO2_Vaporizer": 'CO2_Vaporizer',
        f"{prefix}Egasoline_storage": 'egasoline_storage',
        f"{prefix}Electrolyzer": 'Electrolyzer',
        f"{prefix}Fischer_Tropsch_unit": 'Fischer_Tropsch_Unit',
        f"{prefix}Haber_Bosch_reactor": 'Haber_Bosch_reactor',
        f"{prefix}Hydrogen_storage": 'Hydrogen_storage',
        f"{prefix}Jet_Fuel_storage": 'Jet_Fuel_storage',
        f"{prefix}Methane_storage": 'Methane_storage',
        f"{prefix}Methanol_Plant": 'Methanol_Reactor',
        f"{prefix}Methanol_storage": 'Methanol_storage',
        f"{prefix}RWGS_unit": 'RWGS_unit',
        f"{prefix}Electric_Steam_Boiler": 'Steam_Plant'
    }
    
    # Iterate over each row in df2 and map using the mapping_dict
    for i, parameter in df2['object'].items():
        # Clean the parameter name to ensure consistency with mapping keys
        parameter_cleaned = parameter.strip()

        # Attempt to map the cleaned parameter to the correct Object_name
        if parameter_cleaned in mapping_dict:
            mapped_name = mapping_dict[parameter_cleaned]
            
            # Only assign if the mapped name exists in df1['Object_name']
            if mapped_name in df1['Object_type'].values or mapped_name in df1['Object_name'].values:
                df2.at[i, 'Object_name'] = mapped_name

    # Remove rows where Object_name is None
    df2 = df2[df2['Object_name'].notna()]

    # Return the updated df2 with mapped Object_name
    return df2


#function to reset index by another column of the dataframe
def replace_index_by_column(df, column_name):
    # Check if the column_name exists in the DataFrame
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in the DataFrame.")

    # Drop the previous index
    df.reset_index(drop=True)  
    
    # Set the specified column as the index
    df = df.set_index(column_name)

    df = df.drop(columns=['Parameter'])
    
    # Return the modified DataFrame
    return df

def move_column_to_first(df, column_name):
    # Check if the column exists in the DataFrame
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in the DataFrame.")
    
    # Remove the first column
    df = df.iloc[:, 1:].copy()
    
    # Move the specified column to the first position
    cols = [column_name] + [col for col in df.columns if col != column_name]
    
    # Reorder DataFrame columns
    df = df[cols]
    
    return df
