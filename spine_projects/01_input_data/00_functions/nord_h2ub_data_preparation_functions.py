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
SPDX-FileCopyrightText: Lucia Ciprian <luc.eco@cbs.dk>
SPDX-License-Identifier: GNU GENERAL PUBLIC LICENSE GPL 3.0
'''

'''Import packages'''
import numpy as np
import pandas as pd
import os
import calendar
from datetime import timedelta
import re

'''Define functions'''

#function to get the path to some file locations
def get_excel_file_path():
    # Get the current directory
    current_directory = os.getcwd()
    
    # Initialize variables
    target_directory = "01_input_data"

    # Check if the current directory is already the target directory
    if os.path.basename(current_directory) == target_directory:
        return current_directory.replace("\\", "/")
        
    excel_file_path = None
    
    # Traverse the directory tree upwards to find the target directory
    while True:
        # Check if the target directory exists in the current path
        if target_directory in os.listdir(current_directory):
            excel_file_path = os.path.join(current_directory, target_directory)
            break
        else:
            # Move one level up in the directory tree
            parent_directory = os.path.dirname(current_directory)
            
            # If we have reached the root and haven't found the directory, stop
            if parent_directory == current_directory:
                break
            
            current_directory = parent_directory
        
    # Convert the path to use forward slashes
    if excel_file_path:
        excel_file_path = excel_file_path.replace("\\", "/")
    
    return excel_file_path

def calculate_opt_horizons(datetime_index, num_slices):
    """
    Calculate the roll forward size and used slices for a given datetime index and number of slices.
    
    Args:
    datetime_index (list or pd.DatetimeIndex): The datetime index to be divided into slices.
    num_slices (int): The desired number of slices.
    
    Returns:
    tuple: A tuple containing the roll forward size and used slices.
    """
    # Calculate the number of steps within the horizon
    num_steps = len(datetime_index)

    # Check if the number of slices can be used
    # Find the largest integer divisor that fulfils the condition
    for i in range(num_slices, 0, -1):
        if num_steps % i == 0:
            roll_forward_size = num_steps // i
            used_slices = i
            break
    else:
        print("Cannot divide the number of steps into any integer slices. Please choose a different number of slices.")
        return None

    # Check if num_slices matches the used_slices
    if num_slices != used_slices:
        print("\033[91mWARNING:\033[0m The specified number of slices (", num_slices, ")",
              "does not match the final division factor (", used_slices, ").",
             "\n The calculation uses the factor: ",used_slices, ".")

    return roll_forward_size

#some operations to structure the dataframes
def process_dataframe(df, column_name, category_value):
    df_new = df[[column_name]].copy()
    df_new['Category'] = category_value
    df_new = df_new.rename(columns={column_name: 'Object_name'})
    return df_new

def create_definition_dataframe(df1, df2):
    """
    Create a combined dataframe for units, connections, and nodes.
    
    Args:
    df_model_units (pd.DataFrame): DataFrame containing model units.
    df_model_connections (pd.DataFrame): DataFrame containing model connections.
    
    Returns:
    pd.DataFrame: A combined dataframe for units, connections, and nodes.
    """

    df_units = process_dataframe(df1, 'Unit', 'unit')
    df_connections = process_dataframe(df2, 'Connection', 'connection')

    # Create a list of nodes of the model
    U_input1_nodes = df1['Input1'].tolist()
    U_input2_nodes = df1['Input2'].tolist()
    U_input3_nodes = df1['Input3'].tolist()
    U_input4_nodes = df1['Input4'].tolist()
    U_output1_nodes = df1['Output1'].tolist()
    U_output2_nodes = df1['Output2'].tolist()
    U_output3_nodes = df1['Output3'].tolist()
    U_output4_nodes = df1['Output4'].tolist()
    C_input1_nodes = df2['Input1'].tolist()
    C_input2_nodes = df2['Input2'].tolist()
    C_output1_nodes = df2['Output1'].tolist()
    C_output2_nodes = df2['Output2'].tolist()

    # Combine values from all columns into a single list
    all_nodes_list = (U_input1_nodes + U_input2_nodes + U_input3_nodes + U_input4_nodes + 
                      U_output1_nodes + U_output2_nodes + U_output3_nodes + U_output4_nodes + 
                      C_input1_nodes + C_input2_nodes + C_output1_nodes + C_output2_nodes)

    # Create a list with unique entries
    unique_nodes_list = list(set(all_nodes_list))

    # Create a dataframe for nodes
    df_nodes = pd.DataFrame(unique_nodes_list, columns=['Object_name'])
    df_nodes['Category'] = 'node'
    df_nodes = df_nodes.dropna()

    # Combine dataframes
    df_definition = pd.concat([df_units, df_nodes, df_connections], ignore_index=True)
    #return both dataframes
    return df_definition, df_nodes

# function to assign capacities
def unit_capacity_relations(df1, capacities_exisiting_params, investment_limit_params, powers_capacities):
    """
    Assign chosen capacities to units create object__to/from_node relations.
    
    Args:
    df_model_units (pd.DataFrame): DataFrame containing model units.
    capacities_exisiting_params (pd.DataFrame): DataFrame containing capacities of model units.
    investment_limit_params (pd.DataFrame): DataFrame containing the maximum investment.
    powers_capacities (pd.DataFrame): DataFrame containing capacities of RES units
    """
    # Initialize empty list to store data
    unit_capacity_relations_data = []
    
    # Iterate over each row in the DataFrame
    for index, row in df1.iterrows():
        unit = row['Unit']
        object_type = row['Object_type']
        if object_type in ['PEM_Electrolyzer', 'AEC_Electrolyzer', 'SOEC_Electrolyzer']:
            object_type = 'Electrolyzer'
        
        from_group = {'Electrolyzer', 'Electric_Steam_Boiler'}
        to_group = {'PV_plant', 'CO2_Vaporizer', 'Destilation_tower', 'Methanol_Plant', 'Wind_onshore', 'Wind_offshore'}
        
        # Iterate over Input and Output columns
        for i in range(1, 2):
            input_col = f'Input{i}'
            output_col = f'Output{i}'

            # Check for nodes
            input_node = row[input_col]
            output_node = row[output_col]
            
            # Get chosen capacities
            if object_type == 'solar_plant':
                if 'Solar plant' in powers_capacities and powers_capacities['Solar plant'] is not None:
                    capacity = powers_capacities['Solar plant']
            elif object_type == 'Wind_onshore':
                if 'Wind onshore' in powers_capacities and powers_capacities['Wind onshore'] is not None:
                    capacity = powers_capacities['Wind onshore']
            elif object_type == 'Wind_offshore':
                if 'Wind offshore' in powers_capacities and powers_capacities['Wind offshore'] is not None:
                    capacity = powers_capacities['Wind offshore']
            else:
                pattern_cap = re.compile(rf"capacity_{object_type}")
                pattern_inv = re.compile(rf"inv_limit_{object_type}")
                matching_vars_cap = [key for key in capacities_exisiting_params if pattern_cap.match(key)]
                matching_vars_inv = [key for key in investment_limit_params if pattern_inv.match(key)]
                if pd.notna(matching_vars_cap):
                    capacity = capacities_exisiting_params[matching_vars_cap[0]]
                else:
                    capacity = 100
                if matching_vars_inv: 
                    inv_limit = investment_limit_params[matching_vars_inv[0]]
                    if inv_limit:
                        capacity = max(inv_limit, capacity)
         
        if object_type in from_group:
            unit_capacity_relations_data.append({
                'Relationship_class_name': 'unit__from_node',
                'Object_class': 'unit',
                'Object_name': unit,
                'Node': input_node,
                'Parameter': 'unit_capacity' if pd.notna(capacity) else '',
                'Value': capacity
            })
        else:
            unit_capacity_relations_data.append({
                'Relationship_class_name': 'unit__to_node',
                'Object_class': 'unit',
                'Object_name': unit,
                'Node': output_node,
                'Parameter': 'unit_capacity' if pd.notna(capacity) else '',
                'Value': capacity
            })
    # Create a new DataFrame from the transformed data
    df_unit_capacity_relations_data = pd.DataFrame(unit_capacity_relations_data)

    return df_unit_capacity_relations_data

# function to get all the relations between units and nodes
# function to get all the relations between units and nodes
def object_relationship_unit_nodes(df1, df2):
    """
    Transform unit data into a list of dictionaries for unit relationship parameters.
    
    Args:
    df_model_units (pd.DataFrame): DataFrame containing model units.
    
    Returns:
    list: A list of dictionaries containing transformed unit relationship parameters.
    """
    # Initialize an empty list to store the transformed data
    unit_relation_parameter_data = []

    # Iterate over each row in the DataFrame
    for index, row in df1.iterrows():
        unit = row['Unit']
        cap_node = row['unit_capacity']
        inputs_df = df2.loc[df2['Unit'] == unit, ['Input1', 'Input2', 'Input3', 'Input4']]
        inputs_list = inputs_df.values.flatten().tolist()

        vom_cost_col = f'vom_cost'
        ramp_up_col = f'ramp_up'
        ramp_down_col = f'ramp_down'
        start_up_col = f'start_up_limit'
        shut_down_col = f'shut_down_limit'
        minimum_operating_point_col = f'minimum_op_point'
        
        vom_cost = row[vom_cost_col]
        ramp_up = row[ramp_up_col]
        ramp_down = row[ramp_down_col]
        start_up = row[start_up_col]
        shut_down = row[shut_down_col]
        minimum_op = row[minimum_operating_point_col]

        if cap_node in inputs_list:
            if pd.notna(vom_cost):
                unit_relation_parameter_data.append({
                    'Relationship_class_name': 'unit__from_node',
                    'Object_class': 'unit',
                    'Object_name': unit,
                    'Node': cap_node,
                    'Parameter': 'vom_cost',
                    'Value': vom_cost
                })
            if pd.notna(ramp_up):
                unit_relation_parameter_data.append({
                    'Relationship_class_name': 'unit__from_node',
                    'Object_class': 'unit',
                    'Object_name': unit,
                    'Node': cap_node,
                    'Parameter': 'ramp_up_limit',
                    'Value': ramp_up
                })
            if pd.notna(ramp_down):
                unit_relation_parameter_data.append({
                    'Relationship_class_name': 'unit__from_node',
                    'Object_class': 'unit',
                    'Object_name': unit,
                    'Node': cap_node,
                    'Parameter': 'ramp_down_limit',
                    'Value': ramp_down
                })
            if pd.notna(start_up):
                unit_relation_parameter_data.append({
                    'Relationship_class_name': 'unit__from_node',
                    'Object_class': 'unit',
                    'Object_name': unit,
                    'Node': cap_node,
                    'Parameter': 'start_up_limit',
                    'Value': start_up
                })
            if pd.notna(shut_down):
                unit_relation_parameter_data.append({
                    'Relationship_class_name': 'unit__from_node',
                    'Object_class': 'unit',
                    'Object_name': unit,
                    'Node': cap_node,
                    'Parameter': 'shut_down_limit',
                    'Value': shut_down
                })
            if pd.notna(minimum_op):
                 unit_relation_parameter_data.append({
                     'Relationship_class_name': 'unit__from_node',
                     'Object_class': 'unit',
                     'Object_name': unit,
                     'Node': cap_node,
                     'Parameter': 'minimum_operating_point',
                     'Value': minimum_op
                 })
        else:
            if pd.notna(vom_cost):
                unit_relation_parameter_data.append({
                    'Relationship_class_name': 'unit__to_node',
                    'Object_class': 'unit',
                    'Object_name': unit,
                    'Node': cap_node,
                    'Parameter': 'vom_cost',
                    'Value': vom_cost
                })
            if pd.notna(ramp_up):
                unit_relation_parameter_data.append({
                    'Relationship_class_name': 'unit__to_node',
                    'Object_class': 'unit',
                    'Object_name': unit,
                    'Node': cap_node,
                    'Parameter': 'ramp_up_limit',
                    'Value': ramp_up
                })
            if pd.notna(ramp_down):
                unit_relation_parameter_data.append({
                    'Relationship_class_name': 'unit__to_node',
                    'Object_class': 'unit',
                    'Object_name': unit,
                    'Node': cap_node,
                    'Parameter': 'ramp_down_limit',
                    'Value': ramp_down
                })
            if pd.notna(start_up):
                unit_relation_parameter_data.append({
                    'Relationship_class_name': 'unit__to_node',
                    'Object_class': 'unit',
                    'Object_name': unit,
                    'Node': cap_node,
                    'Parameter': 'start_up_limit',
                    'Value': start_up
                })
            if pd.notna(shut_down):
                unit_relation_parameter_data.append({
                    'Relationship_class_name': 'unit__to_node',
                    'Object_class': 'unit',
                    'Object_name': unit,
                    'Node': cap_node,
                    'Parameter': 'shut_down_limit',
                    'Value': shut_down
                })
            if pd.notna(minimum_op):
                unit_relation_parameter_data.append({
                    'Relationship_class_name': 'unit__to_node',
                    'Object_class': 'unit',
                    'Object_name': unit,
                    'Node': cap_node,
                    'Parameter': 'minimum_operating_point',
                    'Value': minimum_op
                })

    # Create a new DataFrame from the transformed data
    df_unit_relation_parameter_data = pd.DataFrame(unit_relation_parameter_data)

    return df_unit_relation_parameter_data

#function to get all the relations between connections and nodes
def object_relationship_connection_nodes(df_model_connections):
    """
    Transform connection data into a DataFrame for connection relationship parameters.
    
    Args:
    df_model_connections (pd.DataFrame): DataFrame containing model connections.
    
    Returns:
    pd.DataFrame: A DataFrame containing transformed connection relationship parameters.
    """
    # Initialize an empty list to store the transformed data
    connection_relation_parameter_data = []

    # Iterate over each row in the DataFrame
    for index, row in df_model_connections.iterrows():
        connection = row['Connection']

        # Iterate over Input and Output columns
        for i in range(1, 3):
            input_col = f'Input{i}'
            output_col = f'Output{i}'
            cap_input_col = f'Cap_{input_col}_existing'
            cap_output_col = f'Cap_{output_col}_existing'
            vom_cost_input_col = f'vom_cost_{input_col}'
            vom_cost_output_col = f'vom_cost_{output_col}'

            # Check for Input columns
            input_value = row[input_col]
            input_capacity = row[cap_input_col]
            vom_cost_input = row[vom_cost_input_col]

            if pd.notna(input_value):
                connection_relation_parameter_data.append({
                    'Relationship_class_name': 'connection__from_node',
                    'Object_class': 'connection',
                    'Object_name': connection,
                    'Node': input_value,
                    'Parameter': 'connection_capacity' if pd.notna(input_capacity) else '',
                    'Value': input_capacity if pd.notna(input_capacity) else ''
                })
            
                if pd.notna(vom_cost_input):
                    connection_relation_parameter_data.append({
                        'Relationship_class_name': 'connection__from_node',
                        'Object_class': 'connection',
                        'Object_name': connection,
                        'Node': input_value,
                        'Parameter': 'vom_cost',
                        'Value': vom_cost_input
                    })

            # Check for Output columns
            output_value = row[output_col]
            output_capacity = row[cap_output_col]
            vom_cost_output = row[vom_cost_output_col]

            if pd.notna(output_value):
                connection_relation_parameter_data.append({
                    'Relationship_class_name': 'connection__to_node',
                    'Object_class': 'connection',
                    'Object_name': connection,
                    'Node': output_value,
                    'Parameter': 'connection_capacity' if pd.notna(output_capacity) else '',
                    'Value': output_capacity if pd.notna(output_capacity) else ''
                })
            
                if pd.notna(vom_cost_output):
                    connection_relation_parameter_data.append({
                        'Relationship_class_name': 'connection__to_node',
                        'Object_class': 'connection',
                        'Object_name': connection,
                        'Node': output_value,
                        'Parameter': 'vom_cost',
                        'Value': vom_cost_output
                    })

    # Create a new DataFrame from the transformed data
    df_connection_relation_parameter_data = pd.DataFrame(connection_relation_parameter_data)
    
    return df_connection_relation_parameter_data


#function to prepare all parameters that are directly linked to a unit
def create_object_parameters(input_df, object_class_type, parameter_column, run_name):
    # New DataFrame to store the information
    unit_parameter_df = pd.DataFrame(columns=['Object_name', 'Category', 'Parameter', 'Value', 'Alternative'])

    # Iterate through rows and add new rows to the new DataFrame if the parameter has a value
    for index, row in input_df.iterrows():
        if pd.notna(row[parameter_column]):
            new_row = {'Object_name': row[object_class_type], 
                       'Category': object_class_type.lower(), 
                       'Parameter': parameter_column, 
                       'Value': row[parameter_column], 
                       'Alternative': run_name}
            unit_parameter_df = pd.concat([unit_parameter_df, pd.DataFrame([new_row])], ignore_index=True)

            # Check if parameter_column is 'min_down_time'
            if parameter_column == 'min_down_time':
                # Create an additional row with 'online_variable_type' and value 'unit_online_variable_type_integer'
                online_variable_row = {'Object_name': row[object_class_type], 
                                       'Category': object_class_type.lower(), 
                                       'Parameter': 'online_variable_type', 
                                       'Value': 'unit_online_variable_type_integer',
                                       'Alternative': run_name}
                unit_parameter_df = pd.concat([unit_parameter_df, pd.DataFrame([online_variable_row])], ignore_index=True)

    return unit_parameter_df

def create_fom_units(df_units, df_inv, year, investment_res, run_name):
    year_columns = {int(col.split()[-1]): col for col in df_inv.columns if 'Value' in col}
    closest_year = min(year_columns.keys(), key=lambda x: abs(x - year))
    selected_column = year_columns[closest_year]

    unit_fom_cost_df = pd.DataFrame(columns=['Object_name', 'Category', 'Parameter', 'Value', 'Alternative'])

    for index, row in df_units.iterrows():
        object_type = row['Object_type']
        
        matching_row = df_inv[df_inv['Object_type'] == object_type]
        if not matching_row.empty:
            # Extract the investment cost and percentage
            investment_cost = matching_row[selected_column].values[0]
            fom_perc = matching_row['fom_cost_share'].values[0]
            fom_value = int(fom_perc * investment_cost)
        else:
            fom_value = row['fom_cost']
        
        if pd.notna(fom_value):
            new_row = {'Object_name': row['Unit'],
                       'Category': 'unit',
                       'Parameter': 'fom_cost',
                       'Value': fom_value,
                       'Alternative': run_name}
            unit_fom_cost_df = pd.concat([unit_fom_cost_df, pd.DataFrame([new_row])], ignore_index=True)
    
        if not investment_res:
            #remove res from unit_fom_df
            if object_type in {'PV_plant', 'Wind_onshore', 'Wind_offshore'}:
                unit_name = row['Unit']
                unit_fom_cost_df = unit_fom_cost_df[unit_fom_cost_df['Object_name'] != unit_name]
    
    return unit_fom_cost_df

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
def create_connection_dataframe(df1, df2, columns1, columns2):
    # Create the input dataframe
    df1_input = df1[columns1]
    df2_input = df2[columns2]

    # Create a new dataframe for the connections
    connections = {'in': [], 'out': []}

    # Iterate through each row of the input dataframe
    for _, row in df1_input.iterrows():
        in_values = [value for value in [row['Input1'], row['Input2'], row['Input3'], row['Input4']]]
        out_values = [value for value in [row['Output1'], row['Output2'], row['Output3'], row['Output4']]]
        
        # Generate connections for each input-output pair
        for in_val in in_values:
            for out_val in out_values:
                connections['in'].append(in_val)
                connections['out'].append(out_val)

    for _, row in df2_input.iterrows():
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
    filtered_nodes = [entry for entry in nodes if '_st' not in entry]

    return filtered_nodes


#create the object_node relationship for units with variable efficiencies
### If not used by 6/25/2024, please delete and use option below instead ###
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

#create the NEW object_node relationship for units with variable efficiencies
def create_ordered_unit_flow(dataframe, search_value):
    """
    Create a new DataFrame with values from columns containing the specified search value in the first row.

    Parameters:
    - dataframe (pd.DataFrame): Input DataFrame.
    - search_value (str): The value to search for in the first row.

    Returns:
    - New DataFrame with values filled from matching columns.
    """
    matching_column_indices = []
    for idx, val in enumerate(dataframe.iloc[0]):
        if val == search_value:
            matching_column_indices.append(idx)

    if not matching_column_indices:
        print(f"No column with '{search_value}' found in the first row.")
        return pd.DataFrame()

    # Create a new DataFrame
    new_dataframe = pd.DataFrame()

    for matching_column_index in matching_column_indices:
        # create the relationship class based on the search value
        relationship_class_name = str(search_value)

        # Extract object_name and node from the second and third row of the matching column
        object_name = dataframe.iloc[1, matching_column_index]
        node = dataframe.iloc[2, matching_column_index]

        # Assume that parameter_name is 'ordered' and value is 'true'
        parameter_name = 'ordered_unit_flow_op'
        value = True

        # Fill values into the new DataFrame
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

# Replace numerical values with ascending integers starting from 0
def replace_numerical_with_integers(df, column_name):
    numerical_values = {}
    next_integer = 0
    for index, value in enumerate(df[column_name]):
        if isinstance(value, (int, float)):
            if not pd.isna(value):
                if value not in numerical_values:
                    numerical_values[value] = next_integer
                    next_integer += 1
                df.at[index, column_name] = numerical_values[value]
        elif isinstance(value, str) and value.lower() == 'nan':
            df.at[index, column_name] = pd.NA
    return df


#Calculate adjusted efficiency
def create_adj_efficiency(dataframe, mean_eff_goal, unit):
    dataframe_copy = dataframe.copy()
    
    # Calculate the difference in power levels, 'Delta'
    dataframe_copy['Delta'] = dataframe_copy['Power [%]'].diff().fillna(dataframe_copy['Power [%]'])
    
    # Getting the base variables such as maximal efficiency and the index
    max_value = dataframe_copy['Efficiency [%]'].max()
    highest_eff_index_raw = dataframe_copy[dataframe_copy['Efficiency [%]'] == max_value].index.min()
    df_efficiency_adj = dataframe_copy.loc[highest_eff_index_raw:].reset_index(drop=True)
    
    # Adjust the efficiency to the desired efficiency
    weighted_eff = (df_efficiency_adj['Delta'] * df_efficiency_adj['Efficiency [%]']).sum()
    total_delta = df_efficiency_adj['Delta'].sum()
    mean_eff_act = weighted_eff / total_delta
    scaling_factor = mean_eff_goal / mean_eff_act
    df_efficiency_adj['Efficiency_scaled [%]'] = df_efficiency_adj['Efficiency [%]'] * scaling_factor
    
    # Calculate the actual mean efficiency to verify
    mean_eff_scaled = (df_efficiency_adj['Delta'] * df_efficiency_adj['Efficiency_scaled [%]']).sum() / total_delta
    print(f"Actual mean efficiency of {unit} after scaling: {mean_eff_scaled:.4f}")
    
    # Initialize the adjusted efficiency values
    df_efficiency_adj['eff_adjusted_' + unit] = float('nan')
    df_efficiency_adj.loc[0, 'eff_adjusted_' + unit] = df_efficiency_adj.loc[0, 'Efficiency_scaled [%]']
    df_efficiency_adj.loc[0, 'Delta'] = df_efficiency_adj.loc[0, 'Power [%]']
    
    # Calculate the weights for each step
    df_efficiency_adj['weights'] = df_efficiency_adj['Delta'] / df_efficiency_adj['Power [%]']
    
    # Calculate adjusted efficiency values ensuring monotonic decrease
    n = len(df_efficiency_adj['Efficiency_scaled [%]'])
    adjusted_efficiencies = np.zeros(n)
    adjusted_efficiencies[0] = df_efficiency_adj['Efficiency_scaled [%]'][0]
    
    for i in range(1, n):
        target_value = df_efficiency_adj['Efficiency_scaled [%]'][i]
        w = df_efficiency_adj['weights'][i]
        
        # Calculate the new adjusted value ensuring it is monotonously decreasing
        new_value = (target_value - (1 - w) * adjusted_efficiencies[i-1]) / w
        adjusted_efficiencies[i] = min(new_value, adjusted_efficiencies[i-1])
        df_efficiency_adj.loc[i, 'eff_adjusted_' + unit] = adjusted_efficiencies[i]
    
    return df_efficiency_adj


# Operating points and variable efficiency 
def calculate_op_points(unit, des_segment, df_efficiency_adj, input_1, output_1, run_name):
    constraint_name = 'effcurve_' + unit
    #Calculate operating points
    num_segments = des_segment - 1
    
    segment_ranges = np.linspace(df_efficiency_adj['Power [%]'].min(), df_efficiency_adj['Power [%]'].max(), num_segments + 1)
    
    # Fitting a polynomial curve (3rd degree)
    coefficients = np.polyfit(df_efficiency_adj['Power [%]'], df_efficiency_adj['eff_adjusted_' + unit], 3)
    poly_function = np.poly1d(coefficients)
    
    # Generating points for the curve
    x_values = np.linspace(df_efficiency_adj['Power [%]'].min(), df_efficiency_adj['Power [%]'].max(), 100)
    y_values = poly_function(x_values)
    
    segment_averages = []
    segment_x_values = []
    for i in range(num_segments):
        segment_mask = (df_efficiency_adj['Power [%]'] >= segment_ranges[i]) & (df_efficiency_adj['Power [%]'] <= segment_ranges[i + 1])
        segment_data = df_efficiency_adj[segment_mask]
        segment_average = segment_data['eff_adjusted_' + unit].mean()
        segment_averages.append(segment_average)
        segment_x_values.append((segment_ranges[i], segment_ranges[i + 1]))
    
    segment_df = pd.DataFrame({
        'Segment': range(1, num_segments + 1),
        'X-axis Range': [f"{x_start:.2f} to {x_end:.2f}" for x_start, x_end in segment_x_values],
        'Average Y-value': segment_averages
    })
    
    # Creating a DataFrame with the results
    # Add the additional first row starting at 0 to cover the efficiency of the first segment
    first_segment_start = 0
    first_segment_end = segment_ranges[0]
    first_segment_average = df_efficiency_adj['Efficiency_scaled [%]'].max()
    #integrate it into the segment information
    segment_x_values.insert(0, (first_segment_start, first_segment_end))
    segment_averages.insert(0, first_segment_average)
    
    operating_point_segments_df = pd.DataFrame({
        'operating_segment_start': [x[0] for x in segment_x_values],
        'operating_segment_end': [x[1] for x in segment_x_values],
        'average_efficiency': segment_averages
    })
    
    initial_rows_var = pd.DataFrame({
        'relationship_class_name:': ['User_constraint_name', 'Object_name', 'Node_name', 'Alternative', 'Parameter'],
        'unit__from_node__user_constraint': [constraint_name, unit, input_1, run_name, 'unit_flow_coefficient'],
        'unit__to_node__user_constraint': [constraint_name, unit, output_1, run_name, 'unit_flow_coefficient']      
    })
    
    initial_rows_op = pd.DataFrame({
        'relationship_class_name:': ['Object_name', 'Node_name', 'Alternative', 'Parameter'],
        'unit__from_node': [unit, input_1, run_name, 'operating_points']        
    })
    
    var_efficiency_info_df = pd.DataFrame()
    var_efficiency_info_df['relationship_class_name:'] = operating_point_segments_df.index.tolist()
    var_efficiency_info_df['unit__from_node__user_constraint'] = operating_point_segments_df['average_efficiency']
    arbitrary_column = [-1] + [np.nan] * (num_segments)
    var_efficiency_info_df['unit__to_node__user_constraint'] = arbitrary_column
    
    operating_point_info_df = pd.DataFrame()
    operating_point_info_df['relationship_class_name:'] = operating_point_segments_df.index.tolist()
    operating_point_info_df['unit__from_node'] = operating_point_segments_df['operating_segment_end']
    print(operating_point_info_df)
    
    df_var_efficiency = pd.concat([initial_rows_var, var_efficiency_info_df], ignore_index=True)
    df_operating_points = pd.concat([initial_rows_op, operating_point_info_df], ignore_index=True)
    
    return df_var_efficiency, df_operating_points, segment_x_values, segment_averages, x_values, y_values


# Ordered_unit_flow_op
def check_decreasing(dataframe, unit, node, run_name):
    is_decreasing = False
    for column in dataframe.columns:
        if column.startswith('unit__from_node__user_constraint'):
            values = dataframe[column].values
            if len(values) > 6 and values[5] > values[6]:
                is_decreasing = True
                break
    
    result_row = {
        "Relationship_class_name": "unit__from_node",
        "Object_name": unit,
        "Node_name": node,
        "Alternative": run_name,
        "Parameter_name": "ordered_unit_flow_op",
        "Value": "True" if is_decreasing else "False"
    }
    
    return pd.DataFrame([result_row])


# Check if additional demand node is neccessary
resolution_to_block = {
    'h': 'hourly',
    'D': 'daily',
    'W': 'weekly',
    'M': 'monthly',
    'Q': 'quarterly',
    'Y': 'yearly'
}

def check_demand_node(row, df_model_units_relations, temporal_block, resolution_to_block, df_definition, df_nodes, df_connections,
                      df_object__node_definitions, df_object__node_values, df_object_node_node, run_name):
    if not pd.isna(row['demand']):
        row_resolution = resolution_to_block[row['resolution_output']]
        if row_resolution != temporal_block:
            #definition
            output = (df_model_units_relations.loc[df_model_units_relations['Unit'] == row['Unit'], 'Output1']).iloc[0]
            new_def = pd.DataFrame([
                {"Object_name": f"{output}_demand", "Category": "node"},
                {"Object_name": f"pl_{output}_demand", "Category": "connection"}
            ])
            df_definition = pd.concat([df_definition, new_def], ignore_index=True)
            
            #demand value
            new_value = {col: np.nan for col in df_nodes.columns}
            new_value["Object_name"] = f"{output}_demand"
            new_value["Category"] = "node"
            new_value["balance_type"] = "balance_type_node"
            new_value["Alternative"] = run_name
            new_value["nodal_balance_sense"] = ""
            new_value["demand"] = row['demand']
            new_value["node_slack_penalty"] = 100000000
            df_nodes = pd.concat([df_nodes, pd.DataFrame([new_value])], ignore_index=True)
            
            #connection value
            new_con = {col: np.nan for col in df_connections.columns}
            new_con["Object_name"] = f"pl_{output}_demand"
            new_con["Category"] = "connection"
            new_con["Connection_type"] = "connection_type_normal"
            df_connections = pd.concat([df_connections, pd.DataFrame([new_con])], ignore_index=True)
            
            #object_to/from_node
            new_rel = pd.DataFrame([
                {"Relationship_class_name": "connection__from_node", 
                 "Object_class": "connection", 
                 "Object_name": f"pl_{output}_demand",
                 "Node": output
                },
                {"Relationship_class_name": "connection__to_node", 
                 "Object_class": "connection", 
                 "Object_name": f"pl_{output}_demand",
                 "Node": f"{output}_demand",
                }
            ])
            df_object__node_definitions = pd.concat([df_object__node_definitions, new_rel], ignore_index=True)
            
            new_rel_value = pd.DataFrame([
                {"Relationship_class_name": "connection__from_node", 
                 "Object_class": "connection", 
                 "Object_name": f"pl_{output}_demand",
                 "Node": output,
                 "Parameter": "connection_capacity",
                 "Value": 1000,
                 "Alternative": run_name
                },
                {"Relationship_class_name": "connection__to_node", 
                 "Object_class": "connection", 
                 "Object_name": f"pl_{output}_demand",
                 "Node": f"{output}_demand",
                 "Parameter": "connection_capacity",
                 "Value": 1000,
                 "Alternative": run_name
                }
            ])
            df_object__node_values = pd.concat([df_object__node_values, new_rel_value], ignore_index=True)
            
            #object__node__node
            new_rel_nn = pd.DataFrame([
                {"Relationship": "connection__node__node", 
                 "Object_class": "connection", 
                 "Object_name": f"pl_{output}_demand",
                 "Node1": f"{output}_demand",
                 "Node2": output,
                 "Parameter": "fix_ratio_out_in_connection_flow",
                 "Value": 1,
                 "Alternative": run_name
                }
            ])
            df_object_node_node = pd.concat([df_object_node_node, new_rel_nn], ignore_index=True)
            
        else: 
            new_value = {col: np.nan for col in df_nodes.columns}
            new_value["Object_name"] = output
            new_value["Category"] = "node"
            new_value["demand"] = row["demand"]
            new_value["Alternative"] = run_name
            df_nodes = pd.concat([df_nodes, pd.DataFrame([new_value])], ignore_index=True)
            
    return df_definition, df_nodes, df_connections, df_object__node_values, df_object_node_node


# Temporal slicing definition (for demand)
def check_temporal_block(df, df_model_components):
    if pd.isnull(df['resolution_output']).any():
        return
    
    for index, row in df.iterrows():
        temporal_block_name = resolution_to_block.get(row['resolution_output'])
        if temporal_block_name:
            # Check if the temporal block already exists
            exists = df[
                (df_model_components['Object_class_name'] == 'temporal_block') &
                (df_model_components['Object_name'] == temporal_block_name)
            ].shape[0] > 0
        
            if not exists:
                new_row = {'Object_class_name': 'temporal_block', 'Object_name': temporal_block_name}
                df_model_components.loc[len(df_model_components)] = new_row

# Temporal slicing relations
def create_temporal_block_relationships(df1, df2, model_relations, model_name, df_definition, temporal_relations):
    if pd.isnull(df1['resolution_output']).any():
        return

    for index, row in df1.iterrows():
        temporal_block_name = resolution_to_block.get(row['resolution_output'])
        if temporal_block_name:
            #Check if specific demand node exists
            output = (df2.loc[df2['Unit'] == row['Unit'], 'Output1']).iloc[0]
            if f"{output}_demand" in df_definition['Object_name'].values:
                node_name = f"{output}_demand"
            else:
                node_name = output
            
            # Check if relationship already exists
            relationship_exists = model_relations[
                (model_relations['Object_name_1'] == node_name) &
                (model_relations['Object_name_2'] == temporal_block_name)
            ].shape[0] > 0
            
            if not relationship_exists:
                new_relation_mod = {
                    "Relationship_class_name": "model__temporal_block",
                    "Object_class_name_1": "model",
                    "Object_class_name_2": "temporal_block",
                    "Object_name_1": model_name,
                    "Object_name_2": temporal_block_name
                }
                model_relations.loc[len(model_relations)] = new_relation_mod
                new_relation = {
                    "Relationship_class_name": "node__temporal_block",
                    "Node": node_name,
                    "Temporal_block": temporal_block_name
                }
                temporal_relations.loc[len(temporal_relations)] = new_relation

# Temporal blocks values (use only for h, D, M, and Y)
def create_temporal_block_input(df, model, run_name):
    if pd.isnull(df['resolution_output']).any():
        return

    for index, row in df.iterrows():
        temporal_block_name = resolution_to_block.get(row['resolution_output'])
        if temporal_block_name:
            # Check if parameter already exists
            parameter_exists = model[
                (model['Object_name'] == temporal_block_name) &
                (model['Parameter'] == "resolution")
            ].shape[0] > 0
            
            if row['resolution_output'] == 'W':
                value = '{"type":"duration", "data": "7D"}'
            elif row['resolution_output'] == 'Q':
                value = '{"type":"duration", "data": "3M"}'
            else:
                value = '{"type":"duration", "data": "1' + row['resolution_output'] + '"}'
        
            if not parameter_exists:
                new_parameter = {
                    "Object_class_name": "temporal_block",
                    "Object_name": temporal_block_name,
                    "Parameter": "resolution",
                    "Value": value,
                    "Alternative": run_name
                }
                model.loc[len(model)] = new_parameter

# Recalculate frac state loss
def adjust_frac_state_loss(storages_df, column_name):
    '''adjust the frac state loss value to be usable in the SpineOpt logic

    Parameters:
    storages_df (pd.DataFrame): The DataFrame containing the storage data.
    column_name (str): The name of the column to adjust.
    
    Returns:
    pd.DataFrame: The DataFrame with the adjusted column.
    '''
    # Define the adjustment function
    def adjust_value(frac_state_loss):
        return (1 - (1 - frac_state_loss)) / (1 - frac_state_loss)
        
    # Apply the adjustment function to the specified column
    storages_df[column_name] = storages_df[column_name].apply(adjust_value)
    
    return storages_df

# Convert lifetime + investment horizon into days
def convert_to_days(time_string, year):
    if pd.isna(time_string) or not isinstance(time_string, str):
        return None
    
    time_string = time_string.strip()
    
    try:
        # Extract the numeric value and the unit
        if time_string.isalpha():
            num = 1  # Default to 1 if no numeric value is provided
            unit = time_string.upper()  # Ensure uppercase for consistency
        else:
            num = int(time_string[:-1])  # Extract numeric part
            unit = time_string[-1].upper()
    except ValueError:
        return None
    
    # Define conversion factors
    conversion_factors = {
        'Y': 365 + calendar.isleap(year),
        'Q': (365 + calendar.isleap(year))/4,
        'M': (365 + calendar.isleap(year))/12,
        'W': 7,
        'D': 1,
        'h': 1/24
    }
    
    # Convert to days using the appropriate factor
    if unit in conversion_factors:
        days = num * conversion_factors[unit]
        if time_string.isalpha():
            return days
        else:
            return f"{days}D"
    else:
        return None

# Scale investment costs to actual model duration
def scale_costs(df, start, end, object):
    # Calculate days in year
    model_time = (end - start).days + 1
    
    col_time = f"{object}_investment_tech_lifetime"
    col_costs = f"{object}_investment_cost"
    
    # Calculate scaling factor
    df['lifetime_days'] = df[col_time].str.extract(r'(\d+)').astype(float)
    df['factor'] = df['lifetime_days'] / model_time
    
    df[col_costs] = df[col_costs] / df['factor']
    
    df = df.drop(['lifetime_days', 'factor'], axis=1)
    
    return df

# Translate product
def translate_product(product):
    if product == 'ammonia':
        product_tr = 'nh3'
    elif product == 'diesel':
        product_tr = 'diesel'
    elif product == 'egasoline':
        product_tr = 'egasoline'
    elif product == 'hydrogen':
        product_tr = 'h2'
    elif product == 'jet_fuel':
        product_tr = 'jet_fuel'
    elif product == 'methanol':
        product_tr = 'ch3oh'
    elif product == 'methane':
        product_tr = 'ch4'
    
    return product_tr
