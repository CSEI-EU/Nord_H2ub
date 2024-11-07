# The Energy Hub Model

**CSEI's energy hub model**

This is the energy hub model of the Copenhagen School of Energy Infrastructure. The model is a energy system optimization model based on SpineToolbox and SpineOpt. 

For further information about the Spine tools look here: https://github.com/spine-tools

## Contents
* [Description](#Description)
* [Documentation](#documentation)
* [Installation](#installation)
    * [Setting up Spine Tools](#setting-up-spinetools)
    * [Python Packages](#python-packages)
* [Contributing](#contributing)
* [Citing](#citing)
* [License](#License)

## Description

The energy hubmodel is a tool to evaluate the production of hydrogen and hydrogen derivatives based on renewable electricity. The model uses the framework provided by SpineOpt for the optimization. The data management is based on the tools provided by SpineToolbox. The energu hub model provides a data base of technology data, and enables the user to define the technologies and parameters of an energy hub as well as input data preparation and output data preperation routines. The energy hub model offers an investment as well as an pure dispatch optimization. The results are assessed based on the levelized cost of energy. 

## Installation

Please follow the instructions to install SpineOpt (https://github.com/spine-tools/SpineOpt.jl) and SpineToolbox (https://github.com/Spine-tools/Spine-Toolbox). 

The current version of the energy hub model uses SpineOpt v0.8.3 and SpineToolbox v.0.8.2 in combination with Pytohn 3.9.

For the data prepratation, we recommend a virtual environment (e.g. using Anaconda). There you have to install the follwoing packages: 

- numpy
- pandas
- os
- calendar
- datetime
- time
- matplotlib
- re
- sys
- math
- ipywidgets
- IPython
- threading
- subprocess
- papermill
- platform
- pickle
- requests

## License

The Energy Hub Model is licensed under under the same license as Spine Tools, GNU Lesser General Public License version 3.0 or later.
