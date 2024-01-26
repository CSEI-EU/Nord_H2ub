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