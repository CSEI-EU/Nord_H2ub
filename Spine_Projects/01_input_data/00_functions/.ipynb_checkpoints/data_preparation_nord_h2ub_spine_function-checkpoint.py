{
 "cells": [
  {
   "cell_type": "markdown",
   "id": "43ea4b8f-0ba4-4513-8872-53f4a538a0d3",
   "metadata": {},
   "source": [
    "# Data Preparation for the Nord_H2ub Spine Model"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "1aa86773-4431-4a2f-9490-4b3cf0aa8d70",
   "metadata": {},
   "source": [
    "This jupyter notebook contains all routines for the preparation of the input data sources into a input data file for the model in Spine. \n",
    "\n",
    "**Authors:** Johannes Giehl (jfg.eco@cbs.dk), Dana Hentschel (djh.eco@cbs.dk)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "eb8175ae-f246-4788-a309-c1a4890992f2",
   "metadata": {},
   "source": [
    "## General settings"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "5bc68f78-3383-4889-bd9e-8b3e3e2f6c2e",
   "metadata": {},
   "source": [
    "### Packages:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "f8f47a1c-073f-46c0-8a4d-7dafb1716b9b",
   "metadata": {},
   "outputs": [],
   "source": [
    "import numpy as np\n",
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "from datetime import timedelta\n",
    "import math\n",
    "import sys\n",
    "import os"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "92141795-3716-404e-8e35-a096dcaa0c40",
   "metadata": {},
   "source": [
    "### Methods:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "id": "23418a81-7e7c-47c4-afc1-805a5eb7aed1",
   "metadata": {},
   "outputs": [],
   "source": [
    "#import the data preparation functions\n",
    "# Determine the current working directory\n",
    "current_working_dir = os.getcwd()\n",
    "\n",
    "# Set the module path (adjust the relative path if necessary)\n",
    "module_path = os.path.abspath(os.path.join(current_working_dir, '00_functions'))\n",
    "if module_path not in sys.path:\n",
    "    sys.path.append(module_path)\n",
    "\n",
    "#load the functions and methods from the corresponding file\n",
    "from nord_h2ub_data_preparation_functions import *\n",
    "from nord_h2ub_data_preparation_main_functions import *"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "3e50630f-868b-40f0-842e-c74d936b5d54",
   "metadata": {},
   "source": [
    "### Base parameters"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "acd9578f-5900-4581-bf5f-40d6d2661f9b",
   "metadata": {},
   "outputs": [],
   "source": [
    "parameters = {\n",
    "    'year': 2020,   \n",
    "    'area': 'DK1',   \n",
    "    'product': 'methanol', \n",
    "    'scenario': 'Base',\n",
    "    'frequency': '1h',\n",
    "    'model_name': 'Energy_Hub_Model',\n",
    "    'temporal_block': 'hourly',\n",
    "    'stochastic_scenario': \"realisation\",\n",
    "    'stochastic_structure': \"deterministic\",\n",
    "    'report_name': 'Report',\n",
    "    'reports': ['unit_flow', 'connection_flow', 'node_state', 'total_costs', 'unit_flow_op', 'node_slack_neg', 'node_slack_pos'],\n",
    "    'electrolyzer_type': \"Alkaline\",   \n",
    "    'des_segments_electrolyzer': 3,  \n",
    "    'share_of_dh_price_cap': 0.5,\n",
    "    'price_level_power': 1,\n",
    "    'power_price_variance': 1,\n",
    "    'roll_forward_use': True,\n",
    "    'num_slices': 12,\n",
    "}"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "id": "9e407f75-4ba7-4355-8b0a-9204c78e7334",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "\u001b[91mWARNING:\u001b[0m Please control if all the parameters are set correctly\n"
     ]
    }
   ],
   "source": [
    "#set all the model variables\n",
    "#this is relevant for the input from the user drop down value definition\n",
    "(year, start_date, end_date, area, product, scenario, frequency, \n",
    "    model_name,temporal_block, stochastic_scenario, stochastic_structure,\n",
    "    report_name, reports,\n",
    "    electrolyzer_type, des_segments_electrolyzer,\n",
    "    share_of_dh_price_cap, price_level_power, power_price_variance,\n",
    "    roll_forward_use, num_slices, datetime_index) = set_parameters(parameters)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "id": "43a9ee61-1183-4d91-918f-dcebc53122dc",
   "metadata": {},
   "outputs": [],
   "source": [
    "#calculate the size of the roll-forward horizons\n",
    "roll_forward_size = calculate_opt_horizons(datetime_index, num_slices)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "id": "e9af8e78-fedd-4bd5-8328-4587c1228e6c",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Set the default investment period\n",
    "investment_period_default = '1Y'"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "4c56b541-1fbd-4e7e-9cf3-2ff25f8da472",
   "metadata": {},
   "source": [
    "### File paths"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "id": "5b811bdc-ac7b-4cd7-8e32-8f84bda412a2",
   "metadata": {},
   "outputs": [],
   "source": [
    "#set path to correct folders\n",
    "'''still not working if it is not started from this jupyter notebook'''\n",
    "#input data\n",
    "excel_file_path = get_excel_file_path() + '/01_input_raw/'\n",
    "#prepared input data\n",
    "output_file_path = get_excel_file_path() + '/02_input_prepared/'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "id": "89169e64-f204-47bb-9a83-17156a4aefa8",
   "metadata": {},
   "outputs": [],
   "source": [
    "#set name of the relevant files\n",
    "\n",
    "Model_structure_file = '/Model_Data_Base.xlsx'\n",
    "efficiency_electrolyzer_file = '/Efficiency_Electrolyzers.xlsx'\n",
    "distric_heating_price_file = 'energy_prices/district_heating_price_cap.xlsx'\n",
    "investment_costs_file = '/Investment_cost_overview.xlsx'\n",
    "mapping_file = '/methanol_object_mapping.xlsx'\n",
    "\n",
    "PV_data_availabilityfactors = 'PV_availability_factors_Kasso.xlsx'\n",
    "data_powerprices = 'Day_ahead_prices_' + str(year) + '.xlsx'\n",
    "\n",
    "#output file\n",
    "output_file_name = product + '_Input_prepared.xlsx'\n",
    "output_mapping_file_name = product + '_object_mapping.xlsx'"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "86d15fe8-064f-4c28-be28-8d924a4ba31b",
   "metadata": {},
   "source": [
    "\n",
    "## Workflow of the data preparation"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "ef6ad49f-470e-4b29-aa02-c7babb08befb",
   "metadata": {},
   "source": [
    "### General parameters"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "id": "c50f50c3-e43d-41c2-8158-75596632213b",
   "metadata": {},
   "outputs": [],
   "source": [
    "#date index\n",
    "date_index = pd.date_range(start=start_date, end=end_date, freq='h')\n",
    "formatted_dates = date_index.strftime('%Y-%m-%dT%H:%M:%S')\n",
    "df_formatted_dates = pd.DataFrame(formatted_dates, columns=['DateTime'])\n",
    "\n",
    "df_time = pd.DataFrame(df_formatted_dates)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "88fb746a-7cd3-4655-88cf-ac543b003918",
   "metadata": {},
   "source": [
    "### Data import"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 10,
   "id": "a42c5077-74ef-4f63-b6d9-4aa3c11aa878",
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "C:\\Users\\luc.eco\\AppData\\Local\\anaconda3\\Lib\\site-packages\\openpyxl\\worksheet\\_read_only.py:79: UserWarning: Data Validation extension is not supported and will be removed\n",
      "  for idx, row in parser.parse():\n",
      "C:\\Users\\luc.eco\\AppData\\Local\\anaconda3\\Lib\\site-packages\\openpyxl\\worksheet\\_read_only.py:79: UserWarning: Data Validation extension is not supported and will be removed\n",
      "  for idx, row in parser.parse():\n",
      "C:\\Users\\luc.eco\\AppData\\Local\\anaconda3\\Lib\\site-packages\\openpyxl\\worksheet\\_read_only.py:79: UserWarning: Data Validation extension is not supported and will be removed\n",
      "  for idx, row in parser.parse():\n"
     ]
    },
    {
     "ename": "FileNotFoundError",
     "evalue": "[Errno 2] No such file or directory: 'C:/Users/luc.eco/OneDrive - CBS - Copenhagen Business School/Documents/GitHub/Nord_H2ub/Spine_Projects/01_input_data/01_input_raw/methanol/Investment_cost_overview.xlsx'",
     "output_type": "error",
     "traceback": [
      "\u001b[1;31m---------------------------------------------------------------------------\u001b[0m",
      "\u001b[1;31mFileNotFoundError\u001b[0m                         Traceback (most recent call last)",
      "Cell \u001b[1;32mIn[10], line 17\u001b[0m\n\u001b[0;32m     15\u001b[0m df_district_heating_price \u001b[38;5;241m=\u001b[39m pd\u001b[38;5;241m.\u001b[39mread_excel(excel_file_path \u001b[38;5;241m+\u001b[39m distric_heating_price_file, sheet_name\u001b[38;5;241m=\u001b[39m\u001b[38;5;124m'\u001b[39m\u001b[38;5;124mPrice_Cap_Calculation\u001b[39m\u001b[38;5;124m'\u001b[39m, index_col\u001b[38;5;241m=\u001b[39m\u001b[38;5;28;01mNone\u001b[39;00m)\n\u001b[0;32m     16\u001b[0m \u001b[38;5;66;03m#Investment costs\u001b[39;00m\n\u001b[1;32m---> 17\u001b[0m df_investment_costs_raw \u001b[38;5;241m=\u001b[39m pd\u001b[38;5;241m.\u001b[39mread_excel(excel_file_path \u001b[38;5;241m+\u001b[39m product \u001b[38;5;241m+\u001b[39m investment_costs_file, sheet_name\u001b[38;5;241m=\u001b[39m\u001b[38;5;124m'\u001b[39m\u001b[38;5;124mInvestment_Cost\u001b[39m\u001b[38;5;124m'\u001b[39m, index_col\u001b[38;5;241m=\u001b[39m\u001b[38;5;28;01mNone\u001b[39;00m)\n\u001b[0;32m     18\u001b[0m \u001b[38;5;66;03m#Mapping between entity and parameter name\u001b[39;00m\n\u001b[0;32m     19\u001b[0m df_mapping \u001b[38;5;241m=\u001b[39m pd\u001b[38;5;241m.\u001b[39mread_excel(excel_file_path \u001b[38;5;241m+\u001b[39m product \u001b[38;5;241m+\u001b[39m mapping_file, sheet_name\u001b[38;5;241m=\u001b[39m\u001b[38;5;124m'\u001b[39m\u001b[38;5;124mObject_Mapping\u001b[39m\u001b[38;5;124m'\u001b[39m, index_col\u001b[38;5;241m=\u001b[39m\u001b[38;5;28;01mNone\u001b[39;00m)\n",
      "File \u001b[1;32m~\\AppData\\Local\\anaconda3\\Lib\\site-packages\\pandas\\io\\excel\\_base.py:504\u001b[0m, in \u001b[0;36mread_excel\u001b[1;34m(io, sheet_name, header, names, index_col, usecols, dtype, engine, converters, true_values, false_values, skiprows, nrows, na_values, keep_default_na, na_filter, verbose, parse_dates, date_parser, date_format, thousands, decimal, comment, skipfooter, storage_options, dtype_backend, engine_kwargs)\u001b[0m\n\u001b[0;32m    502\u001b[0m \u001b[38;5;28;01mif\u001b[39;00m \u001b[38;5;129;01mnot\u001b[39;00m \u001b[38;5;28misinstance\u001b[39m(io, ExcelFile):\n\u001b[0;32m    503\u001b[0m     should_close \u001b[38;5;241m=\u001b[39m \u001b[38;5;28;01mTrue\u001b[39;00m\n\u001b[1;32m--> 504\u001b[0m     io \u001b[38;5;241m=\u001b[39m ExcelFile(\n\u001b[0;32m    505\u001b[0m         io,\n\u001b[0;32m    506\u001b[0m         storage_options\u001b[38;5;241m=\u001b[39mstorage_options,\n\u001b[0;32m    507\u001b[0m         engine\u001b[38;5;241m=\u001b[39mengine,\n\u001b[0;32m    508\u001b[0m         engine_kwargs\u001b[38;5;241m=\u001b[39mengine_kwargs,\n\u001b[0;32m    509\u001b[0m     )\n\u001b[0;32m    510\u001b[0m \u001b[38;5;28;01melif\u001b[39;00m engine \u001b[38;5;129;01mand\u001b[39;00m engine \u001b[38;5;241m!=\u001b[39m io\u001b[38;5;241m.\u001b[39mengine:\n\u001b[0;32m    511\u001b[0m     \u001b[38;5;28;01mraise\u001b[39;00m \u001b[38;5;167;01mValueError\u001b[39;00m(\n\u001b[0;32m    512\u001b[0m         \u001b[38;5;124m\"\u001b[39m\u001b[38;5;124mEngine should not be specified when passing \u001b[39m\u001b[38;5;124m\"\u001b[39m\n\u001b[0;32m    513\u001b[0m         \u001b[38;5;124m\"\u001b[39m\u001b[38;5;124man ExcelFile - ExcelFile already has the engine set\u001b[39m\u001b[38;5;124m\"\u001b[39m\n\u001b[0;32m    514\u001b[0m     )\n",
      "File \u001b[1;32m~\\AppData\\Local\\anaconda3\\Lib\\site-packages\\pandas\\io\\excel\\_base.py:1563\u001b[0m, in \u001b[0;36mExcelFile.__init__\u001b[1;34m(self, path_or_buffer, engine, storage_options, engine_kwargs)\u001b[0m\n\u001b[0;32m   1561\u001b[0m     ext \u001b[38;5;241m=\u001b[39m \u001b[38;5;124m\"\u001b[39m\u001b[38;5;124mxls\u001b[39m\u001b[38;5;124m\"\u001b[39m\n\u001b[0;32m   1562\u001b[0m \u001b[38;5;28;01melse\u001b[39;00m:\n\u001b[1;32m-> 1563\u001b[0m     ext \u001b[38;5;241m=\u001b[39m inspect_excel_format(\n\u001b[0;32m   1564\u001b[0m         content_or_path\u001b[38;5;241m=\u001b[39mpath_or_buffer, storage_options\u001b[38;5;241m=\u001b[39mstorage_options\n\u001b[0;32m   1565\u001b[0m     )\n\u001b[0;32m   1566\u001b[0m     \u001b[38;5;28;01mif\u001b[39;00m ext \u001b[38;5;129;01mis\u001b[39;00m \u001b[38;5;28;01mNone\u001b[39;00m:\n\u001b[0;32m   1567\u001b[0m         \u001b[38;5;28;01mraise\u001b[39;00m \u001b[38;5;167;01mValueError\u001b[39;00m(\n\u001b[0;32m   1568\u001b[0m             \u001b[38;5;124m\"\u001b[39m\u001b[38;5;124mExcel file format cannot be determined, you must specify \u001b[39m\u001b[38;5;124m\"\u001b[39m\n\u001b[0;32m   1569\u001b[0m             \u001b[38;5;124m\"\u001b[39m\u001b[38;5;124man engine manually.\u001b[39m\u001b[38;5;124m\"\u001b[39m\n\u001b[0;32m   1570\u001b[0m         )\n",
      "File \u001b[1;32m~\\AppData\\Local\\anaconda3\\Lib\\site-packages\\pandas\\io\\excel\\_base.py:1419\u001b[0m, in \u001b[0;36minspect_excel_format\u001b[1;34m(content_or_path, storage_options)\u001b[0m\n\u001b[0;32m   1416\u001b[0m \u001b[38;5;28;01mif\u001b[39;00m \u001b[38;5;28misinstance\u001b[39m(content_or_path, \u001b[38;5;28mbytes\u001b[39m):\n\u001b[0;32m   1417\u001b[0m     content_or_path \u001b[38;5;241m=\u001b[39m BytesIO(content_or_path)\n\u001b[1;32m-> 1419\u001b[0m \u001b[38;5;28;01mwith\u001b[39;00m get_handle(\n\u001b[0;32m   1420\u001b[0m     content_or_path, \u001b[38;5;124m\"\u001b[39m\u001b[38;5;124mrb\u001b[39m\u001b[38;5;124m\"\u001b[39m, storage_options\u001b[38;5;241m=\u001b[39mstorage_options, is_text\u001b[38;5;241m=\u001b[39m\u001b[38;5;28;01mFalse\u001b[39;00m\n\u001b[0;32m   1421\u001b[0m ) \u001b[38;5;28;01mas\u001b[39;00m handle:\n\u001b[0;32m   1422\u001b[0m     stream \u001b[38;5;241m=\u001b[39m handle\u001b[38;5;241m.\u001b[39mhandle\n\u001b[0;32m   1423\u001b[0m     stream\u001b[38;5;241m.\u001b[39mseek(\u001b[38;5;241m0\u001b[39m)\n",
      "File \u001b[1;32m~\\AppData\\Local\\anaconda3\\Lib\\site-packages\\pandas\\io\\common.py:872\u001b[0m, in \u001b[0;36mget_handle\u001b[1;34m(path_or_buf, mode, encoding, compression, memory_map, is_text, errors, storage_options)\u001b[0m\n\u001b[0;32m    863\u001b[0m         handle \u001b[38;5;241m=\u001b[39m \u001b[38;5;28mopen\u001b[39m(\n\u001b[0;32m    864\u001b[0m             handle,\n\u001b[0;32m    865\u001b[0m             ioargs\u001b[38;5;241m.\u001b[39mmode,\n\u001b[1;32m   (...)\u001b[0m\n\u001b[0;32m    868\u001b[0m             newline\u001b[38;5;241m=\u001b[39m\u001b[38;5;124m\"\u001b[39m\u001b[38;5;124m\"\u001b[39m,\n\u001b[0;32m    869\u001b[0m         )\n\u001b[0;32m    870\u001b[0m     \u001b[38;5;28;01melse\u001b[39;00m:\n\u001b[0;32m    871\u001b[0m         \u001b[38;5;66;03m# Binary mode\u001b[39;00m\n\u001b[1;32m--> 872\u001b[0m         handle \u001b[38;5;241m=\u001b[39m \u001b[38;5;28mopen\u001b[39m(handle, ioargs\u001b[38;5;241m.\u001b[39mmode)\n\u001b[0;32m    873\u001b[0m     handles\u001b[38;5;241m.\u001b[39mappend(handle)\n\u001b[0;32m    875\u001b[0m \u001b[38;5;66;03m# Convert BytesIO or file objects passed with an encoding\u001b[39;00m\n",
      "\u001b[1;31mFileNotFoundError\u001b[0m: [Errno 2] No such file or directory: 'C:/Users/luc.eco/OneDrive - CBS - Copenhagen Business School/Documents/GitHub/Nord_H2ub/Spine_Projects/01_input_data/01_input_raw/methanol/Investment_cost_overview.xlsx'"
     ]
    }
   ],
   "source": [
    "#read in the model structure from a new excel\n",
    "df_model_units_raw = pd.read_excel(excel_file_path + product + Model_structure_file, sheet_name='Units', index_col=None)\n",
    "df_model_connections_raw = pd.read_excel(excel_file_path + product + Model_structure_file, sheet_name='Connections', index_col=None)\n",
    "df_model_storages_raw = pd.read_excel(excel_file_path + product + Model_structure_file, sheet_name='Storages', index_col=None)\n",
    "#Variable efficiency\n",
    "df_efficiency_electrolyzer = pd.read_excel(excel_file_path + product + efficiency_electrolyzer_file, sheet_name='Efficiency_'+electrolyzer_type)\n",
    "#Availability factor\n",
    "df_PV_availabilityfactors_values = pd.read_excel(excel_file_path+PV_data_availabilityfactors, skiprows=2, usecols=[0,1,2,3,4,5])\n",
    "#Power prices\n",
    "df_powerprices_total_values = pd.read_excel(excel_file_path+data_powerprices)\n",
    "#only extracting the prices from our earlier defined area\n",
    "df_powerprices_values = df_powerprices_total_values[df_powerprices_total_values['PriceArea'] == area]\n",
    "df_powerprices_values = df_powerprices_values.reset_index(drop=True)\n",
    "#district heating prices\n",
    "df_district_heating_price = pd.read_excel(excel_file_path + distric_heating_price_file, sheet_name='Price_Cap_Calculation', index_col=None)\n",
    "#Investment costs\n",
    "df_investment_costs_raw = pd.read_excel(excel_file_path + product + investment_costs_file, sheet_name='Investment_Cost', index_col=None)\n",
    "#Mapping between entity and parameter name\n",
    "df_mapping = pd.read_excel(excel_file_path + product + mapping_file, sheet_name='Object_Mapping', index_col=None)\n"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "c2693fc2-fe36-47a1-9b08-00f73dd53b9f",
   "metadata": {},
   "source": [
    "### Adjustments"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "28376bad-520d-4ab3-85ce-2d1cf91ac5e5",
   "metadata": {},
   "source": [
    "#### Adjust base elements:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "7dfe4eb9-681a-4574-8170-cdc08156460b",
   "metadata": {},
   "outputs": [],
   "source": [
    "#drop some unnecessary information\n",
    "df_model_units = df_model_units_raw.drop(columns = ['Object_type']).copy()\n",
    "df_model_connections = df_model_connections_raw.drop(columns = ['Object_type']).copy()\n",
    "df_model_storages = df_model_storages_raw.drop(columns = ['Object_type']).copy()\n",
    "\n",
    "#create mapping tables for object name to type\n",
    "df_model_units_mapping = df_model_units_raw[['Unit', 'Object_type']]\n",
    "df_model_connections_mapping = df_model_connections_raw[['Connection', 'Object_type']]\n",
    "df_model_storages_mapping = df_model_storages_raw[['Storage', 'Object_type']]\n",
    "\n",
    "df_model_units_mapping.rename(columns={'Unit': 'Object_Name'}, inplace=True)\n",
    "df_model_connections_mapping.rename(columns={'Connection': 'Object_Name'}, inplace=True)\n",
    "df_model_storages_mapping.rename(columns={'Storage': 'Object_Name'}, inplace=True)\n",
    "\n",
    "#create a dataframe with mapping of all object in the model\n",
    "df_model_object_mapping = pd.concat([df_model_units_mapping, df_model_connections_mapping, df_model_storages_mapping], axis=0)\n",
    "df_model_object_mapping = df_model_object_mapping.reset_index(drop=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "582acf93-55ae-492a-ac60-bb447644e425",
   "metadata": {},
   "outputs": [],
   "source": [
    "df_units = process_dataframe(df_model_units, 'Unit', 'unit')\n",
    "df_connections = process_dataframe(df_model_connections, 'Connection', 'connection')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "28e86607-2ad3-4aa8-8bbd-3bee30a62970",
   "metadata": {
    "scrolled": true
   },
   "outputs": [],
   "source": [
    "#adjust the storage loss rate values to fit to the SpineOpt implementation\n",
    "df_model_storages = adjust_frac_state_loss(df_model_storages, 'frac_state_loss')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "0459358a-3f7b-4b02-ab64-170177f24323",
   "metadata": {},
   "outputs": [],
   "source": [
    "'''def create_definition_dataframe(df_model_units, df_model_connections):\n",
    "    \"\"\"\n",
    "    Create a combined dataframe for units, connections, and nodes.\n",
    "    \n",
    "    Args:\n",
    "    df_model_units (pd.DataFrame): DataFrame containing model units.\n",
    "    df_model_connections (pd.DataFrame): DataFrame containing model connections.\n",
    "    \n",
    "    Returns:\n",
    "    pd.DataFrame: A combined dataframe for units, connections, and nodes.\n",
    "    \"\"\"\n",
    "    # Create a dataframe for units\n",
    "    df_units = df_model_units[['Unit']].copy()\n",
    "    df_units['Category'] = 'unit'\n",
    "    df_units = df_units.rename(columns={'Unit': 'Object_Name'})\n",
    "\n",
    "    # Create a dataframe for connections\n",
    "    df_connections = df_model_connections[['Connection']].copy()\n",
    "    df_connections['Category'] = 'connection'\n",
    "    df_connections = df_connections.rename(columns={'Connection': 'Object_Name'})\n",
    "\n",
    "    # Create a list of nodes of the model\n",
    "    U_input1_nodes = df_model_units['Input1'].tolist()\n",
    "    U_input2_nodes = df_model_units['Input2'].tolist()\n",
    "    U_output1_nodes = df_model_units['Output1'].tolist()\n",
    "    U_output2_nodes = df_model_units['Output2'].tolist()\n",
    "    C_input1_nodes = df_model_connections['Input1'].tolist()\n",
    "    C_input2_nodes = df_model_connections['Input2'].tolist()\n",
    "    C_output1_nodes = df_model_connections['Output1'].tolist()\n",
    "    C_output2_nodes = df_model_connections['Output2'].tolist()\n",
    "\n",
    "    # Combine values from all columns into a single list\n",
    "    all_nodes_list = (U_input1_nodes + U_input2_nodes + U_output1_nodes + U_output2_nodes +\n",
    "                      C_input1_nodes + C_input2_nodes + C_output1_nodes + C_output2_nodes)\n",
    "\n",
    "    # Create a list with unique entries\n",
    "    unique_nodes_list = list(set(all_nodes_list))\n",
    "\n",
    "    # Create a dataframe for nodes\n",
    "    df_nodes = pd.DataFrame(unique_nodes_list, columns=['Object_Name'])\n",
    "    df_nodes['Category'] = 'node'\n",
    "    df_nodes = df_nodes.dropna()\n",
    "\n",
    "    # Combine dataframes\n",
    "    df_definition = pd.concat([df_units, df_nodes, df_connections], ignore_index=True)\n",
    "    \n",
    "    return df_definition, df_nodes'''"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "1f7ec120-9bbf-40af-ac29-9b429051d1a7",
   "metadata": {},
   "outputs": [],
   "source": [
    "#define the elements of the network\n",
    "df_definition, df_nodes = create_definition_dataframe(df_model_units, df_model_connections)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "c31615e3-26bf-4442-a127-f2a183ff8951",
   "metadata": {},
   "outputs": [],
   "source": [
    "df_nodes"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "dee53885-7c29-4a6e-b4a2-b4deeef30be8",
   "metadata": {
    "scrolled": true
   },
   "outputs": [],
   "source": [
    "'''#Create a dataframe for units\n",
    "df_units = df_model_units[['Unit']].copy()\n",
    "df_units['Category'] = 'unit'\n",
    "#df_units['fom_cost'] = df_model_units[['fom_cost']]\n",
    "df_units = df_units.rename(columns={'Unit': 'Object_Name'})\n",
    "\n",
    "#Create a dataframe for connections\n",
    "df_connections = df_model_connections[['Connection']].copy()\n",
    "df_connections['Category'] = 'connection'\n",
    "df_connections = df_connections.rename(columns={'Connection': 'Object_Name'})\n",
    "#df_connections['fom_cost'] = df_model_connections[['fom_cost']]\n",
    "\n",
    "#create a list of nodes of the model\n",
    "U_input1_nodes = df_model_units['Input1'].tolist()\n",
    "U_input2_nodes = df_model_units['Input2'].tolist()\n",
    "U_output1_nodes = df_model_units['Output1'].tolist()\n",
    "U_output2_nodes = df_model_units['Output2'].tolist()\n",
    "C_input1_nodes = df_model_connections['Input1'].tolist()\n",
    "C_input2_nodes = df_model_connections['Input2'].tolist()\n",
    "C_output1_nodes = df_model_connections['Output1'].tolist()\n",
    "C_output2_nodes = df_model_connections['Output2'].tolist()\n",
    "\n",
    "# Combine values from both columns into a single list\n",
    "All_nodes_list = U_input1_nodes+U_input2_nodes+U_output1_nodes+U_output2_nodes+C_input1_nodes+C_input2_nodes+C_output1_nodes+C_output2_nodes\n",
    "\n",
    "# Create a list with unique entries\n",
    "unique_nodes_list = list(set(All_nodes_list))\n",
    "\n",
    "#Create a dataframe for nodes\n",
    "df_nodes = pd.DataFrame(unique_nodes_list, columns=['Object_Name'])\n",
    "df_nodes['Category'] = 'node'\n",
    "df_nodes = df_nodes.dropna()\n",
    "\n",
    "#Combined dataframe\n",
    "df_definition = pd.concat([df_units, df_nodes, df_connections], ignore_index=True)\n",
    "\n",
    "df_definition.head()'''"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "f3c90d86-d62f-49aa-bf8c-a7ceec921d8b",
   "metadata": {},
   "outputs": [],
   "source": [
    "#create a data frame for all parameters of units\n",
    "\n",
    "#add fixed operation and maintenance cost\n",
    "unit_fom_cost_df = create_unit_parameters(df_model_units, 'Unit', 'fom_cost')\n",
    "#add unit minimal downtime\n",
    "unit_min_down_time_df = create_unit_parameters(df_model_units, 'Unit', 'min_down_time')\n",
    "#add unit on cost\n",
    "unit_on_cost_df = create_unit_parameters(df_model_units, 'Unit', 'unit_on_cost')\n",
    "\n",
    "connection_fom_cost_df = create_unit_parameters(df_model_connections, 'Connection', 'fom_cost')\n",
    "\n",
    "#create a complete data frame with all parameters\n",
    "unit_parameters_df = pd.concat([unit_fom_cost_df, unit_on_cost_df, unit_min_down_time_df, connection_fom_cost_df], ignore_index=True)\n",
    "unit_parameters_df"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "470215f7-7b7f-45f3-a1b6-daa11589ff79",
   "metadata": {},
   "outputs": [],
   "source": [
    "#create a new data frame for parameters that are given as durations\n",
    "#necessary as SpineToolbox needs a separate input to map the parameter correctly\n",
    "\n",
    "duration_parameter = 'min_down_time'\n",
    "unit_parameters_duration_df = unit_parameters_df[unit_parameters_df['parameter'] == duration_parameter]\n",
    "# Resetting the index\n",
    "unit_parameters_duration_df = unit_parameters_duration_df.reset_index(drop=True)\n",
    "\n",
    "# Creating another DataFrame with rows that do not meet the condition\n",
    "unit_parameters_rest_df = unit_parameters_df[unit_parameters_df['parameter'] != duration_parameter]\n",
    "unit_parameters_rest_df"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "7c7d5e80-9235-4f61-ae5b-7a815bc5858d",
   "metadata": {},
   "outputs": [],
   "source": [
    "#Create a dataframe for the units' investment parameters\n",
    "df_units_inv_parameters=df_model_units.loc[:, ['Unit','unit_investment_variable_type','candidate_units', 'unit_investment_cost', 'unit_investment_tech_lifetime', 'number_of_units']].rename(columns={'Unit': 'Object_Name'})\n",
    "\n",
    "# Add economical investment lifetime and set to same value as the technical lifetime\n",
    "df_units_inv_parameters['unit_investment_econ_lifetime'] = df_units_inv_parameters['unit_investment_tech_lifetime']\n",
    "\n",
    "# Set initial invested units available to 0\n",
    "df_units_inv_parameters['initial_units_invested_available']='0'\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "1d4e42d4-76d0-480d-b7b2-bdb413adfc55",
   "metadata": {},
   "outputs": [],
   "source": [
    "#create the balance type of the nodes\n",
    "columns_to_select = ['Input1', 'Input2', 'Output1', 'Output2']\n",
    "df_combined = pd.concat([df_model_units, df_model_connections])\n",
    "df_combined = df_combined.reset_index(drop=True)\n",
    "\n",
    "df_nodes_network = create_connection_dataframe(df_combined, columns_to_select)\n",
    "\n",
    "# Get unique values from the 'in' column\n",
    "unique_in_values = df_nodes_network['in'].dropna().unique()\n",
    "\n",
    "# Identify values in 'in' column not present in 'out' column\n",
    "values_not_in_out = unique_in_values[~pd.Series(unique_in_values).isin(df_nodes_network['out'].dropna().unique())]\n",
    "\n",
    "# Get unique values from the 'in' column\n",
    "unique_out_values = df_nodes_network['out'].dropna().unique()\n",
    "\n",
    "# Identify values in 'in' column not present in 'out' column\n",
    "values_not_in_in = unique_out_values[~pd.Series(unique_out_values).isin(df_nodes_network['in'].dropna().unique())]\n",
    "\n",
    "#create list of unique nodes that are either start or end nodes\n",
    "unique_nodes = values_not_in_out.tolist() + values_not_in_in.tolist()\n",
    "unique_nodes\n",
    "\n",
    "df_nodes_network.replace(np.nan, None, inplace=True)\n",
    "\n",
    "#check for combinations that are mirrored\n",
    "mirrored_combinations = find_mirror_combinations(df_nodes_network)\n",
    "\n",
    "#get information of connections for each node\n",
    "partners_dict1 = find_partners(df_nodes_network)\n",
    "partners_dict2 = find_partners(mirrored_combinations)\n",
    "\n",
    "#check both lists if there are identical entries and list nodes that only have a connection to the same node\n",
    "#storages are removed as they must be balanced\n",
    "nodes_identical = find_identical_entries(partners_dict1, partners_dict2)\n",
    "\n",
    "#combined list of start and end nodes that should be unbalanced\n",
    "unbalanced_nodes = nodes_identical + unique_nodes\n",
    "\n",
    "df_nodes['balance_type'] = 'balance_type_node'\n",
    "df_nodes.loc[df_nodes['Object_Name'].isin(unbalanced_nodes), 'balance_type'] = 'balance_type_none'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "0403b80a-9d3f-4557-bda6-2803650bea2d",
   "metadata": {},
   "outputs": [],
   "source": [
    "#add has_state_node_state_cap and frac_state_loss\n",
    "df_storages_short = df_model_storages.loc[:, ['Storage', 'has_state', 'node_state_cap', 'frac_state_loss','storage_investment_variable_type','candidate_storages', 'storage_investment_cost', 'storage_investment_tech_lifetime','number_of_storages']].rename(columns={'Storage': 'Object_Name'})\n",
    "df_storages_short['has_state'] = df_storages_short['has_state'].astype(str).str.lower().replace('true', 'true')\n",
    "\n",
    "# Add economical investment lifetime\n",
    "df_storages_short['storage_investment_econ_lifetime'] = df_storages_short['storage_investment_tech_lifetime']\n",
    "\n",
    "# Set initial invested storages available to 0\n",
    "df_storages_short['initial_storages_invested_available']='0'\n",
    "\n",
    "df_nodes = pd.merge(df_nodes, df_storages_short, on='Object_Name', how='left')\n",
    "df_nodes['demand'] = \"\""
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "bb44a55f-bd0d-41f3-a96a-2fc67ae92a5e",
   "metadata": {
    "scrolled": true
   },
   "outputs": [],
   "source": [
    "#create a dataframe with all nodes that should have a slack based on the unit input and outputs\n",
    "nodes_for_slack_df = check_entries_exist(df_model_units, 'node')\n",
    "#merge the information into the prepared data frame\n",
    "merged_df = pd.merge(df_nodes, nodes_for_slack_df, left_on='Object_Name', right_on='node', how='left')\n",
    "merged_df = merged_df.drop(columns=['node'])\n",
    "merged_df['node_slack_penalty'] = merged_df['node_slack_penalty'].replace({True: 100000, False: ''})\n",
    "#create a dataframe with all nodes that should have a slack based on the connection input and outputs\n",
    "nodes_for_slack_df2 = check_entries_exist(df_model_connections, 'connection')\n",
    "#merge the information into the prepared data frame\n",
    "merged_df2 = pd.merge(df_nodes, nodes_for_slack_df2, left_on='Object_Name', right_on='connection', how='left')\n",
    "merged_df2 = merged_df2.drop(columns=['connection'])\n",
    "merged_df2['node_slack_penalty'] = merged_df2['node_slack_penalty'].replace({True: 100000, False: ''})\n",
    "#link the information about the slack of both data frames\n",
    "merged_df2['node_slack_penalty'] = merged_df['node_slack_penalty'].combine_first(merged_df2['node_slack_penalty'])\n",
    "#clean the information that only nodes with 'balance_type_node' have a penalty\n",
    "merged_df2.loc[merged_df2['balance_type'] == 'balance_type_none', 'node_slack_penalty'] = ''\n",
    "#add the information into the df_nodes\n",
    "df_nodes['node_slack_penalty'] = merged_df2['node_slack_penalty']\n",
    "\n",
    "#show table head for control\n",
    "df_nodes.head()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "ee8799cc-183e-408a-a903-32f8f6e56693",
   "metadata": {},
   "outputs": [],
   "source": [
    "#Add parameters for connections\n",
    "df_connections = df_model_connections.loc[:, ['Connection', 'Connection_type', 'connection_investment_variable_type','candidate_connections','connection_investment_cost', 'connection_investment_tech_lifetime', 'number_of_connections']]\n",
    "# Add economical investment lifetime and set to same value as the technical lifetime\n",
    "df_connections['connection_investment_econ_lifetime'] = df_connections['connection_investment_tech_lifetime']\n",
    "# Set initial invested connections available to 0\n",
    "df_connections['initial_connections_invested_available']='0'\n",
    "\n",
    "insert_index=1\n",
    "parameter_name = ['connection_type']*len(df_connections)\n",
    "df_connections.insert(insert_index, 'Parameter_name', parameter_name)\n",
    "#show table for control\n",
    "df_connections.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "c33f3dc6-ea13-486b-9860-6bd41f57b3a7",
   "metadata": {},
   "source": [
    "#### Times series:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "e60a7947-9d7f-480f-847a-f22419719660",
   "metadata": {},
   "outputs": [],
   "source": [
    "#adjust PV columns names\n",
    "df_PV_availabilityfactors_values.rename(columns={'time': 'time [UTC]', \n",
    "                                                 'local_time': 'time [' + area + ']',\n",
    "                                                 'electricity': 'unit_availability_factor'}, inplace=True)\n",
    "df_powerprices_values.rename(columns={'HourUTC': 'time [UTC]', \n",
    "                                         'HourDK': 'time [' + area + ']'}, inplace=True)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "287b3c37-228f-47f0-a99e-2df1f87512d5",
   "metadata": {},
   "source": [
    "### Fitting data into format"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "1b527344-851f-47c0-a12e-72942d4176eb",
   "metadata": {},
   "source": [
    "#### Relationships:"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "19ea16b2-0e98-4ca2-b6ec-aa840ac09d20",
   "metadata": {},
   "source": [
    "Object__from/to_node:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "2a4c5f93-8fa4-4d88-83f9-767f83ff7ed9",
   "metadata": {},
   "outputs": [],
   "source": [
    "### UNITS ###\n",
    "df_unit_relation_parameter_data = pd.DataFrame(object_relationship_unit_nodes(df_model_units))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "0e0a59d6-76be-4405-8ef7-62428bbe25ba",
   "metadata": {},
   "outputs": [],
   "source": [
    "### UNITS ###\n",
    "'''# Initialize an empty list to store the transformed data\n",
    "unit_relation_parameter_data = []\n",
    "\n",
    "# Iterate over each row in the DataFrame\n",
    "for index, row in df_model_units.iterrows():\n",
    "    unit = row['Unit']\n",
    "\n",
    "    # Iterate over Input and Output columns\n",
    "    for i in range(1, 3):\n",
    "        input_col = f'Input{i}'\n",
    "        output_col = f'Output{i}'\n",
    "        cap_input_col = f'Cap_{input_col}_existing'\n",
    "        cap_output_col = f'Cap_{output_col}_existing'\n",
    "        vom_cost_input_col = f'vom_cost_{input_col}'\n",
    "        vom_cost_output_col = f'vom_cost_{output_col}'\n",
    "        ramp_up_output_col = f'ramp_up_{output_col}'\n",
    "        ramp_down_output_col = f'ramp_down_{output_col}'\n",
    "        start_up_output_col = f'start_up_{output_col}'\n",
    "        shut_down_output_col = f'shut_down_{output_col}'\n",
    "        minimum_operating_point = f'minimum_op_point'\n",
    "\n",
    "        # Check for Input columns\n",
    "        input_value = row[input_col]\n",
    "        input_capacity = row[cap_input_col]\n",
    "        vom_cost_input = row[vom_cost_input_col]\n",
    "        minimum_op = row[minimum_operating_point]\n",
    "\n",
    "        if pd.notna(input_value):\n",
    "            unit_relation_parameter_data.append({\n",
    "                'Relationship_class_name': 'unit__from_node',\n",
    "                'Object_class': 'unit',\n",
    "                'Object_name': unit,\n",
    "                'Node': input_value,\n",
    "                'Parameter': 'unit_capacity' if pd.notna(input_capacity) else '',\n",
    "                'Value': input_capacity if pd.notna(input_capacity) else ''\n",
    "            })\n",
    "        \n",
    "            if pd.notna(input_value) and pd.notna(vom_cost_input):\n",
    "                unit_relation_parameter_data.append({\n",
    "                    'Relationship_class_name': 'unit__from_node',\n",
    "                    'Object_class': 'unit',\n",
    "                    'Object_name': unit,\n",
    "                    'Node': input_value,\n",
    "                    'Parameter': 'vom_cost',\n",
    "                    'Value': vom_cost_input\n",
    "                })\n",
    "            \n",
    "            if pd.notna(input_value) and pd.notna(input_capacity) and pd.notna(minimum_op):\n",
    "                unit_relation_parameter_data.append({\n",
    "                    'Relationship_class_name': 'unit__from_node',\n",
    "                    'Object_class': 'unit',\n",
    "                    'Object_name': unit,\n",
    "                    'Node': input_value,\n",
    "                    'Parameter': 'minimum_operating_point',\n",
    "                    'Value': minimum_op\n",
    "                })\n",
    "\n",
    "\n",
    "        # Check for Output columns\n",
    "        output_value = row[output_col]\n",
    "        output_capacity = row[cap_output_col]\n",
    "        vom_cost_output = row[vom_cost_output_col]\n",
    "        ramp_up_output = row[ramp_up_output_col]\n",
    "        ramp_down_output = row[ramp_down_output_col]\n",
    "        start_up_output = row[start_up_output_col]\n",
    "        shut_down_output = row[shut_down_output_col]\n",
    "\n",
    "        if pd.notna(output_value):\n",
    "            unit_relation_parameter_data.append({\n",
    "                'Relationship_class_name': 'unit__to_node',\n",
    "                'Object_class': 'unit',\n",
    "                'Object_name': unit,\n",
    "                'Node': output_value,\n",
    "                'Parameter': 'unit_capacity' if pd.notna(output_capacity) else '',\n",
    "                'Value': output_capacity if pd.notna(output_capacity) else ''\n",
    "            })\n",
    "        \n",
    "            if pd.notna(output_value) and pd.notna(vom_cost_output):\n",
    "                unit_relation_parameter_data.append({\n",
    "                    'Relationship_class_name': 'unit__to_node',\n",
    "                    'Object_class': 'unit',\n",
    "                    'Object_name': unit,\n",
    "                    'Node': output_value,\n",
    "                    'Parameter': 'vom_cost',\n",
    "                    'Value': vom_cost_output\n",
    "                })\n",
    "\n",
    "            if pd.notna(output_value) and pd.notna(ramp_up_output):\n",
    "                unit_relation_parameter_data.append({\n",
    "                    'Relationship_class_name': 'unit__to_node',\n",
    "                    'Object_class': 'unit',\n",
    "                    'Object_name': unit,\n",
    "                    'Node': output_value,\n",
    "                    'Parameter': 'ramp_up_limit',\n",
    "                    'Value': ramp_up_output\n",
    "                })\n",
    "\n",
    "            if pd.notna(output_value) and pd.notna(ramp_down_output):\n",
    "                unit_relation_parameter_data.append({\n",
    "                    'Relationship_class_name': 'unit__to_node',\n",
    "                    'Object_class': 'unit',\n",
    "                    'Object_name': unit,\n",
    "                    'Node': output_value,\n",
    "                    'Parameter': 'ramp_down_limit',\n",
    "                    'Value': ramp_down_output\n",
    "                })\n",
    "            \n",
    "            if pd.notna(output_value) and pd.notna(start_up_output):\n",
    "                unit_relation_parameter_data.append({\n",
    "                    'Relationship_class_name': 'unit__to_node',\n",
    "                    'Object_class': 'unit',\n",
    "                    'Object_name': unit,\n",
    "                    'Node': output_value,\n",
    "                    'Parameter': 'start_up_limit',\n",
    "                    'Value': start_up_output\n",
    "                })\n",
    "            \n",
    "            if pd.notna(output_value) and pd.notna(shut_down_output):\n",
    "                unit_relation_parameter_data.append({\n",
    "                    'Relationship_class_name': 'unit__to_node',\n",
    "                    'Object_class': 'unit',\n",
    "                    'Object_name': unit,\n",
    "                    'Node': output_value,\n",
    "                    'Parameter': 'shut_down_limit',\n",
    "                    'Value': shut_down_output\n",
    "                })\n",
    "            \n",
    "            if pd.notna(output_value) and pd.notna(output_capacity) and pd.notna(minimum_op):\n",
    "                unit_relation_parameter_data.append({\n",
    "                    'Relationship_class_name': 'unit__to_node',\n",
    "                    'Object_class': 'unit',\n",
    "                    'Object_name': unit,\n",
    "                    'Node': output_value,\n",
    "                    'Parameter': 'minimum_operating_point',\n",
    "                    'Value': minimum_op\n",
    "                })\n",
    "\n",
    "# Create a new DataFrame from the transformed data\n",
    "df_unit_relation_parameter_data = pd.DataFrame(unit_relation_parameter_data)'''\n",
    "df_unit_relation_parameter_data.head()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "74ae88a6",
   "metadata": {},
   "outputs": [],
   "source": [
    "### ADD ADDITIONAL ELECTRICITY CONNECTIONS IF NOT ALREADY EXISTENT ###\n",
    "\n",
    "units = df_units.iloc[:, 0].tolist()\n",
    "length = len(units)\n",
    "data = {\n",
    "    \"Relationship_class_name\": [\"unit__from_node\"] * length,\n",
    "    \"Object_class\": [\"unit\"] * length,\n",
    "    \"Object_name\": units,\n",
    "    \"Node\": [\"Power_Kasso\"] * length\n",
    "}\n",
    "df_electricity = pd.DataFrame(data)\n",
    "\n",
    "units_with_from_node = df_unit_relation_parameter_data[df_unit_relation_parameter_data['Relationship_class_name'].str.contains('unit__from_node')]\n",
    "valid_object_names = units_with_from_node['Object_name']\n",
    "df_electricity_filtered = df_electricity[df_electricity['Object_name'].isin(valid_object_names)]\n",
    "\n",
    "merged_df = pd.merge(df_electricity_filtered, units_with_from_node, on=['Relationship_class_name', 'Object_class', 'Object_name', 'Node'], how='left', indicator=True)\n",
    "df_electricity_nodes = merged_df[merged_df['_merge'] == 'left_only'].drop(columns='_merge')\n",
    "\n",
    "df_unit_relation_parameter_data = pd.concat([df_unit_relation_parameter_data, df_electricity_nodes], ignore_index=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "e92030e0-f252-49f5-b58c-defa9a0da163",
   "metadata": {},
   "outputs": [],
   "source": [
    "### CONNECTIONS ###\n",
    "df_connection_relation_parameter_data = object_relationship_connection_nodes(df_model_connections)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "6031af12-8f24-49f5-8f5b-6526f0065433",
   "metadata": {},
   "outputs": [],
   "source": [
    "### CONNECTIONS ###\n",
    "'''\n",
    "# Initialize an empty list to store the transformed data\n",
    "connection_relation_parameter_data = []\n",
    "\n",
    "# Iterate over each row in the DataFrame\n",
    "for index, row in df_model_connections.iterrows():\n",
    "    connection = row['Connection']\n",
    "\n",
    "    # Iterate over Input and Output columns\n",
    "    for i in range(1, 3):\n",
    "        input_col = f'Input{i}'\n",
    "        output_col = f'Output{i}'\n",
    "        cap_input_col = f'Cap_{input_col}_existing'\n",
    "        cap_output_col = f'Cap_{output_col}_existing'\n",
    "        vom_cost_input_col = f'vom_cost_{input_col}'\n",
    "        vom_cost_output_col = f'vom_cost_{output_col}'\n",
    "        start_up_output_col = f'start_up_{output_col}'\n",
    "        shut_down_output_col = f'shut_down_{output_col}'\n",
    "        #fom_cost_col = 'fom_cost' if i == 1 else None\n",
    "        #vom_cost_col = 'vom_cost' if i == 1 else None\n",
    "\n",
    "        # Check for Input columns\n",
    "        input_value = row[input_col]\n",
    "        input_capacity = row[cap_input_col]\n",
    "        vom_cost_input = row[vom_cost_input_col]\n",
    "\n",
    "        #fom_cost_value = row[fom_cost_col] if fom_cost_col else None\n",
    "        #vom_cost_value = row[vom_cost_col] if vom_cost_col else None\n",
    "\n",
    "        if pd.notna(input_value):\n",
    "            connection_relation_parameter_data.append({\n",
    "                'Relationship_class_name': 'connection__from_node',\n",
    "                'Object_class': 'connection',\n",
    "                'Object_name': connection,\n",
    "                'Node': input_value,\n",
    "                'Parameter': 'connection_capacity' if pd.notna(input_capacity) else '',\n",
    "                'Value': input_capacity if pd.notna(input_capacity) else ''\n",
    "            })\n",
    "        \n",
    "            if pd.notna(input_value) and pd.notna(vom_cost_input):\n",
    "                connection_relation_parameter_data.append({\n",
    "                    'Relationship_class_name': 'connection__from_node',\n",
    "                    'Object_class': 'connection',\n",
    "                    'Object_name': connection,\n",
    "                    'Node': input_value,\n",
    "                    'Parameter': 'vom_cost',\n",
    "                    'Value': vom_cost_input\n",
    "                })\n",
    "\n",
    "        # Check for Output columns\n",
    "        output_value = row[output_col]\n",
    "        output_capacity = row[cap_output_col]\n",
    "        vom_cost_output = row[vom_cost_output_col]\n",
    "\n",
    "        # if pd.notna(output_value):\n",
    "        #     connection_relation_parameter_data.append({\n",
    "        #         'Relationship_class_name': 'connection__to_node',\n",
    "        #         'Object_class': 'connection',\n",
    "        #         'Object_name': connection,\n",
    "        #         'Node': output_value,\n",
    "        #         'Parameter': 'connection_capacity' if pd.notna(output_capacity) else '',\n",
    "        #         'Value': output_capacity if pd.notna(output_capacity) else '',\n",
    "        #         #'fom_cost': fom_cost_value if pd.notna(fom_cost_value) else '',\n",
    "        #         #'vom_cost': vom_cost_value if pd.notna(vom_cost_value) else ''\n",
    "        #     })\n",
    "\n",
    "        if pd.notna(output_value):\n",
    "            connection_relation_parameter_data.append({\n",
    "                'Relationship_class_name': 'connection__to_node',\n",
    "                'Object_class': 'connection',\n",
    "                'Object_name': connection,\n",
    "                'Node': output_value,\n",
    "                'Parameter': 'connection_capacity' if pd.notna(output_capacity) else '',\n",
    "                'Value': output_capacity if pd.notna(output_capacity) else ''\n",
    "            })\n",
    "        \n",
    "        if pd.notna(output_value) and pd.notna(vom_cost_output):\n",
    "            connection_relation_parameter_data.append({\n",
    "                'Relationship_class_name': 'connection__to_node',\n",
    "                'Object_class': 'connection',\n",
    "                'Object_name': connection,\n",
    "                'Node': output_value,\n",
    "                'Parameter': 'vom_cost',\n",
    "                'Value': vom_cost_output\n",
    "            })\n",
    "\n",
    "#Create a new DataFrame from the transformed data\n",
    "df_connection_relation_parameter_data = pd.DataFrame(connection_relation_parameter_data)'''"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "65d8c41c-8fb4-4a60-883b-94b70f5ace80",
   "metadata": {},
   "outputs": [],
   "source": [
    "#Create combined DataFrame:\n",
    "df_object__node = pd.concat([df_unit_relation_parameter_data, df_connection_relation_parameter_data])\n",
    "df_object__node = df_object__node.reset_index(drop=True)\n",
    "\n",
    "#show df head for control\n",
    "df_object__node.head()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "36e1391f-d8cd-45dd-9867-7aefa0327740",
   "metadata": {},
   "outputs": [],
   "source": [
    "#create a DataFrame for the definition of the object_node relationships\n",
    "df_object__node_definitions = pd.DataFrame(df_object__node[['Relationship_class_name', 'Object_class', 'Object_name', 'Node']])\n",
    "df_object__node_definitions = df_object__node_definitions.drop_duplicates()\n",
    "df_object__node_definitions = df_object__node_definitions.reset_index(drop=True)\n",
    "\n",
    "#to avoid import errors the connections  will be removed from the definitions df\n",
    "# Dropping rows where 'Object_class' is 'connection'\n",
    "df_object__node_definitions  = df_object__node_definitions [df_object__node_definitions ['Object_class'] != 'connection']\n",
    "\n",
    "# Drop rows where no parameters for the relationship are defined (column has missing values (NaN or None))\n",
    "drop_no_value_column = 'Parameter'\n",
    "df_object__node_values = df_object__node[df_object__node[drop_no_value_column] != '']\n",
    "df_object__node_definitions.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "9ebeb807-b807-4882-b8cd-67a174c8edbd",
   "metadata": {},
   "source": [
    "Object__node_node:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "1fd5a160-3f18-4656-82ee-484e7e703cc8",
   "metadata": {},
   "outputs": [],
   "source": [
    "#Define which columns to check\n",
    "columns_In_In_Unit = ['Unit', 'Input1', 'Input2']\n",
    "columns_In_Out_Unit = ['Unit', 'Input1', 'Output1']\n",
    "columns_Out_Out_Unit = ['Unit', 'Output1', 'Output2']\n",
    "columns_In_In_Connection = ['Connection', 'Input1', 'Input2']\n",
    "columns_In_Out_Connection = ['Connection', 'Input1', 'Output1']\n",
    "columns_Out_Out_Connection = ['Connection', 'Output1', 'Output2']\n",
    "columns_Out_In_Connection = ['Connection', 'Output1', 'Input1']\n",
    "\n",
    "####UNITS#####\n",
    "#create list of tuples with values of cells + fix_ratio_XXX_XXX\n",
    "values_in_in_units = [('unit__node__node', 'unit', row[columns_In_In_Unit[0]], row[columns_In_In_Unit[1]], row[columns_In_In_Unit[2]], \n",
    "                       'fix_ratio_in_in_unit_flow', row['Relation_In_In']) \n",
    "                      if not pd.isnull(row[columns_In_In_Unit]).any() else (np.nan, np.nan, None) for _, row in df_model_units.iterrows() \n",
    "                      if not pd.isnull(row[columns_In_In_Unit]).any()]\n",
    "values_in_out_units = [('unit__node__node', 'unit', row[columns_In_Out_Unit[0]], row[columns_In_Out_Unit[1]], row[columns_In_Out_Unit[2]], \n",
    "                        'fix_ratio_in_out_unit_flow', row['Relation_In_Out']) \n",
    "                      if not pd.isnull(row[columns_In_Out_Unit]).any() else (np.nan, np.nan, None) for _, row in df_model_units.iterrows() \n",
    "                      if not pd.isnull(row[columns_In_Out_Unit]).any()]\n",
    "values_out_out_units = [('unit__node__node', 'unit', row[columns_Out_Out_Unit[0]], row[columns_Out_Out_Unit[1]], row[columns_Out_Out_Unit[2]], \n",
    "                         'fix_ratio_out_out_unit_flow', row['Relation_Out_Out']) \n",
    "                      if not pd.isnull(row[columns_Out_Out_Unit]).any() else (np.nan, np.nan, None) for _, row in df_model_units.iterrows() \n",
    "                      if not pd.isnull(row[columns_Out_Out_Unit]).any()]\n",
    "\n",
    "df_fix_ratio_in_in_units = pd.DataFrame(values_in_in_units, columns=['Relationship', 'Object_class', 'Object_name', 'Node1', \n",
    "                                                                     'Node2', 'Parameter', 'Value'])\n",
    "df_fix_ratio_in_out_units = pd.DataFrame(values_in_out_units, columns=['Relationship', 'Object_class', 'Object_name', 'Node1', \n",
    "                                                                       'Node2', 'Parameter', 'Value'])\n",
    "df_fix_ratio_out_out_units = pd.DataFrame(values_out_out_units, columns=['Relationship', 'Object_class', 'Object_name', 'Node1', \n",
    "                                                                         'Node2', 'Parameter', 'Value'])\n",
    "\n",
    "####CONNECTIONS\n",
    "values_in_in_connections = [('connection__node__node', 'connection', row[columns_In_In_Connection[0]], \n",
    "                             row[columns_In_In_Connection[1]], row[columns_In_In_Connection[2]], \n",
    "                             'fix_ratio_in_in_connection_flow', row['Relation_In_In']) \n",
    "                            if not pd.isnull(row[columns_In_In_Connection]).any() else (np.nan, np.nan, None) for _, row in df_model_connections.iterrows() \n",
    "                            if not pd.isnull(row[columns_In_In_Connection]).any()]\n",
    "values_in_out_connections = [('connection__node__node', 'connection', row[columns_In_Out_Connection[0]], \n",
    "                              row[columns_In_Out_Connection[1]], row[columns_In_Out_Connection[2]], \n",
    "                              'fix_ratio_in_out_connection_flow', row['Relation_In_Out']) \n",
    "                             if not pd.isnull(row[columns_In_Out_Connection]).any() else (np.nan, np.nan, None) for _, row in df_model_connections.iterrows() \n",
    "                             if not pd.isnull(row[columns_In_Out_Connection]).any()]\n",
    "values_out_out_connections = [('connection__node__node', 'connection', row[columns_Out_Out_Connection[0]], \n",
    "                               row[columns_Out_Out_Connection[1]], row[columns_Out_Out_Connection[2]], \n",
    "                               'fix_ratio_out_out_connection_flow', row['Relation_Out_Out']) \n",
    "                              if not pd.isnull(row[columns_Out_Out_Connection]).any() else (np.nan, np.nan, None) for _, row in df_model_connections.iterrows() \n",
    "                              if not pd.isnull(row[columns_Out_Out_Connection]).any()]\n",
    "values_out_in_connections = [('connection__node__node', 'connection', row[columns_Out_In_Connection[0]], \n",
    "                               row[columns_Out_In_Connection[1]], row[columns_Out_In_Connection[2]], \n",
    "                               'fix_ratio_out_in_connection_flow', row['Relation_Out_In']) \n",
    "                              if not pd.isnull(row[columns_Out_In_Connection]).any() else (np.nan, np.nan, None) for _, row in df_model_connections.iterrows() \n",
    "                              if not pd.isnull(row[columns_Out_In_Connection]).any()]\n",
    "\n",
    "df_fix_ratio_in_in_connections = pd.DataFrame(values_in_in_connections, columns=['Relationship', 'Object_class', 'Object_name', 'Node1', \n",
    "                                                                                 'Node2', 'Parameter', 'Value'])\n",
    "df_fix_ratio_in_out_connections = pd.DataFrame(values_in_out_connections, columns=['Relationship', 'Object_class', 'Object_name', 'Node1', \n",
    "                                                                                   'Node2', 'Parameter', 'Value'])\n",
    "df_fix_ratio_out_out_connections = pd.DataFrame(values_out_out_connections, columns=['Relationship', 'Object_class', 'Object_name', 'Node1', \n",
    "                                                                                     'Node2', 'Parameter', 'Value'])\n",
    "df_fix_ratio_out_in_connections = pd.DataFrame(values_out_in_connections, columns=['Relationship', 'Object_class', 'Object_name', 'Node1', \n",
    "                                                                                     'Node2', 'Parameter', 'Value'])\n",
    "\n",
    "#create Object_node_node\n",
    "df_object_node_node = pd.concat([df_fix_ratio_in_in_units, df_fix_ratio_in_out_units, df_fix_ratio_out_out_units, \n",
    "                                df_fix_ratio_in_in_connections, df_fix_ratio_in_out_connections, \n",
    "                                df_fix_ratio_out_out_connections, df_fix_ratio_out_in_connections])\n",
    "df_object_node_node = df_object_node_node.reset_index(drop=True)\n",
    "\n",
    "df_object_node_node = df_object_node_node.dropna(subset=['Value'])\n",
    "df_object_node_node.head()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "1388dfc3-fb27-4571-ba84-8593ea8413df",
   "metadata": {},
   "outputs": [],
   "source": [
    "#for storages, the out_in_connetion is set in both directions\n",
    "# Step 1: Check if the 'Object_name' column contains the word 'storage'\n",
    "storage_condition = df_object_node_node['Object_name'].str.contains('storage', case=False)\n",
    "\n",
    "# Step 2: Check if the 'Parameter' column starts with 'fix_ratio_'\n",
    "parameter_condition = df_object_node_node['Parameter'].str.startswith('fix_ratio_')\n",
    "\n",
    "# Step 3: Combine both conditions\n",
    "combined_condition = storage_condition & parameter_condition\n",
    "\n",
    "# Step 2: Update the 'Parameter' column for rows that meet the condition\n",
    "df_object_node_node.loc[storage_condition, 'Parameter'] = 'fix_ratio_out_in_connection_flow'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "3ecebeb7",
   "metadata": {},
   "outputs": [],
   "source": [
    "### ADD UNIT__NODE__NODE RELATIONSHIPS FOR UNIT_IDLE_HEAT_RATE ###\n",
    "in_and_outputs = df_model_units[['Unit', 'Input1', 'Output1', 'unit_idle_heat_rate']].copy()\n",
    "length = len(in_and_outputs)\n",
    "data = {\n",
    "    \"Relationship\": [\"unit__node__node\"] * length,\n",
    "    \"Object_class\": [\"unit\"] * length,\n",
    "    \"Object_name\": in_and_outputs.iloc[:, 0].tolist(),\n",
    "    \"Node1\": [\"Power_Kasso\"] * length,\n",
    "    \"Node2\": in_and_outputs.iloc[:, 2].tolist(),\n",
    "    \"Parameter\": [\"unit_idle_heat_rate\"] * length,\n",
    "    \"Value\": in_and_outputs.iloc[:, 3].tolist()\n",
    "}\n",
    "df_idle_node_node = pd.DataFrame(data)\n",
    "#drop all rows that now have input and output of electricity\n",
    "df_electricity_node_node = df_idle_node_node[df_idle_node_node['Node1'] != df_idle_node_node['Node2']]\n",
    "#drop all rows that do not have a unit_idle_heat rate\n",
    "df_electricity_node_node = df_electricity_node_node.dropna(subset=['Value'])\n",
    "\n",
    "df_object_node_node = pd.concat([df_object_node_node, df_electricity_node_node], ignore_index=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "daeff16a-f6c3-40ef-8a0b-25aa00449e1a",
   "metadata": {},
   "outputs": [],
   "source": [
    "#add a unit incremental heat rate of 0 for all units with idle_heat rate\n",
    "#this is necessary as idle_heat rate is always used together with unit_incremental_heat_rate\n",
    "\n",
    "# Filter the rows that meet the conditions to have Power_Kasso and unit_idle_heat_rate in df_object_node_node\n",
    "filtered_power_idleHR_df = df_object_node_node[(df_object_node_node['Node1'] == 'Power_Kasso') \n",
    "                & (df_object_node_node['Parameter'] == 'unit_idle_heat_rate')]\n",
    "\n",
    "# Check if rows already have 'fix_ratio_in_out_unit_flow'\n",
    "existing_fix_ratio_input = df_object_node_node[(df_object_node_node['Parameter'] == 'fix_ratio_in_out_unit_flow') \n",
    "                    & (df_object_node_node['Node1'] == 'Power_Kasso')]\n",
    "#the following might not be relevant\n",
    "existing_fix_ratio_in_in = df_object_node_node[(df_object_node_node['Parameter'] == 'fix_ratio_in_in_unit_flow') \n",
    "                    & (df_object_node_node['Node1'] == 'Power_Kasso')]\n",
    "\n",
    "# Filter out rows from filtered_df that have 'fix_ratio_in_out_unit_flow'\n",
    "filtered_power_idleHR_df = filtered_power_idleHR_df[~filtered_power_idleHR_df['Object_name'].isin(existing_fix_ratio_input['Object_name'])]\n",
    "#filtered_power_idleHR_df = filtered_power_idleHR_df[~filtered_power_idleHR_df['Object_name'].isin(existing_fix_ratio_output['Object_name'])]\n",
    "\n",
    "# Create new rows with the additional parameter of the unit incremental heat rate and the value of 0\n",
    "new_rows_incrementalHR = filtered_power_idleHR_df.copy()\n",
    "new_rows_incrementalHR['Parameter'] = 'unit_incremental_heat_rate'\n",
    "new_rows_incrementalHR['Value'] = 0\n",
    "\n",
    "# Append new rows to the original DataFrame\n",
    "df_object_node_node = pd.concat([df_object_node_node, new_rows_incrementalHR], ignore_index=True)\n",
    "\n",
    "### Create new row with a unit start flow of 1.0 for destilation tower !(ToDo: Soft code)!\n",
    "df_object_node_node.loc[len(df_object_node_node.index)] = ['unit__node__node','unit','Destilation_Tower', 'Power_Kasso', 'E-Methanol_Kasso','unit_start_flow', 1.0]\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "3e8e1c70",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Add unit_node_node relationships for every unit that has power as output (e.g., PV)\n",
    "df_non_electricity_node_node = df_idle_node_node[df_idle_node_node['Node1'] == df_idle_node_node['Node2']].copy()\n",
    "df_non_electricity_node_node.loc[:, 'Node1'] = df_non_electricity_node_node['Object_name'] + '_node'\n",
    "\n",
    "#drop all rows that do not have a unit_idle_heat rate\n",
    "df_non_electricity_node_node = df_non_electricity_node_node.dropna(subset=['Value'])\n",
    "\n",
    "df_object_node_node = pd.concat([df_object_node_node, df_non_electricity_node_node], ignore_index=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "1161ddbe",
   "metadata": {},
   "outputs": [],
   "source": [
    "# add new [arbitrary] nodes to definition\n",
    "new_nodes = df_non_electricity_node_node['Node1']\n",
    "new_nodes = new_nodes[~new_nodes.isin(df_nodes['Object_Name'])]\n",
    "df_new_nodes = pd.DataFrame({\n",
    "    'Object_Name': new_nodes,\n",
    "    'Category': 'node'\n",
    "})\n",
    "\n",
    "df_nodes = pd.concat([df_nodes, df_new_nodes], ignore_index=True)\n",
    "# add new node to definition\n",
    "df_definition = pd.concat([df_definition, df_new_nodes], ignore_index=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "9189bd8d",
   "metadata": {},
   "outputs": [],
   "source": [
    "# add new unit_to_nodes relationship with new nodes\n",
    "df_new = df_non_electricity_node_node.copy()\n",
    "df_new = df_new.iloc[:, :4]\n",
    "new_headers = ['Relationship_class_name', 'Object_class', 'Object_name', 'Node']\n",
    "df_new.columns = new_headers\n",
    "df_new.iloc[:, 0] = \"unit__from_node\"\n",
    "\n",
    "df_object__node_definitions = pd.concat([df_object__node_definitions, df_new], ignore_index=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "68543d3d",
   "metadata": {},
   "outputs": [],
   "source": [
    "#Check if second node is necessary for demand\n",
    "for index, row in df_model_units.iterrows():\n",
    "    df_definition, df_nodes, df_connections, df_object__node_values, df_object_node_node = check_demand_node(\n",
    "        row, temporal_block, resolution_to_block, df_definition, \n",
    "        df_nodes, df_connections, df_object__node_values, \n",
    "        df_object_node_node)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "36be54c5-1d66-4841-a002-30a94697b84e",
   "metadata": {},
   "source": [
    "#### Variable Efficiency Units:"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "17268ecd-53bc-49ec-b6b8-6132ce181b2f",
   "metadata": {},
   "source": [
    "##### Calculate adjusted efficiency for each unit"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "cecb0765",
   "metadata": {
    "scrolled": true
   },
   "outputs": [],
   "source": [
    "#important as the SpineOpt implementation is piecewise but when producing at high capacity the lower segments also produce\n",
    "#this way, we avoid overestimation of production when running at higher capacities\n",
    "\n",
    "for index, row in df_model_units.iterrows():\n",
    "    if pd.notna(row['mean_efficiency']):\n",
    "        # If 'mean_efficiency' column has a value, check if corresponding DataFrame exists\n",
    "        column_name = row['Unit'].lower()\n",
    "        df_name = f\"df_efficiency_{column_name}\"\n",
    "        goal = row['mean_efficiency']\n",
    "        output_1 = row['Output1']\n",
    "        input_1 = row['Input1']\n",
    "        \n",
    "        if df_name in globals() and isinstance(globals()[df_name], pd.DataFrame):\n",
    "            #Calculate adjusted efficiency\n",
    "            df_efficiency_adj = create_adj_efficiency(globals()[df_name], goal, column_name)\n",
    "            globals()[f\"df_efficiency_{column_name}_adj\"] = df_efficiency_adj\n",
    "            #fit with operating points\n",
    "            des_segment = globals()['des_segments_' + column_name]\n",
    "            df_var_efficiency, df_operating_points, segment_x_values, segment_averages, x_values, y_values = calculate_op_points(column_name, des_segment, df_efficiency_adj, input_1, output_1)\n",
    "            globals()[f\"variable_efficiency_{column_name}\"] = df_var_efficiency\n",
    "            globals()[f\"operating_points_{column_name}\"] = df_operating_points\n",
    "            globals()[f\"segment_x_values_{column_name}\"] = segment_x_values\n",
    "            globals()[f\"segment_averages_{column_name}\"] = segment_averages\n",
    "            globals()[f\"x_values_{column_name}\"] = x_values\n",
    "            globals()[f\"y_values_{column_name}\"] = y_values\n",
    "            #create ordered_unit_flow\n",
    "            ordered_unit_flow = check_decreasing(df_var_efficiency, column_name, input_1)\n",
    "            globals()[f\"ordered_unit_flow_{column_name}\"] = ordered_unit_flow\n",
    "        else:\n",
    "            print(f\"WARNING: No variable efficiency defined for {column_name}\")\n",
    "    else:\n",
    "        # If 'mean_efficiency' column is NA, skip\n",
    "        continue"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "6bf17dac-b552-4369-84fc-4417439747a1",
   "metadata": {
    "scrolled": true
   },
   "outputs": [],
   "source": [
    "# Plot the data of the original efficiency curve and the adjusted ones\n",
    "plt.figure(figsize=(7, 3))\n",
    "plt.plot(df_efficiency_electrolyzer_adj['Power [%]'], df_efficiency_electrolyzer_adj['Efficiency [%]'], label='Eff raw', marker='o')\n",
    "plt.plot(df_efficiency_electrolyzer_adj['Power [%]'], df_efficiency_electrolyzer_adj['Efficiency_scaled [%]'], label='Eff scaled', marker='x')\n",
    "plt.plot(df_efficiency_adj['Power [%]'], df_efficiency_adj['eff_adjusted_electrolyzer'], label='Eff adjusted', marker='x', \n",
    "         linestyle='dashed', dashes=(5, 7))\n",
    "\n",
    "plt.xlabel('Power [%]')\n",
    "plt.ylabel('Efficiency [%]')\n",
    "plt.title('Efficiency vs Power')\n",
    "plt.legend()\n",
    "plt.grid(True)\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "6107fc7e",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Plotting the data points and the curve\n",
    "plt.figure(figsize=(5, 4))\n",
    "plt.scatter(df_efficiency_electrolyzer_adj['Power [%]'], df_efficiency_electrolyzer_adj['eff_adjusted_electrolyzer'], color='blue', label='Efficiency Adjusted')\n",
    "plt.plot(x_values_electrolyzer, y_values_electrolyzer, color='red', label='Fitted Efficiency Curve Electrolyzer')\n",
    "\n",
    "# Plotting segment averages\n",
    "for i, (x_start, x_end) in enumerate(segment_x_values_electrolyzer):\n",
    "    plt.plot([x_start, x_end], [segment_averages_electrolyzer[i], segment_averages_electrolyzer[i]], color='green', linestyle='--', linewidth=2)\n",
    "\n",
    "plt.xlabel('x')\n",
    "plt.ylabel('y')\n",
    "plt.title('Curve Fitted to Data Points')\n",
    "plt.legend()\n",
    "plt.grid(True)\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "38694351",
   "metadata": {},
   "outputs": [],
   "source": [
    "###Summarize all variable efficiencies\n",
    "#Collect all data frames that start with variable_efficiency\n",
    "dfs = [value for key, value in globals().items() if key.startswith('variable_efficiency') and isinstance(value, pd.DataFrame)]\n",
    "\n",
    "#Choose the first column with the most segments\n",
    "longest_df = max(dfs, key=lambda df: df.shape[0])\n",
    "first_column = longest_df.iloc[:, 0]\n",
    "\n",
    "#Concatenate the remaining columns from all DataFrames, ensuring no duplicate \"first column\"\n",
    "remaining_columns = [df.iloc[:, 1:] for df in dfs]\n",
    "\n",
    "#Concatenate the remaining columns to the longest first column\n",
    "df_variable_efficiency = pd.concat([first_column] + remaining_columns, axis=1)\n",
    "df_variable_efficiency"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "7b94c1a0-c73d-45b6-b048-df9ae8c0261a",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Relate all user_constraints to entity class name \"user_constraint\" \n",
    "\n",
    "Entity_names_duplicate = df_variable_efficiency.iloc[0,1:]\n",
    "User_constraint_entities = []\n",
    "for name in Entity_names_duplicate:\n",
    "    if name not in User_constraint_entities:\n",
    "        User_constraint_entities.append(name)\n",
    "        \n",
    "\n",
    "User_constraint_column = [\"user_constraint\"]*len(User_constraint_entities)\n",
    "\n",
    "merged_columns = {\"Entity class names\": User_constraint_column, \"Entity names\": User_constraint_entities}\n",
    "df_variable_eff_def= pd.DataFrame(merged_columns)\n",
    "df_variable_eff_def"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "f6fb592c",
   "metadata": {},
   "outputs": [],
   "source": [
    "###Summarize all operating points\n",
    "#Collect all data frames that start with operating_points\n",
    "dfs = [value for key, value in globals().items() if key.startswith('operating_points') and isinstance(value, pd.DataFrame)]\n",
    "\n",
    "#Choose the first column with the most segments\n",
    "longest_df = max(dfs, key=lambda df: df.shape[0])\n",
    "first_column = longest_df.iloc[:, 0]\n",
    "\n",
    "#Concatenate the remaining columns from all DataFrames, ensuring no duplicate \"first column\"\n",
    "remaining_columns = [df.iloc[:, 1:] for df in dfs]\n",
    "\n",
    "#Concatenate the remaining columns to the longest first column\n",
    "df_operating_points = pd.concat([first_column] + remaining_columns, axis=1)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "899403f8",
   "metadata": {},
   "outputs": [],
   "source": [
    "###Summarize all ordered_unit_flow_op\n",
    "#Collect all data frames that start with ordered_unit_flow_op\n",
    "dfs = [value for key, value in globals().items() if key.startswith('ordered_unit_flow_') and isinstance(value, pd.DataFrame)]\n",
    "\n",
    "#Concatenate the remaining columns to the longest first column\n",
    "df_boolean_relations = pd.concat(dfs, ignore_index=True)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "99b06362-af38-4e4b-ab1b-fc2f8024bee0",
   "metadata": {},
   "source": [
    "#### Renewables Availability:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "eccc1b34-e4e6-4187-8299-e66590b125d1",
   "metadata": {},
   "outputs": [],
   "source": [
    "#create table headers and relations\n",
    "column_names_1 = {'DateTime '+area: [None, None],\n",
    "                'Solar_Plant_Kasso': ['unit','unit_availability_factor']}\n",
    "df_blank_table_1 = pd.DataFrame(column_names_1, index=None)\n",
    "#add values\n",
    "df_temp_1 = pd.DataFrame(columns=['DateTime ' + area, 'Solar_Plant_Kasso'])\n",
    "\n",
    "df_temp_1['DateTime '+area] = df_time\n",
    "df_temp_1['Solar_Plant_Kasso'] = df_PV_availabilityfactors_values['unit_availability_factor']\n",
    "\n",
    "df_table_1 = pd.concat([df_blank_table_1, df_temp_1])\n",
    "#show table head for control\n",
    "df_table_1.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "46e74f16-846f-4ba0-b9c6-869e32be6676",
   "metadata": {},
   "source": [
    "#### Energy prices:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "4679f8e3-8ce3-4f00-b57e-e3f1427db970",
   "metadata": {},
   "outputs": [],
   "source": [
    "#adjustemnts of power price variance\n",
    "#df_powerprices_values['SpotPriceEUR']\n",
    "\n",
    "# Calculate the current mean and variance\n",
    "mean = df_powerprices_values['SpotPriceEUR'].mean()\n",
    "current_variance = df_powerprices_values['SpotPriceEUR'].var()\n",
    "\n",
    "# Define the new desired variance \n",
    "desired_variance = current_variance * power_price_variance\n",
    "\n",
    "# Calculate the scaling factor\n",
    "scaling_factor = np.sqrt(desired_variance / current_variance)\n",
    "\n",
    "# Adjust the time series to achieve the new variance\n",
    "df_powerprices_values['SpotPriceEUR'] = mean + (df_powerprices_values['SpotPriceEUR'] - mean) * scaling_factor"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "a785d20b-2cbe-4f0b-8842-2878a3335580",
   "metadata": {
    "scrolled": true
   },
   "outputs": [],
   "source": [
    "column_names_2 = {'DateTime ' + area: ['relationship class','connection','node','parameter name'],\n",
    "                'Power_Wholesale_In': ['connection__from_node','power_line_Wholesale_Kasso','Power_Wholesale','connection_flow_cost'], \n",
    "                'Power_Wholesale_Out': ['connection__to_node','power_line_Wholesale_Kasso','Power_Wholesale','connection_flow_cost'], \n",
    "                'District_Heating': ['connection__to_node','pipeline_District_Heating','District_Heating','connection_flow_cost']}\n",
    "df_blank_table_2 = pd.DataFrame(column_names_2, index=None)\n",
    "df_temp_2 = pd.DataFrame(columns=['DateTime ' + area, 'Power_Wholesale_In', 'Power_Wholesale_Out', 'District_Heating'])\n",
    "\n",
    "df_temp_2['DateTime ' + area] = df_time\n",
    "df_temp_2['Power_Wholesale_In'] = price_level_power * df_powerprices_values['SpotPriceEUR']\n",
    "df_temp_2['Power_Wholesale_Out'] = -1 * price_level_power * df_powerprices_values['SpotPriceEUR']\n",
    "df_temp_2['District_Heating'] = -1 * df_district_heating_price[str(year)].loc[2] * share_of_dh_price_cap\n",
    "\n",
    "df_table_2 = pd.concat([df_blank_table_2, df_temp_2], ignore_index=True)\n",
    "#show table head for control\n",
    "df_table_2.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "df00bdab-f254-437f-b78d-d32b19e2f9db",
   "metadata": {},
   "source": [
    "#### Time Series Storage:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "d5e2a8a3",
   "metadata": {},
   "outputs": [],
   "source": [
    "#date index\n",
    "start_date = pd.to_datetime(start_date)\n",
    "before = start_date-timedelta(hours=1)\n",
    "date_index_beginning = pd.date_range(start=before, end=start_date, freq='H')\n",
    "formatted_beginning = date_index_beginning.strftime('%Y-%m-%dT%H:%M:%S')\n",
    "df_formatted_beginning = pd.DataFrame(formatted_beginning, columns=['DateTime'])\n",
    "df_time_beginning = pd.DataFrame(df_formatted_beginning)\n",
    "#add one blank row\n",
    "new_row = pd.Series([])\n",
    "df_time_beginning = pd.concat([pd.DataFrame([new_row]), df_time_beginning]).reset_index(drop=True)\n",
    "\n",
    "#concat raw data with time index\n",
    "storage_values = df_model_storages.iloc[:,[0, 1, 2, 6]]\n",
    "storage_values = storage_values.iloc[:, [0, 3, 1, 2]]\n",
    "storage_values_transposed = storage_values.T\n",
    "storage_values_transposed.columns = storage_values_transposed.iloc[0]\n",
    "storage_values_transposed = storage_values_transposed[1:]\n",
    "storage_values_transposed.reset_index(drop=True, inplace=True)\n",
    "\n",
    "df_storage = pd.concat([df_time_beginning, storage_values_transposed], axis=1)\n",
    "#show table head for control\n",
    "df_storage.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "89b971c4",
   "metadata": {},
   "source": [
    "#### Model relations:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "ccf465d5",
   "metadata": {},
   "outputs": [],
   "source": [
    "#Writing definition of model components\n",
    "column_names_model_components = {'Object_class_name':['model','temporal_block','stochastic_scenario', 'stochastic_structure', 'report'],\n",
    "                      'Object_name': [model_name, temporal_block, stochastic_scenario, stochastic_structure, report_name]}\n",
    "df_model_components = pd.DataFrame(column_names_model_components, index=None)\n",
    "\n",
    "#Addin a default invetsment temporal block \n",
    "df_model_components.loc[len(df_model_components.index)] = ['temporal_block', 'Default_Investment_period']\n",
    "\n",
    "#outputs:\n",
    "df_outputs = pd.DataFrame({\n",
    "    'Object_class_name': ['output']*len(reports),\n",
    "    'Object_name': reports\n",
    "})\n",
    "df_model_components = pd.concat([df_model_components, df_outputs], axis=0)\n",
    "df_model_components = df_model_components.reset_index(drop=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "c335dd9b",
   "metadata": {},
   "outputs": [],
   "source": [
    "#reports\n",
    "column_names_model_structure = {'Object_class_name':['model','temporal_block','stochastic_scenario', 'stochastic_structure', 'report'],\n",
    "                      'Object_name': [model_name, temporal_block, stochastic_scenario, stochastic_structure, report_name]}\n",
    "df_reports = pd.DataFrame({\n",
    "    'Relationship_class_name': ['report__output']*len(reports),\n",
    "    'Object_class_name_1': ['report']*len(reports),\n",
    "    'Object_class_name_2': ['output']*len(reports),\n",
    "    'Object_name_1': [report_name]*len(reports),\n",
    "    'Object_name_2': reports\n",
    "})\n",
    "#everything else\n",
    "df_model_struc = pd.DataFrame({\n",
    "    'Relationship_class_name': ['model__temporal_block','model__default_temporal_block', \n",
    "                                'model__stochastic_structure', 'model__default_stochastic_structure',\n",
    "                                'stochastic_structure__stochastic_scenario', 'model__report'],\n",
    "    'Object_class_name_1': ['model','model','model','model','stochastic_structure','model'],\n",
    "    'Object_class_name_2': ['temporal_block', 'temporal_block','stochastic_structure','stochastic_structure', 'stochastic_scenario','report'],\n",
    "    'Object_name_1': [model_name, model_name,model_name,model_name,stochastic_structure, model_name],\n",
    "    'Object_name_2': [temporal_block, temporal_block, stochastic_structure, stochastic_structure, stochastic_scenario, report_name]\n",
    "})\n",
    "df_model_relations = pd.concat([df_model_struc, df_reports], axis=0)\n",
    "df_model_relations = df_model_relations.reset_index(drop=True)\n",
    "\n",
    "# Defining default invetsment temporal block\n",
    "df_model_relations.loc[len(df_model_relations.index)] = ['model__default_investment_temporal_block', 'model', 'temporal_block', model_name, 'Default_Investment_period']\n",
    "\n",
    "# Defining default investment stochastic structure \n",
    "df_model_relations.loc[len(df_model_relations.index)] = ['model__default_investment_stochastic_structure', 'model', 'stochastic_structure', model_name, stochastic_structure]\n",
    "\n",
    "#show table head for control\n",
    "df_model_relations.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "892b88dc-3a5b-41c5-b184-64593c28c72c",
   "metadata": {},
   "source": [
    "#### Model:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "3960d14b-394b-4599-9e1e-8831aa59e6f8",
   "metadata": {},
   "outputs": [],
   "source": [
    "### take first 3 columns and add another table with \"Alternative\", \"Value\"\n",
    "column_names_model = {'Object_class_name':['model','model','temporal_block'],\n",
    "                      'Object_name': [model_name, model_name, temporal_block],\n",
    "                      'Parameter':['model_start','model_end','resolution'],\n",
    "                      'Alternative': [scenario, scenario, scenario],\n",
    "                      'Value': ['{\"type\": \"date_time\", \"data\": \"'+df_time.iloc[0]['DateTime']+'\"}',\n",
    "                          '{\"type\": \"date_time\", \"data\": \"'+df_time.iloc[-1]['DateTime']+'\"}', \n",
    "                          '{\"type\":\"duration\", \"data\": \"'+frequency+'\"}']}\n",
    "df_model = pd.DataFrame(column_names_model, index=None)\n",
    "\n",
    "#Add investment temporal blocks to model data frame\n",
    "df_model.loc[len(df_model.index)] = ['temporal_block', 'Default_Investment_period', 'resolution', scenario, '{\"type\":\"duration\", \"data\": \"'+investment_period_default+'\"}']\n",
    "\n",
    "#show table head for control\n",
    "df_model.head()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "4b24d678-4167-4521-a6ab-aae160dc13ae",
   "metadata": {},
   "outputs": [],
   "source": [
    "# add information in case roll forward is used\n",
    "if roll_forward_use == True:\n",
    "    if temporal_block == 'hourly':\n",
    "        unit = 'h'\n",
    "    elif temporal_block == 'daily':\n",
    "        unit = 'D'\n",
    "    elif temporal_block == 'monthly':\n",
    "        unit = 'M'\n",
    "    else:\n",
    "        unit = ''\n",
    "        print(\"\\033[91mWARNING:\\033[0m Duration not defined!!!\")\n",
    "    #now add the new row to the df\n",
    "    roll_forward_size_with_unit = str(roll_forward_size) + unit\n",
    "    roll_forward_row = {'Object_class_name': 'model', \n",
    "                        'Object_name': model_name, \n",
    "                        'Parameter': 'roll_forward',\n",
    "                        'Alternative': scenario,\n",
    "                        'Value': '{\"type\": \"duration\", \"data\": \"' + roll_forward_size_with_unit +'\"}'\n",
    "                       }\n",
    "    # Add new row to df_model DataFrame\n",
    "    df_model.loc[len(df_model)] = roll_forward_row"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "14842492",
   "metadata": {},
   "outputs": [],
   "source": [
    "# temporal resolution for demand\n",
    "#Add temporal block to definition, if necessary\n",
    "df_model_units['resolution_output'].apply(lambda x: check_temporal_block(x, df_model_components))\n",
    "\n",
    "#Add relation to respective node\n",
    "df_model_units.apply(lambda row: create_temporal_block_relationships(row['resolution_output'],row['Output1'], df_model_relations, model_name, df_definition),axis=1)\n",
    "\n",
    "#Add values to temporal block\n",
    "df_model_units['resolution_output'].apply(lambda x: create_temporal_block_input(x, df_model))"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "18dfbf3e-1928-4547-8b3a-dac782ca46a3",
   "metadata": {},
   "source": [
    "### Creating one combined excel and export"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "5523a4cd-ad6f-44d6-993d-3ebaf00680c2",
   "metadata": {},
   "outputs": [],
   "source": [
    "#create the prepared input excel for the use in SpineToolbox\n",
    "with pd.ExcelWriter(output_file_path + output_file_name) as writer:\n",
    "    df_definition.to_excel(writer, sheet_name='Definition', index=False)\n",
    "    unit_parameters_rest_df.to_excel(writer, sheet_name='Definition_parameters', index=False)\n",
    "    unit_parameters_duration_df.to_excel(writer, sheet_name='Definition_parameters_duration', index=False)\n",
    "    df_units_inv_parameters.to_excel(writer, sheet_name='Unit_Investment_Parameters', index=False)\n",
    "    df_nodes.to_excel(writer, sheet_name='Nodes', index=False)\n",
    "    df_connections.to_excel(writer, sheet_name='Connections', index=False)\n",
    "    df_object__node_definitions.to_excel(writer, sheet_name='Object__to_from_node_definition', index=False)\n",
    "    df_object__node_values.to_excel(writer, sheet_name='Object__to_from_node', index=False)\n",
    "    df_boolean_relations.to_excel(writer, sheet_name='Boolean_relations', index=False)\n",
    "    df_object_node_node.to_excel(writer, sheet_name='Object__node_node', index=False)\n",
    "    df_variable_eff_def.to_excel(writer, sheet_name='Variable_Eff_Definition', index=False)\n",
    "    df_variable_efficiency.to_excel(writer, sheet_name='Variable_Eff', index=False)\n",
    "    df_operating_points.to_excel(writer, sheet_name='Operating_points', index=False)\n",
    "    df_storage.to_excel(writer, sheet_name='Time_series_storage', index=False)\n",
    "    df_table_1.to_excel(writer, sheet_name='Demand', index=False)\n",
    "    df_table_2.to_excel(writer, sheet_name='Energy_prices', index=False)\n",
    "    df_model_components.to_excel(writer, sheet_name='Model_components', index=False)\n",
    "    df_model_relations.to_excel(writer, sheet_name='Model_relations', index=False)\n",
    "    df_model.to_excel(writer, sheet_name='Model', index=False)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "7ecfd010-a65f-4cfc-8ec2-a7d3bbded502",
   "metadata": {},
   "outputs": [],
   "source": [
    "#create output of the mapping excel\n",
    "with pd.ExcelWriter(output_file_path + output_mapping_file_name) as writer:\n",
    "    df_model_object_mapping.to_excel(writer, sheet_name='Object_Mapping', index=False)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "6fd66540-33e4-4200-8c13-6ee0ed292334",
   "metadata": {},
   "outputs": [],
   "source": [
    "#copy efficiency\n",
    "other_name = \"other.xlsx\"\n",
    "with pd.ExcelWriter(output_file_path + other_name) as writer:\n",
    "    df_efficiency_electrolyzer_adj.to_excel(writer, sheet_name='efficiency', index=False)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "ba92e5da-4779-47e6-b5f6-ffd79ec6298c",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.7"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
