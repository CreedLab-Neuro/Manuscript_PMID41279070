# -*- coding: utf-8 -*-
"""
Created on Sun Aug  3 19:45:02 2025

@author: meagh
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from glob import glob
from datetime import datetime
from scipy.stats import bootstrap

# === CONFIGURATION ===
base_dir = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit'  # base path where SHAM/ and SNI/ folders reside

groups = ["SHAM", "SNI"]
retrieval_cutoff = 8  # seconds
cmfd_bins = np.linspace(0, retrieval_cutoff, 100)
time_range = range(19, 24)  # 7 PM (19) to 11:59 PM (23)

# === STORAGE ===
group_data = {
    "SHAM_low": [],
    "SHAM_high": [],
    "SNI_low": [],
    "SNI_high": []
}

# === PARSE EACH MOUSE ===
for group in groups:
    file_paths = glob(os.path.join(base_dir, group, "*.csv"))
    for path in file_paths:
        df = pd.read_csv(path)
        df['timestamp'] = pd.to_datetime(df['MM:DD:YYYY hh:mm:ss'], errors='coerce')
        df = df[df['timestamp'].dt.hour.isin(time_range)]

        # Drop any missing retrievals or malformed data
        pellet_rows = df[df['Event'] == "Pellet"].copy()
        pellet_rows = pellet_rows[pd.to_numeric(pellet_rows['Retrieval_Time'], errors='coerce').notnull()]
        pellet_rows['Retrieval_Time'] = pellet_rows['Retrieval_Time'].astype(float)
        pellet_rows = pellet_rows[pellet_rows['Retrieval_Time'] <= retrieval_cutoff]

        # Categorize block
        pellet_rows['Block_Type'] = np.where(
            (pellet_rows['Prob_left'] + pellet_rows['Prob_right']) == 50, "low",
            np.where((pellet_rows['Prob_left'] + pellet_rows['Prob_right']) == 150, "high", "other")
        )
        pellet_rows = pellet_rows[pellet_rows['Block_Type'].isin(['low', 'high'])]

        # Accumulate normalized CMFD
        for block in ['low', 'high']:
            rts = pellet_rows.loc[pellet_rows['Block_Type'] == block, 'Retrieval_Time'].values
            if len(rts) < 3:  # skip sparse traces
                continue
            hist, _ = np.histogram(rts, bins=cmfd_bins, density=True)
            cmfd = np.cumsum(hist) / np.sum(hist)  # Normalize to 1
            key = f"{group}_{block}"
            group_data[key].append(cmfd)

# === PLOT ===
plt.figure(figsize=(10, 6))

colors = {
    "SHAM_low": "blue",
    "SHAM_high": "dodgerblue",
    "SNI_low": "red",
    "SNI_high": "darkred"
}

for key, traces in group_data.items():
    if len(traces) == 0:
        continue
    traces = np.array(traces)
    mean_cmfd = traces.mean(axis=0)
    lower = np.percentile(traces, 5, axis=0)
    upper = np.percentile(traces, 95, axis=0)

    plt.plot(cmfd_bins[1:], mean_cmfd, label=key.replace("_", " "), color=colors[key])
    plt.fill_between(cmfd_bins[1:], lower, upper, color=colors[key], alpha=0.2)

plt.xlabel("Retrieval Time (s)")
plt.ylabel("Cumulative Mean Frequency")
plt.title("CMFD of Pellet Retrieval Times (7 PM–Midnight)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('TB_RetrievalBlocks.svg')
plt.show()
#%% Statistically test the differences
import os
import pandas as pd
import numpy as np
from glob import glob
import pingouin as pg

base_dir = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit'
groups = ["SHAM", "SNI"]
retrieval_cutoff = 10
time_range = range(19, 24)

records = []

for group in groups:
    file_paths = glob(os.path.join(base_dir, group, "*.csv"))
    for path in file_paths:
        df = pd.read_csv(path)
        mouse_id = os.path.splitext(os.path.basename(path))[0]

        df['timestamp'] = pd.to_datetime(df['MM:DD:YYYY hh:mm:ss'], errors='coerce')
        df = df[df['timestamp'].dt.hour.isin(time_range)]

        pellet_rows = df[df['Event'] == "Pellet"].copy()
        pellet_rows = pellet_rows[pd.to_numeric(pellet_rows['Retrieval_Time'], errors='coerce').notnull()]
        pellet_rows['Retrieval_Time'] = pellet_rows['Retrieval_Time'].astype(float)
        pellet_rows = pellet_rows[pellet_rows['Retrieval_Time'] <= retrieval_cutoff]

        pellet_rows['Block_Type'] = np.where(
            (pellet_rows['Prob_left'] + pellet_rows['Prob_right']) == 50, "Low",
            np.where((pellet_rows['Prob_left'] + pellet_rows['Prob_right']) == 150, "High", "Other")
        )
        pellet_rows = pellet_rows[pellet_rows['Block_Type'].isin(['Low', 'High'])]

        # Store mean retrieval times for each block
        for block in ['Low', 'High']:
            rts = pellet_rows.loc[pellet_rows['Block_Type'] == block, 'Retrieval_Time']
            if len(rts) < 3:
                continue
            records.append({
                "Mouse_ID": mouse_id,
                "Group": group,
                "Block": block,
                "Mean_Retrieval_Time": rts.mean()
            })

# Create long-format DataFrame
df_long = pd.DataFrame(records)

# Run 2-way mixed ANOVA
anova = pg.mixed_anova(
    dv="Mean_Retrieval_Time",
    within="Block",
    between="Group",
    subject="Mouse_ID",
    data=df_long
)

print(anova.round(4))


#%%
# ================ USER PARAMETERS =================
sham_dir = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SHAM'
sni_dir = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SNI'


time_start = 19
time_end = 24
max_poke_time = 2.5  # discard poke times above this threshold (seconds)

# ================ HELPER FUNCTIONS =================
def load_cmfd_data(directory, group):
    block_cmfds = {'Low': {'Poke': [], 'Retrieval': []},
                   'Med': {'Poke': [], 'Retrieval': []},
                   'High': {'Poke': [], 'Retrieval': []}}

    for filename in os.listdir(directory):
        if not filename.endswith(".csv"):
            continue

        filepath = os.path.join(directory, filename)
        df = pd.read_csv(filepath, low_memory=False)
        df['Timestamp'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
        df['Hour'] = df['Timestamp'].dt.hour
        df = df[(df['Hour'] >= time_start) & (df['Hour'] < time_end)]

        df = df.copy()
        df['BlockID'] = (df['Prob_left'] != df['Prob_left'].shift()) | (df['Prob_right'] != df['Prob_right'].shift())
        df['BlockID'] = df['BlockID'].cumsum()
        df['BlockType'] = df['Prob_left'] + df['Prob_right']
        df['BlockType'] = df['BlockType'].map({50: 'Low', 100: 'Med', 150: 'High'})

        for block_id, block_df in df.groupby('BlockID'):
            block_type = block_df['BlockType'].iloc[0]
            if block_type not in ['Low', 'Med', 'High']:
                continue

            poke_times = pd.to_numeric(block_df.loc[block_df['Event'].isin(['Left', 'Right']), 'Poke_Time'], errors='coerce').dropna()
            poke_times = poke_times[poke_times <= max_poke_time]

            retrieval_times = pd.to_numeric(block_df.loc[block_df['Event'] == 'Pellet', 'Retrieval_Time'], errors='coerce').dropna()

            if len(poke_times) > 0:
                block_cmfds[block_type]['Poke'].append(np.sort(poke_times))
            if len(retrieval_times) > 0:
                block_cmfds[block_type]['Retrieval'].append(np.sort(retrieval_times))

    return block_cmfds

# ================ LOAD ALL DATA =====================
sham_cmfds = load_cmfd_data(sham_dir, 'SHAM')
sni_cmfds = load_cmfd_data(sni_dir, 'SNI')

# ================ PLOT CONFIG =======================
fig, axs = plt.subplots(2, 3, figsize=(18, 10))
block_types = ['Low', 'Med', 'High']
colors = {'SHAM': 'blue', 'SNI': 'red'}

for i, block in enumerate(block_types):
    ax_top = axs[0, i]
    ax_bot = axs[1, i]

    # POKE CMFDs
    all_poke_times_sham = []
    for trial in sham_cmfds[block]['Poke']:
        ax_top.plot(np.sort(trial), np.linspace(0, 1, len(trial)), color='blue', alpha=0.2)
        all_poke_times_sham.append(trial)

    all_poke_times_sni = []
    for trial in sni_cmfds[block]['Poke']:
        ax_top.plot(np.sort(trial), np.linspace(0, 1, len(trial)), color='red', alpha=0.2)
        all_poke_times_sni.append(trial)

    if all_poke_times_sham:
        pooled = np.concatenate(all_poke_times_sham)
        ax_top.plot(np.sort(pooled), np.linspace(0, 1, len(pooled)), color='blue', lw=2)
    if all_poke_times_sni:
        pooled = np.concatenate(all_poke_times_sni)
        ax_top.plot(np.sort(pooled), np.linspace(0, 1, len(pooled)), color='red', lw=2)

    ax_top.set_title(f'{block} Block - Poke Times')
    ax_top.set_xlabel('Poke Time (s)')
    ax_top.set_ylabel('Cumulative Fraction')

    # RETRIEVAL CMFDs
    all_retrieval_times_sham = []
    for trial in sham_cmfds[block]['Retrieval']:
        ax_bot.plot(np.sort(trial), np.linspace(0, 1, len(trial)), color='blue', alpha=0.2)
        all_retrieval_times_sham.append(trial)

    all_retrieval_times_sni = []
    for trial in sni_cmfds[block]['Retrieval']:
        ax_bot.plot(np.sort(trial), np.linspace(0, 1, len(trial)), color='red', alpha=0.2)
        all_retrieval_times_sni.append(trial)

    if all_retrieval_times_sham:
        pooled = np.concatenate(all_retrieval_times_sham)
        ax_bot.plot(np.sort(pooled), np.linspace(0, 1, len(pooled)), color='blue', lw=2)
    if all_retrieval_times_sni:
        pooled = np.concatenate(all_retrieval_times_sni)
        ax_bot.plot(np.sort(pooled), np.linspace(0, 1, len(pooled)), color='red', lw=2)

    ax_bot.set_title(f'{block} Block - Retrieval Times')
    ax_bot.set_xlabel('Retrieval Time (s)')
    ax_bot.set_xlim(0,30)
    ax_bot.set_ylabel('Cumulative Fraction')

plt.tight_layout()
plt.show()

