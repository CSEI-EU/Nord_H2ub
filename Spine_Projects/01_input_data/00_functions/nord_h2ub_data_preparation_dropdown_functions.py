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
SPDX-FileCopyrightText: Kacper Rokosz <kar.eco@cbs.dk>
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

def update_inv_costs(change, investment_cost_vbox):
    # Get selected product from the dropdown (ammonia, diesel, egasoline, hydrogen, jet_fuel, methanol, and synthetic_methane_gas)
    selected_product = change['new']
    
    # Clear existing investment widgets (if any)
    investment_cost_vbox.children = []
    
    # Clear the investment_cost_values dictionary before updating
    investment_cost_values.clear()
    investment_limit_values.clear()
    
    # Define a layout for descriptions and fields + indent
    description_layout = widgets.Layout(width='210px')
    input_layout = widgets.Layout(width='100px')

    # Headline for the investment costs block
    investment_headline = widgets.Label("Please define the investment cost and maximal installed capacities per MW or MWh. If left empty, default values will be used.",
    style={'font_weight': 'bold', 'font_size': '13px'})
    
    # Assign to products
    if selected_product == 'ammonia':
        
        ammonia_storage_label = widgets.Label("Ammonia storage:")
        ammonia_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        ammonia_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        ammonia_hbox = widgets.HBox([ammonia_storage_description, ammonia_storage_input], layout=inv_cap_indent_layout)
        
        ammonia_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        ammonia_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        ammonia_storage_limit_hbox = widgets.HBox([ammonia_storage_limit_description, ammonia_storage_limit], layout=inv_cap_indent_layout)
        
        asu_label = widgets.Label("Air separation unit")
        asu_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        asu_input = widgets.FloatText(value=placeholder_value, min=0,layout=input_layout)
        asu_hbox = widgets.HBox([asu_description, asu_input], layout=inv_cap_indent_layout)
        
        asu_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        asu_limit_input = widgets.FloatText(value=placeholder_value, min=0,layout=input_layout)
        asu_limit_hbox = widgets.HBox([asu_limit_description, asu_limit_input], layout=inv_cap_indent_layout)
        
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=inv_cap_indent_layout)
        
        haber_label = widgets.Label("Haber-Bosch unit:")
        haber_description = widgets.Label("Costs [€/MW ammonia output]:", layout=description_layout)
        haber_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        haber_hbox = widgets.HBox([haber_description, haber_input], layout=inv_cap_indent_layout)

        haber_limit_description = widgets.Label("Capacity limit [MW ammonia output]:", layout=description_layout)
        haber_limit_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        haber_limit_hbox = widgets.HBox([haber_limit_description, haber_limit_input], layout=inv_cap_indent_layout)

        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=inv_cap_indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=inv_cap_indent_layout)
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_ammonia_storage'] = ammonia_storage_input
        investment_cost_values['inv_cost_asu'] = asu_input
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_haber'] = haber_input
        investment_cost_values['inv_cost_hydrogen_storage'] = hydrogen_storage_input

        investment_limit_values['inv_limit_ammonia_storage'] = ammonia_storage_limit
        investment_limit_values['inv_limit_asu'] = asu_limit_input
        investment_limit_values['inv_limit_electrolyzer'] = electrolyzer_limit
        investment_limit_values['inv_limit_fischer'] = haber_limit_input
        investment_limit_values['inv_limit_hydrogen_storage'] = hydrogen_storage_limit

        investment_cost_vbox.children = [investment_headline,
                                         ammonia_storage_label, ammonia_hbox, ammonia_storage_limit_hbox,
                                         asu_label, asu_hbox, asu_limit_hbox, 
                                         electrolyzer_label, electrolyzer_hbox, electrolyzer_limit_hbox,
                                         haber_label, haber_hbox, haber_limit_hbox,
                                         hydrogen_storage_label, hydrogen_storage_hbox, hydrogen_storage_limit_hbox
                                        ]
    
    elif selected_product == 'diesel':

        diesel_storage_label = widgets.Label("Diesel storage:")
        diesel_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        diesel_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        diesel_storage_hbox = widgets.HBox([diesel_storage_description, diesel_storage_input], layout=inv_cap_indent_layout)
        
        diesel_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        diesel_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        diesel_storage_limit_hbox = widgets.HBox([diesel_storage_limit_description, diesel_storage_limit], layout=inv_cap_indent_layout)

        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=inv_cap_indent_layout)

        fischer_label = widgets.Label("Fischer-Tropsch Reactor:")
        fischer_description = widgets.Label("Costs [€/MW fuels output]:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=inv_cap_indent_layout)

        fischer_limit_description = widgets.Label("Capacity limit [MW fuels output]:", layout=description_layout)
        fischer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_limit_hbox = widgets.HBox([fischer_limit_description, fischer_limit], layout=inv_cap_indent_layout)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=inv_cap_indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=inv_cap_indent_layout)
        
        rwgs_label = widgets.Label("RWGS reactor:")
        rwgs_description = widgets.Label("Costs [€/MWh fuels output]:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=inv_cap_indent_layout)
        
        rwgs_limit_description = widgets.Label("Capacity limit [MW fuels output]:", layout=description_layout)
        rwgs_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_limit_hbox = widgets.HBox([rwgs_limit_description, rwgs_limit], layout=inv_cap_indent_layout)
        
        steam_label = widgets.Label("Steam plant:")
        steam_description = widgets.Label("Costs [€/MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=inv_cap_indent_layout)
        
        steam_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        steam_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_limit_hbox = widgets.HBox([steam_limit_description, steam_limit], layout=inv_cap_indent_layout)
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_diesel_storage'] = diesel_storage_input
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_fischer'] = fischer_input
        investment_cost_values['inv_cost_hydrogen_storage'] = hydrogen_storage_input
        investment_cost_values['inv_cost_rwgs'] = rwgs_input
        investment_cost_values['inv_cost_steam'] = steam_input

        investment_limit_values['inv_limit_diesel_storage'] = diesel_storage_limit
        investment_limit_values['inv_limit_electrolyzer'] = electrolyzer_limit
        investment_limit_values['inv_limit_fischer'] = fischer_limit
        investment_limit_values['inv_limit_hydrogen_storage'] = hydrogen_storage_limit
        investment_limit_values['inv_limit_rwgs'] = rwgs_limit
        investment_limit_values['inv_limit_steam'] = steam_limit
        
        investment_cost_vbox.children = [investment_headline,
                                         diesel_storage_label, diesel_storage_hbox, diesel_storage_limit_hbox,
                                         electrolyzer_label, electrolyzer_hbox, electrolyzer_limit_hbox,
                                         fischer_label, fischer_hbox, fischer_limit_hbox, 
                                         hydrogen_storage_label, hydrogen_storage_hbox, hydrogen_storage_limit_hbox,
                                         rwgs_label, rwgs_hbox, rwgs_limit_hbox,
                                         steam_label, steam_hbox, steam_limit_hbox
                                        ]
        
    elif selected_product == 'egasoline':
        
        egasoline_storage_label = widgets.Label("E-Gasoline storage:")
        egasoline_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        egasoline_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        egasoline_storage_hbox = widgets.HBox([egasoline_storage_description, egasoline_storage_input], layout=inv_cap_indent_layout)
        
        egasoline_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        egasoline_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        egasoline_storage_limit_hbox = widgets.HBox([egasoline_storage_limit_description, egasoline_storage_limit], layout=inv_cap_indent_layout)

        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=inv_cap_indent_layout)

        fischer_label = widgets.Label("Fischer-Tropsch Reactor:")
        fischer_description = widgets.Label("Costs [€/MW fuels output]:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=inv_cap_indent_layout)

        fischer_limit_description = widgets.Label("Capacity limit [MW fuels output]:", layout=description_layout)
        fischer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_limit_hbox = widgets.HBox([fischer_limit_description, fischer_limit], layout=inv_cap_indent_layout)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=inv_cap_indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=inv_cap_indent_layout)
        
        rwgs_label = widgets.Label("RWGS reactor:")
        rwgs_description = widgets.Label("Costs [€/MWh fuels output]:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=inv_cap_indent_layout)
        
        rwgs_limit_description = widgets.Label("Capacity limit [MW fuels output]:", layout=description_layout)
        rwgs_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_limit_hbox = widgets.HBox([rwgs_limit_description, rwgs_limit], layout=inv_cap_indent_layout)
        
        steam_label = widgets.Label("Steam plant:")
        steam_description = widgets.Label("Costs [€/MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=inv_cap_indent_layout)
        
        steam_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        steam_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_limit_hbox = widgets.HBox([steam_limit_description, steam_limit], layout=inv_cap_indent_layout)
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_egasoline_storage'] = egasoline_storage_input
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_fischer'] = fischer_input
        investment_cost_values['inv_cost_hydrogen_storage'] = hydrogen_storage_input
        investment_cost_values['inv_cost_rwgs'] = rwgs_input
        investment_cost_values['inv_cost_steam'] = steam_input

        investment_limit_values['inv_limit_egasoline_storage'] = egasoline_storage_limit
        investment_limit_values['inv_limit_electrolyzer'] = electrolyzer_limit
        investment_limit_values['inv_limit_fischer'] = fischer_limit
        investment_limit_values['inv_limit_hydrogen_storage'] = hydrogen_storage_limit
        investment_limit_values['inv_limit_rwgs'] = rwgs_limit
        investment_limit_values['inv_limit_steam'] = steam_limit
        
        investment_cost_vbox.children = [investment_headline,
                                         egasoline_storage_label, egasoline_storage_hbox, egasoline_storage_limit_hbox,
                                         electrolyzer_label, electrolyzer_hbox, electrolyzer_limit_hbox,
                                         fischer_label, fischer_hbox, fischer_limit_hbox, 
                                         hydrogen_storage_label, hydrogen_storage_hbox, hydrogen_storage_limit_hbox,
                                         rwgs_label, rwgs_hbox, rwgs_limit_hbox,
                                         steam_label, steam_hbox, steam_limit_hbox
                                        ]
    
    elif selected_product == 'hydrogen':
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=inv_cap_indent_layout)

        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=inv_cap_indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=inv_cap_indent_layout)
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_hydrogen_storage'] = hydrogen_storage_input
        
        investment_cost_vbox.children = [investment_headline,
                                         electrolyzer_label, electrolyzer_hbox, electrolyzer_limit_hbox,
                                         hydrogen_storage_label, hydrogen_storage_hbox, hydrogen_storage_limit_hbox
                                        ]

    elif selected_product == 'jet_fuel':
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=inv_cap_indent_layout)

        fischer_label = widgets.Label("Fischer-Tropsch Reactor:")
        fischer_description = widgets.Label("Costs [€/MW fuels output]:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=inv_cap_indent_layout)
        
        fischer_limit_description = widgets.Label("Capacity limit [MW fuels output]:", layout=description_layout)
        fischer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_limit_hbox = widgets.HBox([fischer_limit_description, fischer_limit], layout=inv_cap_indent_layout)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=inv_cap_indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=inv_cap_indent_layout)

        jet_fuel_storage_label = widgets.Label("Jet Fuel storage:")
        jet_fuel_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        jet_fuel_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        jet_fuel_storage_hbox = widgets.HBox([jet_fuel_storage_description, jet_fuel_storage_input], layout=inv_cap_indent_layout)
        
        jet_fuel_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        jet_fuel_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        jet_fuel_storage_limit_hbox = widgets.HBox([jet_fuel_storage_limit_description, jet_fuel_storage_limit], layout=inv_cap_indent_layout)
        
        rwgs_label = widgets.Label("RWGS reactor:")
        rwgs_description = widgets.Label("Costs [€/MWh fuels output]:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=inv_cap_indent_layout)
        
        rwgs_limit_description = widgets.Label("Capacity limit [MW fuels output]:", layout=description_layout)
        rwgs_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_limit_hbox = widgets.HBox([rwgs_limit_description, rwgs_limit], layout=inv_cap_indent_layout)
        
        steam_label = widgets.Label("Steam plant:")
        steam_description = widgets.Label("Costs [€/MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=inv_cap_indent_layout)
        
        steam_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        steam_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_limit_hbox = widgets.HBox([steam_limit_description, steam_limit], layout=inv_cap_indent_layout)
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_jet_fuel_storage'] = jet_fuel_storage_input
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_hydrogen_storage'] = hydrogen_storage_input
        investment_cost_values['inv_cost_fischer'] = fischer_input
        investment_cost_values['inv_cost_rwgs'] = rwgs_input
        investment_cost_values['inv_cost_steam'] = steam_input
        
        investment_limit_values['inv_limit_jet_fuel_storage'] = jet_fuel_storage_limit
        investment_limit_values['inv_limit_electrolyzer'] = electrolyzer_limit
        investment_limit_values['inv_limit_hydrogen_storage'] = hydrogen_storage_limit
        investment_limit_values['inv_limit_fischer'] = fischer_limit
        investment_limit_values['inv_limit_rwgs'] = rwgs_limit
        investment_limit_values['inv_limit_steam'] = steam_limit
        
        investment_cost_vbox.children = [investment_headline,
                                         electrolyzer_label, electrolyzer_hbox, electrolyzer_limit_hbox,
                                         fischer_label, fischer_hbox, fischer_limit_hbox, 
                                         hydrogen_storage_label, hydrogen_storage_hbox, hydrogen_storage_limit_hbox,
                                         jet_fuel_storage_label, jet_fuel_storage_hbox, jet_fuel_storage_limit_hbox,
                                         rwgs_label, rwgs_hbox, rwgs_limit_hbox,
                                         steam_label, steam_hbox, steam_limit_hbox
                                        ]
    
    elif selected_product == 'methanol':
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=inv_cap_indent_layout)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=inv_cap_indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=inv_cap_indent_layout)
        
        methanol_label = widgets.Label("Methanol reactor:")
        methanol_description = widgets.Label("Costs [€/MW output methanol]:", layout=description_layout)
        methanol_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methanol_hbox = widgets.HBox([methanol_description, methanol_input], layout=inv_cap_indent_layout)
        
        methanol_limit_description = widgets.Label("Capacity limit [MW output methanol]:", layout=widgets.Layout(width='210px'))
        methanol_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methanol_limit_hbox = widgets.HBox([methanol_limit_description, methanol_limit], layout=inv_cap_indent_layout)
        
        methanol_storage_label = widgets.Label("Methanol storage:")
        methanol_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        methanol_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methanol_storage_hbox = widgets.HBox([methanol_storage_description, methanol_storage_input], layout=inv_cap_indent_layout)
        
        methanol_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        methanol_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methanol_storage_limit_hbox = widgets.HBox([methanol_storage_limit_description, methanol_storage_limit], layout=inv_cap_indent_layout)

        steam_label = widgets.Label("Steam plant:")
        steam_description = widgets.Label("Costs [€/MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=inv_cap_indent_layout)
        
        steam_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        steam_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_limit_hbox = widgets.HBox([steam_limit_description, steam_limit], layout=inv_cap_indent_layout)
                
        # Store values in investment dictionary
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_hydrogen_storage'] = hydrogen_storage_input
        investment_cost_values['inv_cost_methanol'] = methanol_input
        investment_cost_values['inv_cost_methanol_storage'] = methanol_storage_input
        investment_cost_values['inv_cost_steam'] = steam_input

        investment_limit_values['inv_limit_electrolyzer'] = electrolyzer_limit
        investment_limit_values['inv_limit_hydrogen_storage'] = hydrogen_storage_limit
        investment_limit_values['inv_limit_methanol'] = methanol_limit
        investment_limit_values['inv_limit_methanol_storage'] = methanol_storage_limit
        investment_limit_values['inv_limit_steam'] = steam_limit

        
        investment_cost_vbox.children = [investment_headline,
                                         electrolyzer_label, electrolyzer_hbox, electrolyzer_limit_hbox,
                                         hydrogen_storage_label, hydrogen_storage_hbox, hydrogen_storage_limit_hbox,
                                         methanol_label, methanol_hbox, methanol_limit_hbox,
                                         methanol_storage_label, methanol_storage_hbox, methanol_storage_limit_hbox,
                                         steam_label, steam_hbox, steam_limit_hbox
                                        ]
    
    elif selected_product == 'methane':
        
        anaerobic_label = widgets.Label("Anaerobic digestion plant:")
        anaerobic_description = widgets.Label("Costs [€/MW TBA]:", layout=description_layout)
        anaerobic_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        anaerobic_hbox = widgets.HBox([anaerobic_description, anaerobic_input], layout=inv_cap_indent_layout)

        anaerobic_limit_description = widgets.Label("Capacity limit [MW TBA]:", layout=description_layout)
        anaerobic_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        anaerobic_limit_hbox = widgets.HBox([anaerobic_limit_description, anaerobic_limit], layout=inv_cap_indent_layout)
        
        biomethanation_label = widgets.Label("Biomethanation plant:")
        biomethanation_description = widgets.Label("Costs [€/MW TBA]:", layout=description_layout)
        biomethanation_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        biomethanation_hbox = widgets.HBox([biomethanation_description, biomethanation_input], layout=inv_cap_indent_layout)

        biomethanation_limit_description = widgets.Label("Capacity limit [MW TBA]:", layout=description_layout)
        biomethanation_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        biomethanation_limit_hbox = widgets.HBox([biomethanation_limit_description, biomethanation_limit], layout=inv_cap_indent_layout)
        
        co2_remover_label = widgets.Label("CO2 removal plant:")
        co2_remover_description = widgets.Label("Costs [€/MW TBA]:", layout=description_layout)
        co2_remover_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        co2_remover_hbox = widgets.HBox([co2_remover_description, co2_remover_input], layout=inv_cap_indent_layout)

        co2_remover_limit_description = widgets.Label("Capacity limit [MW TBA]:", layout=description_layout)
        co2_remover_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        co2_remover_limit_hbox = widgets.HBox([co2_remover_limit_description, co2_remover_limit], layout=inv_cap_indent_layout)

        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=inv_cap_indent_layout)

        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=inv_cap_indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=inv_cap_indent_layout)
        
        methane_storage_label = widgets.Label("Methane storage:")
        methane_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        methane_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methane_storage_hbox = widgets.HBox([methane_storage_description, methane_storage_input], layout=inv_cap_indent_layout)
        
        methane_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        methane_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methane_storage_limit_hbox = widgets.HBox([methane_storage_limit_description, methane_storage_limit], layout=inv_cap_indent_layout)

        steam_label = widgets.Label("Steam plant:")
        steam_description = widgets.Label("Costs [€/MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=inv_cap_indent_layout)
        
        steam_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        steam_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_limit_hbox = widgets.HBox([steam_limit_description, steam_limit], layout=inv_cap_indent_layout)
                        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_anaerobic'] = anaerobic_input
        investment_cost_values['inv_cost_biomethanation'] = biomethanation_input
        investment_cost_values['inv_cost_co2_removal'] = co2_remover_input
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_methane_storage'] = methane_storage_input

        investment_limit_values['inv_limit_electrolyzer'] = electrolyzer_limit
        investment_limit_values['inv_limit_hydrogen_storage'] = hydrogen_storage_limit
        investment_limit_values['inv_limit_methane_storage'] = methane_storage_limit
        investment_limit_values['inv_limit_steam'] = steam_limit
        
        investment_cost_vbox.children = [investment_headline, 
                                         anaerobic_label, anaerobic_hbox, anaerobic_limit_hbox,
                                         biomethanation_label, biomethanation_hbox, biomethanation_limit_hbox,
                                         co2_remover_label, co2_remover_hbox, co2_remover_limit_hbox, 
                                         electrolyzer_label, electrolyzer_hbox, electrolyzer_limit_hbox,
                                         hydrogen_storage_label, hydrogen_storage_hbox, hydrogen_storage_limit_hbox,
                                         methane_storage_label, methane_storage_hbox, methane_storage_limit_hbox,
                                         steam_label, steam_hbox, steam_limit_hbox
                                        ]


# Set capacities of units depending on type of product
capacities_vbox = widgets.VBox(layout=widgets.Layout(margin='0 0 15px 0'))
capacities_values = {}

def update_capacities(change, capacities_vbox):
    # Get selected product from the dropdown (ammonia, diesel, egasoline, hydrogen, jet_fuel, methane, or methanol)
    selected_product = change['new']
    
    # Clear existing capacity widgets (if any)
    capacities_vbox.children = []
    
    # Clear the capacities_values dictionary before updating
    capacities_values.clear()
    
    # Define a layout for descriptions and fields + indent
    description_layout = widgets.Layout(width='245px')
    input_layout = widgets.Layout(width='110px')

    label = widgets.Label("Please set the existing capacity:")
    
    steam_description = widgets.Label("Existing capacity [MW input power]:", layout=description_layout)
    steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
    steam_hbox = widgets.HBox([steam_description, steam_input], layout=inv_cap_indent_layout)

    # Assign fields to products
    if selected_product == 'ammonia':
        asu_description = widgets.Label("Air separation unit [MW input power]:", layout=description_layout)
        asu_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        asu_hbox = widgets.HBox([asu_description, asu_input], layout=inv_cap_indent_layout)
        
        electrolyzer_description = widgets.Label("Electrolyzer [MW input power]:",
                                                 layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        haber_description = widgets.Label("Haber-Bosch unit [MW ammonia output]:", layout=description_layout)
        haber_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        haber_hbox = widgets.HBox([haber_description, haber_input], layout=inv_cap_indent_layout)
              
        # Store values in investment dictionary
        capacities_values['capacity_asu'] = asu_input
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_haber'] = haber_input
        
        capacities_vbox.children = [label, asu_hbox, electrolyzer_hbox, haber_hbox]
    
    elif selected_product == 'diesel':
        electrolyzer_description = widgets.Label("Electrolyzer [MW input power]:",
                                                 layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        fischer_description = widgets.Label("Fischer-Tropsch reactor [MW fuels output]:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=inv_cap_indent_layout)
        
        rwgs_description = widgets.Label("RWGS reactor [MW fuels output]:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=inv_cap_indent_layout)
        
        steam_description = widgets.Label("Steam plant [MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=inv_cap_indent_layout)
        
        # Store values in investment dictionary
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_fischer'] = fischer_input
        capacities_values['capacity_rwgs'] = rwgs_input
        capacities_values['capacity_steam'] = steam_input
        
        capacities_vbox.children = [label, electrolyzer_hbox, fischer_hbox, rwgs_hbox, steam_hbox]
    
    elif selected_product == 'egasoline':
        electrolyzer_description = widgets.Label("Electrolyzer [MW input power]:",
                                                 layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        fischer_description = widgets.Label("Fischer-Tropsch reactor [MW fuels output]:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=inv_cap_indent_layout)
        
        rwgs_description = widgets.Label("RWGS reactor [MW fuels output]:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=inv_cap_indent_layout)
        
        steam_description = widgets.Label("Steam plant [MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=inv_cap_indent_layout)
        
        # Store values in investment dictionary
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_fischer'] = fischer_input
        capacities_values['capacity_rwgs'] = rwgs_input
        capacities_values['capacity_steam'] = steam_input
        
        capacities_vbox.children = [label, electrolyzer_hbox, fischer_hbox, rwgs_hbox, steam_hbox]
    
    elif selected_product == 'hydrogen':
        electrolyzer_description = widgets.Label("Electrolyzer [MW input power]:",
                                                 layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        # Store values in investment dictionary
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        
        capacities_vbox.children = [label, electrolyzer_hbox]

    elif selected_product == 'jet_fuel':
        electrolyzer_description = widgets.Label("Electrolyzer [MW input power]:",
                                                 layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        fischer_description = widgets.Label("Fischer-Tropsch reactor [MW fuels output]:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=inv_cap_indent_layout)
        
        rwgs_description = widgets.Label("RWGS reactor [MW fuels output]:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=inv_cap_indent_layout)
        
        steam_description = widgets.Label("Steam plant [MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=inv_cap_indent_layout)
        
        # Store values in investment dictionary
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_fischer'] = fischer_input
        capacities_values['capacity_rwgs'] = rwgs_input
        capacities_values['capacity_steam'] = steam_input
        
        capacities_vbox.children = [label, electrolyzer_hbox, fischer_hbox, rwgs_hbox, steam_hbox]
    
    elif selected_product == 'methanol':
        electrolyzer_description = widgets.Label("Electrolyzer [MW input power]:",
                                                 layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)
        
        methanol_description = widgets.Label("Methanol reactor [MW output methanol]:",
                                             layout=description_layout)
        methanol_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methanol_hbox = widgets.HBox([methanol_description, methanol_input], layout=inv_cap_indent_layout)
        
        steam_description = widgets.Label("Steam plant [MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=inv_cap_indent_layout)
        
        # Store values in investment dictionary
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_methanol'] = methanol_input
        capacities_values['capacity_steam'] = steam_input
        
        capacities_vbox.children = [label, electrolyzer_hbox, methanol_hbox, steam_hbox]
    
    elif selected_product == 'methane':
        anaerobic_description = widgets.Label("Anaerobic digestion plant []:", layout=description_layout)
        anaerobic_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        anaerobic_hbox = widgets.HBox([anaerobic_description, anaerobic_input], layout=inv_cap_indent_layout)
        
        biomethanation_description = widgets.Label("Biomethanation plant []:", layout=description_layout)
        biomethanation_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        biomethanation_hbox = widgets.HBox([biomethanation_description, biomethanation_input], layout=inv_cap_indent_layout)
        
        co2_remover_description = widgets.Label("CO2 removal plant []:", layout=description_layout)
        co2_remover_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        co2_remover_hbox = widgets.HBox([co2_remover_description, co2_remover_input], layout=inv_cap_indent_layout)
        
        electrolyzer_description = widgets.Label("Electrolyzer [MW input power]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=inv_cap_indent_layout)

        steam_description = widgets.Label("Steam plant [MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=inv_cap_indent_layout)
        
        # Store values in investment dictionary
        capacities_values['capacity_anaerobic'] = anaerobic_input
        capacities_values['capacity_biomethanation'] = biomethanation_input
        capacities_values['capacity_co2_removal'] = co2_remover_input
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_steam'] = steam_input
        
        capacities_vbox.children = [label, anaerobic_hbox, biomethanation_hbox, co2_remover_hbox, electrolyzer_hbox, steam_hbox]


# Define demand
def create_demand():
    # Define a layout for descriptions and fields
    description_layout = widgets.Layout(width='140px')
    input_layout = widgets.Layout(width='85px')
    
    # Add fields
    demand_description = widgets.Label("Yearly demand [MWh]:", layout=description_layout)
    
    demand_input = widgets.Text(
        value = '', 
        placeholder = 'e.g. 30,000',
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
        time.sleep(delay)
        warning_label.value = ''
        checkbox.value = True
    
    # Separate options into preselected and non-preselected
    preselected_checks_power = [option for option in options_power if option in preselected_options_power]
    non_preselected_checks_power = [option for option in options_power if option not in preselected_options_power]
    
    # Initiate dictionary for the capacity of each option
    capacities_powers = {}
    capacities_powers_values = {}
    hbox_capacities_powers = []
    
    # Initialize PPA-related dictionaries
    ppa_containers = {}
    ppa_values = {}
    ppa_details_containers = {}
    ppa_capacity_values = {}
    ppa_price_values = {}
    ppa_type_values = {}  # <-- new
    
    # Function to update the capacity fields visibility
    def update_capacity_fields(selected_list, capacities_list):
        for option, hbox in capacities_list.items():
            if option in selected_list:
                hbox.layout.display = 'flex'
            else:
                hbox.layout.display = 'none'
    
    # Function to update PPA section visibility
    def update_ppa_visibility(selected_list):
        for option, container in ppa_containers.items():
            if option in selected_list:
                container.layout.display = 'flex'
            else:
                container.layout.display = 'none'
    
    # Function to update the capacities_powers_values when changed
    def on_capacity_change(change, option):
        capacities_powers_values[option] = change['new']
    
    # Function to handle PPA capacity change
    def on_ppa_capacity_change(change, option):
        ppa_capacity_values[option] = change['new']
    
    # Function to handle PPA price change
    def on_ppa_price_change(change, option):
        ppa_price_values[option] = change['new']
    
    def on_change_MC_power(change, selected_options, checkbox, capacities):
        if change['new'] is False and len(selected_options) == 1:
            warning_label.value = "Warning: At least one power source must be selected!"
            threading.Thread(target=clear_warning, args=(change['owner'],)).start()
        else:
            warning_label.value = ""
            if change['new']:
                selected_options.add(checkbox.description)
            else:
                selected_options.remove(checkbox.description)
            update_capacity_fields(selected_options, capacities)
            update_ppa_visibility(selected_options)
    
    # Create checkboxes
    checkboxes_powers = []
    
    # preselected options
    for option in preselected_checks_power:
        checkbox = widgets.Checkbox(
            value=True,
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
            value=False,
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
    
    # Create PPA sections for power sources (excluding Grid)
    ppa_section_list = []
    for option in options_power:
        # Skip Grid - no PPA for Grid
        if option == 'Grid':
            continue

        # PPA agreement dropdown
        ppa_label = widgets.Label(f"{option} - PPA agreement:", layout=widgets.Layout(width='200px'))
        ppa_dropdown = widgets.Dropdown(
            options=[True, False],
            value=None,
            layout=widgets.Layout(width='100px')
        )
        ppa_values[option] = None

        # PPA type dropdown - shown inline when PPA is True
        ppa_type_label = widgets.Label("Type:", layout=widgets.Layout(width='40px', margin='0px 0px 0px 15px', display='none'))
        ppa_type_dropdown = widgets.Dropdown(
            options=['Base load', 'Pay-as-produced'],
            value=None,
            layout=widgets.Layout(width='100px', display='none')
        )
        ppa_type_values[option] = None
        ppa_type_dropdown.observe(lambda change, option=option: ppa_type_values.update({option: change['new']}), names='value')

        # PPA details (capacity and price) - initially hidden
        ppa_capacity_label = widgets.Label("PPA capacity [MW]:", layout=widgets.Layout(width='150px'))
        ppa_capacity_input = widgets.FloatText(
            value=placeholder_value,
            layout=widgets.Layout(width='100px')
        )
        ppa_capacity_values[option] = placeholder_value
        ppa_capacity_input.observe(lambda change, option=option: on_ppa_capacity_change(change, option), names='value')
        
        ppa_price_label = widgets.Label("PPA price [€/MWh]:", layout=widgets.Layout(width='150px', margin='0px 0px 0px 10px'))
        ppa_price_input = widgets.FloatText(
            value=placeholder_value,
            layout=widgets.Layout(width='100px')
        )
        ppa_price_values[option] = placeholder_value
        ppa_price_input.observe(lambda change, option=option: on_ppa_price_change(change, option), names='value')
        
        # Container for PPA details (capacity and price)
        ppa_details = widgets.HBox(
            [ppa_capacity_label, ppa_capacity_input, ppa_price_label, ppa_price_input],
            layout=widgets.Layout(display='none', padding='5px 0px 0px 30px')
        )
        ppa_details_containers[option] = ppa_details

        # Observe PPA agreement dropdown changes
        def on_ppa_dropdown_change(change, option=option, ppa_type_label=ppa_type_label, ppa_type_dropdown=ppa_type_dropdown):
            ppa_values[option] = change['new']
            if change['new'] is True:
                ppa_details_containers[option].layout.display = 'flex'
                ppa_type_label.layout.display = 'flex'
                ppa_type_dropdown.layout.display = 'flex'
            else:
                ppa_details_containers[option].layout.display = 'none'
                ppa_type_label.layout.display = 'none'
                ppa_type_dropdown.layout.display = 'none'
                ppa_type_values[option] = None

        ppa_dropdown.observe(lambda change, option=option, ppa_type_label=ppa_type_label, 
                             ppa_type_dropdown=ppa_type_dropdown: on_ppa_dropdown_change(
                                 change, option, ppa_type_label, ppa_type_dropdown), names='value')
        
        # Main PPA container (agreement + type on same line, details below)
        ppa_main_container = widgets.VBox(
            [
                widgets.HBox(
                    [ppa_label, ppa_dropdown, ppa_type_label, ppa_type_dropdown],
                    layout=widgets.Layout(padding='5px 15px 0px 30px')
                ),
                ppa_details
            ],
            layout=widgets.Layout(display='none', margin='10px 0px 0px 0px')
        )
        
        ppa_containers[option] = ppa_main_container
        ppa_section_list.append(ppa_main_container)

    # Visibility of initially selected available powers
    update_capacity_fields(preselected_checks_power, capacities_powers)
    update_ppa_visibility(preselected_checks_power)
    
    # Layout for checkboxes and capacity inputs
    power_column = widgets.VBox(checkboxes_powers)
    capacity_column = widgets.VBox(hbox_capacities_powers)
    ppa_column = widgets.VBox(ppa_section_list, layout=widgets.Layout(margin='15px 0px 0px 0px'))
    
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
        return widgets.HBox([label_inv, dropdown_inv], layout=widgets.Layout(margin='30px 15px 0px 30px')), dropdown_inv
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
        
        dropdown_inv_ps.observe(toggle_capacity_widget, names='value')
        toggle_capacity_widget({'new': dropdown_inv_ps.value})
        
        return widgets.HBox([label_inv_ps, dropdown_inv_ps, capacity_container], 
                            layout=widgets.Layout(margin='0px 15px 0px 30px')), dropdown_inv_ps, capacity_ps_widget
        
    inv_ps_column, investment_ps, investment_ps_capacity = create_dropdown_inv_ps()
    
    hbox_warning = widgets.HBox([power_column, warning_label])
    
    return (widgets.VBox([label_power, hbox_warning, capacity_column, ppa_column, inv_res_column, inv_ps_column], 
                         layout=get_general_vbox_layout()), 
            selected_options_power, 
            capacities_powers_values, 
            investment_res, 
            investment_ps, 
            investment_ps_capacity,
            ppa_values,
            ppa_capacity_values,
            ppa_price_values,
            ppa_type_values)

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
        placeholder='e.g. 2020')
    dropdown_price_zone_vbox, dropdown_price_zone = create_dropdown_price_zone()
    dropdown_product_vbox, dropdown_product = create_dropdown_product()
    dropdown_electrolysis_vbox, dropdown_electrolysis = create_dropdown_electrolysis()
    dropdown_temp_box_vbox, dropdown_temp_block = create_dropdown_temp_block()
    number_wacc_box, number_wacc = create_input_with_label(
        key='wacc', 
        description='Set the WACC for the LCOE calculation:', 
        placeholder='e.g. 0.08')
    lcoe_years_box, lcoe_years = create_input_with_label(
        key='lcoe_years', 
        description='Set the number of years for the LCOE calculation:', 
        placeholder='e.g. 25')
    number_dh_price_box, number_dh_price = create_input_with_label(
        key='dh_price', 
        description='Set the assumed value for revenues from district heating as share of a max price:', 
        placeholder='e.g. 0.5')
    number_price_level_power_box, number_price_level_power = create_input_with_label(
        key='power_price_scale', 
        description='Set the assumed value for scaling the power price level up/down:', 
        placeholder='e.g. 1')
    power_price_variance_box, power_price_variance = create_input_with_label(
        key='power_price_var', 
        description='Set the assumed variance of the power prices:', 
        placeholder='e.g. 1')
    run_name_box, run_name = create_text_with_label(
        key='run_name', 
        description='Please choose the name of this run:', 
        placeholder='e.g. base')
    multiple_choice_report_box, selected_reports = create_multiple_choice_report()
    
    # Updated to handle 9 return values from create_multiple_choice_power()
    (multiple_choice_power_box, selected_powers, capacities_powers, investment_res, 
     investment_ps, investment_ps_capacity, ppa_values, ppa_capacity_values, 
     ppa_price_values, ppa_type_values) = create_multiple_choice_power()
    
    dropdown_roll_vbox, dropdown_roll = create_dropdown_roll()
    number_slices_vbox, number_slices = create_input_with_label(
        key='opt_horizons', 
        description='Set the number of optimization horizons for the model:',
        placeholder='e.g. 12')
    levels_elec_box, levels_elec = create_input_with_label(
        key='levels_elec', 
        description='Set the number of operating sections to represent variable efficiency:',
        placeholder='e.g. 3')
    dropdown_investment_vbox, dropdown_investment = create_dropdown_investment()
    dropdown_period_vbox, dropdown_number, dropdown_period = create_dropdown_invest_period()
    demand_hbox, demand_input, demand_res = create_demand()

    # --- Side Products subsection ---
    side_products_header = widgets.HTML(
        "<div style='margin-top:15px; margin-bottom:5px;'>"
        "<b>Side Products</b>"
        "</div>"
    )

    # District heating toggle
    dh_toggle_label = widgets.Label(
        "District heating:",
        layout=widgets.Layout(width='170px')
    )
    dh_toggle = widgets.Dropdown(
        options=[True, False],
        value=None,
        layout=widgets.Layout(width='100px')
    )
    dh_toggle.observe(on_change, names='value')

    dh_toggle_row = widgets.HBox(
        [dh_toggle_label, dh_toggle],
        layout=widgets.Layout(padding='3px 0px 0px 30px')
    )

    # District heating details (shown when toggle is True)
    dh_demand_label = widgets.Label(
        "Max DH demand [MW]:",
        layout=widgets.Layout(width='170px')
    )
    dh_demand_input = widgets.FloatText(
        value=placeholder_value,
        min=0,
        layout=widgets.Layout(width='100px')
    )

    dh_price_label = widgets.Label(
        "DH price [€/MWh]:",
        layout=widgets.Layout(width='150px', margin='0px 0px 0px 15px')
    )
    dh_price_input = widgets.FloatText(
        value=placeholder_value,
        min=0,
        layout=widgets.Layout(width='100px')
    )

    dh_details = widgets.HBox(
        [dh_demand_label, dh_demand_input, dh_price_label, dh_price_input],
        layout=widgets.Layout(display='none', padding='5px 0px 5px 30px')
    )

    def on_dh_toggle_change(change):
        if change['new'] is True:
            dh_details.layout.display = 'flex'
        else:
            dh_details.layout.display = 'none'

    dh_toggle.observe(on_dh_toggle_change, names='value')

    # Oxygen toggle
    o2_toggle_label = widgets.Label(
        "Oxygen:",
        layout=widgets.Layout(width='170px')
    )
    o2_toggle = widgets.Dropdown(
        options=[True, False],
        value=None,
        layout=widgets.Layout(width='100px')
    )
    o2_toggle.observe(on_change, names='value')

    o2_toggle_row = widgets.HBox(
        [o2_toggle_label, o2_toggle],
        layout=widgets.Layout(padding='3px 0px 0px 30px')
    )

    o2_demand_label = widgets.Label(
        "Max O2 demand [MW]:",
        layout=widgets.Layout(width='170px')
    )
    o2_demand_input = widgets.FloatText(
        value=placeholder_value,
        min=0,
        layout=widgets.Layout(width='100px')
    )

    o2_price_label = widgets.Label(
        "O2 price [€/kg]:",
        layout=widgets.Layout(width='150px', margin='0px 0px 0px 15px')
    )
    o2_price_input = widgets.FloatText(
        value=placeholder_value,
        min=0,
        layout=widgets.Layout(width='100px')
    )

    o2_details = widgets.HBox(
        [o2_demand_label, o2_demand_input, o2_price_label, o2_price_input],
        layout=widgets.Layout(display='none', padding='5px 0px 5px 30px')
    )

    def on_o2_toggle_change(change):
        if change['new'] is True:
            o2_details.layout.display = 'flex'
        else:
            o2_details.layout.display = 'none'

    o2_toggle.observe(on_o2_toggle_change, names='value')

    
    dh_section = widgets.VBox(
        [side_products_header, dh_toggle_row, dh_details, o2_toggle_row, o2_details],
        layout=widgets.Layout(display='none', margin='10px 0px 0px 0px')
    )

   
    
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
        'investment_ps_capacity': investment_ps_capacity,
        # PPA-related values
        'ppa_values': ppa_values,
        'ppa_capacity_values': ppa_capacity_values,
        'ppa_price_values': ppa_price_values,
        'ppa_type_values': ppa_type_values,
        # District heating values
        'dh_toggle': dh_toggle,
        'dh_demand_input': dh_demand_input,
        'dh_price_input': dh_price_input,
        # Oxygen values
        'o2_toggle': o2_toggle,
        'o2_demand_input': o2_demand_input,
        'o2_price_input': o2_price_input,
    }

    # Create pages (tabs)
    page1 = widgets.VBox([
        section_1, dropdown_product_vbox, demand_hbox, dh_section
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
            dh_section.layout.display = 'block'
        else:
            demand_hbox.layout.display = 'none'
            dh_section.layout.display = 'none'
    # Hide demand by default
    demand_hbox.layout.display = 'none'
    dh_section.layout.display = 'none'
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
        #'frequency': dropdowns['frequency'].value,
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
        'powers': dropdowns['powers'],
        
        # PPA values 
        'ppa_values': dropdowns['ppa_values'],
        'ppa_capacity_values': dropdowns['ppa_capacity_values'],
        'ppa_price_values': dropdowns['ppa_price_values'],   
        'ppa_type_values': dropdowns['ppa_type_values'],
        
        # District heating values
        'district_heating': dropdowns['dh_toggle'].value,
        'dh_max_demand': dropdowns['dh_demand_input'].value,
        'dh_price': dropdowns['dh_price_input'].value,

        # Oxygen values
        'oxygen': dropdowns['o2_toggle'].value,
        'o2_max_demand': dropdowns['o2_demand_input'].value,
        'o2_price': dropdowns['o2_price_input'].value,
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
    direct_keys = [
        # investment costs
        'inv_cost_ammonia_storage', 'inv_cost_anaerobic', 'inv_cost_asu',
        'inv_cost_biomethanation', 'inv_cost_co2_removal', 'inv_cost_diesel_storage',
        'inv_cost_egasoline_storage', 'inv_cost_electrolyzer', 'inv_cost_fischer',
        'inv_cost_haber', 'inv_cost_hydrogen_storage', 'inv_cost_jet_fuel_storage',
        'inv_cost_methane_storage', 'inv_cost_methanol', 'inv_cost_methanol_storage',
        'inv_cost_rwgs', 'inv_cost_steam',
        # capacities
        'capacity_asu', 'capacity_electrolyzer', 'capacity_haber', 'capacity_fischer',
        'capacity_rwgs', 'capacity_steam', 'capacity_anaerobic',
        'capacity_biomethanation', 'capacity_co2_removal',
        # limits
        'inv_limit_ammonia_storage', 'inv_limit_anaerobic', 'inv_limit_asu',
        'inv_limit_biomethanation', 'inv_limit_co2_removal', 'inv_limit_diesel_storage',
        'inv_limit_egasoline_storage', 'inv_limit_electrolyzer', 'inv_limit_fischer',
        'inv_limit_haber', 'inv_limit_hydrogen_storage', 'inv_limit_jet_fuel_storage',
        'inv_limit_methane_storage', 'inv_limit_methanol', 'inv_limit_methanol_storage',
        'inv_limit_rwgs', 'inv_limit_steam',
    ]

    for key in direct_keys:
        if key in values:
            parameters[key] = values[key]

    # Special cases: methanol capacity/limit also drives distillation
    if 'capacity_methanol' in values:
        parameters['capacity_distillation'] = values['capacity_methanol']
    if 'inv_limit_methanol' in values:
        parameters['inv_limit_distillation'] = values['inv_limit_methanol']

    return parameters