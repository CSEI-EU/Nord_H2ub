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

import os
import subprocess

'''get path to the script'''

def get_script_path():
    """Returns the absolute path of the current script."""
    return os.path.abspath(os.path.dirname(__file__))

'''functions to get the correct path of the script'''

def find_folder_path(root_path, target_folder):
    """
    Finds the full path to a specified folder starting from the root path.

    Parameters:
        root_path (str): The root path where the search begins.
        target_folder (str): The name of the folder to find.

    Returns:
        str: The full path to the target folder, or None if not found.
    """
    # Normalize the root path
    norm_root_path = os.path.normpath(root_path)

    for root, dirs, files in os.walk(norm_root_path):
        if target_folder in dirs:
            return os.path.join(root, target_folder)

    # Return None if the target folder is not found
    return None


def combine_paths(common_folder='Documents'):
    """
    Combines the root part of the Nord_H2ub folder path up to a specified common folder with a new sub-path.
    
    """
    #assuming that the Nord_H2ub folder is saved on C:
    root_path = 'C:\\Users\\'
    target_folder = 'Nord_H2ub'

    folder_path = find_folder_path(root_path, target_folder)
    
    folder_path = folder_path
    new_sub_path = '\\GitHub\\Nord_H2ub\\spine_projects\\01_input_data\\'

    # Normalize the paths
    norm_folder_path = os.path.normpath(folder_path)
    norm_new_sub_path = os.path.normpath(new_sub_path)

    # Extract the root part of the current path up to and including the common folder
    common_folder_index = norm_folder_path.find(common_folder)
    if common_folder_index == -1:
        raise ValueError(f"The current path does not contain the '{common_folder}' folder")

    root_part = norm_folder_path[:common_folder_index + len(common_folder)]

    # Combine the root part with the new sub-path, excluding the leading backslash from the new sub-path
    combined_path = os.path.join(root_part, norm_new_sub_path.lstrip(os.sep))

    return combined_path

'''function to start a jupyter notebook'''

def start_specific_jupyter_notebook(notebook_relative_path):
    try:
        # Get the folder path to the script
        folder_path = combine_paths()
        
        # Construct the full path to the notebook
        notebook_full_path = os.path.join(folder_path, notebook_relative_path)
        
        # Start Jupyter Notebook and open the specified notebook
        subprocess.run(['jupyter', 'notebook', notebook_full_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

'''start'''

if __name__ == "__main__":
    # Replace 'relative/path/to/data_prep.ipynb' with the relative path to your notebook file
    notebook_relative_path = 'nord_h2ub_main.ipynb'
    start_specific_jupyter_notebook(notebook_relative_path)