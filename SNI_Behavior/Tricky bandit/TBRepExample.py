# -*- coding: utf-8 -*-
"""
Created on Tue Aug  5 22:32:25 2025

@author: meagh
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta

# === 1. Load the data ===
file_path = r"C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SHAM\MSHAM_FED019_101023_01.CSV" #"SNI\FSNI_FED006_101023_00.CSV"  # Update this SHAM\MSHAM_FED019_101023_01.CSV
df = pd.read_csv(file_path)
#df = pd.read_csv(file_path, low_memory=False)

# === 2. Parse timestamps ===
df["Timestamp"] = pd.to_datetime(df["MM:DD:YYYY hh:mm:ss"], errors='coerce')
df = df.dropna(subset=["Timestamp"])

# === 3. Set start time ===
start_time = pd.to_datetime("2023-10-12 19:00:00")  # Adjust as needed
end_time = start_time + pd.Timedelta(hours=12)

# === 4. Filter to 12h window ===
df = df[(df["Timestamp"] >= start_time) & (df["Timestamp"] <= end_time)].copy()

# === 5. Extract event timestamps ===
pellet_times = df[df["Event"] == "Pellet"]["Timestamp"]
left_times   = df[df["Event"] == "Left"]["Timestamp"]
right_times  = df[df["Event"] == "Right"]["Timestamp"]

# === 6. Detect block switch points ===
block_switches = df[["Timestamp", "Prob_left", "Prob_right"]].copy()
block_switches = block_switches.dropna()
block_switches["Block_ID"] = (block_switches["Prob_left"].diff() != 0) | (block_switches["Prob_right"].diff() != 0)
block_switches = block_switches[block_switches["Block_ID"]]  # keep only switch points

# Drop duplicates (if multiple events at switch timestamp)
block_switches = block_switches.drop_duplicates(subset=["Timestamp"])

# === 7. Plot ===
plt.figure(figsize=(14, 4))

# Raster ticks
y_pellet = 1
y_left   = 0.5
y_right  = 0.0

plt.eventplot(pellet_times, lineoffsets=y_pellet, colors='black', linelengths=0.3, linewidths=1, label="Pellet")
plt.eventplot(left_times,   lineoffsets=y_left,   colors='green', linelengths=0.3, linewidths=1, label="Left")
plt.eventplot(right_times,  lineoffsets=y_right,  colors='purple', linelengths=0.3, linewidths=1, label="Right")

# Block switch vertical lines
for _, row in block_switches.iterrows():
    ts = row["Timestamp"]
    label = f"{int(row['Prob_left'])}:{int(row['Prob_right'])}"
    plt.axvline(ts, color='gray', linestyle='--', linewidth=1)
    plt.text(ts, 1.05, label, rotation=90, ha='center', va='bottom', fontsize=8, color='gray')

# Formatting
plt.yticks([y_right, y_left, y_pellet], ['Right', 'Left', 'Pellet'])
plt.xlabel("Time")
plt.title("Bandit Task Events Over 12 Hours\n(With Block Switch Markers)")
plt.tight_layout()
#plt.savefig('TrickyBanditExample_SNI3.svg')
plt.show()
#%%
import matplotlib.pyplot as plt

# --- Calculate Left Proportion Between Pellets ---
pellet_df = df[df["Event"] == "Pellet"].copy()
pellet_times = pellet_df["Timestamp"].reset_index(drop=True)

left_prop_x = []
left_prop_y = []

for i in range(1, len(pellet_times)):
    t0 = pellet_times[i - 1]
    t1 = pellet_times[i]
    
    window = df[(df["Timestamp"] > t0) & (df["Timestamp"] <= t1)]
    left_count = (window["Event"] == "Left").sum()
    right_count = (window["Event"] == "Right").sum()
    total = left_count + right_count
    
    if total > 0:
        proportion = left_count / total
    else:
        proportion = None

    if proportion is not None:
        # Add full step function
        left_prop_x.extend([t0, t1])
        left_prop_y.extend([proportion, proportion])

# --- Plot as a step function ---
plt.figure(figsize=(12, 3))
plt.plot(left_prop_x, left_prop_y, drawstyle='steps-post', color='darkgreen', linewidth=2)

# Optional: reference lines and labels
plt.axhline(0.5, linestyle='--', color='gray', linewidth=0.8)
plt.ylim(-0.05, 1.05)
plt.ylabel("Left Choice Proportion")
plt.xlabel("Time")
plt.title("Proportion of Left Choices Between Pellet Events")
plt.tight_layout()
plt.savefig('TB_ExampleStepPlot_SHAM.svg')
plt.show()

#%%


# === 1. Load the data ===
file_path = r"C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SHAM\MSHAM_FED019_101023_01.CSV"  # Update this
df = pd.read_csv(file_path)

# === 2. Parse timestamps ===
df["Timestamp"] = pd.to_datetime(df["MM:DD:YYYY hh:mm:ss"], errors='coerce')
df = df.dropna(subset=["Timestamp"])  # drop bad rows

# === 3. Set start time ===
start_time = pd.to_datetime("2023-10-10 14:36:44")  # Set your desired start time
end_time = start_time + pd.Timedelta(hours=24)

# === 4. Filter to 12h window ===
df = df[(df["Timestamp"] >= start_time) & (df["Timestamp"] <= end_time)]

# === 5. Collect event times ===
pellet_times = df[df["Event"] == "Pellet"]["Timestamp"]
left_times   = df[df["Event"] == "Left"]["Timestamp"]
right_times  = df[df["Event"] == "Right"]["Timestamp"]

# === 6. Plot ===
plt.figure(figsize=(12, 3))

# Y positions
y_pellet = 1
y_left   = 0.5
y_right  = 0.0

plt.eventplot(pellet_times, lineoffsets=y_pellet, colors='black', linelengths=0.3, linewidths=1, label="Pellet")
plt.eventplot(left_times,   lineoffsets=y_left,   colors='green', linelengths=0.3, linewidths=1, label="Left")
plt.eventplot(right_times,  lineoffsets=y_right,  colors='purple', linelengths=0.3, linewidths=1, label="Right")

# Formatting
plt.yticks([y_right, y_left, y_pellet], ['Right', 'Left', 'Pellet'])
plt.xlabel("Time")
plt.title("Bandit Task Events Over 12 Hours")
plt.tight_layout()
plt.show()
