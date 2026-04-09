#!/usr/bin/env python3
"""
Data Quality Validator for ASvLLM Results

Checks for:
- Duplicate rows
- Invalid accuracy values
- Missing LLM responses
- Inconsistent scenario names
- Anomalous DCPA values
"""

import pandas as pd
import glob
import os
import sys
from collections import Counter

def validate_logs(verbose=True):
    log_folder = 'logs'
    all_files = glob.glob(os.path.join(log_folder, "results_*.csv"))
    
    if not all_files:
        print("❌ Error: No result files found in 'logs/'.")
        return False
    
    print(f"\n{'='*60}")
    print(f"  DATA QUALITY VALIDATION REPORT")
    print(f"{'='*60}\n")
    
    # Load all data
    all_data = []
    for f in all_files:
        df = pd.read_csv(f)
        all_data.append(df)
        print(f"✓ Loaded {f}: {len(df)} rows")
    
    df = pd.concat(all_data, ignore_index=True)
    print(f"\nTotal rows merged: {len(df)}\n")
    
    # --- CHECK 1: Duplicates ---
    print(f"{'='*60}")
    print("CHECK 1: DUPLICATE DETECTION")
    print(f"{'='*60}")
    
    # Identify by Experiment ID + Call ID
    if 'Experiment ID' in df.columns and 'Call ID' in df.columns:
        duplicates = df[df.duplicated(subset=['Experiment ID', 'Call ID'], keep=False)]
        if len(duplicates) > 0:
            print(f"⚠️  Found {len(duplicates)} duplicate entries (same Exp ID + Call ID)")
            if verbose:
                print(duplicates[['Experiment ID', 'Call ID', 'Scenario']].head(10))
        else:
            print("✓ No duplicate entries found")
    else:
        print("⚠️  Missing Experiment ID or Call ID columns; skipping duplicate check")
    
    # --- CHECK 2: Accuracy Values ---
    print(f"\n{'='*60}")
    print("CHECK 2: ACCURACY VALUE VALIDATION")
    print(f"{'='*60}")
    
    if 'Accuracy' in df.columns:
        invalid_acc = df[(df['Accuracy'] < 0.0) | (df['Accuracy'] > 1.0)]
        if len(invalid_acc) > 0:
            print(f"❌ Found {len(invalid_acc)} invalid accuracy values (outside [0.0, 1.0])")
            print(invalid_acc[['Accuracy', 'Scenario', 'LLM Provider']].head())
        else:
            print("✓ All accuracy values in valid range [0.0, 1.0]")
        
        print(f"\nAccuracy distribution:")
        print(f"  Mean: {df['Accuracy'].mean():.3f}")
        print(f"  Median: {df['Accuracy'].median():.3f}")
        print(f"  Std Dev: {df['Accuracy'].std():.3f}")
        print(f"  Min: {df['Accuracy'].min():.3f}, Max: {df['Accuracy'].max():.3f}")
    else:
        print("⚠️  'Accuracy' column not found")
    
    # --- CHECK 3: LLM Response Quality ---
    print(f"\n{'='*60}")
    print("CHECK 3: LLM RESPONSE QUALITY")
    print(f"{'='*60}")
    
    if 'llm_response_json' in df.columns:
        empty_responses = df[df['llm_response_json'].isna() | (df['llm_response_json'] == '[]')]
        if len(empty_responses) > 0:
            print(f"⚠️  Found {len(empty_responses)} empty or malformed responses ([])")
            print(f"  Providers: {empty_responses['LLM Provider'].unique()}")
            print(f"  Modes: {empty_responses['Mode'].unique()}")
        else:
            print("✓ All LLM responses contain valid JSON")
    else:
        print("⚠️  'llm_response_json' column not found")
    
    # --- CHECK 4: Scenario Consistency ---
    print(f"\n{'='*60}")
    print("CHECK 4: SCENARIO NAME CONSISTENCY")
    print(f"{'='*60}")
    
    valid_scenarios = {
        "Head-On Scenario",
        "Cross Over Scenario",
        "Over Taking Scenario",
        "Multi vessel Scenario",
        "Multi vessel Scenario 2",
        "Multi vessel Scenario 3",
        "Traffic Separation Scenario"
    }
    
    if 'Scenario' in df.columns:
        unique_scenarios = set(df['Scenario'].unique())
        invalid = unique_scenarios - valid_scenarios
        
        if invalid:
            print(f"❌ Found invalid scenario names: {invalid}")
        else:
            print(f"✓ All scenario names are valid")
        
        scenario_counts = df['Scenario'].value_counts()
        print(f"\nScenario distribution:")
        for sc in valid_scenarios:
            count = scenario_counts.get(sc, 0)
            print(f"  {sc}: {count} calls")
    else:
        print("⚠️  'Scenario' column not found")
    
    # --- CHECK 5: Provider & Mode Consistency ---
    print(f"\n{'='*60}")
    print("CHECK 5: PROVIDER & MODE CONSISTENCY")
    print(f"{'='*60}")
    
    valid_providers = {"openai", "claude", "deepseek"}
    valid_modes = {"standard", "prompt_history", "natural"}
    
    if 'LLM Provider' in df.columns:
        invalid_providers = set(df['LLM Provider'].unique()) - valid_providers
        if invalid_providers:
            print(f"❌ Found invalid providers: {invalid_providers}")
        else:
            print(f"✓ Provider values valid")
            print(f"  Row counts by provider:")
            for prov in df['LLM Provider'].unique():
                count = (df['LLM Provider'] == prov).sum()
                print(f"    {prov}: {count}")
    
    if 'Mode' in df.columns:
        invalid_modes = set(df['Mode'].unique()) - valid_modes
        if invalid_modes:
            print(f"❌ Found invalid modes: {invalid_modes}")
        else:
            print(f"✓ Mode values valid")
            print(f"  Row counts by mode:")
            for mode in df['Mode'].unique():
                count = (df['Mode'] == mode).sum()
                print(f"    {mode}: {count}")
    
    # --- CHECK 6: DCPA/Distance Sanity ---
    print(f"\n{'='*60}")
    print("CHECK 6: DISTANCE METRICS (SANITY CHECK)")
    print(f"{'='*60}")
    
    if 'Min Pairwise Distance (px)' in df.columns:
        dist_px = df['Min Pairwise Distance (px)']
        anomalies = dist_px[dist_px < 0]
        if len(anomalies) > 0:
            print(f"❌ Found {len(anomalies)} negative distance values")
        else:
            print(f"✓ No negative distances")
        
        print(f"\nDistance (pixels) distribution:")
        print(f"  Mean: {dist_px.mean():.1f}, Median: {dist_px.median():.1f}")
        print(f"  Min: {dist_px.min():.1f}, Max: {dist_px.max():.1f}")
    
    # --- CHECK 7: Provider-Mode-Prompt Combinations ---
    print(f"\n{'='*60}")
    print("CHECK 7: EXPECTED COMBINATIONS (Provider × Mode × Prompt)")
    print(f"{'='*60}")
    
    expected_combos = {
        ('openai', 'standard', 'minimal'),
        ('openai', 'standard', 'moderate'),
        ('openai', 'standard', 'detailed'),
        ('openai', 'standard', 'natural'),
        ('openai', 'prompt_history', 'natural_history'),
        ('openai', 'natural', 'natural_vision'),
        ('claude', 'standard', 'minimal'),
        ('claude', 'standard', 'moderate'),
        ('claude', 'standard', 'detailed'),
        ('claude', 'standard', 'natural'),
        ('claude', 'prompt_history', 'natural_history'),
        ('claude', 'natural', 'natural_vision'),
        ('deepseek', 'standard', 'minimal'),
        ('deepseek', 'standard', 'moderate'),
        ('deepseek', 'standard', 'detailed'),
        ('deepseek', 'standard', 'natural'),
        ('deepseek', 'prompt_history', 'natural_history'),
    }
    
    if 'LLM Provider' in df.columns and 'Mode' in df.columns and 'Prompt Type' in df.columns:
        actual_combos = set(zip(df['LLM Provider'], df['Mode'], df['Prompt Type']))
        
        missing = expected_combos - actual_combos
        unexpected = actual_combos - expected_combos
        
        if missing:
            print(f"⚠️  Missing combinations (may be expected for partial runs):")
            for combo in sorted(missing)[:5]:
                print(f"  {combo}")
        
        if unexpected:
            print(f"⚠️  Unexpected combinations:")
            for combo in sorted(unexpected):
                print(f"  {combo}")
        
        if not missing and not unexpected:
            print(f"✓ All expected combinations present (full factorial design)")
    
    # --- SUMMARY ---
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    issues_found = len(invalid_acc) if 'Accuracy' in df.columns and 'invalid_acc' in locals() else 0
    issues_found += len(empty_responses) if 'llm_response_json' in df.columns and 'empty_responses' in locals() else 0
    issues_found += len(invalid) if 'invalid' in locals() else 0
    
    if issues_found == 0:
        print("✅ All checks PASSED - Dataset is ready for analysis!")
        return True
    else:
        print(f"⚠️  Found {issues_found} issue(s) - Review above for details")
        return False

if __name__ == "__main__":
    success = validate_logs(verbose=True)
    sys.exit(0 if success else 1)
