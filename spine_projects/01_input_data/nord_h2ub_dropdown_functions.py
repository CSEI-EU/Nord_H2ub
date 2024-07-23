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

'''Define text query functions'''

def on_text_change(change):
    if change['type'] == 'change' and change['name'] == 'value':
        print(f'You entered: {change["new"]}')

#create the text iput query
def create_text_input():
    label = widgets.Label("Please type the name of the model if other than Model:")
    default_text = "Model"
    text_input = widgets.Text(
        value=default_text,
    )
    text_input.observe(on_text_change, names='value')
    return widgets.VBox([label, text_input]), text_input


'''Define numerical input functions'''

def on_number_change(change):
    if change['type'] == 'change' and change['name'] == 'value':
        print(f'You entered: {change["new"]}')

def create_share_of_dh_price_cap():
    default_number = 50  # Set as a default to not assume 100%
    description_label = widgets.Label("Set the assumed value for revenues from district heating as share of a max price (%):")
    number_input = widgets.BoundedFloatText(
        value=default_number,
        min=0,
        max=200.0,
        step=0.1,
    )
    number_input.observe(on_number_change, names='value')
    
    return widgets.VBox([description_label, number_input]), number_input

'''Define dropdown functions'''

#change the parameter values of the if the drop down menu value is changes
def on_change(change):
    if change['name'] == 'value' and change['new'] != "":
        print(f'You selected: {change["new"]}')

#create dropdown for the year
def create_dropdown_year():
    label1 = widgets.Label("Please select the base year:")
    dropdown1 = widgets.Dropdown(
        options=[2018, 2019, 2020, 2021, 2022],
        value=None
    )
    dropdown1.observe(on_change)
    return widgets.VBox([label1, dropdown1]), dropdown1

#create dropdown for the power price zone
def create_dropdown_price_zone():
    label2 = widgets.Label("Please select the power price zone where the plant is located:")
    dropdown2 = widgets.Dropdown(
        options=['DE', 'DK1', 'DK2', 'NO2', 'SE3', 'SE4', 'SYSTEM'],
        value=None
    )
    dropdown2.observe(on_change)
    return widgets.VBox([label2, dropdown2]), dropdown2   

#create dropdown for the product
def create_dropdown_product():
    label3 = widgets.Label("Please set the product of the plant:")
    dropdown3 = widgets.Dropdown(
        options=['ammonia', 'methanol', 'jet_fuel'],
        value=None
    )
    dropdown3.observe(on_change)
    return widgets.VBox([label3, dropdown3]), dropdown3   

#create dropdown for the electrolysis type
def create_dropdown_electrolysis():
    label4 = widgets.Label("Please select the type of electrolysis:")
    dropdown4 = widgets.Dropdown(
        options=['PEM', 'Alkaline', 'SOEC'],
        value=None
    )
    dropdown4.observe(on_change)
    return widgets.VBox([label4, dropdown4]), dropdown4  

#create dropdown for the model frequency
def create_dropdown_frequency():
    label5 = widgets.Label("Please select the frequency:")
    dropdown5 = widgets.Dropdown(
        options=['1h', '1D', '1W', '1M', '1Q', '1Y'],
        value=None
    )
    dropdown5.observe(on_change)
    return widgets.VBox([label5, dropdown5]), dropdown5

