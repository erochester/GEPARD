# GEPARD (General Environment for Privacy Assistant Research and Design)

**Gepard**, meaning "cheetah" in a number of languages. The Gepard project is a research project that aims to develop a general environment for privacy assistant design and evaluation.

## Requirements

To run this project, you will need:

Python 3.9 or higher
The following Python packages:
 * matplotlib
 * numpy
 * pandas
 * scipy
 * statsmodels
 * tqdm

The code was created and tested on Python 3.9.6.

## Installation

1) Clone this repository: git clone https://github.com/erochester/GEPARD.git
2) Install the required Python packages: pip install -r requirements.txt

## Running the Code

The code can be run in 2 ways:
1) Individual Run
```
python3 main.py -p <protocol> -n <network> -s <scenario> [-d <distribution>]
```
Currently implemented values are:
|Protocols|Networks|Scenarios|Distributions|
|----------|--------|---------|-------------|
|alanezi|ble|hospital|poisson|
|cunche|zigbee|shopping_mall|-|
|concession|lora|university|-|
2) Tournament-style Run (make sure to review "tournament_setup.xml" for tournament settings and make appropriate changes)
```
python3 main.py -t
```

# Proportion of Variation Analysis

The Proportion of Variation Analysis is used to evaluate the impact of different components, i.e. network, scenario, and protocol, on the performance of a privacy assistant. 

**File**: RPOV.py\
**Requirements**: Multiple protocols, networks, and scenarios to be analyzed.

The code expects a CSV file containing the data for the different scenarios, networks, and protocols to be analyzed. The CSV file should contain columns for the network, protocol, and scenario, and measured factors. The code analyzes the data by performing an ANOVA test on each variable and factor combination. The output of the analysis is a dictionary that contains the proportion of variation explained by each factor and factor combination. The results can be used to determine the most significant factors and factor combinations that affect the privacy assistant performance the most.
