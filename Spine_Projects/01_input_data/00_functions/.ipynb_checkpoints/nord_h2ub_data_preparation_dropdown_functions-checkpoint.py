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
import pandas as pd
import threading
import time
import math
import warnings
import re
warnings.simplefilter("ignore", UserWarning)


'''General Layout Settings'''
general_input_layout = widgets.Layout(width='130px', padding = '0 0 0 30px')

def get_general_vbox_layout():
    return widgets.Layout(margin='0 0 15px 0')

general_multiple_choice_layout = widgets.Layout(padding='0 0 0 30px')

inv_cap_indent_layout = widgets.Layout(padding = '0 0 0 30px')

# Define the placeholder value for fields that are not yet interacted with
placeholder_value = math.nan


'''Define text query functions'''
text_values = {}

def on_text_change(change, key, input_widget):
    value = change['new']
    if value is not None:
        text_values[key] = value

def create_text_with_label(key: str, description: str, placeholder: str = 'e.g. xyz'):
    desc_label = widgets.Label(description)
    input_widget = widgets.Text(
        value=None,
        placeholder=placeholder,
        layout=general_input_layout)
    
    input_widget.observe(lambda change: on_text_change(change, key, input_widget), names='value')

    return widgets.VBox([desc_label, input_widget]), input_widget


'''Define 'numerical' input functions'''

parsed_values = {}

def smart_parse_number(text):
    # no spaces in between numbers
    text = text.strip().replace(' ', '')

    # Non-english style
    if re.match(r'^\d{1,3}(\.\d{3})*(,\d+)?$', text):
        normalized = text.replace('.', '').replace(',', '.')
        result = float(normalized)
        return result if result >= 0 else None   # Avoids negative numbers
    
    # English style
    if re.match(r'^\d{1,3}(,\d{3})*(\.\d+)?$', text):
        normalized = text.replace(',', '')
        result = float(normalized)
        return result if result >= 0 else None

    # Avoid 12.34.56
    try:
        result = float(text.replace(',', '.'))
        return result if result >= 0 else None
    except ValueError:
        return None

def on_number_change_2(change, error_label, parsed_key):
    raw_input = change['new']

    if raw_input == '':
        parsed_values[parsed_key] = None
        error_label.value = ''
        return
    
    value = smart_parse_number(raw_input)

    if value is not None:
        parsed_values[parsed_key] = value
        error_label.value = ''
    else:
        parsed_values[parsed_key] = None
        error_label.value = '❌ Invalid number format'

def create_input_with_label(key: str, description: str, placeholder: str = 'e.g. 12,345.57'):
    desc_label = widgets.Label(description)
    input_widget = widgets.Text(
        value='',
        placeholder=placeholder,
        layout=general_input_layout
    )
    error_label = widgets.Label()

    input_widget.observe(lambda change: on_number_change_2(change, error_label, key), names='value')

    return widgets.VBox([desc_label, widgets.HBox([input_widget, error_label])]), input_widget


############# Old way
def on_number_change(change):
    if change['type'] == 'change' and change['name'] == 'value':
        print(f'You entered: {change["new"]}')

# Set investment costs and capacity limit depending on type of product
investment_cost_vbox = widgets.VBox(layout=widgets.Layout(align_items='flex-start', margin='0 0 15px 0'))
investment_cost_values = {}
investment_limit_values = {}

def create_inv_cap_with_label(key: str, description: str, placeholder: str):
    desc_label = widgets.Label(description, 
                               layout=widgets.Layout(width='250px')
                              )
    input_widget = widgets.Text(
        value = '',
        placeholder = placeholder,
        layout = widgets.Layout(width='110px')
    )
    error_label = widgets.Label()

    input_widget.observe(lambda change: on_number_change_2(change, error_label, key), names='value')

    return input_widget, widgets.HBox([desc_label, input_widget, error_label], layout=inv_cap_indent_layout)