def create_multiple_choice_1():
    options = ['binary_gas_connection_flow', 'connection_avg_intact_throughflow', 'connection_avg_throughflow', 'connection_flow', 'connection_flow_costs', 'connection_intact_flow', 'connection_investment_costs', 'connections_decommissioned', 'connections_invested', 'connections_invested_available', 'contingency_is_binding', 'fixed_om_costs', 'fuel_costs', 'mga_objective', 'mp_objective_lowerbound', 'node_injection', 'node_pressure', 'node_slack_neg', 'node_slack_pos', 'node_state', 'node_voltage_angle', 'nonspin_units_shut_down', 'nonspin_units_started_up', 'objective_penalties', 'relative_optimality_gap', 'renewable_curtailment_costs', 'res_proc_costs', 'shut_down_costs', 'start_up_costs', 'storage_investment_costs', 'storages_decommissioned', 'storages_invested', 'storages_invested_available', 'taxes', 'total_costs', 'unit_flow', 'unit_flow_op', 'unit_flow_op_active', 'unit_investment_costs', 'units_invested', 'units_invested_available', 'units_mothballed', 'units_on', 'units_on_costs', 'units_shut_down', 'units_started_up', 'variable_om_costs']
    selected_options = set()
    checkboxes = []
    
    for option in options:
        checkbox = widgets.Checkbox(value=False, description=option)
        checkbox.observe(lambda change, checkbox=checkbox: on_change_MC(change, selected_options, checkbox, 'Output'))
        checkboxes.append(checkbox)
    
    #2 columns
    columns = [widgets.VBox([]), widgets.VBox([])]
    for i, checkbox in enumerate(checkboxes):
        columns[i % 2].children += (checkbox,)
    
    label = widgets.Label("Please select the outputs for the report:")
    return widgets.VBox([label, widgets.HBox(columns)]), selected_options


def create_combined_multiple_choices():
    multiple_choice_1, selected_options = create_multiple_choice_1()
    combined = widgets.VBox([multiple_choice_1])
    return combined, selected_options  

'''Define functions for the combined data definition menu'''

#create a combined function to get all dropdowns in one execution
def create_combined_dropdowns():
    #give the user further information of the data to set
    section_1 = widgets.HTML("<b>Section 1: Please define the base parameters</b>")
    section_2 = widgets.HTML("<b>Section 2: Please define the parameters of electrolysis</b>")
    section_3 = widgets.HTML("<b>Section 3: Please define the economic parameters of the general model</b>")
    section_4 = widgets.HTML("<b>Section 3: Please define the parameters of the general model</b>")
    #get the dropdown menus
    model_name_input_box, model_name_input = create_text_input()
    dropdown_year_vbox, dropdown_year = create_dropdown_year()
    dropdown_price_zone_vbox, dropdown_price_zone = create_dropdown_price_zone()
    dropdown_product_vbox, dropdown_product = create_dropdown_product()
    dropdown_electrolysis_vbox, dropdown_electrolysis = create_dropdown_electrolysis()
    dropdown_frequency_vbox, dropdown_frequency = create_dropdown_frequency()
    number_dh_price_box, number_dh_price = create_share_of_dh_price_cap()
    
    #store dropdowns in a dictionary
    dropdowns = {
        'name': model_name_input,
        'year': dropdown_year,
        'price_zone': dropdown_price_zone,
        'product': dropdown_product,
        'electrolysis': dropdown_electrolysis,
        'frequency': dropdown_frequency,
        'number_dh_price_share': number_dh_price
    }
    #combine all dropdowns
    combined = widgets.VBox([
        section_1, model_name_input_box, dropdown_year_vbox, 
        dropdown_price_zone_vbox, dropdown_product_vbox, 
        section_2, dropdown_electrolysis_vbox,
        section_3, number_dh_price_box,
        section_4, dropdown_frequency_vbox
    ])
    return combined, dropdowns


#create a function to access the values in combined function
def get_dropdown_values(dropdowns):
    return {
        'model_name': dropdowns['name'].value,
        'year': dropdowns['year'].value,
        'price_zone': dropdowns['price_zone'].value,
        'product': dropdowns['product'].value,
        'electrolysis': dropdowns['electrolysis'].value,
        'frequency': dropdowns['frequency'].value,
        'share_of_dh_price_cap': dropdowns['number_dh_price_share'].value / 100
    }

'''Define multiple choice functions'''

def on_change_MC(change, selected_options, checkbox, name):
    if change['type'] == 'change' and change['name'] == 'value':
        if change['new']:
            selected_options.add(checkbox.description)
        else:
            selected_options.discard(checkbox.description)
        print(f'{name} selected: {selected_options}')



