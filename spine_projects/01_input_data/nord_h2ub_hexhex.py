'''
This is the Energy Hub Model of CSEI, an Open-source Tool
for Sector Coupling technologies. Developed at the Copenhagen School of
Energy Infrastructure at the Copenhagen Business School.
---------------------------------------
File to define the import of packages for the main data prep script:
SPDX-FileCopyrightText: Johannes Giehl <jfg.eco@cbs.dk>
SPDX-FileCopyrightText: Dana Hentschel <djh.eco@cbs.dk>
SPDX-License-Identifier: GNU GENERAL PUBLIC LICENSE GPL 3.0
'''

'''Import packages function'''
def simsalabim():
    import sys
    import os
    import pandas as pd
    from datetime import timedelta
    import papermill as pm

    # Get the current directory of the Jupyter Notebook
    notebook_dir = os.getcwd()

    # Construct the path to the subfolder
    subfolder_path = os.path.join(notebook_dir, '00_functions')

    # Add the subfolder to the system path
    if subfolder_path not in sys.path:
        sys.path.append(subfolder_path)

    # Import custom functions from nord_h2ub_dropdown_functions
    try:
        from nord_h2ub_dropdown_functions import *
        print("Custom functions imported successfully.")
    except ImportError as e:
        print(f"Error importing custom functions: {e}")