"""
analysis_utils.py - Shared utility functions for ASvLLM analysis pipeline

Consolidates common functions used across:
  - master_analysis.py
  - final_plots.py
  - ablation_study.py
  - mode_prompt_study.py
"""

import re
import pandas as pd


def extract_rule_num(text):
    """
    Extract COLREG rule numbers from text.
    Handles formats like "Rule 13", "R14", "rule:15", etc.
    
    Args:
        text (str): Text containing rule references
    
    Returns:
        set: Set of rule numbers as strings (e.g., {'13', '14'})
    """
    nums = re.findall(r'(?:Rule|R)\s*[:]?\s*(\d+)', str(text), re.IGNORECASE)
    return set(nums)


def calculate_alignment(row):
    """
    Check if LLM decision is aligned: correct action + correct rule citation.
    
    Args:
        row (pd.Series): Row with Accuracy, GT_Rules, Cited_Rules
    
    Returns:
        bool: True if action is correct (Accuracy==1.0) AND rules match
    """
    if row['Accuracy'] < 1.0:
        return False
    return row['GT_Rules'] == row['Cited_Rules']


def add_analysis_columns(df):
    """
    Add derived columns: Accuracy, Rule alignment, etc.
    
    Args:
        df (pd.DataFrame): Raw results DataFrame
    
    Returns:
        pd.DataFrame: DataFrame with additional analysis columns
    """
    df = df.copy()
    
    # Calculate accuracy from verdict
    def calc_accuracy(verdict):
        v = str(verdict).lower()
        passes = v.count('pass')
        fails = v.count('fail')
        return passes / (passes + fails) if (passes + fails) > 0 else 0
    
    df['Accuracy'] = df['Verdict'].apply(calc_accuracy)
    df['GT_Rules'] = df['GT Rule'].apply(extract_rule_num)
    df['Cited_Rules'] = df['LLM Cited Rule'].apply(extract_rule_num)
    df['Is_Aligned'] = df.apply(calculate_alignment, axis=1)
    
    return df


def calculate_metrics(df):
    """
    Calculate official research metrics from results.
    
    Args:
        df (pd.DataFrame): Merged results with Accuracy column
    
    Returns:
        dict: Metrics dictionary
    """
    config_cols = ['LLM Provider', 'Mode', 'Scenario', 'Prompt Type']
    run_level = df.groupby(config_cols + ['Experiment ID'])['Accuracy'].mean().reset_index()
    
    metrics = {
        'compliance': df.groupby('LLM Provider')['Accuracy'].mean(),
        'reliability': run_level.groupby(config_cols)['Accuracy'].std().groupby('LLM Provider').mean(),
    }
    
    # Robustness: simple vs complex scenarios
    simple_sc = ["Head-On Scenario", "Cross Over Scenario", "Over Taking Scenario"]
    complex_sc = ["Multi vessel Scenario", "Multi vessel Scenario 2", "Multi vessel Scenario 3"]
    
    acc_simple = df[df['Scenario'].isin(simple_sc)].groupby('LLM Provider')['Accuracy'].mean()
    acc_complex = df[df['Scenario'].isin(complex_sc)].groupby('LLM Provider')['Accuracy'].mean()
    metrics['robustness_gap'] = acc_simple - acc_complex
    
    # Rule alignment
    metrics['alignment'] = df[df['Accuracy'] == 1.0].groupby('LLM Provider')['Is_Aligned'].mean()
    
    return metrics


def print_metrics(metrics, run_df=None):
    """Pretty-print research metrics to console."""
    print("\n" + "="*50)
    print("         OFFICIAL RESEARCH METRICS")
    print("="*50)
    
    print(f"\n1. COMPLIANCE RATE:\n{metrics['compliance']}")
    print(f"\n2. RELIABILITY (Mean Std Dev of 10 Runs):\n{metrics['reliability']}")
    print(f"\n3. ROBUSTNESS GAP (Drop in Complex Scenarios):\n{metrics['robustness_gap']}")
    print(f"\n4. RULE ALIGNMENT RATE (Correct Logic):\n{metrics['alignment']}")
    
    if run_df is not None and not run_df.empty:
        print(f"\n5. SCENARIO SUCCESS RATE:\n{run_df.groupby('LLM Provider')['All Reached Goal'].mean()}")
        print(f"\n6. COLLISION RATE:\n{run_df.groupby('LLM Provider')['Any Collision'].mean()}")
        print(f"\n7. AVG MIN CPA-LIKE DISTANCE (km):\n{run_df.groupby('LLM Provider')['Min Pairwise Distance (km)'].mean()}")
