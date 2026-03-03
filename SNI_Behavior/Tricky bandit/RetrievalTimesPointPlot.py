# -*- coding: utf-8 -*-
"""
Created on Sun Aug  3 14:49:44 2025

@author: meagh
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import sem
from statsmodels.formula.api import ols
import statsmodels.api as sm
from datetime import datetime

# ================= USER PARAMETERS =================
sham_dir = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SHAM'
sni_dir = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SNI'
time_start = 0  # 24h format: 19 = 7pm
time_end = 24    # 24h format: midnight
exclude_first_n_pellets = 0

# ================ HELPER FUNCTIONS =================
def load_group_data(group_dir, group_label):
    data = []
    for filename in os.listdir(group_dir):
        if filename.endswith(".csv"):
            filepath = os.path.join(group_dir, filename)
            df = pd.read_csv(filepath, low_memory=False)
            df['Timestamp'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            df['Hour'] = df['Timestamp'].dt.hour
            df = df.loc[(df['Hour'] >= time_start) & (df['Hour'] < time_end)]

            # Determine sex
            sex = 'Female' if filename.startswith('F') else 'Male'
            mouse_id = filename.split('.')[0]

            # Determine block type per row
            df = df.copy()
            df.loc[:, 'BlockType'] = df['Prob_left'] + df['Prob_right']
            df.loc[:, 'BlockType'] = df['BlockType'].map({50: 'Low', 100: 'Med', 150: 'High'})

            # Track pellet counts per block type
            df.loc[:, 'Block_Idx'] = (df['BlockType'] != df['BlockType'].shift()).cumsum()
            df.loc[:, 'Pellet_Count_Block'] = df.groupby(['Block_Idx']).cumcount()

            # Extract pellet events with block info
            pellets = df[df['Event'] == 'Pellet'].copy()
            pellets = pellets[pellets['Pellet_Count_Block'] >= exclude_first_n_pellets]

            # Annotate
            pellets['Mouse'] = mouse_id
            pellets['Sex'] = sex
            pellets['Group'] = group_label
            data.append(pellets)

    return pd.concat(data, ignore_index=True)

# ================ LOAD & PROCESS ====================
sham_data = load_group_data(sham_dir, 'SHAM')
sni_data = load_group_data(sni_dir, 'SNI')
all_data = pd.concat([sham_data, sni_data], ignore_index=True)

# Convert Retrieval_Time to numeric
all_data['Retrieval_Time'] = pd.to_numeric(all_data['Retrieval_Time'], errors='coerce')
all_data = all_data.dropna(subset=['Retrieval_Time', 'BlockType'])

# Set consistent x-axis order
block_order = ['Low', 'Med', 'High']
all_data['BlockType'] = pd.Categorical(all_data['BlockType'], categories=block_order, ordered=True)

# ================ PLOT 1 & 2 ========================
fig, axs = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

# Define color and marker maps
colors = {'SHAM': 'blue', 'SNI': 'red'}
markers = {'Male': 'o', 'Female': 'o'}
facecolors = {'Male': 'black', 'Female': 'white'}

for i, (group, group_df) in enumerate(all_data.groupby('Group')):
    ax = axs[i]
    for sex in ['Male', 'Female']:
        sub_df = group_df[group_df['Sex'] == sex]
        for _, row in sub_df.iterrows():
            x = row['BlockType']
            y = row['Retrieval_Time']
            ax.plot(x, y, marker=markers[sex], markerfacecolor=colors[group],
                    markeredgecolor='black', linestyle='', label=None)

    # Mean ± SEM line overlay
    means = group_df.groupby('BlockType')['Retrieval_Time'].mean().reindex(block_order)
    errors = group_df.groupby('BlockType')['Retrieval_Time'].apply(sem).reindex(block_order)
    ax.errorbar(block_order, means, yerr=errors, fmt='-', color=colors[group], linewidth=2, capsize=5, label='Mean ± SEM')

    ax.set_title(f'{group} Mice')
    ax.set_xlabel('Block Type')
    ax.set_xticks(block_order)
    ax.set_ylim(bottom=0)

axs[0].set_ylabel('Retrieval Time (s)')

# ================ PLOT 3 ===========================
# Aggregate per-mouse means and SEM per block
mouse_block_summary = all_data.groupby(['Mouse', 'Group', 'Sex', 'BlockType'])['Retrieval_Time'].agg(['mean', sem]).reset_index()

ax = axs[2]
for (group, sex), sub_df in mouse_block_summary.groupby(['Group', 'Sex']):
    for _, row in sub_df.iterrows():
        x = row['BlockType']
        y = row['mean']
        yerr = row['sem']
        ax.errorbar(x, y, yerr=yerr, fmt=markers[sex], markerfacecolor=colors[group],
                    markeredgecolor='black', color=colors[group])

axs[2].set_title('Per-Mouse Avg ± SEM by Block')
axs[2].set_xlabel('Block Type')
axs[2].set_xticks(block_order)
axs[2].set_yscale('log')
axs[2].set_ylim(bottom=0)

plt.tight_layout()
plt.show()

# ================ STATS ============================
# Prepare data for ANOVA
anova_df = all_data[['Retrieval_Time', 'Group', 'BlockType']].copy()
model = ols('Retrieval_Time ~ C(Group) * C(BlockType)', data=anova_df).fit()
anova_table = sm.stats.anova_lm(model, typ=2)
print("\n===== Two-way ANOVA Results =====")
print(anova_table)

# Optionally: save the plot or stats to file
fig.savefig("retrieval_time_analysisAll.png", dpi=300)
fig.savefig("retrieval_time_analysisAll.svg", dpi=300)
# anova_table.to_csv("anova_results.csv")
