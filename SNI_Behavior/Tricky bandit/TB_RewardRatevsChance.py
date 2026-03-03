# -*- coding: utf-8 -*-
"""
Created on Tue Jul 29 22:17:19 2025

@author: meagh
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import sem, ttest_1samp, ttest_ind
import os

# ------------------ PARAMETERS ------------------
PELLETS_TO_DISCARD = 3
poke_events = ["Left", "Right"]
pellet_event = "Pellet"

# Update these paths with your actual SHAM and SNI folders
sham_dir = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SHAM'
sni_dir = r'C:\Users\meagh\OneDrive\Desktop\Tricky bandit\SNI'
#%%
def process_directory(directory, group_name):
    results = []
    for fname in os.listdir(directory):
        if not fname.lower().endswith(".csv"):
            continue
        path = os.path.join(directory, fname)
        try:
            df = pd.read_csv(path)
            df["Timestamp"] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
            df = df.dropna(subset=["Timestamp"])
        except Exception as e:
            print(f"⚠️ Could not load {fname}: {e}")
            continue

        df["block_id"] = (df[["Prob_left", "Prob_right"]]
                          .ne(df[["Prob_left", "Prob_right"]].shift())
                          .any(axis=1)).cumsum()

        for block_id, block_df in df.groupby("block_id"):
            pellet_indices = block_df[block_df["Event"] == pellet_event].index
            if len(pellet_indices) < PELLETS_TO_DISCARD + 1:
                continue

            start_idx = pellet_indices[PELLETS_TO_DISCARD - 1] if PELLETS_TO_DISCARD > 0 else block_df.index[0]
            post_block = block_df.loc[start_idx + 1:]

            prob_left = block_df["Prob_left"].iloc[0]
            prob_right = block_df["Prob_right"].iloc[0]
            p_chance = (prob_left + prob_right) / 200
            n_pokes = post_block["Event"].isin(poke_events).sum()
            n_pellets = (post_block["Event"] == pellet_event).sum()
            reward_rate = n_pellets / n_pokes if n_pokes > 0 else 0

            sex = "Female" if fname.startswith("F") else "Male"
            color = "red" if sex == "Female" else "blue"

            results.append({
                "Mouse": fname,
                "Sex": sex,
                "Color": color,
                "P(Chance)": p_chance,
                "Reward Rate": reward_rate,
                "Group": group_name
            })
    return pd.DataFrame(results)

# Process both groups
df_sham = process_directory(sham_dir, "SHAM")
df_sni = process_directory(sni_dir, "SNI")
df_all = pd.concat([df_sham, df_sni], ignore_index=True)

# Grouped means per mouse x P(Chance)
grouped_all = (
    df_all.groupby(["Group", "Mouse", "Sex", "Color", "P(Chance)"])
    .agg(RewardRateMean=("Reward Rate", "mean"),
         RewardRateSEM=("Reward Rate", sem))
    .reset_index()
)

# ------------------ PLOTTING ------------------
fig, axes = plt.subplots(2, 3, figsize=(24, 12), sharey=True)

for i, group in enumerate(["SHAM", "SNI"]):
    df = df_all[df_all["Group"] == group]
    grouped = grouped_all[grouped_all["Group"] == group]

    # Plot 1: Individual regressions
    sns.stripplot(data=df, x="P(Chance)", y="Reward Rate",
                  hue="Sex", palette={"Female": "red", "Male": "blue"},
                  dodge=False, jitter=0.02, marker='o', alpha=0.2, ax=axes[i, 0])
    for mouse in df["Mouse"].unique():
        mdf = df[df["Mouse"] == mouse]
        color = "red" if mdf["Sex"].iloc[0] == "Female" else "blue"
        sns.regplot(data=mdf, x="P(Chance)", y="Reward Rate", scatter=False,
                    color=color, ci=None, line_kws={"alpha": 0.3}, ax=axes[i, 0])
    axes[i, 0].plot([0.25, 0.5, 0.75], [0.25, 0.5, 0.75],
                   linestyle='dotted', color='grey', linewidth=2)
    axes[i, 0].set_title(f"{group}: Per-Mouse Regressions")
    axes[i, 0].legend().set_title("Sex")

    # Plot 2: Overall regression with CI
    sns.stripplot(data=df, x="P(Chance)", y="Reward Rate",
                  hue="Sex", palette={"Female": "red", "Male": "blue"},
                  dodge=False, jitter=0.02, marker='o', alpha=0.2, ax=axes[i, 1])
    sns.regplot(data=df, x="P(Chance)", y="Reward Rate", scatter=False,
                color='black', line_kws={'linewidth': 3}, ci=95, ax=axes[i, 1])
    axes[i, 1].plot([0.25, 0.5, 0.75], [0.25, 0.5, 0.75],
                    linestyle='dotted', color='grey', linewidth=2)
    axes[i, 1].set_title(f"{group}: Overall Regression")

    # Plot 3: Mean ± SEM per mouse
    for sex in ["Male", "Female"]:
        sub = grouped[grouped["Sex"] == sex]
        color = "blue" if sex == "Male" else "red"
        axes[i, 2].errorbar(sub["P(Chance)"], sub["RewardRateMean"],
                            yerr=sub["RewardRateSEM"], fmt='o',
                            color=color, label=sex, alpha=0.6)
    axes[i, 2].plot([0.25, 0.5, 0.75], [0.25, 0.5, 0.75],
                    linestyle='dotted', color='grey', linewidth=2)
    axes[i, 2].set_title(f"{group}: Per-Mouse Mean ± SEM")
    axes[i, 2].legend(title="Sex")

# Formatting
for row in axes:
    for ax in row:
        ax.set_ylim(0, 1)
        ax.set_xlabel("P(Chance)")
        ax.set_ylabel("Reward Rate")

plt.tight_layout()
fig.savefig('TB_RewardRate_vsChance.png')
fig.savefig('TB_RewardRate_vsChance.svg')

# ------------------ STATS ------------------
print("\n🧪 One-sample t-tests (Reward Rate > Chance):")
for group_df, name in zip([df_sham, df_sni], ["SHAM", "SNI"]):
    diff = group_df["Reward Rate"] - group_df["P(Chance)"]
    t, p = ttest_1samp(diff, popmean=0)
    print(f"{name}: mean diff = {diff.mean():.3f}, t = {t:.3f}, p = {p:.4g}")

# Between-group comparison
print("\n🧪 Two-sample t-test (SHAM vs SNI):")
diff_sham = df_sham["Reward Rate"] - df_sham["P(Chance)"]
diff_sni = df_sni["Reward Rate"] - df_sni["P(Chance)"]
t, p = ttest_ind(diff_sham, diff_sni, equal_var=False)
print(f"SHAM vs SNI: t = {t:.3f}, p = {p:.4g}")
fig_path_svg, fig_path_png
