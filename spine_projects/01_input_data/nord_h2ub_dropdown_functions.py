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
from IPython.display import display, HTML


'''Define text query functions'''

def on_text_change(change):
    if change['type'] == 'change' and change['name'] == 'value':
        print(f'You entered: {change["new"]}')

def create_name_input():
    label1 = widgets.Label("Please type the name of the model if other than 'Model':")
    default_text = "Model"
    name_input = widgets.Text(
        value=default_text,
    )
    name_input.observe(on_text_change, names='value')
    return widgets.VBox([label1, name_input]), name_input

def create_name_rep_input():
    label2 = widgets.Label("Please type the name of the report if other than 'Report':")
    default_text = "Report"
    name_rep_input = widgets.Text(
        value=default_text,
    )
    return widgets.VBox([label2, name_rep_input]), name_rep_input

def create_scen_name_input():
    label3 = widgets.Label("Please type the name of the scenario if other than 'Base':")
    default_text = "Base"
    base_name_input = widgets.Text(
        value=default_text,
        description="Base Scenario:"
    )
    additional_names_input = widgets.Textarea(
        value='',
        placeholder='Enter each scenario name on a new line',
        description='Other Scenarios:'
    )
    return widgets.VBox([label3, base_name_input, additional_names_input]), base_name_input, additional_names_input

def create_stoch_scen_input():
    label4 = widgets.Label("Please type the name of the stochastic scenario if other than 'realisation':")
    default_text = "realisation"
    stoch_scen_input = widgets.Text(
        value=default_text,
    )
    return widgets.VBox([label4, stoch_scen_input]), stoch_scen_input

def create_stoch_struc_input():
    label5 = widgets.Label("Please type the name of the stochastic structure if other than 'deterministic':")
    default_text = "deterministic"
    stoch_struc_input = widgets.Text(
        value=default_text,
    )
    return widgets.VBox([label5, stoch_struc_input]), stoch_struc_input


'''Define numerical input functions'''

def on_number_change(change):
    if change['type'] == 'change' and change['name'] == 'value':
        print(f'You entered: {change["new"]}')

def create_share_of_dh_price_cap():
    default_number = 50  # Set as a default to not assume 100%
    description_label_1 = widgets.Label("Set the assumed value for revenues from district heating as share of a max price (%):")
    number_input_1 = widgets.BoundedFloatText(
        value=default_number,
        min=0,
        max=200.0,
        step=0.1,
    )
    number_input_1.observe(on_number_change, names='value')
    return widgets.VBox([description_label_1, number_input_1]), number_input_1

def create_price_level_power():
    description_label_2 = widgets.Label("Set the assumed value for scaling the power price level up/down (%):")
    number_input_2 = widgets.BoundedFloatText(
        value=100,
        min=0,
        max=200.0,
        step=0.1,
    )
    number_input_2.observe(on_number_change, names='value')
    return widgets.VBox([description_label_2, number_input_2]), number_input_2

def create_power_price_variance():
    default_number = 1
    description_label_3 = widgets.Label("Set the assumed variance of the power prices:")
    number_input_3 = widgets.BoundedFloatText(
        value=0,
        min=0,
        max=2.0,
        step=0.01,
    )
    number_input_3.observe(on_number_change, names='value')
    return widgets.VBox([description_label_3, number_input_3]), number_input_3

def create_number_slices():
    default_number = 1
    description_label_4 = widgets.Label("Set the number of slices for the model:")
    number_input_4 = widgets.BoundedFloatText(
        value=12,
        min=0,
        max=30,
        step=1,
    )
    number_input_4.observe(on_number_change, names='value')
    return widgets.VBox([description_label_4, number_input_4]), number_input_4

def create_levels_elec():
    default_number = 1
    description_label_5 = widgets.Label("Set the gradient of variable efficiency:")
    number_input_5 = widgets.BoundedFloatText(
        value=3,
        min=0,
        max=10,
        step=1,
    )
    number_input_5.observe(on_number_change, names='value')
    return widgets.VBox([description_label_5, number_input_5]), number_input_5


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
        value='1h'
    )
    dropdown5.observe(on_change)
    return widgets.VBox([label5, dropdown5]), dropdown5

