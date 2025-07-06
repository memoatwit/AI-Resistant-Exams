#!/usr/bin/env python3
# analyze_overnight_results.py
"""
Quick analysis script for overnight experiment results.
This processes the results from the enhanced attack types and provides insights
on which combinations were most effective against different AI models.
"""

import json
import os
from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

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
    
    # Containers for the analysis
    attack_results = defaultdict(lambda: defaultdict(list))
    attack_types = defaultdict(lambda: defaultdict(list))
    model_results = defaultdict(lambda: defaultdict(list))
    
    # Process the log file
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
    
    for entry in entries:
        if entry.get('status') != 'success' or 'test_run_output' not in entry:
            continue
            
        attack_name = entry['attack_details']['name']
        attack_type = entry['attack_details']['type']
        model = entry.get('model', 'unknown')
        prompt_type = entry.get('prompt_type', 'unknown')
        
        try:
            if 'success_rate' in entry['test_run_output']:
                success_rate = float(entry['test_run_output']['success_rate'])
                
                # Lower success rates mean the attack was more effective at preventing AI reading
                effectiveness_score = 100 - success_rate
                
                # Store by attack name
                attack_results[attack_name][model].append({
                    'prompt_type': prompt_type,
                    'success_rate': success_rate,
                    'effectiveness': effectiveness_score
                })
                
                # Store by attack type
                attack_types[attack_type][model].append({
                    'prompt_type': prompt_type,
                    'success_rate': success_rate,
                    'effectiveness': effectiveness_score,
                    'attack_name': attack_name
                })
                
                # Store by model
                model_results[model][attack_type].append({
                    'prompt_type': prompt_type,
                    'success_rate': success_rate,
                    'effectiveness': effectiveness_score,
                    'attack_name': attack_name
                })
        except (KeyError, TypeError, ValueError) as e:
            print(f"Warning: Error processing entry for {attack_name}: {e}")
    
    # Calculate average effectiveness by attack type
    type_effectiveness = {}
    for attack_type, models in attack_types.items():
        type_effectiveness[attack_type] = {
            'avg_effectiveness': np.mean([result['effectiveness'] 
                                         for model_results in models.values() 
                                         for result in model_results]),
            'model_breakdown': {model: np.mean([r['effectiveness'] for r in results]) 
                               for model, results in models.items()}
        }
    
    # Sort attack types by effectiveness
    sorted_types = sorted(type_effectiveness.items(), 
                         key=lambda x: x[1]['avg_effectiveness'], 
                         reverse=True)
    
    # Generate comprehensive report
    print("\n" + "="*80)
    print("ATTACK EFFECTIVENESS ANALYSIS")
    print("="*80)
    
    print("\nTOP ATTACK TYPES BY EFFECTIVENESS:")
    print("-"*40)
    for attack_type, data in sorted_types:
        print(f"{attack_type:20s}: {data['avg_effectiveness']:.2f}% effective")
        for model, effectiveness in data['model_breakdown'].items():
            print(f"  - Against {model:12s}: {effectiveness:.2f}% effective")
    
    # Find the most effective individual attacks
    all_attacks = []
    for attack_name, models in attack_results.items():
        for model, results in models.items():
            avg_effectiveness = np.mean([r['effectiveness'] for r in results])
            all_attacks.append({
                'name': attack_name,
                'model': model,
                'effectiveness': avg_effectiveness,
                'attack_type': next((a['type'] for a in entries if a['attack_details']['name'] == attack_name), 'unknown')
            })
    
    sorted_attacks = sorted(all_attacks, key=lambda x: x['effectiveness'], reverse=True)
    
    print("\nTOP 10 MOST EFFECTIVE INDIVIDUAL ATTACKS:")
    print("-"*40)
    for i, attack in enumerate(sorted_attacks[:10]):
        print(f"{i+1}. {attack['name']} (type: {attack['attack_type']}):")
        print(f"   - {attack['effectiveness']:.2f}% effective against {attack['model']}")
    
    # Create a visual representation
    create_effectiveness_chart(type_effectiveness, 'attack_effectiveness_by_type.png')
    create_model_vulnerability_chart(model_results, 'model_vulnerability.png')
    
    print("\nCharts generated:")
    print("- attack_effectiveness_by_type.png")
    print("- model_vulnerability.png")

def create_effectiveness_chart(type_effectiveness, output_file):
    """Create a bar chart showing attack type effectiveness"""
    plt.figure(figsize=(12, 8))
    
    # Check if we have data
    if not type_effectiveness:
        print("No data available to generate effectiveness chart.")
        plt.text(0.5, 0.5, "No attack effectiveness data available", 
                horizontalalignment='center', fontsize=16)
        plt.axis('off')
        plt.savefig(output_file, dpi=300)
        return
        
    # Sort by overall effectiveness
    sorted_types = sorted(type_effectiveness.items(), 
                         key=lambda x: x[1]['avg_effectiveness'], 
                         reverse=True)
    
    attack_types = [t[0] for t in sorted_types]
    effectiveness = [t[1]['avg_effectiveness'] for t in sorted_types]
    
    # Handle long type names
    if attack_types and max(len(str(t)) for t in attack_types) > 12:
        plt.figure(figsize=(14, 8))  # Wider figure for long names
    
    bars = plt.bar(attack_types, effectiveness, color='steelblue')
    plt.axhline(y=50, color='r', linestyle='--', alpha=0.7, 
                label='50% Effectiveness Threshold')
    
    plt.title('Attack Type Effectiveness Against AI Models', fontsize=16)
    plt.xlabel('Attack Type', fontsize=14)
    plt.ylabel('Effectiveness (% AI Failure Rate)', fontsize=14)
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

def create_model_vulnerability_chart(model_results, output_file):
    """Create a chart showing model vulnerability to different attack types"""
    plt.figure(figsize=(12, 8))
    
    # Calculate average vulnerability by model and attack type
    data = {}
    for model, attack_types in model_results.items():
        data[model] = {}
        for attack_type, results in attack_types.items():
            data[model][attack_type] = np.mean([r['effectiveness'] for r in results])
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(data)
    
    # Check if we have data to plot
    if df.empty:
        print("No data available to generate model vulnerability chart.")
        # Create a simple message chart instead
        plt.text(0.5, 0.5, "No model comparison data available", 
                horizontalalignment='center', fontsize=16)
        plt.axis('off')
        plt.savefig(output_file, dpi=300)
        return
    
    # Sort attack types by average effectiveness
    attack_types = df.index.tolist()
    models = df.columns.tolist()
    
    # Create grouped bar chart
    x = np.arange(len(attack_types))
    
    # Handle case where there's only one model
    width = 0.8 / max(len(models), 1)
    
    for i, model in enumerate(models):
        offset = width * i - width * len(models) / 2 + width / 2 if len(models) > 1 else 0
        plt.bar(x + offset, df[model], width, label=model)
    
    plt.title('Model Vulnerability by Attack Type', fontsize=16)
    plt.xlabel('Attack Type', fontsize=14)
    plt.ylabel('Vulnerability (% Effectiveness)', fontsize=14)
    plt.xticks(x, attack_types, rotation=45, ha='right')
    plt.legend(title='Model')
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze overnight experiment results')
    parser.add_argument('--log-file', type=str, default='full_experiment_overnight_v3.jsonl',
                        help='Path to the experiment log file')
    args = parser.parse_args()
    
    analyze_experiment_results(args.log_file)