def update_inv_costs(change, investment_cost_vbox):
    # Get selected product from the dropdown (ammonia, diesel, egasoline, hydrogen, jet_fuel, methanol, and synthetic_methane_gas)
    selected_product = change['new']
    
    # Clear existing investment widgets (if any)
    investment_cost_vbox.children = []
    elements = []
    
    # Clear the investment_cost_values dictionary before updating
    investment_cost_values.clear()
    investment_limit_values.clear()
    
    # Headline for the investment costs block
    investment_headline = widgets.Label("Please define the investment cost and maximal installed capacities per MW or MWh. If left empty, default values will be used.",
    style={'font_weight': 'bold'})
    elements.append(investment_headline) 

    # Shared items (for all)
    electrolyzer_label = widgets.Label("Electrolyzer:")
    electrolyzer_input, electrolyzer_hbox = create_inv_cap_with_label('electrolyzer_inv', 'Costs [€/MW power input]:', 'test')
    electrolyzer_limit, electrolyzer_limit_hbox = create_inv_cap_with_label('electrolyzer_inv_limit', 
                                                                            'Capacity limit [MW input power]:', '100')
    
    hydrogen_st_label = widgets.Label("Hydrogen storage:")
    hydrogen_st_input, hydrogen_st_hbox = create_inv_cap_with_label('hydrogen_inv', 'Costs [€/MWh storage]:', 'test')
    hydrogen_st_limit, hydrogen_st_limit_hbox = create_inv_cap_with_label('hydrogen_inv_limit', 
                                                                          'Capacity limit [MW input power]:', '1000')
      
    elements += [electrolyzer_label, electrolyzer_hbox, electrolyzer_limit_hbox, 
                 hydrogen_st_label, hydrogen_st_hbox, hydrogen_st_limit_hbox]
    
    investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
    investment_cost_values['inv_cost_hydrogen_storage'] = hydrogen_st_input
    investment_limit_values['inv_limit_electrolyzer'] = electrolyzer_limit
    investment_limit_values['inv_limit_hydrogen_storage'] = hydrogen_st_limit

    # Shared items for some
    fischer_label = widgets.Label("Fischer-Tropsch Reactor:")
    fischer_input, fischer_hbox = create_inv_cap_with_label('fischer_inv', 'Costs [€/MW fuels output]:', 'test')
    fischer_limit, fischer_limit_hbox = create_inv_cap_with_label('fischer_inv_limit', 'Capacity limit [MW fuels output]:', '100')
    
    rwgs_label = widgets.Label("RWGS reactor:")
    rwgs_input, rwgs_hbox = create_inv_cap_with_label('rwgs_inv', 'Costs [€/MWh fuels output]:', 'test')
    rwgs_limit, rwgs_limit_hbox = create_inv_cap_with_label('rwgs_inv_limit', 'Capacity limit [MW fuels output]:', '100')
    
    steam_label = widgets.Label("Steam plant:")
    steam_input, steam_hbox = create_inv_cap_with_label('steam_inv', 'Costs [€/MW input power]:', 'test')
    steam_limit, steam_limit_hbox = create_inv_cap_with_label('steam_inv_limit', 'Capacity limit [MW input power]:', '100')
    
    # Product specific investment:
    if selected_product == 'ammonia':
        
        ammonia_st_label = widgets.Label("Ammonia storage:")
        ammonia_st_input, ammonia_st_hbox = create_inv_cap_with_label('ammonia_st_inv', 'Costs [€/MWh storage]:', 'test')
        ammonia_st_limit, ammonia_st_limit_hbox = create_inv_cap_with_label('ammonia_st_inv_limit', 
                                                                            'Capacity limit [MWh storage]:', '1000')
    
        asu_label = widgets.Label("Air separation unit")
        asu_input, asu_hbox = create_inv_cap_with_label('asu_inv', 'Costs [€/MW input power]:', 'test')
        asu_limit, asu_limit_hbox = create_inv_cap_with_label('asu_inv_limit', 'Capacity limit [MW input power]:', '100')
        
        haber_label = widgets.Label("Haber-Bosch unit:")
        haber_input, haber_hbox = create_inv_cap_with_label('haber_inv', 'Costs [€/MW ammonia output]:', 'test')
        haber_limit, haber_limit_hbox = create_inv_cap_with_label('haber_inv_limit', 'Capacity limit [MW ammonia output]:', '100')
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_ammonia_storage'] = ammonia_st_input
        investment_cost_values['inv_cost_asu'] = asu_input
        investment_cost_values['inv_cost_haber'] = haber_input
        
        investment_limit_values['inv_limit_ammonia_storage'] = ammonia_st_limit
        investment_limit_values['inv_limit_asu'] = asu_limit
        investment_limit_values['inv_limit_fischer'] = haber_limit
        
        elements += [ammonia_st_label, ammonia_st_hbox, ammonia_st_limit_hbox, 
                     asu_label, asu_hbox, asu_limit_hbox,
                     haber_label, haber_hbox, haber_limit_hbox]
        investment_cost_vbox.children = elements
        
    
    elif selected_product == 'diesel':

        diesel_st_label = widgets.Label("Diesel storage:")
        diesel_st_input, diesel_st_hbox = create_inv_cap_with_label('diesel_st_inv', 'Costs [€/MWh storage]:', 'test')
        diesel_st_limit, diesel_st_limit_hbox = create_inv_cap_with_label('diesel_st_inv_limit', 
                                                                          'Capacity limit [MWh storage]:', '1000')
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_diesel_storage'] = diesel_st_input
        investment_cost_values['inv_cost_fischer'] = fischer_input
        investment_cost_values['inv_cost_rwgs'] = rwgs_input
        investment_cost_values['inv_cost_steam'] = steam_input

        investment_limit_values['inv_limit_diesel_storage'] = diesel_st_limit
        investment_limit_values['inv_limit_fischer'] = fischer_limit
        investment_limit_values['inv_limit_rwgs'] = rwgs_limit
        investment_limit_values['inv_limit_steam'] = steam_limit

        elements += [diesel_st_label, diesel_st_hbox, diesel_st_limit_hbox, 
                     fischer_label, fischer_hbox, fischer_limit_hbox,
                     rwgs_label, rwgs_hbox, rwgs_limit_hbox, 
                     steam_label, steam_hbox, steam_limit_hbox]
        investment_cost_vbox.children = elements
        
        
    elif selected_product == 'egasoline':
        
        egasoline_st_label = widgets.Label("E-Gasoline storage:")
        egasoline_st_input, egasoline_st_hbox = create_inv_cap_with_label('egasoline_st_inv', 'Costs [€/MWh storage]:', 'test')
        egasoline_st_limit, egasoline_st_limit_hbox = create_inv_cap_with_label('egasoline_st_inv_limit', 
                                                                                'Capacity limit [MWh storage]:', '1000')
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_egasoline_storage'] = egasoline_st_input
        investment_cost_values['inv_cost_fischer'] = fischer_input
        investment_cost_values['inv_cost_rwgs'] = rwgs_input
        investment_cost_values['inv_cost_steam'] = steam_input

        investment_limit_values['inv_limit_egasoline_storage'] = egasoline_st_limit
        investment_limit_values['inv_limit_fischer'] = fischer_limit
        investment_limit_values['inv_limit_rwgs'] = rwgs_limit
        investment_limit_values['inv_limit_steam'] = steam_limit
        
        elements += [egasoline_st_label, egasoline_st_hbox, egasoline_st_limit_hbox, 
                     fischer_label, fischer_hbox, fischer_limit_hbox,
                     rwgs_label, rwgs_hbox, rwgs_limit_hbox, 
                     steam_label, steam_hbox, steam_limit_hbox]
        investment_cost_vbox.children = elements
    
    elif selected_product == 'hydrogen':
        
        investment_cost_vbox.children = elements
    
    elif selected_product == 'jet_fuel':
        
        jet_fuel_st_label = widgets.Label("Jet Fuel storage:")
        jet_fuel_st_input, jet_fuel_st_hbox = create_inv_cap_with_label('jet_fuel_st_inv', 'Costs [€/MWh storage]:', 'test')
        jet_fuel_st_limit, jet_fuel_st_limit_hbox = create_inv_cap_with_label('jet_fuel_st_inv_limit', 
                                                                              'Capacity limit [MWh storage]:', '1000')
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_jet_fuel_storage'] = jet_fuel_st_input
        investment_cost_values['inv_cost_fischer'] = fischer_input
        investment_cost_values['inv_cost_rwgs'] = rwgs_input
        investment_cost_values['inv_cost_steam'] = steam_input
        
        investment_limit_values['inv_limit_jet_fuel_storage'] = jet_fuel_st_limit
        investment_limit_values['inv_limit_fischer'] = fischer_limit
        investment_limit_values['inv_limit_rwgs'] = rwgs_limit
        investment_limit_values['inv_limit_steam'] = steam_limit
        
        elements += [jet_fuel_st_label, jet_fuel_st_hbox, jet_fuel_st_limit_hbox, 
                     fischer_label, fischer_hbox, fischer_limit_hbox,
                     rwgs_label, rwgs_hbox, rwgs_limit_hbox, 
                     steam_label, steam_hbox, steam_limit_hbox]
        investment_cost_vbox.children = elements
    
    elif selected_product == 'methanol':
        methanol_label = widgets.Label("Methanol reactor:")
        methanol_input, methanol_hbox = create_inv_cap_with_label('methanol_inv', 'Costs [€/MW output methanol]:', 'test')
        methanol_limit, methanol_limit_hbox = create_inv_cap_with_label('methanol_inv_limit', 
                                                                        'Capacity limit [MW output methanol]:', '100')
        
        methanol_st_label = widgets.Label("Methanol storage:")
        methanol_st_input, methanol_st_hbox = create_inv_cap_with_label('methanol_st_inv', 'Costs [€/MWh storage]:', 'test')
        methanol_st_limit, methanol_st_limit_hbox = create_inv_cap_with_label('methanol_st_inv_limit', 
                                                                              'Capacity limit [MWh storage]:', '1000')
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_methanol'] = methanol_input
        investment_cost_values['inv_cost_methanol_storage'] = methanol_st_input
        investment_cost_values['inv_cost_steam'] = steam_input

        investment_limit_values['inv_limit_methanol'] = methanol_limit
        investment_limit_values['inv_limit_methanol_storage'] = methanol_st_limit
        investment_limit_values['inv_limit_steam'] = steam_limit

        elements += [methanol_label, methanol_hbox, methanol_limit_hbox, 
                     methanol_st_label, methanol_st_hbox, methanol_st_limit_hbox,
                     steam_label, steam_hbox, steam_limit_hbox]
        investment_cost_vbox.children = elements
        
    
    elif selected_product == 'methane':
        
        anaerobic_label = widgets.Label("Anaerobic digestion plant:")
        anaerobic_input, anaerobic_hbox = create_inv_cap_with_label('methanol_inv', 'Costs [€/MW TBA]:', 'test')
        anaerobic_limit, anaerobic_limit_hbox = create_inv_cap_with_label('methanol_inv_limit', 'Capacity limit [MW TBA]:', '100')
        
        biomethanation_label = widgets.Label("Biomethanation plant:")
        biomethanation_input, biomethanation_hbox = create_inv_cap_with_label('biomethanation_inv', 'Costs [€/MW TBA]:', 'test')
        biomethanation_limit, biomethanation_limit_hbox = create_inv_cap_with_label('biomethanation_inv_limit', 
                                                                                    'Capacity limit [MW TBA]:', '100')
        
        co2_remover_label = widgets.Label("CO2 removal plant:")
        co2_remover_input, co2_remover_hbox = create_inv_cap_with_label('co2_remover_inv', 'Costs [€/MW TBA]:', 'test')
        co2_remover_limit, co2_remover_limit_hbox = create_inv_cap_with_label('co2_remover_inv_limit', 'Capacity limit [MW TBA]:', '100')
        
        methane_st_label = widgets.Label("Methane storage:")
        methane_st_input, methane_st_hbox = create_inv_cap_with_label('methane_st_inv', 'Costs [€/MWh storage]:', 'test')
        methane_st_limit, methane_st_limit_hbox = create_inv_cap_with_label('methane_st_inv_limit', 
                                                                            'Capacity limit [MWh storage]:', '1000')
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_anaerobic'] = anaerobic_input
        investment_cost_values['inv_cost_biomethanation'] = biomethanation_input
        investment_cost_values['inv_cost_co2_removal'] = co2_remover_input
        investment_cost_values['inv_cost_methane_storage'] = methane_st_input

        investment_limit_values['inv_limit_methane_storage'] = methane_st_limit
        investment_limit_values['inv_limit_steam'] = steam_limit

        elements += [anaerobic_label, anaerobic_hbox, anaerobic_limit_hbox,
                     biomethanation_label, biomethanation_hbox, biomethanation_limit_hbox,
                     co2_remover_label, co2_remover_hbox, co2_remover_limit_hbox, 
                     methane_st_label, methane_st_hbox, methane_st_limit_hbox,
                     steam_label, steam_hbox, steam_limit_hbox]
        investment_cost_vbox.children = elements
        