#create dropdown for the whether or not roll_forward is used
def create_dropdown_roll():
    label6 = widgets.Label("Please select whether or not roll_forward is used:")
    dropdown6 = widgets.Dropdown(
        options=[True, False],
        value=True
    )
    dropdown6.observe(on_change)
    return widgets.VBox([label6, dropdown6]), dropdown6

roll_forward_use = True
'''Define multiple choice functions'''

def on_change_MC(change, selected_options, checkbox, name):
    if change['type'] == 'change' and change['name'] == 'value':
        if change['new']:
            selected_options.add(checkbox.description)
        else:
            selected_options.discard(checkbox.description)
        print(f'{name} selected: {selected_options}')

def create_multiple_choice_report():
    options = ['binary_gas_connection_flow', 'connection_avg_intact_throughflow', 'connection_avg_throughflow', 'connection_flow', 'connection_flow_costs', 'connection_intact_flow', 'connection_investment_costs', 'connections_decommissioned', 'connections_invested', 'connections_invested_available', 'contingency_is_binding', 'fixed_om_costs', 'fuel_costs', 'mga_objective', 'mp_objective_lowerbound', 'node_injection', 'node_pressure', 'node_slack_neg', 'node_slack_pos', 'node_state', 'node_voltage_angle', 'nonspin_units_shut_down', 'nonspin_units_started_up', 'objective_penalties', 'relative_optimality_gap', 'renewable_curtailment_costs', 'res_proc_costs', 'shut_down_costs', 'start_up_costs', 'storage_investment_costs', 'storages_decommissioned', 'storages_invested', 'storages_invested_available', 'taxes', 'total_costs', 'unit_flow', 'unit_flow_op', 'unit_flow_op_active', 'unit_investment_costs', 'units_invested', 'units_invested_available', 'units_mothballed', 'units_on', 'units_on_costs', 'units_shut_down', 'units_started_up', 'variable_om_costs']
    selected_options_report = set()
    checkboxes = []
    
    for option in options:
        checkbox = widgets.Checkbox(value=False, description=option)
        checkbox.observe(lambda change, checkbox=checkbox: on_change_MC(change, selected_options_report, checkbox, 'Output'))
        checkboxes.append(checkbox)
    
    #3 columns
    columns = [widgets.VBox([]), widgets.VBox([]), widgets.VBox([])]
    for i, checkbox in enumerate(checkboxes):
        columns[i % 3].children += (checkbox,)
    
    label = widgets.Label("Please select the outputs for the report:")
    return widgets.VBox([label, widgets.HBox(columns)]), selected_options_report


'''Define functions for the combined data definition menu'''

