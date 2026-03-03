# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 21:41:35 2025

@author: meagh
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import ks_2samp

# Initialize storage for all data
all_poke_sham = []
all_poke_sni = []
all_retrieval_sham = []
all_retrieval_sni = []

# Set your paths
sham_dir = r'C:\Users\meagh\Downloads\SHAM_PR\SHAM' #r"C:\Users\meagh\Downloads\SHAM\SHAM"
sni_dir = r'C:\Users\meagh\Downloads\SNI_PR\SNI' #r"C:\Users\meagh\Downloads\SNI\SNI"
#%%

# Create plot
fig, axs = plt.subplots(1, 2, figsize=(12, 5))
axs[0].set_title("Poke Time CMFD")
axs[1].set_title("Retrieval Time CMFD")
axs[0].set_xlabel("Poke Time")
axs[0].set_xlim(0, 2)
axs[1].set_xlabel("Retrieval Time")
axs[0].set_ylabel("Cumulative Probability")
axs[1].set_ylabel("Cumulative Probability")

def process_and_plot(directory, group_label, color, ax_poke, ax_retrieval):
    for filename in os.listdir(directory):
        if filename.lower().endswith(".csv"):
            file_path = os.path.join(directory, filename)
            df = pd.read_csv(file_path)

            # Convert to numeric and drop NaNs and zeros
            poke_times = pd.to_numeric(df["Poke_Time"], errors='coerce')
            poke_times = poke_times[(poke_times != 0) & (~poke_times.isna())].sort_values()

            retrieval_times = pd.to_numeric(df["Retrieval_Time"], errors='coerce')
            retrieval_times = retrieval_times[(retrieval_times != 0) & (~retrieval_times.isna())].sort_values()

            # Append to master lists
            if group_label == "SHAM":
                all_poke_sham.extend(poke_times)
                all_retrieval_sham.extend(retrieval_times)
            elif group_label == "SNI":
                all_poke_sni.extend(poke_times)
                all_retrieval_sni.extend(retrieval_times)

            # Plot CMFD
            def plot_cmfd(data, ax):
                if len(data) > 1:
                    y = np.linspace(0, 1, len(data))
                    ax.plot(data, y, color=color, alpha=0.2)

            plot_cmfd(poke_times, ax_poke)
            plot_cmfd(retrieval_times, ax_retrieval)


# Process both groups
process_and_plot(sham_dir, "SHAM", "blue", axs[0], axs[1])
process_and_plot(sni_dir, "SNI", "red", axs[0], axs[1])

plt.tight_layout()
plt.show()


# === K-S Tests ===
poke_stat, poke_p = ks_2samp(all_poke_sham, all_poke_sni, alternative='two-sided')
retrieval_stat, retrieval_p = ks_2samp(all_retrieval_sham, all_retrieval_sni, alternative='two-sided')

print("\n=== Kolmogorov–Smirnov (K-S) Test Results ===")
print(f"Poke Times:      D={poke_stat:.3f}, p={poke_p:.4f}")
print(f"Retrieval Times: D={retrieval_stat:.3f}, p={retrieval_p:.4f}")
#%%
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
#%%
# === CONFIG ===
sham_dir = r"C:\Users\meagh\Downloads\Clean\Clean\SHAM"
sni_dir = r"C:\Users\meagh\Downloads\Clean\Clean\SNI"
#%%
n_bins = 200  # resolution of CMFD x-axis
poke_xlim = (0, 3)  # x-axis for poke times
retrieval_xlim = None  # use full range

# === INIT PLOT ===
fig, axs = plt.subplots(2, 2, figsize=(12, 8))
(ax_poke_indiv, ax_retr_indiv), (ax_poke_mean, ax_retr_mean) = axs

ax_poke_indiv.set_title("Poke Time CMFDs (individual)")
ax_retr_indiv.set_title("Retrieval Time CMFDs (individual)")
ax_poke_mean.set_title("Mean Poke Time CMFD")
ax_retr_mean.set_title("Mean Retrieval Time CMFD")

for ax in [ax_poke_indiv, ax_poke_mean]:
    ax.set_xlim(poke_xlim)
    ax.set_xlabel("Poke Time (s)")
    ax.set_ylabel("Cumulative Probability")

for ax in [ax_retr_indiv, ax_retr_mean]:
    if retrieval_xlim:
        ax.set_xlim(retrieval_xlim)
    ax.set_xlabel("Retrieval Time (s)")
    ax.set_ylabel("Cumulative Probability")

