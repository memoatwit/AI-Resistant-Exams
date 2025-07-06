#!/usr/bin/env python3
"""
Quick analysis script for overnight experiment results with simplified metrics.
"""

import json
import os
from collections import defaultdict
import matplotlib.pyplot as plt
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
    attack_results = defaultdict(list)
    attack_types = defaultdict(list)
    model_results = defaultdict(lambda: defaultdict(list))
    prompt_results = defaultdict(lambda: defaultdict(list))
    
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
        if entry.get('status') != 'success':
            continue
            
        attack_name = entry['attack_details']['name']
        attack_type = entry['attack_details']['type']
        model = entry.get('model', 'unknown')
        prompt_type = entry.get('prompt_type', 'unknown')
        
        # Extract text length as our main success measure
        if 'test_run_output' in entry and 'analysis' in entry['test_run_output']:
            output_length = entry['test_run_output']['analysis'].get('image_output_length', 0)
            is_failed = entry['test_run_output']['analysis'].get('image_test_failed', False)
            
            # Calculate effectiveness score
            # Higher scores = more effective at blocking AI (shorter outputs or failed tests)
            baseline_length = 600  # approximate full text length
            effectiveness = 100 - (output_length / baseline_length * 100)
            if is_failed:
                effectiveness = 100  # Failed tests are 100% effective
                
            # Store results by attack name
            attack_results[attack_name].append({
                'model': model,
                'prompt_type': prompt_type,
                'output_length': output_length,
                'effectiveness': effectiveness,
                'is_failed': is_failed
            })
            
            # Store results by attack type
            attack_types[attack_type].append({
                'attack_name': attack_name,
                'model': model,
                'prompt_type': prompt_type,
                'output_length': output_length,
                'effectiveness': effectiveness,
                'is_failed': is_failed
            })
            
            # Store results by model and attack type
            model_results[model][attack_type].append({
                'output_length': output_length,
                'effectiveness': effectiveness,
                'is_failed': is_failed
            })
            
            # Store results by prompt type
            prompt_results[prompt_type][attack_type].append({
                'output_length': output_length,
                'effectiveness': effectiveness,
                'is_failed': is_failed
            })
    
    # Calculate average effectiveness by attack type
    type_effectiveness = {}
    for attack_type, results in attack_types.items():
        type_effectiveness[attack_type] = {
            'avg_effectiveness': np.mean([r['effectiveness'] for r in results]),
            'model_breakdown': {}
        }
        
        # Get per-model breakdown
        model_data = defaultdict(list)
        for r in results:
            model_data[r['model']].append(r['effectiveness'])
            
        for model, values in model_data.items():
            type_effectiveness[attack_type]['model_breakdown'][model] = np.mean(values)
    
    # Calculate average effectiveness by individual attack
    attack_effectiveness = {}
    for attack_name, results in attack_results.items():
        avg_effectiveness = np.mean([r['effectiveness'] for r in results])
        attack_effectiveness[attack_name] = avg_effectiveness
    
    # Sort attack types by effectiveness
    sorted_types = sorted(type_effectiveness.items(), 
                         key=lambda x: x[1]['avg_effectiveness'], 
                         reverse=True)
    
    # Sort individual attacks by effectiveness
    sorted_attacks = sorted(attack_effectiveness.items(),
                           key=lambda x: x[1],
                           reverse=True)
    
    # Generate comprehensive report
    print("\n" + "="*80)
    print("ATTACK EFFECTIVENESS ANALYSIS")
    print("="*80)
    
    print("\nTOP ATTACK TYPES BY EFFECTIVENESS:")
    print("-"*50)
    for attack_type, data in sorted_types:
        print(f"{attack_type:20s}: {data['avg_effectiveness']:.2f}% effective")
        for model, effectiveness in data['model_breakdown'].items():
            print(f"  - Against {model:12s}: {effectiveness:.2f}% effective")
    
    print("\nTOP 15 MOST EFFECTIVE INDIVIDUAL ATTACKS:")
    print("-"*50)
    for i, (attack_name, effectiveness) in enumerate(sorted_attacks[:15]):
        attack_type = next((entry['attack_details']['type'] for entry in entries 
                           if entry['attack_details']['name'] == attack_name), "unknown")
        print(f"{i+1}. {attack_name} (type: {attack_type}):")
        print(f"   - {effectiveness:.2f}% effective overall")
        
        # Show per-model effectiveness
        model_data = defaultdict(list)
        for r in attack_results[attack_name]:
            model_data[r['model']].append(r['effectiveness'])
            
        for model, values in model_data.items():
            model_avg = np.mean(values)
            print(f"   - Against {model}: {model_avg:.2f}% effective")
    
    # Create a visual representation
    create_effectiveness_chart(type_effectiveness, 'attack_effectiveness_by_type.png')
    create_attack_ranking_chart(sorted_attacks[:15], 'top_attacks_ranking.png')
    create_prompt_comparison(prompt_results, 'prompt_comparison.png')
    
    print("\nCharts generated:")
    print("- attack_effectiveness_by_type.png")
    print("- top_attacks_ranking.png")
    print("- prompt_comparison.png")

