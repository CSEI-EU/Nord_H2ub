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

The energy hubmodel is a tool to evaluate the production of hydrogen and hydrogen derivatives based on renewable electricity. The model uses the framework provided by SpineOpt for the optimization. The data management is based on the tools provided by SpineToolbox. The energy hub model provides three key features: input data preparation, optimization, and result analysis. The input data preparation consists of a data base of technology data, and enables the user to define the technologies and parameters of an energy hub as well as input data preparation and output data preperation routines. The input data preparation features an intuitive graphical interface built in Jupyter Notebook, supported by Python routines to specify case specific parameters.

The optimization phase utilizes SpineOpt, a robust optimization platform implemented in Julia. The EHM currently supports the production of multiple renewable fuels, including hydrogen, ammonia, methanol, gasoline, jet fuel, and methane. The focus is on optimizing energy flows and system interactions within a multi-energy system. The MILP appraoch offers an investment as well as an pure dispatch optimization, while accounting for technical constraints, as well as the economic and technical processes involved in fuel production, storage, and transportation. Within the Spine environment, the energy hub is modeled using object types such as units, nodes, and connections. These objects are interconnected through direct relationships or indirect links mediated by a third object. Nodes serve as buses between units or connections and can also function as storage components.

Finally, Python routines in Jupyter Notebook process and analyze the output data The results are assessed based on the levelized cost of energy. 

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

## Contributing

The energy hub model development is developed by the following people. 

| Person | Contribution |
| --- | --- |
| Johannes Giehl | major development & conceptualization & data collection <br> development of the basic model and tool structure, conceptualizing the input and output data preparation structure and developing functions |
| Dana Hentschel | major development & conceptualization & data collection <br> development of the basic model and tool structure, conceptualizing the input data preparation structure and developing functions |
| Lucia Ciprian | major development & data collection <br> development of the structure of the hub configurations, conceptualizing the output data preparation structure and developing functions|
| Jens Weibezahn | Conceptualization & modelling feedback |

## Citing

We are currently working on a publication to introduce and apply the energy hub model. 

For the current use of the model, please cite: 
Giehl, J., Hentschel, D., Ciprian, L., and Weibezahn, J. (2024): The energy hub model. Applying SpineOpt and SpineToolbox to model synthetic fuels. Copenhagen School of Energy Infrastructure (CSEI), https://github.com/CSEI-EU/Nord_H2ub/, accessed YYYY-MM-DD.

## License

The Energy Hub Model is licensed under under the same license as Spine Tools, GNU Lesser General Public License version 3.0 or later.
