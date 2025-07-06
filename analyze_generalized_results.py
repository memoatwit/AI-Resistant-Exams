#!/usr/bin/env python3
# analyze_generalized_results.py
#
# This script analyzes the results of the generalized experiment
# and generates a detailed report on attack effectiveness

import os
import json
import re
import glob
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# Constants
RESULT_FILES_PATTERN = "results_gen_variant_*.txt"
LOG_FILE = "generalized_experiment_log.jsonl"

class ResultAnalyzer:
    """Analyzes AI-resistant exam experiment results"""
    
    def __init__(self, results_dir="."):
        self.results_dir = results_dir
        self.log_data = self.load_log_data()
        self.result_files = self.find_result_files()
        self.attacks_data = {}
        self.prompt_types = set()
        self.load_all_results()
    
    def load_log_data(self):
        """Load the experiment log data"""
        log_path = os.path.join(self.results_dir, LOG_FILE)
        if not os.path.exists(log_path):
            print(f"Warning: Log file {log_path} not found")
            return {}
        
        log_entries = []
        with open(log_path, "r") as f:
            for line in f:
                try:
                    log_entries.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Warning: Invalid JSON entry in log file")
        
        return log_entries
    
    def find_result_files(self):
        """Find all result files in the directory"""
        pattern = os.path.join(self.results_dir, RESULT_FILES_PATTERN)
        return glob.glob(pattern)
    
    def load_all_results(self):
        """Load data from all result files"""
        for file_path in self.result_files:
            self.load_result_file(file_path)
    
    def load_result_file(self, file_path):
        """Load data from a single result file"""
        filename = os.path.basename(file_path)
        # Extract attack name and prompt type from the filename
        # Format: results_gen_variant_ATTACKNAME_PROMPTTYPE.txt
        match = re.match(r'results_gen_variant_(.+?)_([a-z]+)\.txt$', filename)
        if not match:
            print(f"Warning: Could not parse filename {filename}")
            return
        
        attack_name, prompt_type = match.groups()
        self.prompt_types.add(prompt_type)
        
        # Load the content
        with open(file_path, "r") as f:
            content = f.read()
        
        # Store the result
        if attack_name not in self.attacks_data:
            self.attacks_data[attack_name] = {}
        
        self.attacks_data[attack_name][prompt_type] = content
    
    def extract_model_response(self, content):
        """Extract the model's response from the result content"""
        # Find the response after the separator line
        parts = content.split("IMAGE ANALYSIS RESULTS:")
        if len(parts) < 2:
            return ""
        return parts[1].strip()
    
    def score_effectiveness(self, response, prompt_type):
        """
        Score the effectiveness of an attack based on the model's response
        Returns a score from 0-10 (higher = more effective attack)
        """
        # Default to a medium score
        score = 5
        
        # If response is very short, it's likely effective
        if len(response) < 50:
            return 9
        
        # Look for specific patterns indicating the attack worked
        lower_response = response.lower()
        
        # Attack effectiveness indicators
        if "error" in lower_response or "cannot" in lower_response:
            score += 2
        
        if "unable to" in lower_response or "difficult to" in lower_response:
            score += 2
        
        if "unclear" in lower_response or "hard to see" in lower_response:
            score += 1
        
        # Different prompt types have different indicators
        if prompt_type == "transcription":
            # For transcription, check for completely missing sections
            if len(response) < 200:
                score += 2
            
            # Check for acknowledgment of missing content
            if "missing" in lower_response or "incomplete" in lower_response:
                score += 1
        
        elif prompt_type == "solving":
            # For solving, check if the model failed to solve
            if "cannot solve" in lower_response or "unable to solve" in lower_response:
                score += 3
            
            # Check if the model misunderstood the problem
            if "misunderstood" in lower_response or "misinterpreted" in lower_response:
                score += 2
        
        elif prompt_type == "explanation":
            # For explanation, check if the model failed to explain
            if "cannot explain" in lower_response or "unable to explain" in lower_response:
                score += 3
            
            # Check for confusion
            if "confused" in lower_response or "ambiguous" in lower_response:
                score += 2
        
        # Cap the score at 10
        return min(10, score)
    
    def analyze_results(self):
        """Analyze the results and generate metrics"""
        analysis = {
            "attack_scores": {},
            "prompt_type_scores": defaultdict(list),
            "total_responses": 0,
            "successful_attacks": 0,
        }
        
        for attack_name, prompts_data in self.attacks_data.items():
            attack_scores = []
            
            for prompt_type, content in prompts_data.items():
                response = self.extract_model_response(content)
                score = self.score_effectiveness(response, prompt_type)
                
                attack_scores.append(score)
                analysis["prompt_type_scores"][prompt_type].append(score)
                
                analysis["total_responses"] += 1
                if score > 7:  # Consider score > 7 as a successful attack
                    analysis["successful_attacks"] += 1
            
            # Calculate average score for this attack
            if attack_scores:
                analysis["attack_scores"][attack_name] = sum(attack_scores) / len(attack_scores)
        
        # Calculate average scores by prompt type
        for prompt_type, scores in analysis["prompt_type_scores"].items():
            analysis["prompt_type_scores"][prompt_type] = sum(scores) / len(scores)
        
        # Find the most effective attack
        if analysis["attack_scores"]:
            analysis["best_attack"] = max(analysis["attack_scores"].items(), key=lambda x: x[1])
        else:
            analysis["best_attack"] = ("none", 0)
        
        return analysis
    
    def generate_effectiveness_chart(self, analysis):
        """Generate a chart showing attack effectiveness"""
        attack_names = list(analysis["attack_scores"].keys())
        scores = list(analysis["attack_scores"].values())
        
        # Sort by effectiveness
        sorted_indices = np.argsort(scores)
        attack_names = [attack_names[i] for i in sorted_indices]
        scores = [scores[i] for i in sorted_indices]
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(attack_names, scores, color="skyblue")
        plt.xlabel("Effectiveness Score (0-10)")
        plt.ylabel("Attack Type")
        plt.title("Attack Effectiveness Rankings")
        plt.xlim(0, 10)
        
        # Add value labels
        for bar, score in zip(bars, scores):
            plt.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2, 
                    f"{score:.1f}", va='center')
        
        plt.tight_layout()
        plt.savefig("attack_effectiveness.png")
        plt.close()
    
    def generate_report(self):
        """Generate a comprehensive report on the results"""
        analysis = self.analyze_results()
        
        # Create the report
        report_lines = []
        report_lines.append("# Generalized Attack Experiment Results")
        report_lines.append("\n## Overview")
        report_lines.append(f"- Total PDFs tested: {len(self.attacks_data)}")
        report_lines.append(f"- Total responses analyzed: {analysis['total_responses']}")
        report_lines.append(f"- Successful attacks (score > 7): {analysis['successful_attacks']}")
        report_lines.append(f"- Success rate: {100 * analysis['successful_attacks'] / max(1, analysis['total_responses']):.1f}%")
        
        # Add attack rankings
        report_lines.append("\n## Attack Effectiveness Rankings")
        sorted_attacks = sorted(analysis["attack_scores"].items(), key=lambda x: x[1], reverse=True)
        
        report_lines.append("| Rank | Attack | Effectiveness Score |")
        report_lines.append("|------|--------|---------------------|")
        
        for i, (attack, score) in enumerate(sorted_attacks):
            report_lines.append(f"| {i+1} | {attack} | {score:.1f} |")
        
        # Most effective attack
        best_attack, best_score = analysis["best_attack"]
        report_lines.append(f"\n## Most Effective Attack: **{best_attack}** (Score: {best_score:.1f})")
        
        # Effectiveness by prompt type
        report_lines.append("\n## Effectiveness by Prompt Type")
        report_lines.append("| Prompt Type | Average Score |")
        report_lines.append("|-------------|---------------|")
        
        for prompt_type, score in analysis["prompt_type_scores"].items():
            report_lines.append(f"| {prompt_type} | {score:.1f} |")
        
        # Generate chart if matplotlib is available
        try:
            self.generate_effectiveness_chart(analysis)
            report_lines.append("\n## Attack Effectiveness Chart")
            report_lines.append("![Attack Effectiveness](attack_effectiveness.png)")
        except Exception as e:
            print(f"Warning: Could not generate chart: {e}")
        
        # Detailed attack analysis
        report_lines.append("\n## Detailed Attack Analysis")
        for attack_name in sorted(self.attacks_data.keys()):
            report_lines.append(f"\n### {attack_name}")
            
            # Find attack description from log data
            attack_description = "N/A"
            for entry in self.log_data:
                if entry.get("attack_details", {}).get("name") == attack_name.replace("level2", ""):
                    attack_type = entry.get("attack_details", {}).get("type", "unknown")
                    attack_description = f"Type: {attack_type}"
                    break
            
            report_lines.append(f"Description: {attack_description}")
            report_lines.append(f"Overall Score: {analysis['attack_scores'].get(attack_name, 'N/A'):.1f}")
            
            # Add prompt-specific scores
            for prompt_type in sorted(self.prompt_types):
                if prompt_type in self.attacks_data[attack_name]:
                    response = self.extract_model_response(self.attacks_data[attack_name][prompt_type])
                    score = self.score_effectiveness(response, prompt_type)
                    report_lines.append(f"- {prompt_type}: {score:.1f}")
        
        # Write the report to a file
        report_path = os.path.join(self.results_dir, "generalized_attack_results.md")
        with open(report_path, "w") as f:
            f.write("\n".join(report_lines))
        
        print(f"Report generated at {report_path}")
        return report_path

def main():
    analyzer = ResultAnalyzer()
    analyzer.generate_report()

if __name__ == "__main__":
    main()
