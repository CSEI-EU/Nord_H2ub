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


'''Define text query functions'''

def on_text_change(change):
    if change['type'] == 'change' and change['name'] == 'value':
        print(f'You entered: {change["new"]}')


def create_name_rep_input():
    label2 = widgets.Label(
        "Please type the name of the report if other than 'Report':")
    default_text = "Report"
    name_rep_input = widgets.Text(
        value=default_text
    )
    return widgets.VBox([label2, name_rep_input], layout=widgets.Layout(margin='0 0 15px 0')), name_rep_input


def create_scen_name_input_sev():
    label3 = widgets.Label(
        "Please type the name of the scenario if other than 'Base':")
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
    return widgets.VBox([label3, base_name_input, additional_names_input], layout=widgets.Layout(margin='0 0 15px 0')), base_name_input, additional_names_input


def create_scen_name_input():
    label3 = widgets.Label(
        "Please type the name of the scenario if other than 'Base':")
    default_text = "Base"
    base_name_input = widgets.Text(
        value=default_text,
        description="Base Scenario:"
    )
    return widgets.VBox([label3, base_name_input], layout=widgets.Layout(margin='0 0 15px 0')), base_name_input


def create_stoch_scen_input():
    label4 = widgets.Label(
        "Please type the name of the stochastic scenario if other than 'realization':")
    default_text = "realization"
    stoch_scen_input = widgets.Text(
        value=default_text,
    )
    return widgets.VBox([label4, stoch_scen_input], layout=widgets.Layout(margin='0 0 15px 0')), stoch_scen_input


def create_stoch_struc_input():
    label5 = widgets.Label(
        "Please type the name of the stochastic structure if other than 'deterministic':")
    default_text = "deterministic"
    stoch_struc_input = widgets.Text(
        value=default_text,
    )
    return widgets.VBox([label5, stoch_struc_input], layout=widgets.Layout(margin='0 0 15px 0')), stoch_struc_input

def create_run_name_input():
    label6 = widgets.Label(
        "Please choose the name of this run:")
    default_text = "base_case"
    run_name_input = widgets.Text(
        value=default_text,
    )
    return widgets.VBox([label6, run_name_input], layout=widgets.Layout(margin='0 0 15px 0')), run_name_input


'''Define numerical input functions'''

def on_number_change(change):
    if change['type'] == 'change' and change['name'] == 'value':
        print(f'You entered: {change["new"]}')


def create_share_of_dh_price_cap():
    default_number = 50  # Set as a default to not assume 100%
    description_label_1 = widgets.Label(
        "Set the assumed value for revenues from district heating as share of a max price (%):")
    number_input_1 = widgets.BoundedIntText(
        value=default_number,
        min=0,
        max=200.0,
        step=0.1,
        layout = widgets.Layout(width='100px')
    )
    number_input_1.observe(on_number_change, names='value')
    return widgets.VBox([description_label_1, number_input_1], layout=widgets.Layout(margin='0 0 15px 0')), number_input_1


def create_price_level_power():
    description_label_2 = widgets.Label(
        "Set the assumed value for scaling the power price level up/down (%):")
    number_input_2 = widgets.BoundedIntText(
        value=100,
        min=0,
        max=200.0,
        step=0.1,
        layout = widgets.Layout(width='100px')
    )
    number_input_2.observe(on_number_change, names='value')
    return widgets.VBox([description_label_2, number_input_2], layout=widgets.Layout(margin='0 0 15px 0')), number_input_2


def create_power_price_variance():
    default_number = 1
    description_label_3 = widgets.Label(
        "Set the assumed variance of the power prices:")
    number_input_3 = widgets.BoundedIntText(
        value=1,
        min=0,
        max=2.0,
        step=0.01,
        layout = widgets.Layout(width='100px')
    )
    number_input_3.observe(on_number_change, names='value')
    return widgets.VBox([description_label_3, number_input_3], layout=widgets.Layout(margin='0 0 15px 0')), number_input_3


def create_number_opt_horizons():
    #define the number of horizons for a rolling horizon optimization
    default_number = 1
    description_label_4 = widgets.Label(
        "Set the number of optimization horizons for the model:")
    number_input_4 = widgets.BoundedIntText(
        value=12,
        min=0,
        max=200,
        step=1,
        layout = widgets.Layout(width='100px')
    )
    number_input_4.observe(on_number_change, names='value')
    return widgets.VBox([description_label_4, number_input_4], layout=widgets.Layout(margin='0 0 15px 0')), number_input_4


def create_sections_elec():
    default_number = 1
    description_label_5 = widgets.Label("Set the number of operating sections to represent variable efficiency:")
    number_input_5 = widgets.BoundedIntText(
        value=3,
        min=0,
        max=10,
        step=1,
        layout = widgets.Layout(width='100px')
    )
    number_input_5.observe(on_number_change, names='value')
    return widgets.VBox([description_label_5, number_input_5], layout=widgets.Layout(margin='0 0 15px 0')), number_input_5

