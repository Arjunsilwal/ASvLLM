"""
analysis_config.py - Shared configuration for analysis scripts

Consolidates constants and parameters used across the analysis pipeline.
"""

# Scenario definitions
ALL_SCENARIOS = [
    "Head-On Scenario",
    "Cross Over Scenario",
    "Over Taking Scenario",
    "Multi vessel Scenario",
    "Multi vessel Scenario 2",
    "Multi vessel Scenario 3",
    "Traffic Separation Scenario"
]

SIMPLE_SCENARIOS = [
    "Head-On Scenario",
    "Cross Over Scenario",
    "Over Taking Scenario"
]

COMPLEX_SCENARIOS = [
    "Multi vessel Scenario",
    "Multi vessel Scenario 2",
    "Multi vessel Scenario 3"
]

# Ordering for consistent visualization
MODE_ORDER = ['standard', 'prompt_history', 'natural']
PROVIDER_ORDER = ['openai', 'claude', 'deepseek']
PROMPT_ORDER = ['minimal', 'moderate', 'detailed', 'natural', 'natural_history', 'natural_vision', 'tss']
SCENARIO_ORDER = ALL_SCENARIOS

# Color palettes by use case
PALETTES = {
    'provider': 'Set2',           # For provider comparison
    'mode': 'viridis',            # For mode comparison
    'ablation': 'coolwarm',       # For gain/loss visualization
    'reliability': 'magma',       # For StdDev/consistency
    'robustness': 'coolwarm',     # For complexity tolerance
    'alignment': 'rocket',        # For rule alignment
    'failure': 'Reds',            # For failure rates
    'interaction': 'YlGnBu',      # For heatmaps (good=blue)
}

# Plot styling
PLOT_STYLE = "whitegrid"
PLOT_CONTEXT = "paper"
FONT_SCALE = 1.2

# Figure sizes
FIG_SIZES = {
    'small': (10, 6),
    'medium': (12, 6),
    'heatmap': (10, 5),
    'faceted': (18, 6),
    'wide': (18, 8),
}

# Output directories
OUTPUT_DIRS = {
    'figures': 'figures',
    'study': 'study_results',
    'logs': 'logs',
}

# Expected output files from run_all_analysis.py
EXPECTED_OUTPUTS = [
    # From master_analysis.py
    "master_results.csv",
    "master_run_results.csv",
    "eda_accuracy_by_mode.png",
    "eda_scenario_difficulty.png",
    # From ablation_study.py
    "figures/ablation_prompt_effect_standard_mode.png",
    "figures/ablation_mode_gain_vs_standard.png",
    "figures/ablation_scenario_failure_heatmap.png",
    "figures/ablation_prompt_alignment_standard_mode.png",
    # From mode_prompt_study.py
    "study_results/interaction_mode_prompt_accuracy.png",
    "study_results/interaction_scenario_prompt.png",
    "study_results/interaction_reliability_heatmap.png",
    # From final_plots.py
    "figures/fig1_accuracy_ablation.png",
    "figures/fig2_reliability_ablation.png",
    "figures/fig3_robustness_matrix.png",
    "figures/fig4_explanation_alignment.png",
]
