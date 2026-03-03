# -*- coding: utf-8 -*-
"""
Created on Fri Jul 25 13:31:06 2025

@author: meaghan.creed
"""

import matplotlib.pyplot as plt

def get_pokes_per_min(df_FR):
    # Keep only pokes
    pokes = df_FR[df_FR["Event"].isin(["Left", "Right"])].copy()
    pokes["Timestamp"] = pd.to_datetime(pokes["Timestamp"])
    pokes["Minute"] = pokes["Timestamp"].dt.floor("min")
    counts_per_min = pokes["Minute"].value_counts()
    return counts_per_min

# Compute poke counts per minute for each FR
FR5_counts = get_pokes_per_min(df_FR5)
FR20_counts = get_pokes_per_min(df_FR20)
FR50_counts = get_pokes_per_min(df_FR50)

# Get global bin range
max_count = max(FR5_counts.max(), FR20_counts.max(), FR50_counts.max())
bins = range(1, max_count + 2)

# Plot
plt.figure(figsize=(10, 6))
plt.hist(FR5_counts.values, bins=bins, alpha=0.5, label="FR5", color="blue", edgecolor="black", align="left", density=True)
plt.hist(FR20_counts.values, bins=bins, alpha=0.5, label="FR20", color="orange", edgecolor="black", align="left", density=True)
plt.hist(FR50_counts.values, bins=bins, alpha=0.5, label="FR50", color="green", edgecolor="black", align="left", density=True)

# Formatting
plt.xlabel("Number of Pokes per Minute")
plt.ylabel("Proportion of Minutes")
plt.title("Pokes per Minute Distribution (FR5, FR20, FR50)")
plt.legend()
plt.tight_layout()
plt.show()
