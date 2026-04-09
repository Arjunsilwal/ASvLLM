import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

from analysis_utils import add_analysis_columns
from analysis_config import (MODE_ORDER, PROVIDER_ORDER, PROMPT_ORDER, 
                             PLOT_STYLE, FIG_SIZES)

# 1. LOAD AND PREPARE DATA
df = pd.read_csv("master_results.csv")
os.makedirs("study_results", exist_ok=True)

# Ensure analysis columns exist
if 'Accuracy' not in df.columns:
    df = add_analysis_columns(df)
# Shorten scenario names for cleaner heatmaps if necessary
df['Scenario_Short'] = df['Scenario'].str.replace(' Scenario', '')

# 2. IMPROVEMENT 1: MODE-PROMPT INTERACTION HEATMAPS
# This identifies the "Sweet Spot" (e.g., Is vision best with natural or detailed prompts?)
plt.figure(figsize=(18, 6))
g = sns.FacetGrid(df, col="LLM Provider", height=5, aspect=1.2)
g.map_dataframe(lambda data, **kws: sns.heatmap(
    data.pivot_table(index='Mode', columns='Prompt Type', values='Accuracy', aggfunc='mean').reindex(index=MODE_ORDER, columns=PROMPT_ORDER),
    annot=True, fmt=".2f", cmap="YlGnBu", cbar=True, **kws
))
g.set_axis_labels("Prompt Style", "Intelligence Mode")
g.fig.suptitle("Mode-Prompt Interaction: Finding the Optimal Configuration", y=1.05)
plt.savefig("study_results/interaction_mode_prompt_accuracy.png")

# 3. IMPROVEMENT 2: SCENARIO-PROMPT PERFORMANCE HEATMAP
# This identifies which prompt style is most "Robust" across different encounter types
plt.figure(figsize=(18, 8))
# We group by Scenario and Prompt Type to see which combinations fail/succeed
scenario_prompt = df.groupby(['Scenario_Short', 'Prompt Type'])['Accuracy'].mean().unstack()
scenario_prompt = scenario_prompt.reindex(columns=[p for p in PROMPT_ORDER if p in scenario_prompt.columns])
sns.heatmap(scenario_prompt, annot=True, fmt=".2f", cmap="Blues")
plt.title("Scenario-Prompt Analysis: Which Prompt Solves Which Encounter?")
plt.ylabel("Navigational Scenario")
plt.xlabel("Prompt Engineering Style")
plt.savefig("study_results/interaction_scenario_prompt.png")

# 4. IMPROVEMENT 3: RELIABILITY HEATMAP (STABILITY STUDY)
# High accuracy is good, but high consistency (low StdDev) is safer for ASVs
plt.figure(figsize=(18, 6))
# Calculate StdDev for each configuration
reliability_pivot = df.groupby(['LLM Provider', 'Mode', 'Prompt Type'])['Accuracy'].std().reset_index()

g_rel = sns.FacetGrid(reliability_pivot, col="LLM Provider", height=5, aspect=1.2)
g_rel.map_dataframe(lambda data, **kws: sns.heatmap(
    data.pivot_table(index='Mode', columns='Prompt Type', values='Accuracy').reindex(index=MODE_ORDER, columns=PROMPT_ORDER),
    annot=True, fmt=".2f", cmap="YlOrRd_r", cbar=True, **kws # Red means high variance (bad)
))
g_rel.set_axis_labels("Prompt Style", "Intelligence Mode")
g_rel.fig.suptitle("Decision Stability: Lower Values (Blue/Green) = More Reliable", y=1.05)
plt.savefig("study_results/interaction_reliability_heatmap.png")

# 5. GENERATE DATA TABLES FOR THE PAPER
print("\n--- BEST CONFIGURATION PER PROVIDER ---")
for provider in df['LLM Provider'].unique():
    prov_data = df[df['LLM Provider'] == provider]
    best = prov_data.groupby(['Mode', 'Prompt Type'])['Accuracy'].mean().idxmax()
    score = prov_data.groupby(['Mode', 'Prompt Type'])['Accuracy'].mean().max()
    print(f"{provider.upper()}: Best performance at {best} with {score:.2f} accuracy")

print("\n--- HARDEST SCENARIOS PER PROMPT ---")
hardest = df.groupby(['Scenario', 'Prompt Type'])['Accuracy'].mean().unstack().idxmin()
print(hardest)
