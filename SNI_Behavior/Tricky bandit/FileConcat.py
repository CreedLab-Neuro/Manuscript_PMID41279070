# -*- coding: utf-8 -*-
"""
Created on Sat Aug  2 08:14:26 2025

@author: meagh
"""

import os
import pandas as pd
from datetime import datetime
from glob import glob

# === SETTINGS ===
input_folder = r"C:\Users\meagh\Downloads\Tricky bandit(1)\Tricky bandit\Male SNI 18\Data"  # Replace with your folder containing the CSVs
file_pattern = "*.CSV"        # Pattern to match CSV files (you can adjust if needed)
#%%
# === HELPERS ===
def get_first_timestamp(file_path):
    try:
        df = pd.read_csv(file_path, skiprows=0)
        # Get first value in the first column
        timestamp_str = str(df.iloc[0, 0]).strip()
        return datetime.strptime(timestamp_str, "%m/%d/%Y %H:%M:%S")
    except Exception as e:
        raise ValueError(f"Failed to parse timestamp from {file_path}: {timestamp_str}") from e

def concat_csv_files(file1, file2):
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2, skiprows=1)  # skip header row
    return pd.concat([df1, df2], ignore_index=True)

# === MAIN LOGIC ===
def find_and_concat_pairs(folder):
    files = sorted(glob(os.path.join(folder, file_pattern)))
    if len(files) < 2:
        print("Need at least two files to concatenate.")
        return

    # Get timestamps and sort files by timestamp
    timestamps = [(f, get_first_timestamp(f)) for f in files]
    timestamps.sort(key=lambda x: x[1])

    for i in range(len(timestamps) - 1):
        file1, ts1 = timestamps[i]
        file2, ts2 = timestamps[i + 1]

        time_diff = ts2 - ts1
        print(f"Concatenating:\n  {os.path.basename(file1)}\n  {os.path.basename(file2)}")
        print(f"Time difference: {time_diff}")

        df_combined = concat_csv_files(file1, file2)
        out_name = os.path.splitext(os.path.basename(file1))[0] + "_concat.csv"
        out_path = os.path.join(folder, out_name)
        df_combined.to_csv(out_path, index=False)
        print(f"Saved to: {out_path}\n")

# === RUN ===
if __name__ == "__main__":
    find_and_concat_pairs(input_folder)
