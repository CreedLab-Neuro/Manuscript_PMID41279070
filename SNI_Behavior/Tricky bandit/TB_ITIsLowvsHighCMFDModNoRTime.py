# -*- coding: utf-8 -*-
"""
Created on Sat Aug  2 09:40:41 2025

@author: meagh
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import ttest_rel, wilcoxon

# ========================
# USER SETTINGS
# ========================
DATA_DIR = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SNI'  # 🔁 Change to your folder path
TIME_WINDOW = (19, 24)              # ⏰ Time window: 7PM–8PM
BIN_WIDTH = 1                       # 📊 Histogram bin width (seconds)
MAX_ITI = 20                        # 🚫 Drop ITIs longer than this (in seconds)
SAVE_NAME = "combined_iti_histogram"  # 📁 Filename (without extension)
# ========================
#%%
def load_and_concat_csvs(directory):
    dfs = []
    for file in os.listdir(directory):
        if file.lower().endswith(".csv"):
            path = os.path.join(directory, file)
            try:
                df = pd.read_csv(path)
                df["Timestamp"] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
                if df["Timestamp"].dt.second.nunique() <= 1 and df["Timestamp"].dt.second.mode().iloc[0] == 0:
                    print(f"⏩ Skipping {file}: no seconds in timestamp.")
                    continue
                df["Mouse"] = file.split(".")[0]
                dfs.append(df)
            except Exception as e:
                print(f"⚠️ Failed reading {file}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def preprocess_df(df):
    df["Retrieval_Time"] = pd.to_numeric(df.get("Retrieval_Time", 0), errors="coerce").fillna(0)
    df["Is_Poke"] = df["Event"].isin(["Left", "Right"])
    df["Is_Pellet"] = df["Event"] == "Pellet"
    df["Block_ID"] = (df["Prob_left"].shift() != df["Prob_left"]) | (df["Prob_right"].shift() != df["Prob_right"])
    df["Block_ID"] = df["Block_ID"].cumsum()
    df["P_Chance"] = (df["Prob_left"] + df["Prob_right"]) / 200
    return df

def compute_itis(df):
    success, unsuccess = [], []
    for (mouse, block_id), block in df.groupby(["Mouse", "Block_ID"]):
        block = block.sort_values("Timestamp")
        last_event_type = None
        last_event_time = None
        for _, row in block.iterrows():
            if row["Is_Poke"]:
                if last_event_type == "Pellet":
                    iti = (row["Timestamp"] - last_event_time).total_seconds()
                    if iti >= 0:
                        success.append({
                            "Mouse": row["Mouse"],
                            "P_Chance": row["P_Chance"],
                            "ITI": iti,
                            "Timestamp": row["Timestamp"]
                        })
                elif last_event_type in ["Left", "Right"]:
                    iti = (row["Timestamp"] - last_event_time).total_seconds()
                    if iti >= 0:
                        unsuccess.append({
                            "Mouse": row["Mouse"],
                            "P_Chance": row["P_Chance"],
                            "ITI": iti,
                            "Timestamp": row["Timestamp"]
                        })
                last_event_type = row["Event"]
                last_event_time = row["Timestamp"]
            elif row["Is_Pellet"]:
                last_event_type = "Pellet"
                last_event_time = row["Timestamp"]
    
    return pd.DataFrame(success), pd.DataFrame(unsuccess)



def filter_by_time(df, time_window):
    return df[(df["Timestamp"].dt.hour >= time_window[0]) & (df["Timestamp"].dt.hour < time_window[1])]

def plot_combined_histograms(success_df, unsuccess_df, save_name=None):
    bins = np.arange(0, MAX_ITI + BIN_WIDTH, BIN_WIDTH)
    plt.figure(figsize=(10, 6))
    labels_colors = [
        (success_df[success_df["P_Chance"] == 0.25], 'green', 'Success Low'),
        (success_df[success_df["P_Chance"] == 0.75], 'blue', 'Success High'),
        (unsuccess_df[unsuccess_df["P_Chance"] == 0.25], 'orange', 'Fail Low'),
        (unsuccess_df[unsuccess_df["P_Chance"] == 0.75], 'red', 'Fail High'),
    ]
    for cond_df, color, label in labels_colors:
        all_counts = np.zeros(len(bins) - 1)
        for _, group in cond_df.groupby("Mouse"):
            counts, _ = np.histogram(group["ITI"], bins=bins)
            if counts.sum() > 0:
                all_counts += counts / counts.sum()
        all_counts = all_counts / len(cond_df["Mouse"].unique()) if len(cond_df["Mouse"].unique()) > 0 else all_counts
        plt.plot(bins[:-1], all_counts, drawstyle="steps-post", label=label, color=color)

    plt.xlim(0, MAX_ITI)
    plt.xlabel("Inter-Trial Interval (s)")
    plt.ylabel("Normalized Density (Equal Mouse Weighting)")
    plt.title(f"Combined ITI Histogram ({TIME_WINDOW[0]}:00–{TIME_WINDOW[1]}:00)")
    plt.legend()
    plt.tight_layout()
    if save_name:
        plt.savefig(f"{save_name}.png", dpi=300)
        plt.savefig(f"{save_name}.svg")
    plt.show()

def run_dual_stats(success_df, unsuccess_df):
    results = {}
    for name, df in zip(["Success", "Unsuccess"], [success_df, unsuccess_df]):
        means = df.groupby(["Mouse", "P_Chance"])["ITI"].mean().unstack()
        means = means[[0.25, 0.75]].dropna()
        if not means.empty:
            t, p = ttest_rel(means[0.75], means[0.25])
            try:
                w, pw = wilcoxon(means[0.75], means[0.25])
            except ValueError:
                w, pw = None, None
        else:
            t, p, w, pw = None, None, None, None
        results[name] = (t, p, w, pw)
    return results

def plot_cmfd(success_df):
    bins = np.linspace(0, MAX_ITI, 1000)
    cmfd_by_mouse = []
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = {0.25: "green", 0.75: "blue"}
    for pchance in [0.25, 0.75]:
        subs = []
        for mouse, group in success_df.groupby("Mouse"):
            sub = group[group["P_Chance"] == pchance]
            if len(sub) == 0:
                continue
            data = sub["ITI"].clip(upper=MAX_ITI)
            hist, bin_edges = np.histogram(data, bins=bins, density=True)
            cdf = np.cumsum(hist * np.diff(bin_edges))
            ax.plot(bins[1:], cdf, color=colors[pchance], alpha=0.2)
            subs.append(cdf)
        if subs:
            all_cmfd = np.stack(subs)
            mean_cmfd = np.mean(all_cmfd, axis=0)
            ci_low = np.percentile(all_cmfd, 5, axis=0)
            ci_high = np.percentile(all_cmfd, 95, axis=0)
            ax.plot(bins[1:], mean_cmfd, color=colors[pchance], label=f"{pchance} (mean)", linewidth=2.5)
            ax.fill_between(bins[1:], ci_low, ci_high, color=colors[pchance], alpha=0.3)

    ax.set_xlim(0, MAX_ITI)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Inter-Trial Interval (s)")
    ax.set_ylabel("Cumulative Fraction of Trials")
    ax.set_title("Cumulative ITI Distributions (Success Only)")
    ax.legend()
    plt.tight_layout()
    plt.savefig("ITIDistr_Success_SNIv20s.svg")
    plt.savefig("ITIDistr_Success_SNIv20s.png")
    plt.show()

# Run pipeline
raw_df = load_and_concat_csvs(DATA_DIR)
if raw_df.empty:
    print("❌ No valid files loaded.")
else:
    pre_df = preprocess_df(raw_df)
    success_df, unsuccess_df = compute_itis(pre_df)

    success_df = filter_by_time(success_df, TIME_WINDOW)
    unsuccess_df = filter_by_time(unsuccess_df, TIME_WINDOW)

    success_df = success_df[success_df["ITI"] <= MAX_ITI]
    unsuccess_df = unsuccess_df[unsuccess_df["ITI"] <= MAX_ITI]

    plot_combined_histograms(success_df, unsuccess_df, save_name=SAVE_NAME)
    plot_cmfd(success_df)

    stats = run_dual_stats(success_df, unsuccess_df)
    print("\n📊 Statistical Results:")
    for trial_type, (t, p, w, pw) in stats.items():
        print(f"\n🔹 {trial_type} Trials")
        print(f"  Paired t-test: t = {t}, p = {p}")
        print(f"  Wilcoxon test: W = {w}, p = {pw}")
