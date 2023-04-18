import pandas as pd
import os
import statsmodels.formula.api as smf
import statsmodels.stats.anova as sma


# Ask user for file path
file_path = input("Enter file path to results file (.csv): ")

# Check if file exists
if not os.path.isfile(file_path):
    print("File not found. Exiting...")
    exit()

# Read in the CSV file
df = pd.read_csv(file_path)

# replace 'Average User Utility' and 'Total User Power Consumption (kWh)' with the column names you want to analyze
for col in ['Consent Percentage (%)', 'Average User Utility', 'Total User Power Consumption (kWh)',
            'Total User Time Spent (s)']:
    formula = f"Q(\'{col}\') ~ Network + Algorithm + Scenario + Network:Algorithm + Network:Scenario + Algorithm:Scenario"
    model = smf.ols(formula=formula, data=df).fit()

    # compute the ANOVA table to get the sum of squares for each factor and factor combination
    anova_table = sma.anova_lm(model, typ=2)
    sst = anova_table['sum_sq'].sum()

    # compute the proportion of variation explained by each factor and factor combination
    variation_prop = {
        'Network': anova_table.loc['Network', 'sum_sq'] / sst,
        'Algorithm': anova_table.loc['Algorithm', 'sum_sq'] / sst,
        'Scenario': anova_table.loc['Scenario', 'sum_sq'] / sst,
        'Network:Algorithm': anova_table.loc['Network:Algorithm', 'sum_sq'] / sst,
        'Network:Scenario': anova_table.loc['Network:Scenario', 'sum_sq'] / sst,
        'Algorithm:Scenario': anova_table.loc['Algorithm:Scenario', 'sum_sq'] / sst
    }

    # sort the proportion of variation dictionary by values
    sorted_variation_prop = sorted(variation_prop.items(), key=lambda x: x[1], reverse=True)

    print(col)
    for factor, prop in sorted_variation_prop:
        print(f"Proportion of variation - {factor}: {prop}")
    print("------------------------")
