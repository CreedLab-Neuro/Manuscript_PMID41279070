# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 21:38:27 2024

@author: meagh
"""

import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import ols
import statsmodels.api as sm
from statsmodels.formula.api import ols
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

# Directory containing .csv files
directory = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\Haloperidol\rPR_7h')
#directory = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Acute')
 #%%

# List to hold data for each file
data_list = []

# Iterate over each file in the directory
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        # Extract file name without extension
        file_name_without_ext = os.path.splitext(filename)[0]
        
        # Determine 'Sex' based on file name
        if 'M_' in file_name_without_ext:
            sex = 'M'
        elif 'F_' in file_name_without_ext:
            sex = 'F'
        else:
            sex = 'Uknown'
        
        # Determine 'Group' based on file name
        if '_H1_' in file_name_without_ext:
            group = 'HAL'
        elif '_V1_' in file_name_without_ext:
            group = 'VEH'
        else:
            group = 'Oops'

        
        # Read the csv file
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path)
        
        # Check if required columns are present
        if 'Binary_Left_Pokes' in df.columns:
            # Procedure for files with 'Binary_Left_Pokes'
            
            # Calculate 'Pellets'
            pellets = (df['Event'] == 'Pellet').sum()
            
            # Calculate 'PPP1'
            binary_left_pokes_sum = df['Binary_Left_Pokes'].sum()
            ppp1 = binary_left_pokes_sum / pellets if pellets > 0 else 0
            
            # Calculate 'PPP2'
            ppp2 = df['Event'].str.contains('oke').sum() / pellets if pellets > 0 else 0
            
            # Calculate 'Accuracy'
            correct_pokes = df['Correct_Poke'].sum()
            total_pokes = df['Binary_Left_Pokes'].sum() + df.get('Binary_Right_Pokes', pd.Series()).sum()
            accuracy = correct_pokes / total_pokes if total_pokes > 0 else 0
        
        else:
            # Procedure for files without 'Binary_Left_Pokes'
            
            # Calculate 'Pellets'
            pellets = (df['Event'] == 'Pellet').sum()
            
            # Calculate 'PPP1'
            left_pokes = df['Event'].str.contains('Left').sum()
            ppp1 = left_pokes / pellets if pellets > 0 else 0
            
            # Calculate 'PPP2'
            left_pokes = df['Event'].str.contains('Left').sum()
            right_pokes = df['Event'].str.contains('Right').sum()
            ppp2 = (left_pokes + right_pokes) / pellets if pellets > 0 else 0
            
            # Calculate 'Accuracy'
            correct_pokes = df['Event'].str.contains('Left').sum()
            total_pokes = df['Event'].str.contains('Left').sum() + df['Event'].str.contains('Right').sum()
            accuracy = correct_pokes / total_pokes if total_pokes > 0 else 0
        
        # Create a dictionary for the current file
        file_data = {
            'File': filename,
            'Sex': sex,
            'Group': group,
            'Pellets': pellets,
            'PPP1': ppp1,
            'PPP2': ppp2,
            'Accuracy': accuracy
        }
        
        # Append the dictionary to the list
        data_list.append(file_data)

# Create a DataFrame from the list of dictionaries
df_summary = pd.DataFrame(data_list)

# Save the DataFrame to a new .csv file
df_summary.to_csv('PR_summary_metadata_Haloperidol.csv', index=False)

print("Summary DataFrame created and saved to 'summary_metadata.csv'.")
#%%
df_analysis = pd.read_csv('PR_summary_metadata_Haloperidol.csv') ## CHANGE TO WHAT YOU'VE GOT ABOVE

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

sns.boxplot(x="Pellets", y = 'Group', data = df_analysis, palette='magma', ax=axes[0])
sns.swarmplot(x="Pellets", y = 'Group', data = df_analysis, hue= 'Sex',ax=axes[0])
axes[0].set_title('Pellets')

sns.boxplot(x="PPP1", y = 'Group', data = df_analysis, palette='magma', ax=axes[1])
sns.swarmplot(x="PPP1", y = 'Group', data = df_analysis, hue= 'Sex',ax=axes[1]) 
axes[1].set_title('Pokes per Pellet')

sns.boxplot(x="Accuracy", y = 'Group', data = df_analysis, palette='magma', ax=axes[2])
sns.swarmplot(x="Accuracy", y = 'Group', data = df_analysis, hue= 'Sex',ax=axes[2])
axes[2].set_title('Accuracy')

plt.savefig('PR_summary_metadata_HaloperidolSWARM.svg')
#%%
df_analysis = pd.read_csv('PR_summary_metadata_Haloperidol.csv')
# Define the model
model = ols('PPP1 ~ C(Sex) * C(Group)', data=df_analysis).fit()

# Perform the ANOVA
anova_table = sm.stats.anova_lm(model, typ=2)

# Print the ANOVA table
print("Summary 2 way ANOVA for Pokes per Pellets rPR Pellets")
print(anova_table)

# Group the data by 'Group' and 'Sex', then calculate the mean and SEM for each group
grouped = df_analysis.groupby(['Group', 'Sex'])['PPP1']

# Calculate the mean
means = grouped.mean()

# Calculate the SEM
sems = grouped.sem()

# Print the results
print("Means by Group and Sex:")
print(means)

print("\nSEMs by Group and Sex:")
print(sems)

#%%
# Define the model
df_analysis = pd.read_csv('PR_summary_metadata_Haloperidol.csv') ## CHANGE TO WHAT YOU'VE GOT ABOVE
model = ols('Accuracy ~ C(Sex) * C(Group)', data=df_analysis).fit()

# Perform the ANOVA
anova_table = sm.stats.anova_lm(model, typ=2)

# Print the ANOVA table
print("Summary 2 way ANOVA for Accuracy")
print(anova_table)

# Group the data by 'Group' and 'Sex', then calculate the mean and SEM for each group
grouped = df_analysis.groupby(['Group', 'Sex'])['Accuracy']

# Calculate the mean
means = grouped.mean()

# Calculate the SEM
sems = grouped.sem()

# Print the results
print("Means by Group and Sex:")
print(means)

print("\nSEMs by Group and Sex:")
print(sems)

 # Group the data by 'Group' and 'Sex', then calculate the mean and SEM for each group
grouped = df_analysis.groupby(['Group'])['Accuracy']

 # Calculate the mean
means = grouped.mean()

 # Calculate the SEM
sems = grouped.sem()

 # Print the results
print("Means by Group:")
print(means)

print("\nSEMs by Group:")
print(sems)















