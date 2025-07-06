#!/usr/bin/env python3
# analyze_generalized_results_v2.py
#
# Enhanced version with better analysis of AI responses

import os
import json
import re
import glob
from collections import defaultdict

# Constants
RESULT_FILES_PATTERN = "results_gen_variant_*.txt"
LOG_FILE = "generalized_experiment_log.jsonl"

def extract_response_text(content):
    """Extract the model's response from result file content"""
    if "IMAGE ANALYSIS RESULTS:" in content:
        parts = content.split("IMAGE ANALYSIS RESULTS:")
        if len(parts) >= 2:
            return parts[1].strip()
    return content.strip()

def analyze_response_issues(response, attack_type="unknown", prompt_type="unknown"):
    """
    Analyze response text for signs of attack success.
    Returns a dict of identified issues.
    """
    issues = {
        "missing_content": False,
        "confusion": False,
        "incompleteness": False,
        "errors": False,
        "acknowledgment": False,
        "misrepresentation": False
    }
    
    # Convert to lowercase for case-insensitive matching
    text = response.lower()
    
    # Check for missing content indicators
    if any(phrase in text for phrase in [
            "unable to read", "can't see", "not visible",
            "unclear", "difficult to see", "hard to make out",
            "not legible", "missing", "incomplete"]):
        issues["missing_content"] = True
    
    # Check for signs of confusion
    if any(phrase in text for phrase in [
            "confus", "ambiguous", "unclear what", 
            "not sure what", "hard to determine", 
            "difficult to interpret"]):
        issues["confusion"] = True
        
    # Check for incompleteness
    if any(phrase in text for phrase in [
            "partial", "incomplete", "missing parts",
            "can only see", "unable to access", 
            "cannot view", "limited view"]):
        issues["incompleteness"] = True
    
    # Check for errors
    if any(phrase in text for phrase in [
            "error", "unable to process", "failed to",
            "cannot parse", "issue with"]):
        issues["errors"] = True
    
    # Check for explicit acknowledgment of difficulty
    if any(phrase in text for phrase in [
            "i apologize", "i cannot", "i'm unable to",
            "i can't", "i'm having trouble", "i'm struggling"]):
        issues["acknowledgment"] = True
        
    # Check for misrepresentation of content
    # This requires domain-specific knowledge of expected content
    # For our math problems, we'll look for certain keywords
    if prompt_type == "solving" and not any(phrase in text for phrase in [
            "partial derivative", "derivative", "hill", "slope",
            "graph", "function", "hamilton"]):
        issues["misrepresentation"] = True
    
    return issues

def score_response(response, issues, prompt_type):
    """Calculate an effectiveness score based on response issues"""
    base_score = 4.0  # Start with a neutral score
    
    # Add points for each issue found
    if issues["missing_content"]:
        base_score += 1.5
    if issues["confusion"]:
        base_score += 1.5
    if issues["incompleteness"]:
        base_score += 1.0
    if issues["errors"]:
        base_score += 2.0
    if issues["acknowledgment"]:
        base_score += 2.0
    if issues["misrepresentation"]:
        base_score += 1.5
    
    # Adjust based on response length (shorter responses often indicate attack success)
    if len(response) < 100:
        base_score += 2.0
    elif len(response) < 250:
        base_score += 1.0
    
    # Adjust for prompt type
    if prompt_type == "solving" and "unable to solve" in response.lower():
        base_score += 1.5
    if prompt_type == "explanation" and "unable to explain" in response.lower():
        base_score += 1.5
    
    # Cap the score
    return min(10.0, base_score)

def find_attack_in_log(attack_name, log_data):
    """Find attack description in log data"""
    for entry in log_data:
        if "attack_details" in entry:
            details = entry["attack_details"]
            if details.get("name") == attack_name.replace("_level2", ""):
                return {
                    "type": details.get("type", "unknown"),
                    "params": details.get("params", {})
                }
    return {"type": "unknown", "params": {}}

