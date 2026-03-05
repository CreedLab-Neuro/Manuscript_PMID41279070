# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 22:46:23 2024

@author: meagh
"""

import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import ols
#%%
# Directory containing the CSV files
directory = r'C:\Users\meaghan.creed\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_FR1\ProcessedData'# Initialize lists to store file names and groups

# List all .csv files in the directory (case insensitive)
csv_files = [f for f in os.listdir(directory) if f.lower().endswith('.csv')]
print(csv_files)

#%%
# Initialize an empty list to store the summary
summary_data = []

# Loop through each file and classify based on the file name ending
for file in csv_files:
    file_lower = file.lower()
    if file_lower.endswith('fsham.csv'):
        group = 'FSHAM'
    elif file_lower.endswith('msham.csv'):
        group = 'MSHAM'
    elif file_lower.endswith('fsni.csv'):
        group = 'FSNI'
    elif file_lower.endswith('msni.csv'):
        group = 'MSNI'
    else:
        group = 'Unknown'
    
    # Append the file name and group to the summary data
#    summary_data.append([file, group])

# # Create a DataFrame from the summary data
# summary_df = pd.DataFrame(summary_data, columns=['File Name', 'Group'])

# # Print the summary DataFrame
# print(summary_df)

    # Load the current CSV file
    file_path = os.path.join(directory, file)
    try:
        df = pd.read_csv(file_path)
        
        # Count the occurrences of "Pellet" in the "Event" column
        pellets = (df['Event'] == 'Pellet').sum()

        # Count the occurrences of "Left" or "Right" in the "Event" column
        #pokes = df['Event'].str.contains('Left|Right', case=False, na=False).sum()
        left = (df['Event'] == 'Left').sum()
        right = (df['Event'] == 'Right').sum()
        pokes = left + right
        
        #Calculatae efficiency
        efficiency = pokes/pellets
        
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        pellets, pokes = 0, 0  # In case of error, set counts to 0
    
#     # Append the data (file name, group, pellets, and pokes) to the summary list
#     summary_data.append([file, group, pellets, pokes, efficiency])

# # Create a DataFrame from the summary data
# summary_df = pd.DataFrame(summary_data, columns=['File Name', 'Group', 'Pellets', 'Pokes', 'Efficiency'])

# # Print the summary DataFrame
# print(summary_df)

    # Determine "Sex" and "Treatment" based on the "Group"
    if group == 'FSHAM':
        sex = 'F'
        treatment = 'SHAM'
    elif group == 'MSHAM':
        sex = 'M'
        treatment = 'SHAM'
    elif group == 'FSNI':
        sex = 'F'
        treatment = 'SNI'
    elif group == 'MSNI':
        sex = 'M'
        treatment = 'SNI'
    else:
        sex = 'Unknown'
        treatment = 'Unknown'
    
    # Append the data (file name, group, pellets, pokes, sex, and treatment) to the summary list
    summary_data.append([file, group, pellets, pokes, efficiency, sex, treatment])

# Create a DataFrame from the summary data
summary_df = pd.DataFrame(summary_data, columns=['File Name', 'Group', 'Pellets', 'Pokes', 'Efficiency', 'Sex', 'Treatment'])

# Print the summary DataFrame
print(summary_df)
#%%
#%%
# Drop rows where Group is 'Unknown'
summary_df = summary_df[summary_df['Group'] != 'Unknown']
fig, axes = plt.subplots(1, 2, figsize=(18, 6))

sns.boxplot(x="Pellets", y = 'Treatment', data = summary_df, palette='seismic', ax=axes[0])
sns.swarmplot(x="Pellets", y = 'Treatment', data = summary_df, hue= 'Sex', ax=axes[0])
axes[0].set_title('Pellets')

sns.boxplot(x="Efficiency", y = 'Treatment', data = summary_df, palette='seismic', ax=axes[1])
sns.swarmplot(x="Efficiency", y = 'Treatment', data = summary_df, hue= 'Sex',ax=axes[1])
axes[1].set_title('Efficiency')

# sns.boxplot(x="Accuracy", y = 'Group', data = df_analysis, palette='seismic', ax=axes[2])
# sns.scatterplot(x="Accuracy", y = 'Group', data = df_analysis, hue= 'Sex',ax=axes[2])
# axes[2].set_title('Accuracy')

#plt.savefig('FR1_SummaryPelletsEfficiencyChronic.svg')
#%%
# Define the model
model = ols('Efficiency ~ C(Sex) * C(Treatment)', data=summary_df).fit()

# Perform the ANOVA
anova_table = sm.stats.anova_lm(model, typ=2)

# Print the ANOVA table
print("Summary 2 way ANOVA for FR1 Pokes/Pellet")
print(anova_table)
print()

model = ols('Pellets ~ C(Sex) * C(Treatment)', data=summary_df).fit()

# Perform the ANOVA
anova_table = sm.stats.anova_lm(model, typ=2)

# Print the ANOVA table
print("Summary 2 way ANOVA for FR1 Pellet")
print(anova_table)