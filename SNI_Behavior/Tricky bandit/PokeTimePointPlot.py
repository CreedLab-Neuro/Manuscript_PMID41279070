# -*- coding: utf-8 -*-
"""
Created on Sun Aug  3 17:01:24 2025

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
time_start = 19  # 24h format: 19 = 7pm
time_end = 24    # 24h format: midnight
exclude_first_n_pellets = 3
max_poke_time = 2.0  # maximum allowed poke time in seconds

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

            sex = 'Female' if filename.startswith('F') else 'Male'
            mouse_id = filename.split('.')[0]

            df = df.copy()
            df.loc[:, 'BlockType'] = df['Prob_left'] + df['Prob_right']
            df.loc[:, 'BlockType'] = df['BlockType'].map({50: 'Low', 100: 'Med', 150: 'High'})
            df.loc[:, 'Block_Idx'] = (df['BlockType'] != df['BlockType'].shift()).cumsum()
            df.loc[:, 'Pellet_Count_Block'] = df.groupby('Block_Idx').cumcount()

            df['Mouse'] = mouse_id
            df['Sex'] = sex
            df['Group'] = group_label
            data.append(df)

    return pd.concat(data, ignore_index=True)

# ================ LOAD & PROCESS ====================
sham_data = load_group_data(sham_dir, 'SHAM')
sni_data = load_group_data(sni_dir, 'SNI')
all_data = pd.concat([sham_data, sni_data], ignore_index=True)

all_data['Poke_Time'] = pd.to_numeric(all_data['Poke_Time'], errors='coerce')
all_data = all_data.dropna(subset=['Poke_Time', 'BlockType'])
all_data = all_data[all_data['Poke_Time'] <= max_poke_time]

block_order = ['Low', 'Med', 'High']
all_data['BlockType'] = pd.Categorical(all_data['BlockType'], categories=block_order, ordered=True)

# ================ PLOT 1 & 2 ========================
fig, axs = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
colors = {'SHAM': 'blue', 'SNI': 'red'}
markers = {'Male': 'o', 'Female': 'o'}
facecolors = {'Male': 'black', 'Female': 'white'}

for i, group in enumerate(['SHAM', 'SNI']):
    ax = axs[i]
    group_df = all_data[(all_data['Group'] == group) & (all_data['Event'].isin(['Left', 'Right']))]

    mouse_block_means = group_df.groupby(['Mouse', 'Sex', 'Block_Idx', 'BlockType'])['Poke_Time'].mean().reset_index()

    for _, row in mouse_block_means.iterrows():
        sex = row['Sex']
        ax.plot(row['BlockType'], row['Poke_Time'], marker=markers[sex],
                markerfacecolor=facecolors[sex], markeredgecolor='black', color=colors[group], linestyle='')

    means = group_df.groupby('BlockType')['Poke_Time'].mean().reindex(block_order)
    errors = group_df.groupby('BlockType')['Poke_Time'].apply(sem).reindex(block_order)
    ax.errorbar(block_order, means, yerr=errors, fmt='-', color=colors[group], linewidth=2, capsize=5)
    ax.set_title(f'{group} Mice')
    ax.set_xlabel('Block Type')
    ax.set_xticks(block_order)
    ax.set_ylim(bottom=0)

axs[0].set_ylabel('Poke Time (s)')

# ================ PLOT 3 ===========================
summary = all_data[all_data['Event'].isin(['Left', 'Right'])].copy()
summary = summary.groupby(['Mouse', 'Group', 'Sex', 'BlockType'])['Poke_Time'].agg(['mean', sem]).reset_index()

ax = axs[2]
for (group, sex), sub_df in summary.groupby(['Group', 'Sex']):
    for _, row in sub_df.iterrows():
        ax.errorbar(row['BlockType'], row['mean'], yerr=row['sem'], fmt=markers[sex],
                    markerfacecolor=colors[group], markeredgecolor='black', color=colors[group])

ax.set_title('Per-Mouse Avg ± SEM by Block')
ax.set_xlabel('Block Type')
ax.set_xticks(block_order)
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig('PokeTimesAcrossBlocks.png')
plt.savefig('PokeTimesAcrossBlocks.svg')
plt.show()

# ================ STATS ============================
stats_df = all_data[all_data['Event'].isin(['Left', 'Right'])].copy()
stats_df = stats_df[['Poke_Time', 'Group', 'BlockType']].dropna()
model = ols('Poke_Time ~ C(Group) * C(BlockType)', data=stats_df).fit()
anova_table = sm.stats.anova_lm(model, typ=2)
print("\n===== Two-way ANOVA Results =====")
print(anova_table)

