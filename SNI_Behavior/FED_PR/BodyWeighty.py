# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 22:46:01 2024

@author: meagh
"""
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import ols
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

df = pd.read_csv(r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\Haloperidol\Haloperidol_BodyWeights.csv')
#%%
# Filter data for 'Acute' and 'Chronic' TimePoints
acute_data = df[df['TimePoint'] == 'Null']
chronic_data = df[df['TimePoint'] == 'Chronic']

print(acute_data)
#%%

# Create a figure with 2 subplots (one for Acute, one for Chronic)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Boxplot for 'Acute'
sns.boxplot(data=acute_data, x='Group', y='Weight', hue='Sex', ax=axes[0])
axes[0].set_title('Weight Distribution (Acute)')
axes[0].set_xlabel('Group')
axes[0].set_ylabel('Weight')

# # Boxplot for 'Chronic'
# sns.boxplot(data=chronic_data, x='Group', y='Weight', hue='Sex', ax=axes[1])
# axes[1].set_title('Weight Distribution (Chronic)')
# axes[1].set_xlabel('Group')
# axes[1].set_ylabel('Weight')

# Adjust the layout and show the plot
plt.tight_layout()
#plt.show()
#plt.savefig('METBodyWeights.svg')

#%%
#acute_data = acute_data.dropna()
model = ols('Group ~ C(Sex)', data=acute_data).fit()
#%%
# Fit the two-way ANOVA model
# 'Weight' is the dependent variable, 'Group' and 'Sex' are independent factors
model = ols('Weight ~ C(Group) * C(Sex)', data=acute_data).fit()

# Perform ANOVA
anova_results = anova_lm(model)

# Display the results
print(anova_results)

# Group the data by 'Group' and 'Sex', then calculate the mean and SEM for each group
grouped = acute_data.groupby(['Group', 'Sex'])['Weight']

# Calculate the mean
means = grouped.mean()

# Calculate the SEM
sems = grouped.sem()

# Print the results
print("Means by Group and Sex:")
print(means)

print("\nSEMs by Group and Sex:")
print(sems)