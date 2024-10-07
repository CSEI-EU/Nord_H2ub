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


'''Define text query functions'''

def on_text_change(change):
    if change['type'] == 'change' and change['name'] == 'value':
        print(f'You entered: {change["new"]}')

        
def create_name_input():
    label1 = widgets.Label(
        "Please type the name of the model if other than 'Model':")
    default_text = "Model"
    name_input = widgets.Text(
        value=default_text,
    )
    name_input.observe(on_text_change, names='value')
    return widgets.VBox([label1, name_input]), name_input


def create_name_rep_input():
    label2 = widgets.Label(
        "Please type the name of the report if other than 'Report':")
    default_text = "Report"
    name_rep_input = widgets.Text(
        value=default_text,
    )
    return widgets.VBox([label2, name_rep_input]), name_rep_input


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
    return widgets.VBox([label3, base_name_input, additional_names_input]), base_name_input, additional_names_input


def create_scen_name_input():
    label3 = widgets.Label(
        "Please type the name of the scenario if other than 'Base':")
    default_text = "Base"
    base_name_input = widgets.Text(
        value=default_text,
        description="Base Scenario:"
    )
    return widgets.VBox([label3, base_name_input]), base_name_input


def create_stoch_scen_input():
    label4 = widgets.Label(
        "Please type the name of the stochastic scenario if other than 'realization':")
    default_text = "realization"
    stoch_scen_input = widgets.Text(
        value=default_text,
    )
    return widgets.VBox([label4, stoch_scen_input]), stoch_scen_input


def create_stoch_struc_input():
    label5 = widgets.Label(
        "Please type the name of the stochastic structure if other than 'deterministic':")
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
    description_label_1 = widgets.Label(
        "Set the assumed value for revenues from district heating as share of a max price (%):")
    number_input_1 = widgets.BoundedIntText(
        value=default_number,
        min=0,
        max=200.0,
        step=0.1,
    )
    number_input_1.observe(on_number_change, names='value')
    return widgets.VBox([description_label_1, number_input_1]), number_input_1


def create_price_level_power():
    description_label_2 = widgets.Label(
        "Set the assumed value for scaling the power price level up/down (%):")
    number_input_2 = widgets.BoundedIntText(
        value=100,
        min=0,
        max=200.0,
        step=0.1,
    )
    number_input_2.observe(on_number_change, names='value')
    return widgets.VBox([description_label_2, number_input_2]), number_input_2


def create_power_price_variance():
    default_number = 1
    description_label_3 = widgets.Label(
        "Set the assumed variance of the power prices:")
    number_input_3 = widgets.BoundedIntText(
        value=1,
        min=0,
        max=2.0,
        step=0.01,
    )
    number_input_3.observe(on_number_change, names='value')
    return widgets.VBox([description_label_3, number_input_3]), number_input_3


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
    )
    number_input_4.observe(on_number_change, names='value')
    return widgets.VBox([description_label_4, number_input_4]), number_input_4


def create_sections_elec():
    default_number = 1
    description_label_5 = widgets.Label("Set the number of operating sections to represent variable efficiency:")
    number_input_5 = widgets.BoundedIntText(
        value=3,
        min=0,
        max=10,
        step=1,
    )
    number_input_5.observe(on_number_change, names='value')
    return widgets.VBox([description_label_5, number_input_5]), number_input_5


# Set investment costs and capacity limit depending on type of product
investment_cost_vbox = widgets.VBox()
investment_cost_values = {}
investment_limit_values = {}

