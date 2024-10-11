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

# Function to map Object_name to Parameter with priority for pipelines (specific types), storage (specific types), then the rest
def map_parameters_by_similarity(df1, df2):
    # Initialize a new column in df2 to store the matched Object_name
    df2['Object_name'] = None

    # List of possible storage types
    storage_types = ['hydrogen', 'methanol', 'methane', 'egasoline', 'jet_fuel', 'power', 'ammonia']
    
    # List of possible pipeline types
    pipeline_types = ['hydrogen', 'methanol', 'methane', 'egasoline', 'jet_fuel', 'power', 'ammonia']

    # Helper function to remove the word "plant" from strings and convert to lowercase
    def clean_string(s):
        return s.lower().replace('plant', '').strip()

    # Iterate over each row in df2 to compare with each Object_name in df1
    for i, parameter in df2['object'].items():
        matched_object_name = None
        parameter_cleaned = clean_string(parameter)

        # Priority 1: Check for pipelines and identify the correct pipeline type
        for object_name in df1['Object_name']:
            object_name_cleaned = clean_string(object_name)

            if 'pipeline' in object_name_cleaned and 'pipeline' in parameter_cleaned:
                # Check for specific types of pipelines: hydrogen, methanol, heat, power
                for pipeline_type in pipeline_types:
                    if pipeline_type in parameter_cleaned and pipeline_type in object_name_cleaned:
                        matched_object_name = object_name
                        break
            if matched_object_name:
                break

        # Priority 2: Check for storage (excluding pipelines), and identify the correct storage type
        if matched_object_name is None:
            for object_name in df1['Object_name']:
                object_name_cleaned = clean_string(object_name)

                if 'storage' in object_name_cleaned and 'pipeline' not in object_name_cleaned and 'storage' in parameter_cleaned and 'pipeline' not in parameter_cleaned:
                    # Check for specific types of storage: hydrogen, methanol, methane, egasoline, jet_fuel, power, ammonia
                    for storage_type in storage_types:
                        if storage_type in parameter_cleaned and storage_type in object_name_cleaned:
                            matched_object_name = object_name
                            break
                if matched_object_name:
                    break

        # Priority 3: All other objects, ignoring "Plant" in the comparison
        if matched_object_name is None:
            for object_name in df1['Object_name']:
                object_name_cleaned = clean_string(object_name)

                # Split the cleaned object_name into meaningful parts (ignoring "plant")
                object_parts = object_name_cleaned.split('_')  # Split by underscore or other delimiters

                # Check if any part of the cleaned object_name is in the parameter (ignoring "plant")
                if any(part in parameter_cleaned for part in object_parts if part):  # Only consider non-empty parts
                    matched_object_name = object_name
                    break

        # Add the matched Object_name to the new column in df2
        df2.at[i, 'Object_name'] = matched_object_name

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
