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
import ipywidgets as widgets
from IPython.display import display

'''Define functions'''

def on_change(change):
    if change['name'] == 'value' and change['new'] != "":
        print(f'You selected: {change["new"]}')


def create_dropdown(variable):
    if variable == 'year':
        dropdown = widgets.Dropdown(
            options=[2018, 2019, 2020, 2021, 2022],
            description='year:',
            value=None
        )
    elif variable == 'area':
        dropdown = widgets.Dropdown(
            options=['DE', 'DK1', 'DK2', 'NO2', 'SE3', 'SE4', 'SYSTEM'],
            description='area:',
            value='DK1'
        )
    elif variable == 'product':
        dropdown = widgets.Dropdown(
            options=['ammonia', 'methanol', 'jet_fuel'],
            description='product:',
            value='methanol'
        )
    elif variable == 'frequency':
        dropdown = widgets.Dropdown(
            options=['1h', '1D', '1M', '1Y'],
            description='frequency:',
            value='1h'
        )
    elif variable == 'electrolyzer_type':
        dropdown = widgets.Dropdown(
            options=['PEM', 'Alkaline', 'SOEC'],
            description='electrolyzer_type:',
            value='Alkaline'
        )
    elif variable == 'des_segments_electrolyzer':
        dropdown = widgets.Dropdown(
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            description='des_segments_electrolyzer:',
            value=None
        )
    else:
        dropdown = widgets.Dropdown(
            options=[1, 2, 3],
            description=f'{variable}:',
            value=None  # Initial value
        )
    
    dropdown.observe(on_change, names='value')
    return dropdown



'binary_gas_connection_flow',
'connection_avg_intact_throughflow',
'connection_avg_throughflow',
'connection_flow',
'connection_flow_costs',
'connection_intact_flow',
'connection_investment_costs',
'connections_decommissioned',
'connections_invested',
'connections_invested_available',
'contingency_is_binding''fixed_om_costs',
'fuel_costs',
'mga_objective',
'mp_objective_lowerbound',
'node_injection',
'node_pressure',
'node_slack_neg',
'node_slack_pos',
'node_state',
'node_voltage_angle',
'nonspin_units_shut_down',
'nonspin_units_started_up',
'objective_penalties',
'relative_optimality_gap',
'renewable_curtailment_costs',
'res_proc_costs',
'shut_down_costs',
'start_up_costs',
'storage_investment_costs',
'storages_decommissioned',
'storages_invested',
'storages_invested_available',
'taxes',
'total_costs',
'unit_flow',
'unit_flow_op',
'unit_flow_op_active',
'unit_investment_costs',
'units_invested',
'units_invested_available',
'units_mothballed',
'units_on',
'units_on_costs',
'units_shut_down',
'units_started_up',
'variable_om_costs'


def on_change_MC(change, selected_options, checkbox, name):
    if change['type'] == 'change' and change['name'] == 'value':
        if change['new']:
            selected_options.add(checkbox.description)
        else:
            selected_options.discard(checkbox.description)
        print(f'{name} selected: {selected_options}')

def create_multiple_choice_1():
    options = ['Option 1', 'Option 2', 'Option 3']
    selected_options = set()
    checkboxes = []
    
    for option in options:
        checkbox = widgets.Checkbox(value=False, description=option)
        checkbox.observe(lambda change, checkbox=checkbox: on_change_MC(change, selected_options, checkbox, 'Multiple Choice 1'))
        checkboxes.append(checkbox)
    
    label = widgets.Label("Multiple Choice 1:")
    return widgets.VBox([label] + checkboxes)

def create_combined_multiple_choices():
    multiple_choice_1 = create_multiple_choice_1()
    combined = widgets.VBox([multiple_choice_1])
    return combined    