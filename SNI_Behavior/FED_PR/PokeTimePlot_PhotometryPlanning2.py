# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 15:36:22 2025

@author: meaghan.creed
"""

#%%
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === Load data ===
file_path = r'C:\Users\meaghan.creed\Desktop\New folder (2)\FED002_060624_01.csv'  # ⬅️ Replace this with your full path
df = pd.read_csv(file_path)

# === Ensure correct timestamp format ===
df['Timestamp'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')  # auto-detect timestamp column

# === Keep only poke events (Left or Right) and FR conditions of interest ===
df = df[df['Event'].isin(['Left', 'Right', 'Pellet'])]

# === Define FR values ===
fr_values = [5, 13, 32]
colors = {5: 'green', 13: 'orange', 32: 'purple'}
intervals = {}
pellet_counts = {}

# === Loop over FRs and extract inter-poke intervals ===
for fr in fr_values:
    df_fr = df[df['FR'] == fr].copy()

    # Track poke timestamps excluding the ones after "Pellet"
    poke_times = []
    previous_event = None
    for i, row in df_fr.iterrows():
        if row['Event'] in ['Left', 'Right']:
            if previous_event != 'Pellet':  # exclude intervals that follow a Pellet
                poke_times.append(row['Timestamp'])
        previous_event = row['Event']

    # Calculate inter-poke intervals in seconds
    poke_times = pd.Series(poke_times).sort_values()
    ipi = poke_times.diff().dropna().dt.total_seconds()
    intervals[fr] = ipi

    # Count pellets for this FR
    pellet_counts[fr] = (df_fr['Event'] == 'Pellet').sum()

# === Plot normalized histograms ===
plt.figure(figsize=(10, 6))
bins = np.linspace(0, 120, 120)

for fr in fr_values:
    plt.hist(intervals[fr], bins=bins, density=True, alpha=0.6,
             label=f"FR{fr} (Pellets = {pellet_counts[fr]})", color=colors[fr], edgecolor='black')

plt.xlabel("Inter-poke interval (s)")
plt.ylabel("Normalized count (density)")
plt.title("Inter-poke intervals by FR")
#plt.xscale('log')
plt.legend()
plt.tight_layout()
plt.show()