# === CMFD Calculation ===
def compute_cmfd(data, x_grid):
    data_sorted = np.sort(data)
    y = np.linspace(0, 1, len(data_sorted))
    return np.interp(x_grid, data_sorted, y, left=0, right=1)

# === MAIN LOOP ===
group_data = {"SHAM": {"poke": [], "retr": [], "color": "blue"},
              "SNI": {"poke": [], "retr": [], "color": "red"}}

def process_group(directory, group, ax_poke, ax_retr):
    for fname in os.listdir(directory):
        if not fname.lower().endswith(".csv"):
            continue
        path = os.path.join(directory, fname)
        df = pd.read_csv(path)

        # Process Poke Time
        poke = pd.to_numeric(df["Poke_Time"], errors="coerce")
        poke = poke[(poke != 0) & (poke <3) & (~poke.isna())].sort_values()
        if len(poke) > 1:
            x_grid = np.linspace(*poke_xlim, n_bins)
            y = compute_cmfd(poke, x_grid)
            ax_poke.plot(x_grid, y, color=group_data[group]["color"], alpha=0.2)
            group_data[group]["poke"].append(y)

        # Process Retrieval Time
        retr = pd.to_numeric(df["Retrieval_Time"], errors="coerce")
        retr = retr[(retr != 0) & (~retr.isna())].sort_values()
        if len(retr) > 1:
            x_grid = np.linspace(retr.min(), retr.max(), n_bins)
            y = compute_cmfd(retr, x_grid)
            ax_retr.plot(x_grid, y, color=group_data[group]["color"], alpha=0.2)
            group_data[group]["retr"].append((x_grid, y))

# Process each group
process_group(sham_dir, "SHAM", ax_poke_indiv, ax_retr_indiv)
process_group(sni_dir, "SNI", ax_poke_indiv, ax_retr_indiv)

# === Plot Mean ± SEM for Poke Time ===
x_grid = np.linspace(*poke_xlim, n_bins)
for group in group_data:
    curves = np.array(group_data[group]["poke"])
    if len(curves) == 0:
        continue
    mean = np.mean(curves, axis=0)
    sem = np.std(curves, axis=0) / np.sqrt(curves.shape[0])
    color = group_data[group]["color"]

    ax_poke_mean.plot(x_grid, mean, color=color, label=group)
    ax_poke_mean.fill_between(x_grid, mean - sem, mean + sem, color=color, alpha=0.3)

ax_poke_mean.legend()

# === Plot Mean ± SEM for Retrieval Time ===
# First, align all retrieval CMFDs to the same x-axis
min_x = min(np.min(x) for x, _ in group_data["SHAM"]["retr"] + group_data["SNI"]["retr"])
max_x = max(np.max(x) for x, _ in group_data["SHAM"]["retr"] + group_data["SNI"]["retr"])
x_grid_r = np.linspace(min_x, max_x, n_bins)

for group in group_data:
    curves = []
    for x, y in group_data[group]["retr"]:
        y_interp = np.interp(x_grid_r, x, y, left=0, right=1)
        curves.append(y_interp)

    if len(curves) == 0:
        continue
    curves = np.array(curves)
    mean = np.mean(curves, axis=0)
    sem = np.std(curves, axis=0) / np.sqrt(curves.shape[0])
    color = group_data[group]["color"]

    ax_retr_mean.plot(x_grid_r, mean, color=color, label=group)
    ax_retr_mean.fill_between(x_grid_r, mean - sem, mean + sem, color=color, alpha=0.3)

ax_retr_mean.legend()

# === Final layout ===
plt.tight_layout()
plt.savefig('CMFDPokeRetrievalPR.svg')
plt.savefig('CMFDPokeRetrievalPR.png')
plt.show()
#%% PLOTTING MEDIAN POKE and RETRIEVAL TIME AND RUNNING STATS
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu

# === Set your directories ===
SHAM_DIR = r'C:\Users\meagh\Downloads\SHAM_PR\SHAM' #r"C:\Users\meagh\Downloads\Clean\Clean\SHAM" #r"C:\Users\meagh\Downloads\Clean" #
SNI_DIR = r'C:\Users\meagh\Downloads\SNI_PR\SNI' #r"C:\Users\meagh\Downloads\Clean\Clean\SNI" #r'C:\Users\meagh\Downloads\SNI\SNI' #r

