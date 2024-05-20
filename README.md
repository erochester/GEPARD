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
**Note**: We provide _example_scenario_ option and class to test the code with small number of users in the environment, since other scenarios may take long time to run:
```
python3 main.py -p <protocol> -n <network> -s example_scenario [-d <distribution>]
```
The example scenario supports any network technology and negotiation protocol.

_Currently implemented values are_:
|Protocols|Networks|Scenarios|Distributions|
|----------|--------|---------|-------------|
|alanezi|ble|hospital|poisson|
|cunche|zigbee|shopping_mall|-|
|concession|lora|university|-|
|-|-|example_scenario|-|

2) Tournament-style Run (make sure to review "tournament_setup.xml" for tournament settings and make appropriate changes)
```
python3 main.py -t
```
## Results

The results are stored under the _results_ folder.

# Proportion of Variation Analysis

The Proportion of Variation Analysis is used to evaluate the impact of different components, i.e. network, scenario, and protocol, on the performance of a privacy assistant. 

**File**: RPOV.py\
**Running the Code**: 
```
python3 RPOV.py
```
**Requirements**: Multiple protocols, networks, and scenarios to be analyzed.

_Note_: The code expects a CSV file containing the data for the different scenarios, networks, and protocols to be analyzed. The CSV file should contain columns for the network, protocol, and scenario, and measured factors. The code analyzes the data by performing an ANOVA test on each variable and factor combination. The output of the analysis is a dictionary that contains the proportion of variation explained by each factor and factor combination. The results can be used to determine the most significant factors and factor combinations that affect the privacy assistant performance the most.

# Notes/Assumptions

**Assumptions**:

1. The users traverse the IoT environment with the provided speed, without any stops or changes in the speed.
2. For now, we assume that the IoT owner precisely knows the user's privacy preferences and what to offer to them. We can add the estimator further down the line, but for now, we go through the list of users, offer to them the privacy policies and see if they consent and if it is after 1 phase or 2 phases

## Introducing new scenarios, networking technologies or negotiation protocols

To implement any new scenarios, networking technologies or negotiation protocols, mainly 2 things need to be done:
1. Create the new class. For any assumptions or as a starter you may want to use the existing classes.
2. Add the new class to the respective "metaclass", e.g., for scenarios it is _scenario.py_
