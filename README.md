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

# Proportion of Variation Analysis

The Proportion of Variation Analysis is used to evaluate the impact of different components, i.e. network, scenario, algorithm, on the performance of a privacy assistant. 

**File**: RPOV.py\
**Requirements**: Multiple algorithms, networks scenarios to be analyzed.

The code expects a CSV file containing the data for the different scenarios, network and algorithm to be analyzed. The CSV file should contain columns for the network, algorithm, and scenario and measured factors. The code analyzes the data by performing an ANOVA test on each variable and factor combination. The output of the analysis is a dictionary that contains the proportion of variation explained by each factor and factor combination. The results can be used to determine the most significant factors and factor combinations that affect the privacy assistant performance the most.