def update_inv_costs(change, investment_cost_vbox):
    # Get selected product from the dropdown (methanol, ammonia, or jet_fuel)
    selected_product = change['new']
    
    # Clear existing investment widgets (if any)
    investment_cost_vbox.children = []
    
    # Clear the investment_cost_values dictionary before updating
    investment_cost_values.clear()
    investment_limit_values.clear()
    
    # Define the placeholder value for fields that are not yet interacted with
    placeholder_value = 1.0

    # Define a layout for the FloatText widgets with wider description space
    float_text_layout = widgets.Layout(width='400px')  
    float_text_style = {'description_width': '200px', 'text_align': 'left'}

    # Headline for the investment costs block
    investment_headline = widgets.Label("Please define the investment cost and maximal installed capacities per MW or MWh",
    style={'font_weight': 'bold', 'font_size': '13px'})

    
    if selected_product == 'ammonia':
        ammonia_storage_label = widgets.Label("Ammonia storage:")
        ammonia_storage_input = widgets.FloatText(description="Costs [€/MWh storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        asu_label = widgets.Label("Air separation unit")
        asu_input = widgets.FloatText(description="Costs [€/MW TBA]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Costs [€/MW power input]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        haber_label = widgets.Label("Haber-Bosch unit:")
        haber_input = widgets.FloatText(description="Costs [€/MW TBA]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_input = widgets.FloatText(description="Costs [€/MWh storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_ammonia_storage'] = ammonia_storage_input
        investment_cost_values['inv_cost_asu'] = asu_input
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_haber'] = haber_input
        investment_cost_values['inv_cost_hydrogen_storage'] = hydrogen_storage_input

        investment_cost_vbox.children = [investment_headline,
                                         ammonia_storage_label, ammonia_storage_input,
                                         asu_label, asu_input,
                                         electrolyzer_label, electrolyzer_input, 
                                         haber_label, haber_input,
                                         hydrogen_storage_label, hydrogen_storage_input
                                        ]
    
    elif selected_product == 'egasoline':
        egasoline_storage_label = widgets.Label("E-Gasoline storage:")
        egasoline_storage_input = widgets.FloatText(description="Costs [€/MWh storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Costs [€/MW power input]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        fischer_label = widgets.Label("Fischer-Tropsch reactor:")
        fischer_input = widgets.FloatText(description="Costs [€/MW TBA]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_input = widgets.FloatText(description="Costs [€/MWh storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        rwgs_label = widgets.Label("RWGS reactor:")
        rwgs_input = widgets.FloatText(description="Costs [€/MW TBA]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_egasoline_storage'] = egasoline_storage_input
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_fischer'] = fischer_input
        investment_cost_values['inv_cost_hydrogen_storage'] = hydrogen_storage_input
        investment_cost_values['inv_cost_rwgs'] = rwgs_input
        
        investment_cost_vbox.children = [investment_headline,
                                         egasoline_storage_label, egasoline_storage_input,
                                         electrolyzer_label, electrolyzer_input, 
                                         fischer_label, fischer_input,
                                         hydrogen_storage_label, hydrogen_storage_input,
                                         rwgs_label, rwgs_input
                                        ]
    
    elif selected_product == 'hydrogen':
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Costs [€/MW input power]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_input = widgets.FloatText(description="Costs [€/MWh storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_hydrogen_storage'] = hydrogen_storage_input
        
        investment_cost_vbox.children = [investment_headline,
                                         electrolyzer_label, electrolyzer_input, 
                                         hydrogen_storage_label, hydrogen_storage_input
                                        ]
    
    elif selected_product == 'jet_fuel':
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Costs [€/MW input power]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        fischer_label = widgets.Label("Fischer-Tropsch reactor:")
        fischer_input = widgets.FloatText(description="Costs [€/MW TBA]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_input = widgets.FloatText(description="Costs [€/MWh storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        jet_fuel_storage_label = widgets.Label("Jet fuel storage:")
        jet_fuel_storage_input = widgets.FloatText(description="Costs [€/MWh storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        rwgs_label = widgets.Label("RWGS reactor:")
        rwgs_input = widgets.FloatText(description="Costs [€/MW TBA]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_fischer'] = fischer_input
        investment_cost_values['inv_cost_hydrogen_storage'] = hydrogen_storage_input
        investment_cost_values['inv_cost_jet_fuel_storage'] = jet_fuel_storage_input
        investment_cost_values['inv_cost_rwgs'] = rwgs_input
        
        investment_cost_vbox.children = [investment_headline,
                                         electrolyzer_label, electrolyzer_input, 
                                         fischer_label, fischer_input,
                                         hydrogen_storage_label, hydrogen_storage_input,
                                         jet_fuel_storage_label, jet_fuel_storage_input,
                                         rwgs_label, rwgs_input
                                        ]
    
    elif selected_product == 'methanol':

        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Costs [€/MW input power]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style, justify_content="flex-end")
        electrolyzer_limit = widgets.FloatText(description="Capacity limit [MW input power]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        hydrogen_storage_label = widgets.Label("Hydrogen storage:")
        hydrogen_storage_input = widgets.FloatText(description="Costs [€/MWh storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        hydrogen_storage_limit = widgets.FloatText(description="Capacity limit [MWh storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        methanol_label = widgets.Label("Methanol reactor:")
        methanol_input = widgets.FloatText(description="Costs [€/MW output methanol]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        methanol_limit = widgets.FloatText(description="Capacity limit [MW output methanol]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        methanol_storage_label = widgets.Label("Methanol storage:")
        methanol_storage_input = widgets.FloatText(description="Costs [€/MWh storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        methanol_storage_limit = widgets.FloatText(description="Capacity limit [MWh storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        steam_label = widgets.Label("Steam plant:")
        steam_input = widgets.FloatText(description="Costs [€/MW input power]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        steam_limit = widgets.FloatText(description="Capacity limit [MW input power]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
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
                                         electrolyzer_label, electrolyzer_input, electrolyzer_limit,
                                         hydrogen_storage_label, hydrogen_storage_input, hydrogen_storage_limit,
                                         methanol_label, methanol_input, methanol_limit,
                                         methanol_storage_label, methanol_storage_input, methanol_storage_limit,
                                         steam_label, steam_input, steam_limit
                                        ]
    
    elif selected_product == 'synthetic_methane_gas':
        anaerobic_label = widgets.Label("Anaerobic digestion plant:")
        anaerobic_input = widgets.FloatText(description="Costs [€/MW TBA]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        biomethanation_label = widgets.Label("Biomethanation plant:")
        biomethanation_input = widgets.FloatText(description="Costs [€/MW TBA]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        co2_remover_label = widgets.Label("CO2 removal plant:")
        co2_remover_input = widgets.FloatText(description="Costs [€/MW TBA]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Costs [€/MW input power]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        methane_storage_label = widgets.Label("Methane storage:")
        methane_storage_input = widgets.FloatText(description="Costs [€/MW storage]:", value=placeholder_value, min=0,
        layout=float_text_layout, style=float_text_style)
        
        # Store values in investment dictionary
        investment_cost_values['inv_cost_anaerobic'] = anaerobic_input
        investment_cost_values['inv_cost_biomethanation'] = biomethanation_input
        investment_cost_values['inv_cost_co2_removal'] = co2_remover_input
        investment_cost_values['inv_cost_electrolyzer'] = electrolyzer_input
        investment_cost_values['inv_cost_methane_storage'] = methane_storage_input
        
        investment_cost_vbox.children = [investment_headline, 
                                         anaerobic_label, anaerobic_input,
                                         biomethanation_label, biomethanation_input,
                                         co2_remover_label, co2_remover_input,
                                         electrolyzer_label, electrolyzer_input, 
                                         methane_storage_label, methane_storage_input
                                        ]


# Set capacities of units depending on type of product
capacities_vbox = widgets.VBox()
capacities_values = {}

def update_capacities(change, capacities_vbox):
    # Get selected product from the dropdown (methanol, ammonia, or jet_fuel)
    selected_product = change['new']
    
    # Clear existing capacity widgets (if any)
    capacities_vbox.children = []
    
    # Clear the capacities_values dictionary before updating
    capacities_values.clear()
    
    # Define the placeholder value for fields that are not yet interacted with
    placeholder_value = 1.0
    
    if selected_product == 'ammonia':        
        asu_label = widgets.Label("Air separation unit")
        asu_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        haber_label = widgets.Label("Haber-Bosch unit:")
        haber_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
                
        # Store values in investment dictionary
        capacities_values['capacity_asu'] = asu_input
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_haber'] = haber_input
        
        capacities_vbox.children = [asu_label, asu_input,
                                    electrolyzer_label, electrolyzer_input,
                                    haber_label, haber_input
                                   ]
    
    elif selected_product == 'egasoline':
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        fischer_label = widgets.Label("Fischer-Tropsch reactor:")
        fischer_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        rwgs_label = widgets.Label("RWGS reactor:")
        rwgs_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        # Store values in investment dictionary
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_fischer'] = fischer_input
        capacities_values['capacity_rwgs'] = rwgs_input
        
        capacities_vbox.children = [electrolyzer_label, electrolyzer_input,
                                    fischer_label, fischer_input,
                                    rwgs_label, rwgs_input
                                   ]
    
    elif selected_product == 'hydrogen':
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        # Store values in investment dictionary
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        
        capacities_vbox.children = [electrolyzer_label, electrolyzer_input]
    
    elif selected_product == 'jet_fuel':
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        fischer_label = widgets.Label("Fischer-Tropsch reactor:")
        fischer_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        rwgs_label = widgets.Label("RWGS reactor:")
        rwgs_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        # Store values in investment dictionary
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_fischer'] = fischer_input
        capacities_values['capacity_rwgs'] = rwgs_input
        
        capacities_vbox.children = [electrolyzer_label, electrolyzer_input,
                                    fischer_label, fischer_input,
                                    rwgs_label, rwgs_input
                                   ]
    
    elif selected_product == 'methanol':
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        methanol_label = widgets.Label("Methanol reactor:")
        methanol_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        steam_label = widgets.Label("Steam plant:")
        steam_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        # Store values in investment dictionary
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        capacities_values['capacity_methanol'] = methanol_input
        capacities_values['capacity_steam'] = steam_input
        
        capacities_vbox.children = [electrolyzer_label, electrolyzer_input,
                                    methanol_label, methanol_input,
                                    steam_label, steam_input
                                   ]
    
    elif selected_product == 'synthetic_methane_gas':
        anaerobic_label = widgets.Label("Anaerobic digestion plant:")
        anaerobic_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        biomethanation_label = widgets.Label("Biomethanation plant:")
        biomethanation_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        co2_remover_label = widgets.Label("CO2 removal plant:")
        co2_remover_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        electrolyzer_label = widgets.Label("Electrolyzer:")
        electrolyzer_input = widgets.FloatText(description="Capacity:", value=placeholder_value, min=0)
        
        # Store values in investment dictionary
        capacities_values['capacity_anaerobic'] = anaerobic_input
        capacities_values['capacity_biomethanation'] = biomethanation_input
        capacities_values['capacity_co2_removal'] = co2_remover_input
        capacities_values['capacity_electrolyzer'] = electrolyzer_input
        
        capacities_vbox.children = [anaerobic_label, anaerobic_input,
                                    biomethanation_label, biomethanation_input,
                                    co2_remover_label, co2_remover_input,
                                    electrolyzer_label, electrolyzer_input
                                    ]


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
    label1 = widgets.Label("Please select the base year:")
    dropdown1 = widgets.Dropdown(
        options=[2018, 2019, 2020, 2021, 2022],
        value=2019
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
        options = ['ammonia', 'egasoline', 'hydrogen', 'jet_fuel', 'methanol', 'synthetic_methane_gas'],
        value = None
    )
    def on_dropdown_change(change):
        update_inv_costs(change, investment_cost_vbox)  # Update investment costs box
        update_capacities(change, capacities_vbox)      # Update capacities box

    dropdown3.observe(on_dropdown_change, names='value')
    
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
        value='1h'
    )
    selected_option_widget = widgets.Label(dropdown5.value)
    selected_value_widget = widgets.Label(option_values[dropdown5.value])
    
    dropdown5.observe(on_change_dict, names='value')
    return widgets.VBox([label5, dropdown5]), selected_option_widget, selected_value_widget


#create dropdown for the whether or not roll_forward is used
roll_forward_use = True
def create_dropdown_roll():
    label6 = widgets.Label(
        "Please select whether or not the model should run with a rolling horizon optimization:"
    )
    dropdown6 = widgets.Dropdown(
        options=[True, False],
        value=False
    )
    dropdown6.observe(on_change)
    return widgets.VBox([label6, dropdown6]), dropdown6


#create dropdown for whether or not investments can be made
def create_dropdown_investment():
    
    label7 = widgets.Label("Please select whether or not the model should run an investment optimization:")
    dropdown7 = widgets.Dropdown(
        options=[True, False],
        value=False
    )
    dropdown7.observe(on_change)
    return widgets.VBox([label7, dropdown7]), dropdown7


# Create dropdown for the default investment period
def create_dropdown_invest_period():
    # Dictionary to map options to their corresponding values
    label8 = widgets.Label("Please select the investment period:")
    
    number_input_8 = widgets.BoundedIntText(
        value=1,
        min=1,
        max=30,
        step=1
    )
    number_input_8.observe(on_number_change, names='value')

    
    dropdown8 = widgets.Dropdown(
        options=['h', 'D', 'W', 'M', 'Q', 'Y'],
        value='Y'
    )

    dropdown8.observe(on_change)
    
    return widgets.VBox([label8, number_input_8, dropdown8]), number_input_8, dropdown8


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
    options_power = ['Solar plant', 'Wind onshore', 'Wind offshore']
    
    # Define preselected options
    preselected_options_power = {'Solar plant'}
    
    # Initialize selected_options_power with preselected options
    selected_options_power = set(preselected_options_power)
    
    # Separate options into preselected and non-preselected
    preselected_checks_power = [option for option in options_power if option in preselected_options_power]
    non_preselected_checks_power = [option for option in options_power if option not in preselected_options_power]
    
    checkboxes_powers = []
    
    # Initiate dictionary for the capacity of each option
    capacities_powers = {}
    capacities_powers_values = {}
    hbox_capacities_powers = []
    
    def on_change_MC_power(change, selected_options_power, checkbox):
        if checkbox.value:  # If checkbox is checked
            selected_options_power.add(checkbox.description)
        else:  # Remove the option if unchecked
            selected_options_power.discard(checkbox.description)
        update_capacity_fields()  
    
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
    
    # Create checkboxes for preselected options first
    for option in preselected_checks_power:
        checkbox = widgets.Checkbox(
            value=True,  # All preselected options should be checked
            description=option)
        checkbox.observe(lambda change, 
                         checkbox=checkbox: on_change_MC_power(change, selected_options_power, checkbox),
                         names='value')
        checkboxes_powers.append(checkbox)
    
    # Create checkboxes for non-preselected options
    for option in non_preselected_checks_power:
        checkbox = widgets.Checkbox(
            value=False,  # Non-preselected options should be unchecked
            description=option)
        checkbox.observe(lambda change, 
                         checkbox=checkbox: on_change_MC_power(change, selected_options_power, checkbox),
                         names='value')
        checkboxes_powers.append(checkbox)
    
    # Create capacity fields for each option (hidden initially):
    for option in options_power:
        capacity_widget = widgets.FloatText(
            value=1.0,
            layout=widgets.Layout(width='50%')
        )
        label = widgets.Label(f"{option} capacity (MW):")
        
        hbox = widgets.HBox([label, capacity_widget], layout=widgets.Layout(display='none'))
        capacities_powers[option] = hbox
        hbox_capacities_powers.append(hbox)
        
        capacities_powers_values[option] = capacity_widget.value
        capacity_widget.observe(lambda change, option=option: on_capacity_change(change, option), names='value')
    
    # Layout for checkboxes and capacity inputs
    power_column = widgets.VBox(checkboxes_powers)
    capacity_column = widgets.VBox(hbox_capacities_powers)
    
    #Update capacity fields visibiliy based on preselected options
    update_capacity_fields()
    
    return widgets.VBox([label_power, power_column, capacity_column]), selected_options_power, capacities_powers_values
  

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
            description=option
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
            description=option
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
    hbox_report = widgets.HBox(columns,
                        layout = widgets.Layout(overflow = 'hidden',
                                                justify_content = 'flex-start',
                                                width = '130%'
                                               ))
    
    label2 = widgets.Label("Please select the outputs for the report:")
    return widgets.VBox([label2, hbox_report]), selected_options_report



'''Define functions for the combined data definition menu'''

def create_combined_dropdowns_tabs():
    # Provide information for each section
    section_1 = widgets.HTML("<b>Section 1: Please define the parameters of the general model</b>")
    section_2 = widgets.HTML("<b>Section 2: Please define the base parameters</b>")
    section_3 = widgets.HTML("<b>Section 3: Please define the parameters of electrolysis</b>")
    section_4 = widgets.HTML("<b>Section 4: Please define the economic parameters of the general model</b>")
    section_5 = widgets.HTML("<b>Section 5: Please define the parameters for the investments</b>")
    section_6 = widgets.HTML("<b>Section 6: Please define the variables for the report</b>")
    section_7 = widgets.HTML("<b>Section 7: Please define the parameters for the different scenarios</b>")

    # Get the dropdown menus
    model_name_input_box, model_name_input = create_name_input()
    dropdown_year_vbox, dropdown_year = create_dropdown_year()
    dropdown_price_zone_vbox, dropdown_price_zone = create_dropdown_price_zone()
    dropdown_product_vbox, dropdown_product = create_dropdown_product()
    dropdown_electrolysis_vbox, dropdown_electrolysis = create_dropdown_electrolysis()
    dropdown_frequency_vbox, dropdown_frequency, dropdown_temporal = create_dropdown_frequency()
    number_dh_price_box, number_dh_price = create_share_of_dh_price_cap()
    number_price_level_power_box, number_price_level_power = create_price_level_power()
    power_price_variance_box, power_price_variance = create_power_price_variance()
    report_name_box, report_name = create_name_rep_input()
    multiple_choice_report_box, selected_reports = create_multiple_choice_report()
    multiple_choice_power_box, selected_powers, capacities_powers = create_multiple_choice_power()
    scen_name_box, base_scen = create_scen_name_input()
    #scen_name_box, base_scen, other_scen = create_scen_name_input_sev()
    stoch_scen_vbox, stoch_scen = create_stoch_scen_input()
    stoch_struc_vbox, stoch_struc = create_stoch_struc_input()
    dropdown_roll_vbox, dropdown_roll = create_dropdown_roll()
    number_slices_vbox, number_slices = create_number_opt_horizons()
    levels_elec_box, levels_elec = create_sections_elec()
    dropdown_investment_vbox, dropdown_investment = create_dropdown_investment()
    dropdown_period_vbox, dropdown_number, dropdown_period = create_dropdown_invest_period()
    
    # Store dropdowns in a dictionary
    dropdowns = {
        'name': model_name_input,
        'year': dropdown_year,
        'price_zone': dropdown_price_zone,
        'product': dropdown_product,
        'powers': selected_powers,
        'capacities_powers': capacities_powers,
        'electrolysis': dropdown_electrolysis,
        'frequency': dropdown_frequency,
        'temporal_block': dropdown_temporal,
        'number_dh_price_share': number_dh_price,
        'number_price_level_power': number_price_level_power,
        'power_price_variance': power_price_variance,
        'report_name': report_name,
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
        'default_investment_duration': dropdown_period
    }

    # Create pages (tabs)
    page1 = widgets.VBox([
        section_1, model_name_input_box, dropdown_frequency_vbox, dropdown_roll_vbox, number_slices_vbox
    ])
    
    page2 = widgets.VBox([
        section_2, multiple_choice_power_box, dropdown_product_vbox, capacities_vbox, dropdown_year_vbox, 
        dropdown_price_zone_vbox
    ])
    
    page3 = widgets.VBox([
        section_3, dropdown_electrolysis_vbox, levels_elec_box
    ])
    
    page4 = widgets.VBox([
        section_4, number_dh_price_box, number_price_level_power_box, power_price_variance_box
    ])
    
    page5 = widgets.VBox([
            section_5, dropdown_investment_vbox, dropdown_period_vbox, investment_cost_vbox
    ])

    page6 = widgets.VBox([
        section_6, scen_name_box, stoch_scen_vbox, stoch_struc_vbox
    ])

    page7 = widgets.VBox([
        section_7, report_name_box, multiple_choice_report_box
    ])  

    # Create Tab widget
    tabs = widgets.Tab()
    tabs.children = [page1, page2, page3, page4, page5, page6, page7]
    tabs.set_title(0, 'Model Base')
    tabs.set_title(1, 'Plant')
    tabs.set_title(2, 'Electrolysis')
    tabs.set_title(3, 'Economic')
    tabs.set_title(4, 'Investment')
    tabs.set_title(5, 'Scenario')
    tabs.set_title(6, 'Results')
    
    
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
        'model_name': dropdowns['name'].value,
        'year': dropdowns['year'].value,
        'price_zone': dropdowns['price_zone'].value,
        'product': dropdowns['product'].value,
        'electrolysis': dropdowns['electrolysis'].value,
        'frequency': dropdowns['frequency'].value,
        'temporal_block': dropdowns['temporal_block'].value,
        'roll_forward': dropdowns['roll_forward'].value,
        #'default_investment_period': dropdowns['default_investment_period'].value,
        'candidate_nonzero': dropdowns['candidate_nonzero'].value,
        'default_investment_number': dropdowns['default_investment_number'].value,
        'default_investment_duration': dropdowns['default_investment_duration'].value,
        
        # Numerical values (percent) adjusted
        'capacities_powers': dropdowns['capacities_powers'],
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
    
    # Removing the power capacities if unchanged
    for key, value in dropdowns['capacities_powers'].items():
        if value == 1:
            dropdowns['capacities_powers'][key] = None
    values['capacities_powers'] = dropdowns['capacities_powers']
    
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
    #investment costs
    if 'inv_cost_electrolyzer' in values:
        parameters['inv_cost_electrolyzer'] = values['inv_cost_electrolyzer']
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
    if 'inv_cost_egasoline_storage' in values:
        parameters['inv_cost_egasoline_storage'] = values['inv_cost_egasoline_storage']
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
    #capacities
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
    if 'capacity_steam' in values:
        parameters['capacity_steam'] = values['capacity_steam']
    if 'capacity_anaerobic' in values:
        parameters['capacity_anaerobic'] = values['capacity_anaerobic']
    if 'capacity_biomethanation' in values:
        parameters['capacity_biomethanation'] = values['capacity_biomethanation']
    if 'capacity_co2_removal' in values:
        parameters['capacity_co2_removal'] = values['capacity_co2_removal']
    #limits
    if 'inv_limit_electrolyzer' in values:
        parameters['inv_limit_electrolyzer'] = values['inv_limit_electrolyzer']
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
    if 'inv_limit_egasoline_storage' in values:
        parameters['inv_limit_egasoline_storage'] = values['inv_limit_egasoline_storage']
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
    if 'inv_limit_methanol_storage' in values:
        parameters['inv_limit_methanol_storage'] = values['inv_limit_methanol_storage']
    if 'inv_limit_rwgs' in values:
        parameters['inv_limit_rwgs'] = values['inv_limit_rwgs']
    if 'inv_limit_steam' in values:
        parameters['inv_limit_steam'] = values['inv_limit_steam']
    
    return parameters
    