def create_effectiveness_chart(type_effectiveness, output_file):
    """Create a bar chart showing attack type effectiveness"""
    plt.figure(figsize=(14, 8))
    
    # Sort by overall effectiveness
    sorted_types = sorted(type_effectiveness.items(), 
                         key=lambda x: x[1]['avg_effectiveness'], 
                         reverse=True)
    
    attack_types = [t[0] for t in sorted_types]
    effectiveness = [t[1]['avg_effectiveness'] for t in sorted_types]
    
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

def create_attack_ranking_chart(sorted_attacks, output_file):
    """Create a horizontal bar chart showing top attacks"""
    plt.figure(figsize=(12, 10))
    
    attack_names = [a[0] for a in sorted_attacks]
    effectiveness = [a[1] for a in sorted_attacks]
    
    # Create horizontal bar chart
    y_pos = np.arange(len(attack_names))
    bars = plt.barh(y_pos, effectiveness, color='lightseagreen')
    
    plt.axvline(x=50, color='r', linestyle='--', alpha=0.7,
               label='50% Effectiveness Threshold')
    
    plt.yticks(y_pos, attack_names)
    plt.title('Most Effective Individual Attacks', fontsize=16)
    plt.xlabel('Effectiveness (% AI Failure Rate)', fontsize=14)
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

def create_prompt_comparison(prompt_results, output_file):
    """Create a chart comparing effectiveness across prompt types"""
    plt.figure(figsize=(14, 8))
    
    # Calculate average effectiveness by prompt type and attack type
    data = {}
    for prompt, attack_types in prompt_results.items():
        data[prompt] = {}
        for attack_type, results in attack_types.items():
            data[prompt][attack_type] = np.mean([r['effectiveness'] for r in results])
    
    # Get list of attack types that appear in all prompt types
    common_attacks = set.intersection(*[set(d.keys()) for d in data.values()])
    if not common_attacks:
        print("No common attack types across all prompt types")
        # Find attack types that appear in at least 2 prompt types
        all_attacks = set.union(*[set(d.keys()) for d in data.values()])
        attack_counts = {attack: sum(1 for d in data.values() if attack in d) 
                        for attack in all_attacks}
        common_attacks = [attack for attack, count in attack_counts.items() 
                        if count >= 2]
    
    if not common_attacks:
        plt.text(0.5, 0.5, "Insufficient data for prompt comparison", 
                horizontalalignment='center', fontsize=16)
        plt.axis('off')
        plt.savefig(output_file, dpi=300)
        return
    
    # Set up grouped bar chart
    x = np.arange(len(common_attacks))
    width = 0.8 / len(data)
    
    # Create a bar for each prompt type
    for i, (prompt, attack_data) in enumerate(data.items()):
        values = [attack_data.get(attack, 0) for attack in common_attacks]
        offset = width * i - width * len(data) / 2 + width / 2
        plt.bar(x + offset, values, width, label=prompt)
    
    plt.title('Attack Effectiveness by Prompt Type', fontsize=16)
    plt.xlabel('Attack Type', fontsize=14)
    plt.ylabel('Effectiveness (%)', fontsize=14)
    plt.xticks(x, common_attacks, rotation=45, ha='right')
    plt.legend(title='Prompt Type')
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
