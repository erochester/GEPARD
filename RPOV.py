import pandas as pd
import os
import statsmodels.formula.api as smf
import statsmodels.stats.anova as sma
import logging

"""
Calculates the relative proportion of variation over the tournament results 
to analyze the contribution of each PA component to the overall performance of the PA.
"""

# Ask user for file path
file_path = input("Enter file path to results file (.csv): ")

# Check if file exists
if not os.path.isfile(file_path):
    logging.error("File not found. Exiting...")
    exit()

# Read in the CSV file
df = pd.read_csv(file_path)

# replace 'Average User Utility' and 'Total User Power Consumption (kWh)' with the column names you want to analyze
for col in ['Consent Percentage (%)', 'Average User Utility', 'Total User Power Consumption (W)',
            'Total User Time Spent (s)']:
    formula = f"Q(\'{col}\') ~ Network + Protocol + Scenario + Network:Protocol + Network:Scenario + Protocol:Scenario"
    model = smf.ols(formula=formula, data=df).fit()

    # compute the ANOVA table to get the sum of squares for each factor and factor combination
    anova_table = sma.anova_lm(model, typ=2)
    sst = anova_table['sum_sq'].sum()

    # compute the proportion of variation explained by each factor and factor combination
    variation_prop = {
        'Network': anova_table.loc['Network', 'sum_sq'] / sst,
        'Protocol': anova_table.loc['Protocol', 'sum_sq'] / sst,
        'Scenario': anova_table.loc['Scenario', 'sum_sq'] / sst,
        'Network:Protocol': anova_table.loc['Network:Protocol', 'sum_sq'] / sst,
        'Network:Scenario': anova_table.loc['Network:Scenario', 'sum_sq'] / sst,
        'Protocol:Scenario': anova_table.loc['Protocol:Scenario', 'sum_sq'] / sst
    }

    # sort the proportion of variation dictionary by values
    sorted_variation_prop = sorted(variation_prop.items(), key=lambda x: x[1], reverse=True)

    logging.info(col)
    for factor, prop in sorted_variation_prop:
        logging.info(f"Proportion of variation - {factor}: {prop}")
    logging.info("------------------------")
