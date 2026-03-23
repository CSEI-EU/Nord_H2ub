import pandas as pd

def get_district_heating_sheets(run_name):

    dh__definition = pd.DataFrame({
        "Object_name": ["pth_dummy_unit", "pth_dummy_node", "excess_heat", "excess_heat_exchanger", "heat_recovery", "dh_heat_exchanger"],
        "Category":    ["unit", "node", "node", "unit", "investment_group", "unit"]
    })

    dh__definition_parameters = pd.DataFrame({
        "Object_name": ["heat_recovery"],
        "Category":    ["investment_group"],
        "Parameter":   ["equal_investments"],
        "Value":       ["true"],
        "Alternative": [run_name]
    })

    dh__unit_inv_parameters = pd.DataFrame({
        "Object_name":                        ["pth_dummy_unit", "excess_heat_exchanger", "dh_heat_exchanger"],
        "unit_investment_variable_type":      ["unit_investment_variable_type_continuous", "unit_investment_variable_type_continuous", "unit_investment_variable_type_continuous"],
        "initial_units_invested_available":   [0, 0, 0],
        "number_of_units":                    [0, 0, 0],
        "candidate_units":                    [1, 1, 1],
        "unit_investment_cost":               [0, 1083333.333, 0],
        "unit_investment_tech_lifetime":      ["10950D", "10950D", "10950D"],
        "unit_investment_econ_lifetime":      ["10950D", "10950D", "10950D"],
        "Alternative":                        [run_name, run_name, run_name]
    })

    df__nodes = pd.DataFrame({
        "Object_name":          ["pth_dummy_node", "excess_heat"],
        "Category":             ["node", "node"],
        "balance_type":         ["balance_type_node", "balance_type_node"],
        "Alternative":          [run_name, run_name],
        "nodal_balance_sense":  [None, ">="],
        "has_state":            [None, None],
        "node_state_cap":       [None, None],
        "frac_state_loss":      [None, None],
        "demand":               [None, None],
        "node_slack_penalty":   [100000000, 100000000]
    })

    dh__object__to_from_node_definition = pd.DataFrame({
        "Relationship_class_name": ["unit__to_node", "unit__from_node", "unit__to_node", "unit__from_node", "unit__to_node", "unit__from_node", "unit__investment_group", "unit__investment_group"],
        "Object_class":            ["unit", "unit", "unit", "unit", "unit", "unit", "unit", "unit"],
        "Object_name":             ["pth_dummy_unit", "pth_dummy_unit", "excess_heat_exchanger", "excess_heat_exchanger", "dh_heat_exchanger", "dh_heat_exchanger", "steam_plant", "excess_heat_exchanger"],
        "object_to_from":          ["node", "node", "node", "node", "node", "node", "investment_group", "investment_group"],
        "object_to_from_name":     ["pth_dummy_node", "power", "pth_dummy_node", "excess_heat", "heat", "excess_heat", "heat_recovery", "heat_recovery"]
    })

    dh__object__to_from_node = pd.DataFrame({
        "Relationship_class_name": ["unit__to_node"],
        "Object_class":            ["unit"],
        "Object_name":             ["excess_heat_exchanger"],
        "object_to_from":          ["node"],
        "object_to_from_name":     ["pth_dummy_node"],
        "Parameter":               ["unit_capacity"],
        "Value":                   [500],
        "Alternative":             [run_name]
    })

    dh__object__node_node_def = pd.DataFrame({
        "Relationship":    ["unit__node__node", "unit__node__node", "unit__node__node", "unit__node__node", "unit__node__node", "unit__node__node", "unit__node__node", "unit__to_node__investment_group", "unit__from_node__investment_group"],
        "Object_class_1":  ["unit", "unit", "unit", "unit", "unit", "unit", "unit", "unit", "unit"],
        "Object_name_1":   ["steam_plant", "steam_plant", "electrolyzer", "ch3oh_reactor", "pth_dummy_unit", "excess_heat_exchanger", "dh_heat_exchanger", "excess_heat_exchanger", "steam_plant"],
        "Object_class_2":  ["node", "node", "node", "node", "node", "node", "node", "node", "node"],
        "Object_name_2":   ["pth_dummy_node", "pth_dummy_node", "h2", "raw_ch3oh", "power", "excess_heat", "excess_heat", "pth_dummy_node", "pth_dummy_node"],
        "Object_class_3":  ["node", "node", "node", "node", "node", "node", "node", "investment_group", "investment_group"],
        "Object_name_3":   ["water", "steam", "excess_heat", "excess_heat", "pth_dummy_node", "pth_dummy_node", "heat", "heat_recovery", "heat_recovery"]
    })

    dh__object__node_node = pd.DataFrame({
        "Relationship": ["unit__node__node", "unit__node__node", "unit__node__node", "unit__node__node", "unit__node__node", "unit__node__node", "unit__node__node"],
        "Object_class": ["unit", "unit", "unit", "unit", "unit", "unit", "unit"],
        "Object_name":  ["steam_plant", "steam_plant", "electrolyzer", "ch3oh_reactor", "pth_dummy_unit", "excess_heat_exchanger", "dh_heat_exchanger"],
        "Node1":        ["pth_dummy_node", "pth_dummy_node", "h2", "raw_ch3oh", "power", "excess_heat", "excess_heat"],
        "Node2":        ["water", "steam", "excess_heat", "excess_heat", "pth_dummy_node", "pth_dummy_node", "heat"],
        "Parameter":    ["fix_ratio_in_in_unit_flow", "fix_ratio_in_out_unit_flow", "fix_ratio_out_out_unit_flow", "fix_ratio_out_out_unit_flow", "fix_ratio_in_out_unit_flow", "fix_ratio_in_out_unit_flow", "fix_ratio_in_out_unit_flow"],
        "Value":        [0.000724378, 0.99, 1.76, 4.32, 1, 10, 1],
        "Alternative":  [run_name, run_name, run_name, run_name, run_name, run_name, run_name]
    })

    dh_sheets_mapping = {
        "Definition":                       dh__definition,
        "Definition_parameters":            dh__definition_parameters,
        "Unit_inv_parameters":              dh__unit_inv_parameters,
        "Nodes":                            df__nodes,
        "Object__to_from_node_definition":  dh__object__to_from_node_definition,
        "Object__to_from_node":             dh__object__to_from_node,
        "Object__node_node_def":            dh__object__node_node_def,
        "Object__node_node":                dh__object__node_node
    }

    return dh_sheets_mapping