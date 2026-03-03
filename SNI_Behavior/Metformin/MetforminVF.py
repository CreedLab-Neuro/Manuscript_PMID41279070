# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 14:44:18 2025

@author: meaghan.creed
"""

import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import ols

df = pd.read_csv(r'C:\Users\meaghan.creed\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\Metformin\MetforminVF.csv')
#%%
# Melt dataframe to long format
df1 = df.melt(id_vars=['Subject', "Sex"], value_vars=['Pre', 'Post', 'Veh', 'Met', 'Sal'], var_name='Condition', value_name='Value')
df2 = df.melt(id_vars=['Subject', "Sex"], value_vars=['PreL', 'PostL', 'VEHL', 'MetL', 'SalL'], var_name='Condition', value_name='Value')

#%%
sns.lineplot(data = df1, x = "Condition", y = "Value", hue = 'Sex', units = "Subject", estimator = None, alpha = 0.5)
sns.lineplot(data = df1, x = "Condition", y = "Value", marker ='o', color = 'black')
plt.savefig('MetforminVonFrey.svg')

#%%
sns.lineplot(data = df2, x = "Condition", y = "Value", hue = 'Sex', units = "Subject", estimator = None, alpha = 0.5)
sns.lineplot(data = df2, x = "Condition", y = "Value", marker ='o', color = 'black')
plt.savefig('MetforminVonFreyV2.svg')
#%%
# Define the model
model = ols('Value ~ C(Sex) * C(Condition)', data=df2).fit()

# Perform the ANOVA
anova_table = sm.stats.anova_lm(model, typ=2)

# Print the ANOVA table
print("Summary 2 way ANOVA for Pokes per Pellets rPR Pellets")
print(anova_table)
#%%
# Group the data by 'Group' and 'Sex', then calculate the mean and SEM for each group
grouped = df2.groupby(['Condition'])['Value']

# Calculate the mean
means = grouped.mean()

# Calculate the SEM
sems = grouped.sem()

# Print the results
print("Means by Group and Sex:")
print(means)

print("\nSEMs by Group and Sex:")
print(sems)