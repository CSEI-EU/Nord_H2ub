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

'''Define functions'''

#method to identify all nodes that should become slack nodes within the network
def check_entries_exist(df, type):
    # Get the entries in Input1 or Input2 that exist in Output1 or Output2
    input1_output = df[df['Input1'].isin(df['Output1']) | df['Input1'].isin(df['Output2'])]['Input1'].tolist()
    input2_output = df[df['Input2'].isin(df['Output1']) | df['Input2'].isin(df['Output2'])]['Input2'].tolist()

    entries_exist = input1_output + input2_output

    # Create a dictionary with True or False for each entry
    entries_exist_status = {entry: entry in entries_exist for entry in df['Input1'].tolist() + df['Input2'].tolist()}

    entries_exist_status_df = pd.DataFrame(entries_exist_status.items())

    entries_exist_status_df = entries_exist_status_df[entries_exist_status_df[0] != '']
    entries_exist_status_df = entries_exist_status_df.rename(columns={0: type})
    entries_exist_status_df = entries_exist_status_df.rename(columns={1: 'node_slack_penalty'})
    
    return entries_exist_status_df

#check if a value exist once 
def check_exclusively_once(val):
    count = sum(1 for col in inputs_outputs if val in occurrences[col] and occurrences[col][val] == 1)
    return count == 1

#method to get information of all possible connections between nodes of the network
def create_connection_dataframe(df, columns):
    # Create the input dataframe
    #df_input = pd.DataFrame(data)
    df_input = df[columns]

    # Create a new dataframe for the connections
    connections = {'in': [], 'out': []}

    # Iterate through each row of the input dataframe
    for _, row in df_input.iterrows():
        in_values = [value for value in [row['Input1'], row['Input2']]]
        out_values = [value for value in [row['Output1'], row['Output2']]]
        
        # Generate connections for each input-output pair
        for in_val in in_values:
            for out_val in out_values:
                connections['in'].append(in_val)
                connections['out'].append(out_val)

    # Create the final dataframe
    df_output = pd.DataFrame(connections)

    # Drop rows where 'in' and 'out' in the same row are identical
    df_output = df_output[df_output['in'] != df_output['out']]

    # Drop duplicate pairs
    df_output = df_output.drop_duplicates()

    return df_output

#method to identify all nodes that have only a mirrored connection to one other node of the network
def find_mirror_combinations(df):
    #replace NaN with None to make this function work
    df.replace(np.nan, None, inplace=True)

    # Create a new column with sorted tuples of 'in' and 'out' values
    df['sorted_combinations'] = df.apply(lambda row: tuple(sorted([row['in'], row['out']])) if None not in [row['in'], row['out']] else None, axis=1)

    # Check for duplicated sorted tuples
    duplicated_combinations = df['sorted_combinations'].duplicated(keep=False)

    # Filter the DataFrame to show only rows with mirrored combinations
    mirrored_rows = df[duplicated_combinations]

    # Drop rows with 'None' entry in 'in' or 'out'
    mirrored_rows = mirrored_rows.dropna(subset=['in', 'out'])

    return mirrored_rows[['in', 'out']]

#method to identify all nodes that are connected to one node
def find_partners(df):
    #replace NaN with None to make this function work
    df.replace(np.nan, None, inplace=True)

    partners = {}

    for index, row in df.iterrows():
        if row['in'] not in partners:
            partners[row['in']] = set()
        if row['out'] is not None:
            partners[row['in']].add(row['out'])

        if row['out'] not in partners:
            partners[row['out']] = set()
        if row['in'] is not None:
            partners[row['out']].add(row['in'])

    return partners

#identification of nodes that have only one connection to another node
def find_identical_entries(dict1, dict2):
    identical_entries = {}

    for key1, value1 in dict1.items():
        if key1 in dict2 and value1 == dict2[key1]:
            identical_entries[key1] = value1

    nodes = list(identical_entries.keys())
    
    #remove storage nodes as they must be balanced
    filtered_nodes = [entry for entry in nodes if 'storage' not in entry]

    return filtered_nodes


#create the object_node relationship for units with variable efficiencies
def create_efficiency_object_node_rel(dataframe, header):
    """
    Create a new DataFrame with values from columns with the specified header.

    Parameters:
    - dataframe (pd.DataFrame): Input DataFrame.
    - header (str): The header to search for.

    Returns:
    - New DataFrame with values filled from matching columns.
    """
    matching_columns = [col for col in dataframe.columns if header in col]

    if not matching_columns:
        print(f"No columns with '{header}' header found.")
        return pd.DataFrame()

    # Create a new DataFrame
    new_dataframe = pd.DataFrame()

    # create the relationship class based on the header
    relationship_class_name = str(header)

    # Extract object_name and node from the first and second row of the header column
    object_name = dataframe.at[0, header]
    node = dataframe.at[1, header]

    # Assume that parameter_name is 'ordered' and value is 'true'
    parameter_name = 'ordered_unit_flow_op'
    value = True

    # Fill values into the new DataFrame
    for column in matching_columns:
        temp_df = pd.DataFrame({
            'relationship_class_name': [relationship_class_name],
            'object_class': ['unit'],
            'object_name': [object_name],
            'node': [node],
            'parameter_name': [parameter_name],
            'value': [str(value)]
        })
        new_dataframe = pd.concat([new_dataframe, temp_df], ignore_index=True)

    return new_dataframe    