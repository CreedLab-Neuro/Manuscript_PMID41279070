# -*- coding: utf-8 -*-
"""
Created on Mon Jul 28 22:22:54 2025

@author: meagh
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import sem, ttest_1samp, ttest_ind
import os

# ------------------ PARAMETERS ------------------
PELLETS_TO_DISCARD = 0
poke_events = ["Left", "Right"]
pellet_event = "Pellet"

# Set these paths to your local directories
sham_dir = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SHAM'
sni_dir = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SNI'

def compute_accuracy(df, pellets_to_discard):
    results = []
    df["block_id"] = (df[["Prob_left", "Prob_right"]]
                      .ne(df[["Prob_left", "Prob_right"]].shift())
                      .any(axis=1)).cumsum()
    
    for block_id, block_df in df.groupby("block_id"):
        pellet_indices = block_df[block_df["Event"] == pellet_event].index
        if len(pellet_indices) < pellets_to_discard + 1:
            continue
        start_idx = pellet_indices[pellets_to_discard - 1] if pellets_to_discard > 0 else block_df.index[0]
        post_block = block_df.loc[start_idx + 1:]

        if "High_prob_poke" not in post_block.columns:
            continue  # skip if required column is missing

        post_block = post_block[post_block["Event"].isin(poke_events)]

        if post_block.empty:
            continue

        correct = (
            (post_block["Event"] == post_block["High_prob_poke"])
        ).sum()

        total = len(post_block)
        accuracy = correct / total if total > 0 else np.nan

        prob_left = block_df["Prob_left"].iloc[0]
        prob_right = block_df["Prob_right"].iloc[0]
        p_chance = (prob_left + prob_right) / 200

        results.append((p_chance, accuracy))

    return results

def process_directory_accuracy(directory, group_name):
    all_data = []
    for fname in os.listdir(directory):
        if not fname.lower().endswith(".csv"):
            continue
        path = os.path.join(directory, fname)
        try:
            df = pd.read_csv(path)
            df["Timestamp"] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
            df = df.dropna(subset=["Timestamp"])
        except Exception as e:
            print(f"⚠️ Skipping {fname}: {e}")
            continue

        sex = "Female" if fname.startswith("F") else "Male"
        color = "red" if sex == "Female" else "blue"

        acc_data = compute_accuracy(df, PELLETS_TO_DISCARD)
        for p_chance, acc in acc_data:
            all_data.append({
                "Mouse": fname,
                "Group": group_name,
                "Sex": sex,
                "Color": color,
                "P(Chance)": p_chance,
                "Accuracy": acc
            })
    return pd.DataFrame(all_data)

# Load data
df_sham = process_directory_accuracy(sham_dir, "SHAM")
df_sni = process_directory_accuracy(sni_dir, "SNI")
df_all = pd.concat([df_sham, df_sni], ignore_index=True)

# Compute per-mouse averages
grouped = (
    df_all.groupby(["Group", "Mouse", "Sex", "Color", "P(Chance)"])
    .agg(AccuracyMean=("Accuracy", "mean"), AccuracySEM=("Accuracy", sem))
    .reset_index()
)

# ------------------ PLOT ------------------
fig, axes = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

for ax, group in zip(axes, ["SHAM", "SNI"]):
    df = grouped[grouped["Group"] == group]
    for sex in ["Male", "Female"]:
        sub = df[df["Sex"] == sex]
        color = "blue" if sex == "Male" else "red"
        ax.errorbar(sub["P(Chance)"], sub["AccuracyMean"],
                    yerr=sub["AccuracySEM"], fmt='o', color=color,
                    alpha=0.7, label=sex)
    ax.plot([0.25, 0.5, 0.75], [0.5, 0.5, 0.5], 'k--', label='Chance')
    ax.set_title(f"{group}: Accuracy vs P(Chance)")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Accuracy")
    ax.legend()

axes[1].set_xlabel("P(Chance)")
plt.tight_layout()
#fig_path_svg = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SHAM'
#fig_path_png = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SHAM'
fig.savefig('TB_Accuracy.png')
fig.savefig('TB_Accuracy.svg')

# ------------------ STATS ------------------
print("\n🧪 One-sample t-tests (Accuracy > 0.5):")
for df_group, name in zip([df_sham, df_sni], ["SHAM", "SNI"]):
    diff = df_group["Accuracy"] - 0.5
    t, p = ttest_1samp(diff.dropna(), popmean=0)
    print(f"{name}: mean acc = {df_group['Accuracy'].mean():.3f}, t = {t:.3f}, p = {p:.4g}")

print("\n🧪 Between-group test (SHAM vs SNI):")
t, p = ttest_ind(df_sham["Accuracy"].dropna(), df_sni["Accuracy"].dropna(), equal_var=False)
print(f"SHAM vs SNI: t = {t:.3f}, p = {p:.4g}")
plt.show()