def create_combined_dropdowns_tabs():
    # Provide information for each section
    section_1 = widgets.HTML("<b>Section 1: Please define the parameters of the general model</b>")
    section_2 = widgets.HTML("<b>Section 2: Please define the base parameters</b>")
    section_3 = widgets.HTML("<b>Section 3: Please define the parameters of electrolysis</b>")
    section_4 = widgets.HTML("<b>Section 4: Please define the economic parameters of the general model</b>")
    section_5 = widgets.HTML("<b>Section 5: Please define the variables for the report</b>")
    section_6 = widgets.HTML("<b>Section 6: Please define the parameters for the different scenarios</b>")

    # Get the dropdown menus
    model_name_input_box, model_name_input = create_name_input()
    dropdown_year_vbox, dropdown_year = create_dropdown_year()
    dropdown_price_zone_vbox, dropdown_price_zone = create_dropdown_price_zone()
    dropdown_product_vbox, dropdown_product = create_dropdown_product()
    dropdown_electrolysis_vbox, dropdown_electrolysis = create_dropdown_electrolysis()
    dropdown_frequency_vbox, dropdown_frequency = create_dropdown_frequency()
    number_dh_price_box, number_dh_price = create_share_of_dh_price_cap()
    number_price_level_power_box, number_price_level_power = create_price_level_power()
    power_price_variance_box, power_price_variance = create_power_price_variance()
    report_name_box, report_name = create_name_rep_input()
    multiple_choice_report, selected_options_report = create_multiple_choice_report()
    scen_name_box, base_scen, other_scen = create_scen_name_input()
    stoch_scen_vbox, stoch_scen = create_stoch_scen_input()
    stoch_struc_vbox, stoch_struc = create_stoch_struc_input()
    dropdown_roll_vbox, dropdown_roll = create_dropdown_roll()
    number_slices_vbox, number_slices = create_number_slices()
    levels_elec_box, levels_elec = create_levels_elec()
    
    # Store dropdowns in a dictionary
    dropdowns = {
        'name': model_name_input,
        'year': dropdown_year,
        'price_zone': dropdown_price_zone,
        'product': dropdown_product,
        'electrolysis': dropdown_electrolysis,
        'frequency': dropdown_frequency,
        'number_dh_price_share': number_dh_price,
        'number_price_level_power': number_price_level_power,
        'power_price_variance': power_price_variance,
        'report_name': report_name,
        'reports': selected_options_report,
        'base_scen': base_scen,
        'other_scen': other_scen,
        'stoch_scen': stoch_scen,
        'stoch_struc': stoch_struc,
        'roll_forward': dropdown_roll,
        'number_slices': number_slices,
        'levels_elec': levels_elec
    }

    # Create pages (tabs)
    page1 = widgets.VBox([
        section_1, model_name_input_box, dropdown_frequency_vbox,
        dropdown_roll_vbox, number_slices_vbox
    ])
    
    page2 = widgets.VBox([
        section_2, dropdown_year_vbox, 
        dropdown_price_zone_vbox, dropdown_product_vbox
    ])
    
    page3 = widgets.VBox([
        section_3, dropdown_electrolysis_vbox, levels_elec_box
    ])
    
    page4 = widgets.VBox([
        section_4, number_dh_price_box, number_price_level_power_box, 
        power_price_variance_box
    ])
    
    page5 = widgets.VBox([
        section_5, report_name_box, multiple_choice_report
    ])
    
    page6 = widgets.VBox([
        section_6, scen_name_box, stoch_scen_vbox, stoch_struc_vbox
    ])
    
    # Create Tab widget
    tabs = widgets.Tab()
    tabs.children = [page1, page2, page3, page4, page5, page6]
    tabs.set_title(0, 'General Model Parameters')
    tabs.set_title(1, 'Base Parameters')
    tabs.set_title(2, 'Electrolysis Parameters')
    tabs.set_title(3, 'Economic Parameters')
    tabs.set_title(4, 'Report')
    tabs.set_title(5, 'Scenarios')
    
    display(tabs)
    
    return tabs, dropdowns


#create a function to access the values in combined function
def get_dropdown_values(dropdowns):
    return {
        'model_name': dropdowns['name'].value,
        'year': dropdowns['year'].value,
        'price_zone': dropdowns['price_zone'].value,
        'product': dropdowns['product'].value,
        'electrolysis': dropdowns['electrolysis'].value,
        'frequency': dropdowns['frequency'].value,
        'roll_forward': dropdowns['roll_forward'].value,
        #numerical values that are given in percent are divided by 100 to get the right numbers for the model
        'share_of_dh_price_cap': dropdowns['number_dh_price_share'].value / 100,
        'number_price_level_power': dropdowns['number_price_level_power'].value / 100,
        'power_price_variance': dropdowns['power_price_variance'].value,
        'num_slices': dropdowns['number_slices'].value,
        'des_segments_electrolyzer': dropdowns['levels_elec'].value,
        #other text fields
        'base_scen': dropdowns['base_scen'].value,
        'other_scen': dropdowns['other_scen'].value,
        'stoch_scen': dropdowns['stoch_scen'].value,
        'stoch_struc': dropdowns['stoch_struc'].value,
        'report_name': dropdowns['report_name'].value,
        #multiple choice values
        'outputs': dropdowns['reports']
    }


