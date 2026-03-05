# -*- coding: utf-8 -*-
"""
Created on Mon Aug  4 17:00:51 2025

@author: meaghan.creed
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# === Load CSV ===
df = pd.read_csv(r'C:\Users\meaghan.creed\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\ReversalPellets.csv')  # replace with your filename

# === Filter for Task == 'Determ' ===
df_determ = df[df['Task'] == 'Tricky']

# === Create figure ===
plt.figure(figsize=(8, 6))

# === Draw swarmplot with closed circles for males ===
sns.swarmplot(
    data=df_determ[df_determ['Sex'] == 'M'],
    x='Group',
    y='Pellets',
    marker='o',
    edgecolor='black',
    linewidth=0.5,
    color='steelblue',
    label='Male'
)

# === Overlay open circles for females ===
sns.swarmplot(
    data=df_determ[df_determ['Sex'] == 'F'],
    x='Group',
    y='Pellets',
    marker='o',
    facecolors='none',
    edgecolor='black',
    linewidth=0.8,
    color='darkorange',
    label='Female'
)

sns.boxplot(data = df_determ, x = 'Group', y = 'Pellets')

# === Labeling ===
plt.xlabel("Group")
plt.ylim(300,700)
plt.ylabel("Pellets")
plt.title("Pellets Earned (Task: Determ)")

# Optional: Add a custom legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='Male', markerfacecolor='steelblue', markeredgecolor='black'),
    Line2D([0], [0], marker='o', color='w', label='Female', markerfacecolor='white', markeredgecolor='darkorange')
]
plt.legend(handles=legend_elements)

plt.tight_layout()
plt.savefig('TrickyPellets.svg')
plt.savefig('TrickyPellets.png')
plt.show()

#%%
import pandas as pd
import pingouin as pg
from scipy.stats import sem

df_determ = df[df['Task'] == 'Tricky']
# Run two-way ANOVA

print("Pellets Earned During Probabalistic Reversal")
aov = pg.anova(dv='Pellets', between=['Group', 'Sex'], data=df_determ, detailed=True)

print(aov)



# Group by 'Group' and 'Sex', and compute mean and SEM
grouped = df_determ.groupby(['Group', 'Sex'])['Pellets']
summary = grouped.agg(['mean', sem]).reset_index()

# Print mean ± SEM for each group
for _, row in summary.iterrows():
    group = row['Group']
    sex = row['Sex']
    mean_val = row['mean']
    sem_val = row['sem']
    print(f"{group} ({sex}): {mean_val:.2f} ± {sem_val:.2f} pellets")