# === Initialize storage ===
sham_medians_poke = []
sham_medians_retrieval = []
sni_medians_poke = []
sni_medians_retrieval = []

# === Helper function to extract clean times ===
def get_clean_times(df, column):
    times = pd.to_numeric(df[column], errors='coerce').dropna()
    return times[times != 0]

# === Process SHAM ===
for file in os.listdir(SHAM_DIR):
    if file.endswith(".csv"):
        path = os.path.join(SHAM_DIR, file)
        df = pd.read_csv(path)

        poke = get_clean_times(df, "Poke_Time")
        retrieval = get_clean_times(df, "Retrieval_Time")

        if not poke.empty:
            median_poke = np.median(poke)
            sham_medians_poke.append(median_poke)
            print(f"SHAM - {file}: median poke time = {median_poke:.3f}")

        if not retrieval.empty:
            median_retrieval = np.median(retrieval)
            sham_medians_retrieval.append(median_retrieval)

# === Process SNI ===
for file in os.listdir(SNI_DIR):
    if file.endswith(".csv"):
        path = os.path.join(SNI_DIR, file)
        df = pd.read_csv(path)

        poke = get_clean_times(df, "Poke_Time")
        retrieval = get_clean_times(df, "Retrieval_Time")

        if not poke.empty:
            median_poke = np.median(poke)
            sni_medians_poke.append(median_poke)
            print(f"SNI - {file}: median poke time = {median_poke:.3f}")

        if not retrieval.empty:
            median_retrieval = np.median(retrieval)
            sni_medians_retrieval.append(median_retrieval)
#%%
# === Run stats ===
poke_stat, poke_p = mannwhitneyu(sham_medians_poke, sni_medians_poke, alternative='two-sided')
retrieval_stat, retrieval_p = mannwhitneyu(sham_medians_retrieval, sni_medians_retrieval, alternative='two-sided')

print("\n=== Mann-Whitney U Test Results ===")
print(f"Poke Times:      U={poke_stat:.2f}, p={poke_p:.4f}")
print(f"Retrieval Times: U={retrieval_stat:.2f}, p={retrieval_p:.4f}")

# === Plot ===
fig, axs = plt.subplots(1, 2, figsize=(10, 5), sharey=False)

# Left panel: Poke times
axs[0].scatter(np.repeat(0, len(sham_medians_poke)), sham_medians_poke, color='blue', alpha=0.6, label='SHAM')
axs[0].scatter(np.repeat(1, len(sni_medians_poke)), sni_medians_poke, color='red', alpha=0.6, label='SNI')
axs[0].bar([0,1],
           [np.mean(sham_medians_poke), np.mean(sni_medians_poke)],
           yerr=[np.std(sham_medians_poke)/np.sqrt(len(sham_medians_poke)),
                 np.std(sni_medians_poke)/np.sqrt(len(sni_medians_poke))],
           color=['blue', 'red'], alpha=0.3, width=0.5)
axs[0].set_title(f"Poke Times\np = {poke_p:.4f}")
axs[0].set_xticks([0, 1])
axs[0].set_xticklabels(['SHAM', 'SNI'])
axs[0].set_ylabel("Median Poke Time (s)")

# Right panel: Retrieval times
axs[1].scatter(np.repeat(0, len(sham_medians_retrieval)), sham_medians_retrieval, color='blue', alpha=0.6)
axs[1].scatter(np.repeat(1, len(sni_medians_retrieval)), sni_medians_retrieval, color='red', alpha=0.6)
axs[1].bar([0,1],
           [np.mean(sham_medians_retrieval), np.mean(sni_medians_retrieval)],
           yerr=[np.std(sham_medians_retrieval)/np.sqrt(len(sham_medians_retrieval)),
                 np.std(sni_medians_retrieval)/np.sqrt(len(sni_medians_retrieval))],
           color=['blue', 'red'], alpha=0.3, width=0.5)
axs[1].set_title(f"Retrieval Times\np = {retrieval_p:.4f}")
axs[1].set_xticks([0, 1])
axs[1].set_xticklabels(['SHAM', 'SNI'])
axs[1].set_ylabel("Median Retrieval Time (s)")

plt.tight_layout()
plt.savefig('MedianPokeRetrievalPR.svg')
plt.savefig('MedianPokeRetrievalPR.png')
plt.show()