# Set capacities of units depending on type of product
capacities_vbox = widgets.VBox(layout=widgets.Layout(margin='0 0 15px 0'))
capacities_values = {}

def update_capacities(change, capacities_vbox):
    # Get selected product from the dropdown (ammonia, diesel, egasoline, hydrogen, jet_fuel, methane, or methanol)
    selected_product = change['new']
    
    # Clear existing capacity widgets (if any)
    capacities_vbox.children = []
    elements_capacities = []
    
    # Clear the capacities_values dictionary before updating
    capacities_values.clear()
    
    # Headline for the investment costs block
    label = widgets.Label("Please define the existing capacities. If left empty, default values will be used.",
    style={'font_weight': 'bold'})
    elements_capacities.append(label) 

    # Shared values
    electrolyzer_input, electrolyzer_hbox = create_inv_cap_with_label('electrolyzer_cap', 'Electrolyzer [MW input power]:', '0')
    elements_capacities += [electrolyzer_hbox]

    capacities_values['capacity_electrolyzer'] = electrolyzer_input

    # Shared for some
    steam_input, steam_hbox = create_inv_cap_with_label('steam_cap', 'Steam plant [MW input power]:', '0')
    
    # Assign fields to products
    if selected_product == 'ammonia':

        asu_input, asu_hbox = create_inv_cap_with_label('asu_cap', 'Air separation unit [MW input power]:', '0')
        haber_input, haber_hbox = create_inv_cap_with_label('haber_cap', 'Haber-Bosch unit [MW ammonia output]:', '0')
        
        # Store values in capacity dictionary
        capacities_values['capacity_asu'] = asu_input
        capacities_values['capacity_haber'] = haber_input

        elements_capacities += [asu_hbox, haber_hbox]
        capacities_vbox.children = elements_capacities
    
    elif selected_product == 'hydrogen':

        capacities_vbox.children = elements_capacities
    
    elif selected_product == 'methanol':

        methanol_input, methanol_hbox = create_inv_cap_with_label('methanol_cap', 'Methanol reactor [MW output methanol]:', '0')
        
        # Store values in capacity dictionary
        capacities_values['capacity_methanol'] = methanol_input
        capacities_values['capacity_steam'] = steam_input
        
        elements_capacities += [methanol_hbox, steam_hbox]
        capacities_vbox.children = elements_capacities
    
    elif selected_product == 'methane':

        anaerobic_input, anaerobic_hbox = create_inv_cap_with_label('anaerobic_cap', 'Anaerobic digestion plant []:', '0')
        biomethanation_input, biomethanation_hbox = create_inv_cap_with_label('biomethanation_cap', 'Biomethanation plant []:', '0')
        co2_remover_input, co2_remover_hbox = create_inv_cap_with_label('co2_remover_cap', 'CO2 removal plant []:', '0')
        
        # Store values in capacity dictionary
        capacities_values['capacity_anaerobic'] = anaerobic_input
        capacities_values['capacity_biomethanation'] = biomethanation_input
        capacities_values['capacity_co2_removal'] = co2_remover_input
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_steam'] = steam_input
        
        elements_capacities += [anaerobic_hbox, biomethanation_hbox, co2_remover_hbox, steam_hbox]
        capacities_vbox.children = elements_capacities

    else:

        fischer_input, fischer_hbox = create_inv_cap_with_label('fischer_cap', 'Fischer-Tropsch reactor [MW fuels output]:', '0')
        rwgs_input, rwgs_hbox = create_inv_cap_with_label('rwgs_cap', 'RWGS reactor [MW fuels output]:', '0')
        
        # Store values in capacity dictionary
        capacities_values['capacity_fischer'] = fischer_input
        capacities_values['capacity_rwgs'] = rwgs_input
        capacities_values['capacity_steam'] = steam_input

        elements_capacities += [fischer_hbox, rwgs_hbox, steam_hbox]
        capacities_vbox.children = elements_capacities
        

