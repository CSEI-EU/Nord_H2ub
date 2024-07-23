'''
This is the Energy Hub Model of CSEI, an Open-source Tool
for Sector Coupling technologies. Developed at the Copenhagen School of
Energy Infrastructure at the Copenhagen Business School.
---------------------------------------
Functions File for Data Prep:
The functions include the logical prossecing, mathematical calculation
logic for the preparation of the input data file for the model runs.
SPDX-FileCopyrightText: Johannes Giehl <jfg.eco@cbs.dk>
SPDX-License-Identifier: GNU GENERAL PUBLIC LICENSE GPL 3.0
'''

'''import packages'''

import subprocess

'''function to start a jupyter notebook'''

def start_specific_jupyter_notebook(notebook_path):
    try:
        # Start Jupyter Notebook and open the specified notebook
        subprocess.run(['jupyter', 'notebook', notebook_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

'''start'''

if __name__ == "__main__":
    # Replace 'data_prep.ipynb' with the path to your notebook file
    start_specific_jupyter_notebook('C://Users//jfg.eco//Documents//GitHub//Nord_H2ub//spine_projects//01_input_data//master_notebook_test.ipynb')