def generate_report():
    """Generate a comprehensive report on the results"""
    # Find all result files
    result_files = glob.glob(RESULT_FILES_PATTERN)
    if not result_files:
        print("No result files found!")
        return

    # Load log data if available
    log_data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            for line in f:
                try:
                    log_data.append(json.loads(line))
                except json.JSONDecodeError:
                    print("Warning: Invalid JSON entry in log file")
    
    # Organize results by attack and prompt type
    results = {}
    prompt_types = set()
    
    for file_path in result_files:
        filename = os.path.basename(file_path)
        # Extract attack name and prompt type from the filename
        match = re.match(r'results_gen_variant_(.+?)_([a-z]+)\.txt$', filename)
        if not match:
            print(f"Warning: Could not parse filename {filename}")
            continue
        
        attack_name, prompt_type = match.groups()
        prompt_types.add(prompt_type)
        
        # Load the content
        with open(file_path, "r") as f:
            content = f.read()
            response = extract_response_text(content)
            
            # Find attack details
            attack_details = find_attack_in_log(attack_name, log_data)
            
            # Analyze the response
            issues = analyze_response_issues(response, attack_details["type"], prompt_type)
            score = score_response(response, issues, prompt_type)
            
            # Store the result
            if attack_name not in results:
                results[attack_name] = {
                    "details": attack_details,
                    "prompt_results": {}
                }
            
            results[attack_name]["prompt_results"][prompt_type] = {
                "response": response,
                "issues": issues,
                "score": score
            }
    
    # Calculate aggregate scores
    attack_scores = {}
    prompt_scores = defaultdict(list)
    
    for attack_name, attack_data in results.items():
        scores = [data["score"] for data in attack_data["prompt_results"].values()]
        avg_score = sum(scores) / len(scores) if scores else 0
        attack_scores[attack_name] = avg_score
        
        for prompt, data in attack_data["prompt_results"].items():
            prompt_scores[prompt].append(data["score"])
    
    # Find most and least effective attacks
    sorted_attacks = sorted(attack_scores.items(), key=lambda x: x[1], reverse=True)
    most_effective = sorted_attacks[0] if sorted_attacks else ("none", 0)
    least_effective = sorted_attacks[-1] if len(sorted_attacks) > 1 else ("none", 0)
    
    # Calculate prompt type averages
    prompt_averages = {p: sum(s)/len(s) if s else 0 for p, s in prompt_scores.items()}
    
    # Generate report
    report_lines = []
    report_lines.append("# Generalized Attack Experiment Results")
    report_lines.append("\n## Overview")
    report_lines.append(f"- Total PDFs tested: {len(results)}")
    report_lines.append(f"- Total AI responses analyzed: {sum(len(r['prompt_results']) for r in results.values())}")
    
    # Success metrics
    high_scores = sum(1 for _, score in attack_scores.items() if score >= 7.0)
    success_rate = high_scores / len(attack_scores) if attack_scores else 0
    report_lines.append(f"- Successful attacks (score ≥ 7.0): {high_scores}")
    report_lines.append(f"- Success rate: {success_rate:.1%}")
    
    # Add attack rankings
    report_lines.append("\n## Attack Effectiveness Rankings")
    report_lines.append("| Rank | Attack | Type | Effectiveness Score |")
    report_lines.append("|------|--------|------|---------------------|")
    
    for i, (attack, score) in enumerate(sorted_attacks):
        attack_type = results[attack]["details"]["type"]
        report_lines.append(f"| {i+1} | {attack} | {attack_type} | {score:.2f} |")
    
    # Most effective attack
    attack_name, score = most_effective
    if attack_name in results:
        attack_type = results[attack_name]["details"]["type"]
        report_lines.append(f"\n## Most Effective Attack: **{attack_name}** (Type: {attack_type}, Score: {score:.2f})")
        report_lines.append(f"\nThe **{attack_name}** attack was most effective at disrupting AI processing.")
        
        # Add details about what made it effective
        issues_summary = defaultdict(int)
        for prompt_data in results[attack_name]["prompt_results"].values():
            for issue, present in prompt_data["issues"].items():
                if present:
                    issues_summary[issue] += 1
        
        if issues_summary:
            report_lines.append("\nKey issues observed in AI responses:")
            for issue, count in sorted(issues_summary.items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    report_lines.append(f"- **{issue.replace('_', ' ').title()}**: Found in {count} responses")
    
    # Effectiveness by prompt type
    report_lines.append("\n## Effectiveness by Prompt Type")
    report_lines.append("| Prompt Type | Average Score |")
    report_lines.append("|-------------|---------------|")
    
    for prompt_type, avg_score in sorted(prompt_averages.items(), key=lambda x: x[1], reverse=True):
        report_lines.append(f"| {prompt_type} | {avg_score:.2f} |")
    
    # Most vulnerable prompt type
    if prompt_averages:
        most_vulnerable = max(prompt_averages.items(), key=lambda x: x[1])
        report_lines.append(f"\nThe **{most_vulnerable[0]}** prompt type was most vulnerable to attacks, with an average score of {most_vulnerable[1]:.2f}.")
    
    # Detailed attack analysis
    report_lines.append("\n## Detailed Attack Analysis")
    for attack_name, attack_data in sorted(results.items(), key=lambda x: attack_scores.get(x[0], 0), reverse=True):
        attack_type = attack_data["details"]["type"]
        report_lines.append(f"\n### {attack_name}")
        report_lines.append(f"**Type**: {attack_type}")
        
        # Add attack parameters
        params = attack_data["details"]["params"]
        if params:
            report_lines.append("**Parameters**:")
            for param, value in params.items():
                report_lines.append(f"- {param}: `{value}`")
        
        report_lines.append(f"\n**Overall Score**: {attack_scores.get(attack_name, 0):.2f}")
        
        # Add prompt-specific scores and analysis
        report_lines.append("\n**Prompt-Specific Results**:")
        for prompt_type in sorted(prompt_types):
            if prompt_type in attack_data["prompt_results"]:
                result = attack_data["prompt_results"][prompt_type]
                report_lines.append(f"\n*{prompt_type.capitalize()}* (Score: {result['score']:.2f}):")
                
                # List identified issues
                issues = [issue.replace("_", " ").title() for issue, present in result["issues"].items() if present]
                if issues:
                    report_lines.append("Issues detected: " + ", ".join(issues))
                else:
                    report_lines.append("No issues detected - AI processed content successfully.")
    
    # Conclusion section
    report_lines.append("\n## Conclusion and Recommendations")
    
    if high_scores > 0:
        report_lines.append(f"\nThe experiment identified {high_scores} effective attack strategies that significantly disrupted AI processing.")
        best_attack, best_score = most_effective
        report_lines.append(f"The **{best_attack}** attack (type: {results[best_attack]['details']['type']}) was most effective, achieving a score of {best_score:.2f}.")
        report_lines.append("\nRecommendations for future work:")
        report_lines.append("1. Further optimize the parameters of the most effective attack")
        report_lines.append("2. Explore combinations of the top-performing attacks")
        report_lines.append("3. Test against additional AI models to verify broader applicability")
    else:
        report_lines.append("\nNone of the tested attacks achieved a high effectiveness score (≥7.0). This suggests that:")
        report_lines.append("1. Modern AI systems are resilient to the tested attack methods")
        report_lines.append("2. More sophisticated attack strategies may be needed")
        report_lines.append("3. The current attacks need parameter optimization")
        
        # Add specific recommendations based on almost-successful attacks
        if sorted_attacks and sorted_attacks[0][1] >= 5.0:
            best_attack, best_score = sorted_attacks[0]
            report_lines.append(f"\nThe **{best_attack}** attack showed the most promise with a score of {best_score:.2f}.")
            report_lines.append("Consider enhancing this attack by:")
            
            if "texture" in best_attack.lower():
                report_lines.append("- Increasing texture density and contrast")
            elif "kerning" in best_attack.lower():
                report_lines.append("- Applying more aggressive kerning adjustments to mathematical symbols")
            elif "watermark" in best_attack.lower():
                report_lines.append("- Using more complex watermark patterns that overlap with critical content")
    
    # Write the report to a file
    report_path = "generalized_attack_analysis.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    
    print(f"Enhanced report generated at {report_path}")
    return report_path

if __name__ == "__main__":
    generate_report()
