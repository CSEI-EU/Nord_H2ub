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
    if change['type'] == 'change' and change['name'] == 'value':
        print(f'You selected: {change["new"]}')

def create_dropdown():
    dropdown = widgets.Dropdown(
        options=[1, 2, 3],
        value=1,
        description='Choose:',
    )
    dropdown.observe(on_change)
    return dropdown