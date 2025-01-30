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

#packages to shutdown the notebook and be able to continue in spinetoolbox
import time
import requests
from IPython.display import display, Javascript
import subprocess
import platform
import pickle
import os

#find correct folder
def get_base_path():
    current_dir = os.getcwd()
    while current_dir:
        if os.path.basename(current_dir) == "Nord_H2ub":
            return current_dir
        directory = os.path.dirname(current_dir)
        if directory == current_dir:
            break
        current_dir = directory
    raise FileNotFoundError("The base directory 'Nord_H2ub' was not found.")

def present_value_factor(n, r):
    """
    Calculate the present value factor of an annuity (Rentenbarwertfaktor).

    Parameters:
    n (int): The number of periods (time horizon).
    r (float): The discount rate (WACC).

    Returns:
    float: The present value factor of the annuity.
    """
    if r == 0:
        return n
    else:
        return (1 - (1 + r) ** -n) / r

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