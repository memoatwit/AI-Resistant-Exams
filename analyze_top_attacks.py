#!/usr/bin/env python3
"""
Script to analyze the results from the top attacks experiment.
This provides a focused analysis of our most effective attacks.
"""

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse

def analyze_top_attacks_results(log_file='top_attacks_results.jsonl', output_prefix='top_attacks'):
    """
    Analyze the results of the top attacks experiment.
    
    Args:
        log_file (str): Path to the experiment log file
        output_prefix (str): Prefix for output files
    """
    if not os.path.exists(log_file):
        print(f"Error: Log file '{log_file}' not found.")
        return
    
    print(f"Analyzing results from {log_file}...")
    
    # Load the log data
    try:
        with open(log_file, 'r') as f:
            entries = []
            for line in f:
                if not line.strip():
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON line: {e}")
    except Exception as e:
        print(f"Error reading log file: {e}")
        return
    
    if not entries:
        print("No valid entries found in the log file.")
        return
        
    print(f"Found {len(entries)} test results to analyze.")
    
    # First, find baseline output length for each model and prompt type
    baseline_lengths = {}
    for entry in entries:
        if entry.get('status') == 'success' and entry['attack_details']['type'] == 'none':
            model = entry.get('model', 'unknown')
            prompt_type = entry.get('prompt_type', 'unknown')
            if 'test_run_output' in entry and 'analysis' in entry['test_run_output']:
                output_length = entry['test_run_output']['analysis'].get('image_output_length', 0)
                baseline_lengths[(model, prompt_type)] = output_length
    
    print(f"Baseline output lengths: {baseline_lengths}")
    
    # Now analyze each attack's effectiveness relative to its baseline
    attack_data = []
    
    for entry in entries:
        if entry.get('status') != 'success':
            continue
            
        attack_name = entry['attack_details']['name']
        attack_type = entry['attack_details']['type']
        model = entry.get('model', 'unknown')
        prompt_type = entry.get('prompt_type', 'unknown')
        
        # Skip baseline for effectiveness calculation
        if attack_type == 'none':
            continue
        
        if 'test_run_output' in entry and 'analysis' in entry['test_run_output']:
            output_length = entry['test_run_output']['analysis'].get('image_output_length', 0)
            is_failed = entry['test_run_output']['analysis'].get('image_test_failed', False)
            
            # Get corresponding baseline length
            baseline_length = baseline_lengths.get((model, prompt_type), 0)
            if baseline_length == 0:
                print(f"Warning: No baseline found for {model}, {prompt_type}")
                continue
            
            # Calculate relative reduction in output (effectiveness)
            length_reduction = baseline_length - output_length
            effectiveness = (length_reduction / baseline_length) * 100
            
            # If test failed entirely (no output), that's maximum effectiveness
            if is_failed or output_length == 0:
                effectiveness = 100
            
            attack_data.append({
                'attack_name': attack_name,
                'attack_type': attack_type,
                'model': model,
                'prompt_type': prompt_type,
                'output_length': output_length,
                'baseline_length': baseline_length,
                'length_reduction': length_reduction,
                'effectiveness': effectiveness,
                'is_failed': is_failed
            })
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(attack_data)
    if df.empty:
        print("No attack data available for analysis.")
        return
    
    print(f"\nAnalyzed {len(df)} attack instances against baselines.")
    
    # Get average effectiveness by attack
    attack_summary = df.groupby('attack_name')['effectiveness'].agg(['mean', 'std', 'count']).reset_index()
    attack_summary = attack_summary.sort_values(by='mean', ascending=False)
    
    # Get effectiveness by prompt type
    prompt_summary = df.pivot_table(index='attack_name', columns='prompt_type', 
                                    values='effectiveness', aggfunc='mean')
    
    # Save detailed results to CSV for further analysis
    df.to_csv(f'{output_prefix}_detailed_results.csv', index=False)
    
    # Create effectiveness chart
    plt.figure(figsize=(12, 8))
    bars = plt.bar(attack_summary['attack_name'], attack_summary['mean'], 
                   yerr=attack_summary['std'], capsize=5,
                   color=sns.color_palette('viridis', len(attack_summary)))
    
    # Add reference line at 0%
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.7, 
                label='Baseline (0% = no effect)')
    
    # Add a line at 25% as a "good effectiveness" threshold
    plt.axhline(y=25, color='g', linestyle='--', alpha=0.7,
               label='Good effectiveness threshold (25%)')
    
    plt.title('Top Attack Effectiveness Against AI Models', fontsize=16)
    plt.xlabel('Attack Name', fontsize=14)
    plt.ylabel('Effectiveness (% reduction in AI output)', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.legend()
    
    # Add value labels to the bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_effectiveness.png', dpi=300)
    
    # Create heatmap for prompt types
    plt.figure(figsize=(12, 8))
    sns.heatmap(prompt_summary, annot=True, fmt='.1f', cmap='RdYlGn', center=0,
               linewidths=0.5, cbar_kws={'label': 'Effectiveness (%)'})
    
    plt.title('Attack Effectiveness by Prompt Type', fontsize=16)
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_by_prompt_type.png', dpi=300)
    
    # Print summary report
    print("\n" + "="*80)
    print("TOP ATTACKS EFFECTIVENESS ANALYSIS")
    print("="*80)
    
    print("\nATTACKS RANKED BY EFFECTIVENESS:")
    print("-"*50)
    for _, row in attack_summary.iterrows():
        print(f"{row['attack_name']:30s}: {row['mean']:6.2f}% effective (±{row['std']:5.2f}, n={row['count']})")
    
    print("\nEFFECTIVENESS BY PROMPT TYPE:")
    print("-"*50)
    print(prompt_summary)
    
    print("\nOutput files:")
    print(f"- {output_prefix}_detailed_results.csv (detailed data table)")
    print(f"- {output_prefix}_effectiveness.png (effectiveness chart)")
    print(f"- {output_prefix}_by_prompt_type.png (effectiveness heatmap by prompt type)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze top attacks experiment results')
    parser.add_argument('--log-file', type=str, default='top_attacks_results.jsonl',
                        help='Path to the experiment log file')
    parser.add_argument('--output-prefix', type=str, default='top_attacks',
                        help='Prefix for output files')
    
    args = parser.parse_args()
    analyze_top_attacks_results(args.log_file, args.output_prefix)