def create_wacc_elec():
    default_number = 8
    description_label_6 = widgets.Label("Set the WACC you want to use for the LCOE calculation (%):")
    number_input_6 = widgets.BoundedIntText(
        value=8,
        min=0,
        max=15,
        step=0.01,
        layout = widgets.Layout(width='100px')
    )
    number_input_6.observe(on_number_change, names='value')
    return widgets.VBox([description_label_6, number_input_6], layout=widgets.Layout(margin='0 0 15px 0')), number_input_6


def create_lcoe_starting_year_elec():
    default_number = 2020
    description_label_7 = widgets.Label("Set the starting year you want to use for the LCOE calculation:")
    number_input_7 = widgets.BoundedIntText(
        value=2020,
        min=0,
        max=2200,
        step=1,
        layout = widgets.Layout(width='100px')
    )
    number_input_7.observe(on_number_change, names='value')
    return widgets.VBox([description_label_7, number_input_7], layout=widgets.Layout(margin='0 0 15px 0')), number_input_7


def create_lcoe_years_elec():
    default_number = 25
    description_label_8 = widgets.Label("Set the number of years for the LCOE calculation:")
    number_input_8 = widgets.BoundedIntText(
        value=25,
        min=0,
        max=100,
        step=1,
        layout = widgets.Layout(width='100px')
    )
    number_input_8.observe(on_number_change, names='value')
    return widgets.VBox([description_label_8, number_input_8], layout=widgets.Layout(margin='0 0 15px 0')), number_input_8


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
    
    # Define the placeholder value for fields that are not yet interacted with
    placeholder_value = 1.0

    # Define a layout for descriptions and fields + indent
    description_layout = widgets.Layout(width='210px')
    input_layout = widgets.Layout(width='110px')
    indent_layout = widgets.Layout(padding='0px 0px 0px 30px', justify_content='flex-start')

    # Headline for the investment costs block
    investment_headline = widgets.Label("Please define the investment cost and maximal installed capacities per MW or MWh",
    style={'font_weight': 'bold', 'font_size': '13px'})
    
    # Assign to products
    if selected_product == 'ammonia':
        
        ammonia_storage_label = widgets.Label("Ammonia storage:")
        ammonia_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        ammonia_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        ammonia_hbox = widgets.HBox([ammonia_storage_description, ammonia_storage_input], layout=indent_layout)
        
        ammonia_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        ammonia_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        ammonia_storage_limit_hbox = widgets.HBox([ammonia_storage_limit_description, ammonia_storage_limit], layout=indent_layout)
        
        asu_label = widgets.Label("Air separation unit")
        asu_description = widgets.Label("Costs [€/MW TBA]:", layout=description_layout)
        asu_input = widgets.FloatText(value=placeholder_value, min=0,layout=input_layout)
        asu_hbox = widgets.HBox([asu_description, asu_input], layout=indent_layout)
        
        asu_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        asu_limit_input = widgets.FloatText(value=placeholder_value, min=0,layout=input_layout)
        asu_limit_hbox = widgets.HBox([asu_limit_description, asu_limit_input], layout=indent_layout)
        
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=indent_layout)
        
        haber_label = widgets.Label("Haber-Bosch unit:")
        haber_description = widgets.Label("Costs [€/MW TBA]:", layout=description_layout)
        haber_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        haber_hbox = widgets.HBox([haber_description, haber_input], layout=indent_layout)

        haber_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        haber_limit_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        haber_limit_hbox = widgets.HBox([haber_limit_description, haber_limit_input], layout=indent_layout)

        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=indent_layout)
        
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
        diesel_storage_hbox = widgets.HBox([diesel_storage_description, diesel_storage_input], layout=indent_layout)
        
        diesel_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        diesel_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        diesel_storage_limit_hbox = widgets.HBox([diesel_storage_limit_description, diesel_storage_limit], layout=indent_layout)

        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=indent_layout)

        fischer_label = widgets.Label("Fischer-Tropsch Reactor:")
        fischer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=indent_layout)

        fischer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        fischer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_limit_hbox = widgets.HBox([fischer_limit_description, fischer_limit], layout=indent_layout)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=indent_layout)
        
        rwgs_label = widgets.Label("RWGS reactor:")
        rwgs_description = widgets.Label("Costs [€/MWh TBA]:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=indent_layout)
        
        rwgs_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        rwgs_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_limit_hbox = widgets.HBox([rwgs_limit_description, rwgs_limit], layout=indent_layout)
        
        steam_label = widgets.Label("Steam plant:")
        steam_description = widgets.Label("Costs [€/MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=indent_layout)
        
        steam_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        steam_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_limit_hbox = widgets.HBox([steam_limit_description, steam_limit], layout=indent_layout)
        
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
        egasoline_storage_hbox = widgets.HBox([egasoline_storage_description, egasoline_storage_input], layout=indent_layout)
        
        egasoline_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        egasoline_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        egasoline_storage_limit_hbox = widgets.HBox([egasoline_storage_limit_description, egasoline_storage_limit], layout=indent_layout)

        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=indent_layout)

        fischer_label = widgets.Label("Fischer-Tropsch Reactor:")
        fischer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=indent_layout)

        fischer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        fischer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_limit_hbox = widgets.HBox([fischer_limit_description, fischer_limit], layout=indent_layout)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=indent_layout)
        
        rwgs_label = widgets.Label("RWGS reactor:")
        rwgs_description = widgets.Label("Costs [€/MWh TBA]:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=indent_layout)
        
        rwgs_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        rwgs_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_limit_hbox = widgets.HBox([rwgs_limit_description, rwgs_limit], layout=indent_layout)
        
        steam_label = widgets.Label("Steam plant:")
        steam_description = widgets.Label("Costs [€/MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=indent_layout)
        
        steam_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        steam_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_limit_hbox = widgets.HBox([steam_limit_description, steam_limit], layout=indent_layout)
        
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
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=indent_layout)

        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=indent_layout)
        
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
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=indent_layout)

        fischer_label = widgets.Label("Fischer-Tropsch Reactor:")
        fischer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=indent_layout)
        
        fischer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        fischer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_limit_hbox = widgets.HBox([fischer_limit_description, fischer_limit], layout=indent_layout)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=indent_layout)

        jet_fuel_storage_label = widgets.Label("Jet Fuel storage:")
        jet_fuel_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        jet_fuel_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        jet_fuel_storage_hbox = widgets.HBox([jet_fuel_storage_description, jet_fuel_storage_input], layout=indent_layout)
        
        jet_fuel_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        jet_fuel_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        jet_fuel_storage_limit_hbox = widgets.HBox([jet_fuel_storage_limit_description, jet_fuel_storage_limit], layout=indent_layout)
        
        rwgs_label = widgets.Label("RWGS reactor:")
        rwgs_description = widgets.Label("Costs [€/MWh TBA]:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=indent_layout)
        
        rwgs_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        rwgs_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_limit_hbox = widgets.HBox([rwgs_limit_description, rwgs_limit], layout=indent_layout)
        
        steam_label = widgets.Label("Steam plant:")
        steam_description = widgets.Label("Costs [€/MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=indent_layout)
        
        steam_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        steam_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_limit_hbox = widgets.HBox([steam_limit_description, steam_limit], layout=indent_layout)
        
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
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=indent_layout)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=indent_layout)
        
        methanol_label = widgets.Label("Methanol reactor:")
        methanol_description = widgets.Label("Costs [€/MW output methanol]:", layout=description_layout)
        methanol_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methanol_hbox = widgets.HBox([methanol_description, methanol_input], layout=indent_layout)
        
        methanol_limit_description = widgets.Label("Capacity limit [MW output methanol]:", layout=widgets.Layout(width='210px'))
        methanol_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methanol_limit_hbox = widgets.HBox([methanol_limit_description, methanol_limit], layout=indent_layout)
        
        methanol_storage_label = widgets.Label("Methanol storage:")
        methanol_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        methanol_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methanol_storage_hbox = widgets.HBox([methanol_storage_description, methanol_storage_input], layout=indent_layout)
        
        methanol_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        methanol_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methanol_storage_limit_hbox = widgets.HBox([methanol_storage_limit_description, methanol_storage_limit], layout=indent_layout)

        steam_label = widgets.Label("Steam plant:")
        steam_description = widgets.Label("Costs [€/MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=indent_layout)
        
        steam_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        steam_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_limit_hbox = widgets.HBox([steam_limit_description, steam_limit], layout=indent_layout)
                
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
        anaerobic_hbox = widgets.HBox([anaerobic_description, anaerobic_input], layout=indent_layout)
        
        biomethanation_label = widgets.Label("Biomethanation plant:")
        biomethanation_description = widgets.Label("Costs [€/MW TBA]:", layout=description_layout)
        biomethanation_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        biomethanation_hbox = widgets.HBox([biomethanation_description, biomethanation_input], layout=indent_layout)
        
        co2_remover_label = widgets.Label("CO2 removal plant:")
        co2_remover_description = widgets.Label("Costs [€/MW TBA]:", layout=description_layout)
        co2_remover_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        co2_remover_hbox = widgets.HBox([co2_remover_description, co2_remover_input], layout=indent_layout)

        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_description = widgets.Label("Costs [€/MW power input]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        electrolyzer_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        electrolyzer_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_limit_hbox = widgets.HBox([electrolyzer_limit_description, electrolyzer_limit], layout=indent_layout)

        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        hydrogen_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_hbox = widgets.HBox([hydrogen_storage_description, hydrogen_storage_input], layout=indent_layout)
        
        hydrogen_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        hydrogen_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        hydrogen_storage_limit_hbox = widgets.HBox([hydrogen_storage_limit_description, hydrogen_storage_limit], layout=indent_layout)
        
        methane_storage_label = widgets.Label("Methane storage:")
        methane_storage_description = widgets.Label("Costs [€/MWh storage]:", layout=description_layout)
        methane_storage_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methane_storage_hbox = widgets.HBox([methane_storage_description, methane_storage_input], layout=indent_layout)
        
        methane_storage_limit_description = widgets.Label("Capacity limit [MWh storage]:", layout=description_layout)
        methane_storage_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methane_storage_limit_hbox = widgets.HBox([methane_storage_limit_description, methane_storage_limit], layout=indent_layout)

        steam_label = widgets.Label("Steam plant:")
        steam_description = widgets.Label("Costs [€/MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=indent_layout)
        
        steam_limit_description = widgets.Label("Capacity limit [MW input power]:", layout=description_layout)
        steam_limit = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_limit_hbox = widgets.HBox([steam_limit_description, steam_limit], layout=indent_layout)
                        
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
                                         anaerobic_label, anaerobic_hbox,
                                         biomethanation_label, biomethanation_hbox,
                                         co2_remover_label, co2_remover_hbox,
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
    
    # Define the placeholder value for fields that are not yet interacted with
    placeholder_value = 0
    
    # Define a layout for descriptions and fields + indent
    description_layout = widgets.Layout(width='220px')
    input_layout = widgets.Layout(width='100px')
    indent_layout = widgets.Layout(padding='0px 0px 0px 40px', justify_content='flex-start')

    label = widgets.Label("Existing capacity:")
    
    steam_description = widgets.Label("Existing capacity [MW input power]:", layout=description_layout)
    steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
    steam_hbox = widgets.HBox([steam_description, steam_input], layout=indent_layout)

    # Assign fields to products
    if selected_product == 'ammonia':
        asu_description = widgets.Label("Air separation unit []:", layout=description_layout)
        asu_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        asu_hbox = widgets.HBox([asu_description, asu_input], layout=indent_layout)
        
        electrolyzer_description = widgets.Label("Electrolyzer [MW input power]:",
                                                 layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        haber_description = widgets.Label("Haber-Bosch unit []:", layout=description_layout)
        haber_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        haber_hbox = widgets.HBox([haber_description, haber_input], layout=indent_layout)
              
        # Store values in investment dictionary
        capacities_values['capacity_asu'] = asu_input
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_haber'] = haber_input
        
        capacities_vbox.children = [label, asu_hbox, electrolyzer_hbox, haber_hbox]
    
    elif selected_product == 'diesel':
        electrolyzer_description = widgets.Label("Electrolyzer [MW input power]:",
                                                 layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        fischer_description = widgets.Label("Fischer-Tropsch reactor []:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=indent_layout)
        
        rwgs_description = widgets.Label("RWGS reactor []:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=indent_layout)
        
        steam_description = widgets.Label("Steam plant [MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=indent_layout)
        
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
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)

        fischer_label = widgets.Label("")
        fischer_description = widgets.Label("Fischer-Tropsch reactor []:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=indent_layout)
        
        rwgs_description = widgets.Label("RWGS reactor []:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=indent_layout)
        
        steam_description = widgets.Label("Steam plant [MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=indent_layout)
        
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
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        # Store values in investment dictionary
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        
        capacities_vbox.children = [label, electrolyzer_hbox]

    elif selected_product == 'jet_fuel':
        electrolyzer_description = widgets.Label("Electrolyzer [MW input power]:",
                                                 layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        fischer_description = widgets.Label("Fischer-Tropsch reactor []:", layout=description_layout)
        fischer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        fischer_hbox = widgets.HBox([fischer_description, fischer_input], layout=indent_layout)
        
        rwgs_description = widgets.Label("RWGS reactor []:", layout=description_layout)
        rwgs_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        rwgs_hbox = widgets.HBox([rwgs_description, rwgs_input], layout=indent_layout)
        
        steam_description = widgets.Label("Steam plant [MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=indent_layout)
        
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
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        methanol_description = widgets.Label("Methanol reactor [MW output methanol]:",
                                             layout=description_layout)
        methanol_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        methanol_hbox = widgets.HBox([methanol_description, methanol_input], layout=indent_layout)
        
        steam_description = widgets.Label("Steam plant [MW input power]:", layout=description_layout)
        steam_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        steam_hbox = widgets.HBox([steam_description, steam_input], layout=indent_layout)
        
        # Store values in investment dictionary
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_methanol'] = methanol_input
        capacities_values['capacity_steam'] = steam_input
        
        capacities_vbox.children = [label, electrolyzer_hbox, methanol_hbox, steam_hbox]
    
    elif selected_product == 'methane':
        anaerobic_description = widgets.Label("Anaerobic digestion plant []:", layout=description_layout)
        anaerobic_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        anaerobic_hbox = widgets.HBox([anaerobic_description, anaerobic_input], layout=indent_layout)
        
        biomethanation_description = widgets.Label("Biomethanation plant []:", layout=description_layout)
        biomethanation_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        biomethanation_hbox = widgets.HBox([biomethanation_description, biomethanation_input], layout=indent_layout)
        
        co2_remover_description = widgets.Label("CO2 removal plant []:", layout=description_layout)
        co2_remover_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        co2_remover_hbox = widgets.HBox([co2_remover_description, co2_remover_input], layout=indent_layout)
        
        electrolyzer_description = widgets.Label("Electrolyzer [MW input power]:", layout=description_layout)
        electrolyzer_input = widgets.FloatText(value=placeholder_value, min=0, layout=input_layout)
        electrolyzer_hbox = widgets.HBox([electrolyzer_description, electrolyzer_input], layout=indent_layout)
        
        # Store values in investment dictionary
        capacities_values['capacity_anaerobic'] = anaerobic_input
        capacities_values['capacity_biomethanation'] = biomethanation_input
        capacities_values['capacity_co2_removal'] = co2_remover_input
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        
        capacities_vbox.children = [label, anaerobic_hbox, biomethanation_hbox, co2_remover_hbox, electrolyzer_hbox]


# Define demand
def create_demand():
    demand_vbox = widgets.VBox(layout=widgets.Layout(margin='0 0 0 0'))
    
    # Define a layout for descriptions and fields
    description_layout = widgets.Layout(width='140px')
    input_layout = widgets.Layout(width='85px')

    demand_per = widgets.Label(" with this resolution:")

    # Add fields
    demand_description = widgets.Label("Yearly demand [MWh]:", layout=description_layout)
    
    demand_input = widgets.IntText(
        value=180000, 
        min=0, 
        layout=input_layout
    )
    demand_input.observe(on_number_change, names='value')

    def create_dropdown_res():
        global option_values, selected_option_widget, selected_value_widget  
        option_values = ['hourly', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly']
        
        label_d_res = widgets.Label(" with a(n) ", layout=widgets.Layout(width='80px', justify_content='center'))
        label_d_res_2 = widgets.Label(" resolution")
        
        dropdown_d_res = widgets.Dropdown(
            options=option_values,
            value='daily',
            layout=input_layout
        )
        dropdown_d_res.observe(on_change)
        demand_d_res_hbox = widgets.HBox([label_d_res, dropdown_d_res, label_d_res_2])

        return demand_d_res_hbox, dropdown_d_res

    demand_d_res_hbox, dropdown_d_res = create_dropdown_res() 
    demand_input_hbox = widgets.HBox([demand_input, demand_d_res_hbox])
    
    return widgets.VBox([demand_description, demand_input_hbox], layout=widgets.Layout(margin='0 0 15px 0')), demand_input, dropdown_d_res


'''Define dropdown functions'''

#change the parameter values of the if the drop down menu value is changes
def on_change(change):
    if change['name'] == 'value' and change['new'] != "":
        print(f'You selected: {change["new"]}')


# Function to handle the change in dropdown selection
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
        value=2019,
        layout = widgets.Layout(width='100px')
    )
    dropdown1.observe(on_change)
    return widgets.VBox([label1, dropdown1], layout=widgets.Layout(margin='0 0 15px 0')), dropdown1


#create dropdown for the power price zone
def create_dropdown_price_zone():
    label2 = widgets.Label("Please select the power price zone where the plant is located:")
    dropdown2 = widgets.Dropdown(
        options=['DK_1', 'DK_2', 'DK_BHM', 'NO_1', 'NO_2', 'NO_3', 'NO_4', 'NO_5', 'SE_1', 'SE_2', 'SE_3', 'SE_4'],
        value='DK_1',
        layout = widgets.Layout(width='100px')
    )
    dropdown2.observe(on_change)
    return widgets.VBox([label2, dropdown2], layout=widgets.Layout(margin='0 0 15px 0')), dropdown2   


#create dropdown for the product
def create_dropdown_product():
    label3 = widgets.HTML("Please set the product of the plant <i>(required)</i>: ")
    dropdown3 = widgets.Dropdown(
        options = ['ammonia', 'diesel', 'egasoline', 'hydrogen', 'jet_fuel', 'methane', 'methanol'],
        value = None,
        layout = widgets.Layout(width='100px')
    )
    def on_dropdown_change(change):
        update_inv_costs(change, investment_cost_vbox)   # Update investment costs box
        update_capacities(change, capacities_vbox)   # Update capacities box

    dropdown3.observe(on_dropdown_change, names='value')
    
    return widgets.VBox([label3, dropdown3], layout=widgets.Layout(margin='0 0 15px 0')), dropdown3   


#create dropdown for the electrolysis type
def create_dropdown_electrolysis():
    label4 = widgets.Label("Please select the type of electrolysis:")
    dropdown4 = widgets.Dropdown(
        options=['PEM', 'Alkaline', 'SOEC'],
        value='PEM',
        layout = widgets.Layout(width='100px')
    )
    dropdown4.observe(on_change)
    return widgets.VBox([label4, dropdown4], layout=widgets.Layout(margin='0 0 15px 0')), dropdown4  


# Create dropdown for the model frequency
def create_dropdown_frequency():
    # Dictionary to map options to their corresponding values
    # Declare as global to access in on_change_dict
    global option_values, selected_option_widget, selected_value_widget  
    option_values = {
        '1h': 'hourly',
        '1D': 'daily',
        '1W': 'weekly',
        '1M': 'monthly',
        '1Q': 'quarterly',
        '1Y': 'yearly'
    }

    label5 = widgets.Label("Please select the frequency:")
    dropdown5 = widgets.Dropdown(
        options=list(option_values.keys()),
        value='1h',
        layout = widgets.Layout(width='100px')
    )
    selected_option_widget = widgets.Label(dropdown5.value)
    selected_value_widget = widgets.Label(option_values[dropdown5.value])
    
    dropdown5.observe(on_change_dict, names='value')
    return widgets.VBox([label5, dropdown5], layout=widgets.Layout(margin='0 0 15px 0')), selected_option_widget, selected_value_widget


#create dropdown for the whether or not roll_forward is used
roll_forward_use = True
def create_dropdown_roll():
    label6 = widgets.Label(
        "Please select whether or not the model should run with a rolling horizon optimization:"
    )
    dropdown6 = widgets.Dropdown(
        options=[True, False],
        value=False, 
        layout = widgets.Layout(width='100px')
    )
    dropdown6.observe(on_change)
    return widgets.VBox([label6, dropdown6], layout=widgets.Layout(margin='0 0 15px 0')), dropdown6


#create dropdown for whether or not investments can be made
def create_dropdown_investment():
    
    label7 = widgets.Label("Please select whether or not the model should run an investment optimization:")
    dropdown7 = widgets.Dropdown(
        options=[True, False],
        value=False,
        layout=widgets.Layout(width='100px')
    )
    dropdown7.observe(on_change)
    return widgets.VBox([label7, dropdown7], layout=widgets.Layout(margin='0 0 15px 0')), dropdown7


# Create dropdown for the default investment period
def create_dropdown_invest_period():
    # Dictionary to map options to their corresponding values
    label8 = widgets.Label("Please select the investment period:")
    
    number_input_8 = widgets.BoundedIntText(
        value=1,
        min=1,
        max=30,
        step=1,
        layout=widgets.Layout(width='100px')
    )
    number_input_8.observe(on_number_change, names='value')
    
    dropdown8 = widgets.Dropdown(
        options=['h', 'D', 'W', 'M', 'Q', 'Y'],
        value='Y',
        layout=widgets.Layout(width='100px')
    )
    dropdown8.observe(on_change)

    input_hbox = widgets.HBox([number_input_8, dropdown8])
    
    return widgets.VBox([label8, input_hbox], layout=widgets.Layout(margin='0 0 15px 0')), number_input_8, dropdown8


'''Define multiple choice functions'''

def on_change_MC_report(change, selected_options_report, checkbox):
    if change['new']:
        selected_options_report.add(checkbox.description)
        print(f'You added {checkbox.description} to the report.') #added more text to make it clearer for reports
    else:
        selected_options_report.discard(checkbox.description)

        
def create_multiple_choice_power():
    label_power = widgets.Label("Please select the different power sources available:")
    
    # Define the list of options
    options_power = ['Grid', 'Solar plant', 'Wind onshore', 'Wind offshore', 'Power Storage']
    
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
    def update_capacity_fields():
        for option, hbox in capacities_powers.items():
            if option in selected_options_power:
                hbox.layout.display = 'flex'
            else:
                hbox.layout.display = 'none'
    
    # Function to update the capacities_powers_values when changed
    def on_capacity_change(change, option):
        capacities_powers_values[option] = change['new']
    
    def on_change_MC_power(change, selected_options_power, checkbox):
        if change['new'] is False and len(selected_options_power) == 1:
            warning_label.value = "Warning: At least one power source must be selected!"
            threading.Thread(target=clear_warning, args=(change['owner'],)).start()
        else:
            warning_label.value = ""
            if change['new']:  # If the checkbox was checked
                selected_options_power.add(checkbox.description)
            else:  # If the checkbox was unchecked
                selected_options_power.remove(checkbox.description)
            update_capacity_fields()
    
    # Create checkboxes
    checkboxes_powers = []
    
    # preselected options
    for option in preselected_checks_power:
        checkbox = widgets.Checkbox(
            value=True,  # All preselected options should be checked
            description=option,
            indent=False,
            layout=widgets.Layout(padding='0px 0px 0px 30px')
        )
        checkbox.observe(lambda change, 
                         checkbox=checkbox: on_change_MC_power(change, selected_options_power, checkbox),
                         names='value')
        checkboxes_powers.append(checkbox)
    
    # non-preselected options
    for option in non_preselected_checks_power:
        checkbox = widgets.Checkbox(
            value=False,  # Non-preselected options should be unchecked
            description=option,
            indent=False,
            layout=widgets.Layout(padding='0px 0px 0px 30px')
        )
        checkbox.observe(lambda change, 
                         checkbox=checkbox: on_change_MC_power(change, selected_options_power, checkbox),
                         names='value')
        checkboxes_powers.append(checkbox)
    
    # Create capacity fields for each option except grid (hidden initially):
    res = ['Solar plant', 'Wind onshore', 'Wind offshore', 'Power Storage']
    for option in res:
        capacity_widget = widgets.FloatText(
            value=0,
            layout=widgets.Layout(width='100px')
        )
        label = widgets.Label(f"{option} capacity (MW):", layout=widgets.Layout(width='220px'))
        
        hbox = widgets.HBox([label, capacity_widget], layout=widgets.Layout(display='none', 
                                                                            padding='0px 0px 0px 30px',
                                                                            justify_content='flex-start'))
        capacities_powers[option] = hbox
        hbox_capacities_powers.append(hbox)
        
        capacities_powers_values[option] = capacity_widget.value
        capacity_widget.observe(lambda change, option=option: on_capacity_change(change, option), names='value')

    # Layout for checkboxes and capacity inputs
    power_column = widgets.VBox(checkboxes_powers)
    capacity_column = widgets.VBox(hbox_capacities_powers)
    
    # Add possibility for investment
    def create_dropdown_inv():
        label_inv = widgets.HTML(
            "Possibility for investment in RES <i>(not recommended)</i>:"
        )
        dropdown_inv = widgets.Dropdown(
            options=[True, False],
            value=False,
            layout=widgets.Layout(width='100px', padding='0px 0px 0px 5px')
        )
        dropdown_inv.observe(on_change)
        return widgets.HBox([label_inv, dropdown_inv], layout=widgets.Layout(padding='0px 0px 0px 30px')), dropdown_inv

    inv_res_column, investment_res = create_dropdown_inv()
    
    #Update capacity fields visibiliy based on preselected options
    update_capacity_fields()
    
    hbox_warning = widgets.HBox([power_column, warning_label])
    
    return widgets.VBox([label_power, hbox_warning, capacity_column, inv_res_column], layout=widgets.Layout(margin='0 0 15px 0')), selected_options_power, capacities_powers_values, investment_res
  

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
    
    return widgets.VBox([label2, hbox_report], layout=widgets.Layout(margin='0 0 15px 0')), selected_options_report



'''Define functions for the combined data definition menu'''

def create_combined_dropdowns_tabs():
    # Provide information for each section
    section_1 = widgets.HTML("<b>Section 1: Please define the base parameters</b>")
    section_2 = widgets.HTML("<b>Section 2: Please define the energy sources</b>")
    section_3 = widgets.HTML("<b>Section 3: Please define the parameters of the general model</b>")
    section_4 = widgets.HTML("<b>Section 4: Please define the parameters of electrolysis</b>")
    section_5 = widgets.HTML("<b>Section 5: Please define the economic parameters of the general model</b>")
    section_6 = widgets.HTML("<b>Section 6: Please define the parameters for the investments</b>")
    section_7 = widgets.HTML("<b>Section 7: Please define the variables for the report</b>")
    section_8 = widgets.HTML("<b>Section 8: Please define the parameters for the different scenarios</b>")

    # Get the dropdown menus
    dropdown_year_vbox, dropdown_year = create_dropdown_year()
    number_starting_year_box, number_starting_year = create_lcoe_starting_year_elec()
    dropdown_price_zone_vbox, dropdown_price_zone = create_dropdown_price_zone()
    dropdown_product_vbox, dropdown_product = create_dropdown_product()
    dropdown_electrolysis_vbox, dropdown_electrolysis = create_dropdown_electrolysis()
    dropdown_frequency_vbox, dropdown_frequency, dropdown_temporal = create_dropdown_frequency()
    number_wacc_box, number_wacc = create_wacc_elec()
    lcoe_years_box, lcoe_years = create_lcoe_years_elec()
    number_dh_price_box, number_dh_price = create_share_of_dh_price_cap()
    number_price_level_power_box, number_price_level_power = create_price_level_power()
    power_price_variance_box, power_price_variance = create_power_price_variance()
    report_name_box, report_name = create_name_rep_input()
    run_name_box, run_name = create_run_name_input()
    multiple_choice_report_box, selected_reports = create_multiple_choice_report()
    multiple_choice_power_box, selected_powers, capacities_powers, investment_res = create_multiple_choice_power()
    scen_name_box, base_scen = create_scen_name_input()
    #scen_name_box, base_scen, other_scen = create_scen_name_input_sev()
    stoch_scen_vbox, stoch_scen = create_stoch_scen_input()
    stoch_struc_vbox, stoch_struc = create_stoch_struc_input()
    dropdown_roll_vbox, dropdown_roll = create_dropdown_roll()
    number_slices_vbox, number_slices = create_number_opt_horizons()
    levels_elec_box, levels_elec = create_sections_elec()
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
        'frequency': dropdown_frequency,
        'temporal_block': dropdown_temporal,
        'number_wacc': number_wacc,
        'lcoe_years': lcoe_years,
        'number_dh_price_share': number_dh_price,
        'number_price_level_power': number_price_level_power,
        'power_price_variance': power_price_variance,
        'report_name': report_name,
        'run_name': run_name,
        'reports': selected_reports,
        'base_scen': base_scen,
        #'other_scen': other_scen,
        'stoch_scen': stoch_scen,
        'stoch_struc': stoch_struc,
        'roll_forward': dropdown_roll,
        'number_slices': number_slices,
        'levels_elec': levels_elec,
        'candidate_nonzero': dropdown_investment,
        'default_investment_number': dropdown_number,
        'default_investment_duration': dropdown_period,
        'demand': demand_input,
        'demand_res': demand_res,
        'investment_res': investment_res
    }

    # Create pages (tabs)
    page1 = widgets.VBox([
        section_1, dropdown_product_vbox, demand_hbox, capacities_vbox
    ])

    page2 = widgets.VBox([
        section_2, multiple_choice_power_box, dropdown_year_vbox, dropdown_price_zone_vbox
    ])
    
    page3 = widgets.VBox([
        section_3, run_name_box, dropdown_frequency_vbox, dropdown_roll_vbox, number_slices_vbox
    ])
    
    page4 = widgets.VBox([
        section_4, dropdown_electrolysis_vbox, levels_elec_box
    ])
    
    page5 = widgets.VBox([
        section_5, number_wacc_box, number_starting_year_box, lcoe_years_box, number_dh_price_box, number_price_level_power_box, power_price_variance_box
    ])
    
    page6 = widgets.VBox([
        section_6, dropdown_investment_vbox, dropdown_period_vbox, investment_cost_vbox
    ])

    page7 = widgets.VBox([
        section_7, scen_name_box, stoch_scen_vbox, stoch_struc_vbox
    ])

    page8 = widgets.VBox([
        section_8, report_name_box, multiple_choice_report_box
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
                #tabs.set_title(6, 'Scenario')
                #tabs.set_title(7, 'Results')
    dropdown_product.observe(add_tabs_on_product_selection, names='value')
    
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
        'frequency': dropdowns['frequency'].value,
        'temporal_block': dropdowns['temporal_block'].value,
        'roll_forward': dropdowns['roll_forward'].value,
        #'default_investment_period': dropdowns['default_investment_period'].value,
        'candidate_nonzero': dropdowns['candidate_nonzero'].value,
        'default_investment_number': dropdowns['default_investment_number'].value,
        'default_investment_duration': dropdowns['default_investment_duration'].value,
        'investment_res': dropdowns['investment_res'].value,
        
        # Numerical values (percent) adjusted
        'capacities_powers': dropdowns['capacities_powers'],
        'wacc': dropdowns['number_wacc'].value / 100,
        'lcoe_years': dropdowns['lcoe_years'].value,
        'share_of_dh_price_cap': dropdowns['number_dh_price_share'].value / 100,
        'number_price_level_power': dropdowns['number_price_level_power'].value / 100,
        'power_price_variance': dropdowns['power_price_variance'].value,
        'num_slices': dropdowns['number_slices'].value,
        'des_segments_electrolyzer': dropdowns['levels_elec'].value,
        
        # Other text fields
        'base_scen': dropdowns['base_scen'].value,
        #'other_scen': dropdowns['other_scen'].value,
        'stoch_scen': dropdowns['stoch_scen'].value,
        'stoch_struc': dropdowns['stoch_struc'].value,
        'report_name': dropdowns['report_name'].value,
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


def compute_other_values(values):
    # Create DatetimeIndex for the range of dates
    start_date = pd.Timestamp(f"{values['year']}-01-01 00:00:00")
    end_date = pd.Timestamp(f"{values['year']}-12-31 23:00:00")
    datetime_index = pd.date_range(start=start_date, end=end_date, freq=values['frequency'])
    
    # Calculate the number of steps within the horizon
    num_slices = int(values['num_slices'])
    num_steps = len(datetime_index)

    # Find the largest integer divisor that fulfills the condition
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
             "\n The calculation uses the factor: ", used_slices, ".")

    # Determine the temporal block
    frequency_mapping = {
        '1h': 'hourly',
        '1D': 'daily',
        '1W': 'weekly',
        '1M': 'monthly',
        '1Q': 'quarterly'
    }
    temporal_block = frequency_mapping.get(values['frequency'], 'yearly')

    return {
        'start_date': start_date,
        'end_date': end_date,
        'datetime_index': datetime_index,
        'roll_forward_size': roll_forward_size,
        'temporal_block': temporal_block,
        'num_steps': num_steps
    }


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
    