# Define demand
def create_demand():
    # Define a layout for descriptions and fields
    description_layout = widgets.Layout(width='140px')
    input_layout = widgets.Layout(width='85px')
    
    # Add fields
    demand_description = widgets.Label("Yearly demand [MWh]:", layout=description_layout)
    
    demand_input = widgets.Text(
        value = '', 
        placeholder = '30,000',
        layout=input_layout
    )
    error_label = widgets.Label()

    demand_input.observe(lambda change: on_number_change_2(change, error_label, 'demand'), names='value')
    
    def create_dropdown_res():
        global option_values, selected_option_widget, selected_value_widget  
        option_values = ['hourly', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly']
        
        label_d_res = widgets.Label(" with a(n) ", layout=widgets.Layout(width='80px', justify_content='center'))
        label_d_res_2 = widgets.Label(" demand resolution")
        
        dropdown_d_res = widgets.Dropdown(
            options=option_values,
            value = None,
            layout=input_layout
        )
        dropdown_d_res.observe(on_change)
        demand_d_res_hbox = widgets.HBox([label_d_res, dropdown_d_res, label_d_res_2])

        return demand_d_res_hbox, dropdown_d_res

    demand_d_res_hbox, dropdown_d_res = create_dropdown_res() 
    demand_input_hbox = widgets.HBox([demand_input, error_label, demand_d_res_hbox], layout = general_multiple_choice_layout)
    
    return widgets.VBox([demand_description, demand_input_hbox], layout=get_general_vbox_layout()), demand_input, dropdown_d_res


'''Define dropdown functions'''

# Function to handle the change in dropdown selection
def on_change(change):
    if change['name'] == 'value' and change['new'] != "":
        print(f'You selected: {change["new"]}')


# Function to handle the change in dropdown selection for dictionaries
def on_change_dict(change):
    if change['type'] == 'change' and change['name'] == 'value':
        selected_option = change['new']
        selected_value = option_values[selected_option]
        selected_option_widget.value = selected_option
        selected_value_widget.value = selected_value

        
# Function to handle the change in investment dropdown selection
def on_change_dict_investment(change):
    if change['type'] == 'change' and change['name'] == 'value':
        selected_option = change['new']
        selected_value = option_values_invest[selected_option]
        selected_option_widget_invest_period.value = selected_option
        selected_value_widget_invest_period.value = selected_value


#create dropdown for the year
def create_dropdown_year():
    label1 = widgets.Label("Please select the base year for electricity prices:")
    dropdown1 = widgets.Dropdown(
        options=[2018, 2019],
        value = None,
        layout = general_input_layout
    )
    dropdown1.observe(on_change)
    return widgets.VBox([label1, dropdown1], layout=get_general_vbox_layout()), dropdown1


#create dropdown for the power price zone
def create_dropdown_price_zone():
    label2 = widgets.Label("Please select the power price zone where the plant is located:")
    dropdown2 = widgets.Dropdown(
        options=['DK_1', 'DK_2', 'DK_BHM', 'FI', 'NO_1', 'NO_2', 'NO_3', 'NO_4', 'NO_5', 'SE_1', 'SE_2', 'SE_3', 'SE_4'],
        value = None,
        layout = general_input_layout
    )
    dropdown2.observe(on_change)
    return widgets.VBox([label2, dropdown2], layout=get_general_vbox_layout()), dropdown2   


#create dropdown for the product
def create_dropdown_product():
    label3 = widgets.HTML("Please select the product of the plant <i>(required)</i>: ")
    dropdown3 = widgets.Dropdown(
        options = ['ammonia', 'diesel', 'egasoline', 'hydrogen', 'jet_fuel', 'methane', 'methanol'],
        value = None,
        layout = general_input_layout
    )
    def on_dropdown_change(change):
        update_inv_costs(change, investment_cost_vbox)   # Update investment costs box
        update_capacities(change, capacities_vbox)   # Update capacities box

    dropdown3.observe(on_dropdown_change, names='value')
    
    return widgets.VBox([label3, dropdown3], layout=get_general_vbox_layout()), dropdown3   


#create dropdown for the electrolysis type
def create_dropdown_electrolysis():
    label4 = widgets.Label("Please select the type of electrolysis:")
    dropdown4 = widgets.Dropdown(
        options = ['PEM', 'Alkaline', 'SOEC'],
        value = None,
        layout = general_input_layout
    )
    dropdown4.observe(on_change)
    return widgets.VBox([label4, dropdown4], layout=get_general_vbox_layout()), dropdown4  


# Create dropdown for the model frequency
def create_dropdown_temp_block():
    global option_values

    option_values = ['hourly', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly']
    
    label5 = widgets.Label("Please select the model resolution:")
    dropdown5 = widgets.Dropdown(
        options = option_values,
        value = None,
        layout = general_input_layout
    )
    
    dropdown5.observe(on_change, names='value')
    return widgets.VBox([label5, dropdown5], layout=get_general_vbox_layout()), dropdown5


#create dropdown for the whether roll_forward is used
roll_forward_use = True
def create_dropdown_roll():
    label6 = widgets.Label(
        "Please select whether the model should run with a rolling horizon optimization:"
    )
    dropdown6 = widgets.Dropdown(
        options=[True, False],
        value = None,
        layout = general_input_layout
    )
    dropdown6.observe(on_change)
    return widgets.VBox([label6, dropdown6], layout=get_general_vbox_layout()), dropdown6


#create dropdown for whether investments can be made
def create_dropdown_investment():
    
    label7 = widgets.Label("Please select whether the model should run an investment optimization:")
    dropdown7 = widgets.Dropdown(
        options=[True, False],
        value = None,
        layout=general_input_layout
    )
    dropdown7.observe(on_change)
    return widgets.VBox([label7, dropdown7], layout=get_general_vbox_layout()), dropdown7


# Create dropdown for the default investment period
def create_dropdown_invest_period():
    # Dictionary to map options to their corresponding values
    label8 = widgets.Label("Please select the investment period:")
    
    number_input_8 = widgets.BoundedFloatText(
        value=placeholder_value,
        min=1,
        max=30,
        step=1,
        layout=general_input_layout
    )
    number_input_8.observe(on_number_change, names='value')
    
    dropdown8 = widgets.Dropdown(
        options=['h', 'D', 'W', 'M', 'Q', 'Y'],
        value=None,
        layout=widgets.Layout(width='100px')
    )
    dropdown8.observe(on_change)

    input_hbox = widgets.HBox([number_input_8, dropdown8])
    
    return widgets.VBox([label8, input_hbox], layout=get_general_vbox_layout()), number_input_8, dropdown8


'''Define multiple choice functions'''

def on_change_MC_report(change, selected_options_report, checkbox):
    if change['new']:
        selected_options_report.add(checkbox.description)
        print(f'You added {checkbox.description} to the report.') #added more text to make it clearer for reports
    else:
        selected_options_report.discard(checkbox.description)

        
def create_multiple_choice_power():
    label_power = widgets.Label("Please select the different power sources already available:")
    
    # Define the list of options
    options_power = ['Grid', 'Solar plant', 'Wind onshore', 'Wind offshore']
    
    # Define preselected options and initialize selected_options_power
    preselected_options_power = {'Grid', 'Solar plant'}
    selected_options_power = set(preselected_options_power)
    
    # Create warning label
    warning_label = widgets.Label(value='')
    def clear_warning(checkbox, delay=2):
        time.sleep(delay)  # Waits for the specified time
        warning_label.value = ''  # Clears the warning message
        checkbox.value = True # Rechecks checkbox
    
    # Separate options into preselected and non-preselected
    preselected_checks_power = [option for option in options_power if option in preselected_options_power]
    non_preselected_checks_power = [option for option in options_power if option not in preselected_options_power]
    
    # Initiate dictionary for the capacity of each option
    capacities_powers = {}
    capacities_powers_values = {}
    hbox_capacities_powers = []
    
    # Function to update the capacity fields visibility
    def update_capacity_fields(selected_list, capacities_list):
        for option, hbox in capacities_list.items():
            if option in selected_list:
                hbox.layout.display = 'flex'
            else:
                hbox.layout.display = 'none'
    
    # Function to update the capacities_powers_values when changed
    def on_capacity_change(change, option):
        capacities_powers_values[option] = change['new']
    
    def on_change_MC_power(change, selected_options, checkbox, capacities):
        if change['new'] is False and len(selected_options) == 1:
            warning_label.value = "Warning: At least one power source must be selected!"
            threading.Thread(target=clear_warning, args=(change['owner'],)).start()
        else:
            warning_label.value = ""
            if change['new']:  # If the checkbox was checked
                selected_options.add(checkbox.description)
            else:  # If the checkbox was unchecked
                selected_options.remove(checkbox.description)
            update_capacity_fields(selected_options, capacities)
    
    # Create checkboxes
    checkboxes_powers = []
    
    # preselected options
    for option in preselected_checks_power:
        checkbox = widgets.Checkbox(
            value=True,  # All preselected options should be checked
            description=option,
            indent=False,
            layout=general_multiple_choice_layout
        )
        checkbox.observe(lambda change, 
                         checkbox=checkbox: on_change_MC_power(change, selected_options_power, checkbox, capacities_powers),
                         names='value')
        checkboxes_powers.append(checkbox)
    
    # non-preselected options
    for option in non_preselected_checks_power:
        checkbox = widgets.Checkbox(
            value=False,  # Non-preselected options should be unchecked
            description=option,
            indent=False,
            layout=general_multiple_choice_layout
        )
        checkbox.observe(lambda change, 
                         checkbox=checkbox: on_change_MC_power(change, selected_options_power, checkbox, capacities_powers),
                         names='value')
        checkboxes_powers.append(checkbox)
    
    # Create capacity fields for each option except grid (hidden initially):
    res = ['Solar plant', 'Wind onshore', 'Wind offshore']
    for option in res:
        capacity_widget = widgets.FloatText(
            value=placeholder_value,
            layout=widgets.Layout(width='100px')
        )
        label = widgets.Label(f"{option} capacity [MW]:", layout=widgets.Layout(width='180px'))
        
        hbox = widgets.HBox([label, capacity_widget], layout=widgets.Layout(display='none',
                                                                            padding='0px 15px 0px 30px',
                                                                            justify_content='flex-start'))
        capacities_powers[option] = hbox
        hbox_capacities_powers.append(hbox)
        
        capacities_powers_values[option] = capacity_widget.value
        capacity_widget.observe(lambda change, option=option: on_capacity_change(change, option), names='value')

    # Visibility of initially selected available powers
    update_capacity_fields(preselected_checks_power, capacities_powers)
    
    # Layout for checkboxes and capacity inputs
    power_column = widgets.VBox(checkboxes_powers)
    capacity_column = widgets.VBox(hbox_capacities_powers)
    
    # Add possibility for investment
    def create_dropdown_inv():
        label_inv = widgets.HTML(
            "Possibility for investment instead of fix values in RES <i>(not recommended)</i>:"
        )
        dropdown_inv = widgets.Dropdown(
            options=[True, False],
            value=None,
            layout=widgets.Layout(width='100px', margin='3px 0px 0 5px')
        )
        dropdown_inv.observe(on_change)
        return widgets.HBox([label_inv, dropdown_inv], layout=widgets.Layout(margin='0px 15px 0px 30px')), dropdown_inv
    inv_res_column, investment_res = create_dropdown_inv()

    # Add possibility of investment into a power storage
    def create_dropdown_inv_ps():
        label_inv_ps = widgets.HTML(
            "Possibility for investment in a power storage:"
        )
        dropdown_inv_ps = widgets.Dropdown(
            options=[True, False],
            value=None,
            layout=widgets.Layout(width='100px', margin='3px 5px 0 5px')
        )
        dropdown_inv_ps.observe(on_change)

        capacity_label = widgets.Label("with a maximum capacity of", layout=widgets.Layout(width='170px'))
        capacity_ps_widget = widgets.BoundedFloatText(
            value=placeholder_value,
            min=0,
            layout=widgets.Layout(width='100px'),
        )
        MW_label = widgets.Label(" MWh")
        capacity_container = widgets.HBox([capacity_label, capacity_ps_widget, MW_label])

        def toggle_capacity_widget(change):
            capacity_container.layout.display = 'flex' if change['new'] else 'none'
        
        # Observe changes in dropdown
        dropdown_inv_ps.observe(toggle_capacity_widget, names='value')
        
        # Initially hide capacity widgets if dropdown is False
        toggle_capacity_widget({'new': dropdown_inv_ps.value})
        
        return widgets.HBox([label_inv_ps, dropdown_inv_ps, capacity_container], 
                            layout=widgets.Layout(margin='0px 15px 0px 30px')), dropdown_inv_ps, capacity_ps_widget
        
    inv_ps_column, investment_ps, investment_ps_capacity = create_dropdown_inv_ps()
    
    hbox_warning = widgets.HBox([power_column, warning_label])
    
    return widgets.VBox([label_power, hbox_warning, capacity_column, inv_res_column, inv_ps_column], layout=get_general_vbox_layout()), selected_options_power, capacities_powers_values, investment_res, investment_ps, investment_ps_capacity
  

def create_multiple_choice_report():
    # Define the list of options
    options = [
        'binary_gas_connection_flow', 'connection_avg_intact_throughflow', 'connection_avg_throughflow', 
        'connection_flow', 'connection_flow_costs', 'connection_intact_flow', 'connection_investment_costs', 
        'connections_decommissioned', 'connections_invested', 'connections_invested_available', 
        'contingency_is_binding', 'fixed_om_costs', 'fuel_costs', 'mga_objective', 'mp_objective_lowerbound', 
        'node_injection', 'node_pressure', 'node_slack_neg', 'node_slack_pos', 'node_state','node_voltage_angle', 
        'nonspin_units_shut_down', 'nonspin_units_started_up', 'objective_penalties', 'relative_optimality_gap', 
        'renewable_curtailment_costs', 'res_proc_costs', 'shut_down_costs', 'start_up_costs', 
        'storage_investment_costs', 'storages_decommissioned', 'storages_invested','storages_invested_available', 
        'taxes', 'total_costs', 'unit_flow', 'unit_flow_op', 'unit_flow_op_active', 'unit_investment_costs', 
        'units_invested', 'units_invested_available', 'units_mothballed', 'units_on', 'units_on_costs', 
        'units_shut_down', 'units_started_up', 'variable_om_costs'
    ]
    
    # Define preselected options
    preselected_options = {
        'connection_flow', 'node_slack_pos', 'node_slack_neg', 'node_state', 'total_costs', 
        'unit_flow', 'unit_flow_op', 
        'connection_investment_costs', 'connections_invested',
        'storage_investment_costs', 'storages_invested',
        'unit_investment_costs', 'units_invested'
    }
    
    # Initialize selected_options_report with preselected options
    selected_options_report = set(preselected_options)
    
    # Separate options into preselected and non-preselected
    preselected_checks = [option for option in options if option in preselected_options]
    non_preselected_checks = [option for option in options if option not in preselected_options]
    
    checkboxes = []
    
    # Create checkboxes for preselected options first
    for option in preselected_checks:
        checkbox = widgets.Checkbox(
            value=True,  # All preselected options should be checked
            description=option,
            indent=False
        )
        checkbox.observe(lambda change, 
                         checkbox=checkbox: on_change_MC_report(change, selected_options_report, checkbox),
                         names='value'
                        )
        checkboxes.append(checkbox)
    
    # Create checkboxes for non-preselected options
    for option in non_preselected_checks:
        checkbox = widgets.Checkbox(
            value=False,  # Non-preselected options should be unchecked
            description=option,
            indent=False
        )
        checkbox.observe(lambda change, 
                         checkbox=checkbox: on_change_MC(change, selected_options_report, checkbox),
                         names='value'
                        )
        checkboxes.append(checkbox)
    
    # Create 3 columns
    columns = [widgets.VBox([]), widgets.VBox([]), widgets.VBox([])]
    for i, checkbox in enumerate(checkboxes):
        columns[i % 3].children += (checkbox,)
    hbox_report = widgets.HBox(columns, layout = widgets.Layout(overflow = 'hidden',
                                                                justify_content = 'flex-start'))
    
    label2 = widgets.Label("Please select the outputs for the report:")
    
    return widgets.VBox([label2, hbox_report], layout=get_general_vbox_layout()), selected_options_report



'''Define functions for the combined data definition menu'''

def create_combined_dropdowns_tabs():
    # Provide information for each section
    section_1 = widgets.HTML("<b>Section 1: Define the base parameters. If not specified, default values will be applied.</b>")
    section_2 = widgets.HTML("<b>Section 2: Define the energy sources. If not specified, default values will be applied.</b>")
    section_3 = widgets.HTML("<b>Section 3: Define the parameters of the general model. If not specified, default values will be applied.</b>")
    section_4 = widgets.HTML("<b>Section 4: Define the parameters of electrolysis. If not specified, default values will be applied.</b>")
    section_5 = widgets.HTML("<b>Section 5: Define the economic parameters of the general model. If not specified, default values will be applied.</b>")
    section_6 = widgets.HTML("<b>Section 6: Define the parameters for additional investments. If not specified, default values will be applied.</b>")
    
    # Get the dropdown menus
    dropdown_year_vbox, dropdown_year = create_dropdown_year()
    number_starting_year_box, number_starting_year = create_input_with_label(
        key='lcoe_starting_year', 
        description='Set the starting year for the LCOE calculation:', 
        placeholder='2020')
    dropdown_price_zone_vbox, dropdown_price_zone = create_dropdown_price_zone()
    dropdown_product_vbox, dropdown_product = create_dropdown_product()
    dropdown_electrolysis_vbox, dropdown_electrolysis = create_dropdown_electrolysis()
    dropdown_temp_box_vbox, dropdown_temp_block = create_dropdown_temp_block()
    number_wacc_box, number_wacc = create_input_with_label(
        key='wacc', 
        description='Set the WACC for the LCOE calculation:', 
        placeholder='0.08')
    lcoe_years_box, lcoe_years = create_input_with_label(
        key='lcoe_years', 
        description='Set the number of years for the LCOE calculation:', 
        placeholder='25')
    number_dh_price_box, number_dh_price = create_input_with_label(
        key='dh_price', 
        description='Set the assumed value for revenues from district heating as share of a max price:', 
        placeholder='0.5')
    number_price_level_power_box, number_price_level_power = create_input_with_label(
        key='power_price_scale', 
        description='Set the assumed value for scaling the power price level up/down:', 
        placeholder='1')
    power_price_variance_box, power_price_variance = create_input_with_label(
        key='power_price_var', 
        description='Set the assumed variance of the power prices:', 
        placeholder='1')
    run_name_box, run_name = create_text_with_label(
        key='run_name', 
        description='Please choose the name of this run:', 
        placeholder='base')
    multiple_choice_report_box, selected_reports = create_multiple_choice_report()
    multiple_choice_power_box, selected_powers, capacities_powers, investment_res, investment_ps, investment_ps_capacity = create_multiple_choice_power()
    dropdown_roll_vbox, dropdown_roll = create_dropdown_roll()
    number_slices_vbox, number_slices = create_input_with_label(
        key='opt_horizons', 
        description='Set the number of optimization horizons for the model:',
        placeholder='12')
    levels_elec_box, levels_elec = create_input_with_label(
        key='levels_elec', 
        description='Set the number of operating sections to represent variable efficiency:',
        placeholder='3')
    dropdown_investment_vbox, dropdown_investment = create_dropdown_investment()
    dropdown_period_vbox, dropdown_number, dropdown_period = create_dropdown_invest_period()
    demand_hbox, demand_input, demand_res = create_demand()
    
    # Store dropdowns in a dictionary
    dropdowns = {
        'year': dropdown_year,
        'starting_year': number_starting_year,
        'price_zone': dropdown_price_zone,
        'product': dropdown_product,
        'powers': selected_powers,
        'capacities_powers': capacities_powers,
        'electrolysis': dropdown_electrolysis,
        #'frequency': dropdown_frequency,
        'temporal_block': dropdown_temp_block,
        'number_wacc': number_wacc,
        'lcoe_years': lcoe_years,
        'number_dh_price_share': number_dh_price,
        'number_price_level_power': number_price_level_power,
        'power_price_variance': power_price_variance,
        'run_name': run_name,
        'reports': selected_reports,
        'roll_forward': dropdown_roll,
        'number_slices': number_slices,
        'levels_elec': levels_elec,
        'candidate_nonzero': dropdown_investment,
        'default_investment_number': dropdown_number,
        'default_investment_period': dropdown_period,
        'demand': demand_input,
        'demand_res': demand_res,
        'investment_res': investment_res,
        'investment_ps': investment_ps,
        'investment_ps_capacity': investment_ps_capacity
    }

    # Create pages (tabs)
    page1 = widgets.VBox([
        section_1, dropdown_product_vbox, demand_hbox
    ])

    page2 = widgets.VBox([
        section_2, multiple_choice_power_box, dropdown_year_vbox, dropdown_price_zone_vbox
    ])
    
    page3 = widgets.VBox([
        section_3, run_name_box, dropdown_temp_box_vbox, dropdown_roll_vbox, number_slices_vbox
    ])
    
    page4 = widgets.VBox([
        section_4, dropdown_electrolysis_vbox, levels_elec_box
    ])
    
    page5 = widgets.VBox([
        section_5, number_wacc_box, number_starting_year_box, lcoe_years_box, number_dh_price_box, number_price_level_power_box, power_price_variance_box
    ])
    
    page6 = widgets.VBox([
        section_6, capacities_vbox, dropdown_investment_vbox, dropdown_period_vbox, investment_cost_vbox
    ])

    # Create Tab widget
    tabs = widgets.Tab()
    
    tabs.children = [page1]
    tabs.set_title(0, 'Plant')
    def add_tabs_on_product_selection(change):
        if change['new'] is not None:
            # Only add tabs if they're not already added
            if len(tabs.children) == 1:
                # Add pages to tabs
                tabs.children = [page1, page2, page3, page4, page5, page6]
                tabs.set_title(1, 'Energy Sources')
                tabs.set_title(2, 'Model Base')
                tabs.set_title(3, 'Electrolysis')
                tabs.set_title(4, 'Economic')
                tabs.set_title(5, 'Investment')
    dropdown_product.observe(add_tabs_on_product_selection, names='value')

    # Function to show/hide demand based on product value
    def show_demand(change):
        if change['new']:
            demand_hbox.layout.display = 'block'
        else:
            demand_hbox.layout.display = 'none'
    # Hide demand by default
    demand_hbox.layout.display = 'none'
    # Observe changes in product
    dropdown_product.observe(show_demand, names='value')
    
    # Function to show/hide number_slices based on dropdown_roll value
    def toggle_number_slices(change):
        if change['new']:
            number_slices_vbox.layout.display = 'block'
        else:
            number_slices_vbox.layout.display = 'none'
    # Hide number_slices by default
    number_slices_vbox.layout.display = 'none'
    # Observe changes in dropdown_roll
    dropdown_roll.observe(toggle_number_slices, names='value')

    
    # Function to show/hide investment period and costs based on investment value
    def toggle_investment_period(change):
        if change['new']:
            dropdown_period_vbox.layout.display = 'block'
            investment_cost_vbox.layout.display = 'block'
        else:
            dropdown_period_vbox.layout.display = 'none'
            investment_cost_vbox.layout.display = 'none'
    # Hide investment period and costs by default
    dropdown_period_vbox.layout.display = 'none'
    investment_cost_vbox.layout.display = 'none'
    # Observe changes in dropdown_investment
    dropdown_investment.observe(toggle_investment_period, names='value')
   
    display(tabs)
    
    return tabs, dropdowns


#create a function to access the values in combined function
def get_dropdown_values(dropdowns):
    values = {
        'year': dropdowns['year'].value,
        'starting_year': dropdowns['starting_year'].value,
        'price_zone': dropdowns['price_zone'].value,
        'product': dropdowns['product'].value,
        'demand': dropdowns['demand'].value,
        'demand_res': dropdowns['demand_res'].value,
        'electrolysis': dropdowns['electrolysis'].value,
        'temporal_block': dropdowns['temporal_block'].value,
        'roll_forward': dropdowns['roll_forward'].value,
        'candidate_nonzero': dropdowns['candidate_nonzero'].value,
        'default_investment_number': dropdowns['default_investment_number'].value,
        'default_investment_period': dropdowns['default_investment_period'].value,
        'investment_res': dropdowns['investment_res'].value,
        'investment_ps': dropdowns['investment_ps'].value,
        'investment_ps_capacity': dropdowns['investment_ps_capacity'].value,
        
        # Numerical values (percent) adjusted
        'capacities_powers': dropdowns['capacities_powers'],
        'wacc': dropdowns['number_wacc'].value,
        'lcoe_years': dropdowns['lcoe_years'].value,
        'share_of_dh_price_cap': dropdowns['number_dh_price_share'].value,
        'number_price_level_power': dropdowns['number_price_level_power'].value,
        'power_price_variance': dropdowns['power_price_variance'].value,
        'num_slices': dropdowns['number_slices'].value,
        'des_segments_electrolyzer': dropdowns['levels_elec'].value,
        
        # Other text fields
        'run_name': dropdowns['run_name'].value,
        
        # Multiple choice values
        'outputs': dropdowns['reports'],
        'powers': dropdowns['powers']
    }
    
    # Adding the dynamic investment cost values from investment_cost_values if changed
    placeholder_value = 1.0
    for key, widget in investment_cost_values.items():
        if widget.value == placeholder_value:
            values[key] = None
        else:
            values[key] = widget.value

    # Adding the investment limit values from investment_limit_values if changed
    placeholder_value = 1.0
    for key, widget in investment_limit_values.items():
        if widget.value == placeholder_value:
            values[key] = None
        else:
            values[key] = widget.value

    # Adding the dynamic capacities values if changed
    for key, widget in capacities_values.items():
        if widget.value == placeholder_value:
            values[key] = None
        else:
            values[key] = widget.value
    
    return values


# Add investment costs and capacities to the parameters definition if previously set
def set_inv_cap_values(values, parameters):
    # investment costs
    if 'inv_cost_ammonia_storage' in values:
        parameters['inv_cost_ammonia_storage'] = values['inv_cost_ammonia_storage']
    if 'inv_cost_anaerobic' in values:
        parameters['inv_cost_anaerobic'] = values['inv_cost_anaerobic']
    if 'inv_cost_asu' in values:
        parameters['inv_cost_asu'] = values['inv_cost_asu']
    if 'inv_cost_biomethanation' in values:
        parameters['inv_cost_biomethanation'] = values['inv_cost_biomethanation']
    if 'inv_cost_co2_removal' in values:
        parameters['inv_cost_co2_removal'] = values['inv_cost_co2_removal']
    if 'inv_cost_diesel_storage' in values:
        parameters['inv_cost_diesel_storage'] = values['inv_cost_diesel_storage']
    if 'inv_cost_egasoline_storage' in values:
        parameters['inv_cost_egasoline_storage'] = values['inv_cost_egasoline_storage']
    if 'inv_cost_electrolyzer' in values:
        parameters['inv_cost_electrolyzer'] = values['inv_cost_electrolyzer']
    if 'inv_cost_fischer' in values:
        parameters['inv_cost_fischer'] = values['inv_cost_fischer'] 
    if 'inv_cost_haber' in values:
        parameters['inv_cost_haber'] = values['inv_cost_haber'] 
    if 'inv_cost_hydrogen_storage' in values:
        parameters['inv_cost_hydrogen_storage'] = values['inv_cost_hydrogen_storage']
    if 'inv_cost_jet_fuel_storage' in values:
        parameters['inv_cost_jet_fuel_storage'] = values['inv_cost_jet_fuel_storage']    
    if 'inv_cost_methane_storage' in values:
        parameters['inv_cost_methane_storage'] = values['inv_cost_methane_storage']
    if 'inv_cost_methanol' in values:
        parameters['inv_cost_methanol'] = values['inv_cost_methanol']
    if 'inv_cost_methanol_storage' in values:
        parameters['inv_cost_methanol_storage'] = values['inv_cost_methanol_storage']
    if 'inv_cost_rwgs' in values:
        parameters['inv_cost_rwgs'] = values['inv_cost_rwgs']
    if 'inv_cost_steam' in values:
        parameters['inv_cost_steam'] = values['inv_cost_steam']
    # capacities
    if 'capacity_asu' in values:
        parameters['capacity_asu'] = values['capacity_asu']
    if 'capacity_electrolyzer' in values:
        parameters['capacity_electrolyzer'] = values['capacity_electrolyzer']
    if 'capacity_haber' in values:
        parameters['capacity_haber'] = values['capacity_haber']
    if 'capacity_fischer' in values:
        parameters['capacity_fischer'] = values['capacity_fischer']
    if 'capacity_rwgs' in values:
        parameters['capacity_rwgs'] = values['capacity_rwgs']
    if 'capacity_methanol' in values:
        parameters['capacity_methanol'] = values['capacity_methanol']
        parameters['capacity_distillation'] = values['capacity_methanol']
    if 'capacity_steam' in values:
        parameters['capacity_steam'] = values['capacity_steam']
    if 'capacity_anaerobic' in values:
        parameters['capacity_anaerobic'] = values['capacity_anaerobic']
    if 'capacity_biomethanation' in values:
        parameters['capacity_biomethanation'] = values['capacity_biomethanation']
    if 'capacity_co2_removal' in values:
        parameters['capacity_co2_removal'] = values['capacity_co2_removal']
    # limits
    if 'inv_limit_ammonia_storage' in values:
        parameters['inv_limit_ammonia_storage'] = values['inv_limit_ammonia_storage']
    if 'inv_limit_anaerobic' in values:
        parameters['inv_limit_anaerobic'] = values['inv_limit_anaerobic']
    if 'inv_limit_asu' in values:
        parameters['inv_limit_asu'] = values['inv_limit_asu']
    if 'inv_limit_biomethanation' in values:
        parameters['inv_limit_biomethanation'] = values['inv_limit_biomethanation']
    if 'inv_limit_co2_removal' in values:
        parameters['inv_limit_co2_removal'] = values['inv_limit_co2_removal']
    if 'inv_limit_diesel_storage' in values:
        parameters['inv_limit_diesel_storage'] = values['inv_limit_diesel_storage']
    if 'inv_limit_egasoline_storage' in values:
        parameters['inv_limit_egasoline_storage'] = values['inv_limit_egasoline_storage']
    if 'inv_limit_electrolyzer' in values:
        parameters['inv_limit_electrolyzer'] = values['inv_limit_electrolyzer']
    if 'inv_limit_fischer' in values:
        parameters['inv_limit_fischer'] = values['inv_limit_fischer'] 
    if 'inv_limit_haber' in values:
        parameters['inv_limit_haber'] = values['inv_limit_haber'] 
    if 'inv_limit_hydrogen_storage' in values:
        parameters['inv_limit_hydrogen_storage'] = values['inv_limit_hydrogen_storage']
    if 'inv_limit_jet_fuel_storage' in values:
        parameters['inv_limit_jet_fuel_storage'] = values['inv_limit_jet_fuel_storage']    
    if 'inv_limit_methane_storage' in values:
        parameters['inv_limit_methane_storage'] = values['inv_limit_methane_storage']
    if 'inv_limit_methanol' in values:
        parameters['inv_limit_methanol'] = values['inv_limit_methanol']
        parameters['inv_limit_distillation'] = values['inv_limit_methanol']
    if 'inv_limit_methanol_storage' in values:
        parameters['inv_limit_methanol_storage'] = values['inv_limit_methanol_storage']
    if 'inv_limit_rwgs' in values:
        parameters['inv_limit_rwgs'] = values['inv_limit_rwgs']
    if 'inv_limit_steam' in values:
        parameters['inv_limit_steam'] = values['inv_limit_steam']
    
    return parameters
    
