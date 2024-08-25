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

'''Import packages'''

import sys
import os
import pandas as pd
from datetime import timedelta
import papermill as pm
#packages to shutdown the notebook and be able to continue in spinetoolbox
import time
import requests
from IPython.display import display, Javascript
import subprocess
import platform
import pickle
import sys


with open('sys_log.txt', 'w') as f:
    f.write(f"Current sys: {sys.executable}\n")


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

#function to save_and_shutdown
def avada_kedavra():
    # Shutdown the Jupyter server
    print("Shutting down the Jupyter server...")
    print("\033[1m\033[31mPlease accept leaving the page and go back to SpineToolbox\033[0m")
    
    # Pause to ensure saving and closing actions complete
    time.sleep(3)

    # Save the notebook
    print("Saving the notebook...")
    try:
        # Execute JavaScript to save the notebook
        display(Javascript('IPython.notebook.save_checkpoint()'))
        print("Notebook save requested.")
    except Exception as e:
        print(f"Error saving notebook: {e}")

    # Optionally, close the browser tab
    try:
        display(Javascript('window.close()'))
        print("Attempted to close the browser tab.")
    except Exception as e:
        print(f"Error closing browser tab: {e}")

    try:
        # Get the server URL and token from environment variables
        server_url = os.getenv('JUPYTER_SERVER_URL', 'http://localhost:8888')
        token = os.getenv('JUPYTER_TOKEN', 'your_token_here')
        
        # Send a request to shutdown the server
        response = requests.post(f'{server_url}/api/shutdown', headers={
            'Authorization': f'token {token}'
        })
        
        if response.status_code == 200:
            print("Jupyter server shutdown request sent successfully.")
        else:
            print(f"Failed to send shutdown request. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending shutdown request: {e}")

    # Ensure Jupyter server process is terminated
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "jupyter-notebook.exe"], check=True)
        else:
            subprocess.run(["pkill", "-f", "jupyter-notebook"], check=True)
        print("Jupyter server process terminated.")
    except Exception as e:
        print(f"Error terminating Jupyter server process: {e}")