#!/usr/bin/env python3
"""
Detailed analysis script for overnight experiment results.
This script analyzes the effectiveness of different attack types against AI models.
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

def analyze_experiment_results(log_file):
    """
    Analyze the results of the overnight experiment.
    
    Args:
        log_file (str): Path to the experiment log file
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
    
    # Count successful tests vs failures
    success_count = sum(1 for e in entries if e.get('status') == 'success')
    failed_count = len(entries) - success_count
    print(f"Successful tests: {success_count}, Failed tests: {failed_count}")
    
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
    
    # Get average effectiveness by attack type
    attack_type_summary = df.groupby('attack_type')['effectiveness'].agg(['mean', 'std', 'count']).reset_index()
    attack_type_summary = attack_type_summary.sort_values(by='mean', ascending=False)
    
    # Get average effectiveness by specific attack
    attack_name_summary = df.groupby('attack_name')['effectiveness'].agg(['mean', 'std', 'count']).reset_index()
    attack_name_summary = attack_name_summary.sort_values(by='mean', ascending=False)
    
    # Get effectiveness by model
    model_summary = df.groupby(['attack_type', 'model'])['effectiveness'].mean().reset_index()
    model_summary = model_summary.pivot(index='attack_type', columns='model', values='effectiveness')
    
    # Get effectiveness by prompt type
    prompt_summary = df.groupby(['attack_type', 'prompt_type'])['effectiveness'].mean().reset_index()
    prompt_summary = prompt_summary.pivot(index='attack_type', columns='prompt_type', values='effectiveness')
    
    # Print summary report
    print("\n" + "="*80)
    print("ATTACK EFFECTIVENESS ANALYSIS")
    print("="*80)
    
    print("\nTOP ATTACK TYPES BY EFFECTIVENESS:")
    print("-"*50)
    for _, row in attack_type_summary.iterrows():
        print(f"{row['attack_type']:20s}: {row['mean']:6.2f}% effective (±{row['std']:5.2f}, n={row['count']})")
    
    print("\nEFFECTIVENESS BY MODEL:")
    print("-"*50)
    print(model_summary)
    
    print("\nEFFECTIVENESS BY PROMPT TYPE:")
    print("-"*50)
    print(prompt_summary)
    
    print("\nTOP 15 MOST EFFECTIVE INDIVIDUAL ATTACKS:")
    print("-"*50)
    for i, (_, row) in enumerate(attack_name_summary.head(15).iterrows()):
        attack_type = df[df['attack_name'] == row['attack_name']]['attack_type'].iloc[0]
        print(f"{i+1}. {row['attack_name']} (type: {attack_type}):")
        print(f"   - {row['mean']:6.2f}% effective (±{row['std']:5.2f}, n={row['count']})")
        
        # Get per-model breakdown
        attack_models = df[df['attack_name'] == row['attack_name']].groupby('model')['effectiveness'].mean()
        for model_name, eff in attack_models.items():
            print(f"   - Against {model_name}: {eff:6.2f}% effective")
    
    # Generate visualizations
    create_attack_type_chart(attack_type_summary, 'attack_type_effectiveness.png')
    create_top_attacks_chart(attack_name_summary.head(15), 'top_attacks_effectiveness.png')
    create_heatmap(model_summary, 'model_effectiveness_heatmap.png')
    create_heatmap(prompt_summary, 'prompt_effectiveness_heatmap.png')
    
    # Do more detailed analysis on top attacks
    if not df.empty:
        top_attacks = attack_name_summary.head(5)['attack_name'].tolist()
        create_model_comparison(df, top_attacks, 'top_attacks_model_comparison.png')
    
    print("\nCharts generated:")
    print("- attack_type_effectiveness.png")
    print("- top_attacks_effectiveness.png")
    print("- model_effectiveness_heatmap.png")
    print("- prompt_effectiveness_heatmap.png")
    print("- top_attacks_model_comparison.png")
    
    # Save detailed results to CSV for further analysis
    df.to_csv('attack_detailed_results.csv', index=False)
    print("- attack_detailed_results.csv (detailed data table)")

def create_attack_type_chart(df, output_file):
    """Create a bar chart showing attack type effectiveness"""
    plt.figure(figsize=(14, 8))
    
    # Plot bars
    bars = plt.bar(df['attack_type'], df['mean'], 
                   yerr=df['std'], capsize=5,
                   color=sns.color_palette('viridis', len(df)))
    
    # Add reference line at 0%
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.7, 
                label='Baseline (0% = no effect)')
    
    # Add a line at 25% as a "good effectiveness" threshold
    plt.axhline(y=25, color='g', linestyle='--', alpha=0.7,
               label='Good effectiveness threshold (25%)')
    
    plt.title('Attack Type Effectiveness Against AI Models', fontsize=16)
    plt.xlabel('Attack Type', fontsize=14)
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
    plt.savefig(output_file, dpi=300)

def create_top_attacks_chart(df, output_file):
    """Create a horizontal bar chart showing top attacks"""
    plt.figure(figsize=(14, 10))
    
    # Plot horizontal bars
    bars = plt.barh(df['attack_name'], df['mean'], xerr=df['std'], capsize=5,
                   color=sns.color_palette('viridis', len(df)))
    
    # Add reference lines
    plt.axvline(x=0, color='r', linestyle='-', alpha=0.7, 
                label='Baseline (0% = no effect)')
    plt.axvline(x=25, color='g', linestyle='--', alpha=0.7,
               label='Good effectiveness threshold (25%)')
    
    plt.title('Most Effective Individual Attacks', fontsize=16)
    plt.xlabel('Effectiveness (% reduction in AI output)', fontsize=14)
    plt.ylabel('Attack Name', fontsize=14)
    plt.grid(axis='x', alpha=0.3)
    plt.legend()
    
    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{width:.1f}%', ha='left', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)

def create_heatmap(df, output_file):
    """Create a heatmap visualization"""
    plt.figure(figsize=(12, 10))
    
    # Create heatmap
    sns.heatmap(df, annot=True, fmt='.1f', cmap='RdYlGn', center=0,
               linewidths=0.5, cbar_kws={'label': 'Effectiveness (%)'})
    
    plt.title('Attack Effectiveness Heatmap', fontsize=16)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)

def create_model_comparison(df, top_attacks, output_file):
    """Create a grouped bar chart comparing models for top attacks"""
    plt.figure(figsize=(14, 8))
    
    # Filter for top attacks only
    df_top = df[df['attack_name'].isin(top_attacks)]
    
    # Pivot data for plotting
    plot_data = df_top.pivot_table(index='attack_name', columns='model', 
                                   values='effectiveness', aggfunc='mean')
    
    # Create grouped bar chart
    ax = plot_data.plot(kind='bar', width=0.8, figsize=(14, 8),
                       colormap='viridis')
    
    plt.title('Top Attacks: Effectiveness Comparison by Model', fontsize=16)
    plt.xlabel('Attack Name', fontsize=14)
    plt.ylabel('Effectiveness (%)', fontsize=14)
    plt.grid(axis='y', alpha=0.3)
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.5)
    plt.legend(title='Model')
    
    # Add value labels
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f%%', padding=3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze overnight experiment results')
    parser.add_argument('--log-file', type=str, default='full_experiment_overnight_v3.jsonl',
                        help='Path to the experiment log file')
    args = parser.parse_args()
    
    analyze_experiment_results(args.log_file)
