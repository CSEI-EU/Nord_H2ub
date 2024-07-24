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
from jupyter_dash import JupyterDash
from dash import dcc, html

'''create the dashboard'''

def create_dash_app():
    # Initialize Dash app
    app = JupyterDash(__name__)

    # Define the layout of the app with class names for styling
    app.layout = html.Div([
        dcc.Tabs([
            dcc.Tab(label='General Model Parameters', children=[
                html.Div([
                    html.H3('Section 1: Please define the parameters of the general model'),
                    html.Div([
                        html.Label('Model Name:', className='input-label'),
                        dcc.Input(id='model-name', type='text', placeholder='Model Name')
                    ]),
                    html.Div([
                        html.Label('Select Frequency:', className='dropdown-label'),
                        dcc.Dropdown(id='dropdown-frequency', className='dropdown-menu', options=[
                            {'label': 'Option 1', 'value': '1'},
                            {'label': 'Option 2', 'value': '2'}
                        ], placeholder='Select Frequency')
                    ]),
                    html.Div([
                        html.Label('Select Roll:', className='dropdown-label'),
                        dcc.Dropdown(id='dropdown-roll', className='dropdown-menu', options=[
                            {'label': 'Option 1', 'value': '1'},
                            {'label': 'Option 2', 'value': '2'}
                        ], placeholder='Select Roll')
                    ]),
                    html.Div([
                        html.Label('Number of Slices:', className='input-label'),
                        dcc.Input(id='number-slices', type='number', placeholder='Number of Slices')
                    ])
                ])
            ]),
            dcc.Tab(label='Base Parameters', children=[
                html.Div([
                    html.H3('Section 2: Please define the base parameters'),
                    html.Div([
                        html.Label('Select Year:', className='dropdown-label'),
                        dcc.Dropdown(id='dropdown-year', className='dropdown-menu', options=[
                            {'label': '2020', 'value': '2020'},
                            {'label': '2021', 'value': '2021'}
                        ], placeholder='Select Year')
                    ]),
                    html.Div([
                        html.Label('Select Price Zone:', className='dropdown-label'),
                        dcc.Dropdown(id='dropdown-price-zone', className='dropdown-menu', options=[
                            {'label': 'Zone 1', 'value': '1'},
                            {'label': 'Zone 2', 'value': '2'}
                        ], placeholder='Select Price Zone')
                    ]),
                    html.Div([
                        html.Label('Select Product:', className='dropdown-label'),
                        dcc.Dropdown(id='dropdown-product', className='dropdown-menu', options=[
                            {'label': 'Product 1', 'value': '1'},
                            {'label': 'Product 2', 'value': '2'}
                        ], placeholder='Select Product')
                    ])
                ])
            ]),
            dcc.Tab(label='Electrolysis Parameters', children=[
                html.Div([
                    html.H3('Section 3: Please define the parameters of electrolysis'),
                    html.Div([
                        html.Label('Select Electrolysis:', className='dropdown-label'),
                        dcc.Dropdown(id='dropdown-electrolysis', className='dropdown-menu', options=[
                            {'label': 'Electrolysis 1', 'value': '1'},
                            {'label': 'Electrolysis 2', 'value': '2'}
                        ], placeholder='Select Electrolysis')
                    ]),
                    html.Div([
                        html.Label('Levels of Electrolysis:', className='input-label'),
                        dcc.Input(id='levels-elec', type='number', placeholder='Levels of Electrolysis')
                    ])
                ])
            ]),
            dcc.Tab(label='Economic Parameters', children=[
                html.Div([
                    html.H3('Section 4: Please define the economic parameters of the general model'),
                    html.Div([
                        html.Label('Share of DH Price Cap:', className='input-label'),
                        dcc.Input(id='number-dh-price-share', type='number', placeholder='Share of DH Price Cap')
                    ]),
                    html.Div([
                        html.Label('Price Level Power:', className='input-label'),
                        dcc.Input(id='number-price-level-power', type='number', placeholder='Price Level Power')
                    ]),
                    html.Div([
                        html.Label('Power Price Variance:', className='input-label'),
                        dcc.Input(id='power-price-variance', type='number', placeholder='Power Price Variance')
                    ])
                ])
            ]),
            dcc.Tab(label='Report', children=[
                html.Div([
                    html.H3('Section 5: Please define the variables for the report'),
                    html.Div([
                        html.Label('Report Name:', className='input-label'),
                        dcc.Input(id='report-name', type='text', placeholder='Report Name')
                    ]),
                    html.Div([
                        html.Label('Select Report Options:', className='dropdown-label'),
                        dcc.Checklist(id='multiple-choice-report', options=[
                            {'label': 'Option 1', 'value': '1'},
                            {'label': 'Option 2', 'value': '2'}
                        ], inline=True)
                    ])
                ])
            ]),
            dcc.Tab(label='Scenarios', children=[
                html.Div([
                    html.H3('Section 6: Please define the parameters for the different scenarios'),
                    html.Div([
                        html.Label('Scenario Name:', className='input-label'),
                        dcc.Input(id='scen-name', type='text', placeholder='Scenario Name')
                    ]),
                    html.Div([
                        html.Label('Select Stochastic Scenario:', className='dropdown-label'),
                        dcc.Dropdown(id='stoch-scen', className='dropdown-menu', options=[
                            {'label': 'Scenario 1', 'value': '1'},
                            {'label': 'Scenario 2', 'value': '2'}
                        ], placeholder='Select Stochastic Scenario')
                    ]),
                    html.Div([
                        html.Label('Select Stochastic Structure:', className='dropdown-label'),
                        dcc.Dropdown(id='stoch-struc', className='dropdown-menu', options=[
                            {'label': 'Structure 1', 'value': '1'},
                            {'label': 'Structure 2', 'value': '2'}
                        ], placeholder='Select Stochastic Structure')
                    ])
                ])
            ])
        ])
    ])

    # Return the app object
    return app

# To run the app in a Jupyter notebook, use the following code:
app = create_dash_app()
app.run_server(mode='inline', debug=True)


