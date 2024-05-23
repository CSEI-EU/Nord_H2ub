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

#function to prepare all parameters that are directly linked to a unit
def create_unit_parameters(input_df, object_class_type, parameter_column):
    # New DataFrame to store the information
    unit_parameter_df = pd.DataFrame(columns=['Object_Name', 'Category', 'parameter', 'value'])

    # Iterate through rows and add new rows to the new DataFrame if the parameter has a value
    for index, row in input_df.iterrows():
        if pd.notna(row[parameter_column]):
            new_row = {'Object_Name': row[object_class_type], 'Category': object_class_type.lower(), 'parameter': parameter_column, 'value': row[parameter_column]}
            unit_parameter_df = pd.concat([unit_parameter_df, pd.DataFrame([new_row])], ignore_index=True)

            # Check if parameter_column is 'min_down_time'
            if parameter_column == 'min_down_time':
                # Create an additional row with 'online_variable_type' and value 'unit_online_variable_type_integer'
                online_variable_row = {'Object_Name': row[object_class_type], 'Category': object_class_type.lower(), 'parameter': 'online_variable_type', 'value': 'unit_online_variable_type_integer'}
                unit_parameter_df = pd.concat([unit_parameter_df, pd.DataFrame([online_variable_row])], ignore_index=True)

    return unit_parameter_df

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
    dataframe_copy['Delta'] = dataframe_copy['Power [%]'].diff().fillna(dataframe_copy['Power [%]'])
    
    # Adjust the efficiency to the desired efficiency
    mean_eff_act = (dataframe_copy['Delta'] * dataframe_copy['Efficiency [%]']).sum()
    dataframe_copy['Efficiency_scaled [%]'] = dataframe_copy['Efficiency [%]'] + (mean_eff_goal - mean_eff_act)
    
    # Getting the base variables such as maximal efficiency and the index
    highest_eff_index_raw = dataframe_copy['Efficiency_scaled [%]'].idxmax()
    df_efficiency_adj = dataframe_copy.loc[highest_eff_index_raw:].reset_index(drop=True)
    
    # Set first adjusted efficiency value
    df_efficiency_adj['eff_adjusted_' + unit] = float('nan')
    df_efficiency_adj.loc[0, 'eff_adjusted_' + unit] = df_efficiency_adj.loc[0, 'Efficiency_scaled [%]']
    df_efficiency_adj.loc[0, 'Delta'] = df_efficiency_adj.loc[0, 'Power [%]']
    
    # Calculate adjusted efficiency values
    for i in range(1, len(df_efficiency_adj) - 1):
        efficiency = df_efficiency_adj.loc[i, 'Efficiency_scaled [%]']
        power = df_efficiency_adj.loc[i, 'Power [%]']
        delta = df_efficiency_adj.loc[i, 'Delta']
        
        sum_product = (df_efficiency_adj.loc[:i-1, 'eff_adjusted_' + unit] * df_efficiency_adj.loc[:i-1, 'Delta']).sum()
        
        new_value = (efficiency * power - sum_product) / delta
        
        df_efficiency_adj.loc[i, 'eff_adjusted_' + unit] = new_value
    
    # Set the last value equal to the second last value
    df_efficiency_adj.loc[len(df_efficiency_adj) - 1, 'eff_adjusted_' + unit] = df_efficiency_adj.loc[len(df_efficiency_adj) - 2, 'eff_adjusted_' + unit]
    
    return df_efficiency_adj


def calculate_op_points(unit, des_segment, df_efficiency_adj):
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
    
    operating_point_info_df = pd.DataFrame()
    operating_point_info_df['relationship_class:'] = operating_point_segments_df.index.tolist()
    operating_point_info_df['unit__from_node__user_constraint'] = operating_point_segments_df['average_efficiency']
    operating_point_info_df['unit__from_node'] = operating_point_segments_df['operating_segment_end']
    
    return operating_point_info_df, segment_x_values, segment_averages, x_values, y_values

