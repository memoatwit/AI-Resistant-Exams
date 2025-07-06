#!/usr/bin/env python3
# benchmark_attacks.py
#
# This script benchmarks different attacks against various AI models
# to determine which attacks are most effective for different problem types

import os
import json
import time
from pathlib import Path
import subprocess
from exam_test import run_test_suite, DEFAULT_MODEL, DEFAULT_PROMPT, SOLVE_PROMPT, EXPLAIN_PROMPT

# Define models to test (if available)
MODELS_TO_TEST = [
    DEFAULT_MODEL,  # Typically gemma3:4b from your setup
    "llava",        # If you have llava installed
    # Add other models you have installed
]

# Define prompts to test
PROMPTS = {
    "transcription": DEFAULT_PROMPT,
    "solving": SOLVE_PROMPT,
    "explanation": EXPLAIN_PROMPT,
}

def check_model_available(model_name):
    """Check if a model is available in Ollama"""
    try:
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True
        )
        return model_name in result.stdout
    except:
        return False

def get_available_models():
    """Get list of available models"""
    available = []
    for model in MODELS_TO_TEST:
        if check_model_available(model):
            available.append(model)
            print(f"Model {model} is available")
        else:
            print(f"Model {model} is not available, skipping")
    return available

def score_attack_effectiveness(result_text, prompt_type):
    """
    Score how effective an attack was based on AI output
    Returns a score from 0-10 (higher = more effective attack)
    """
    # This is a very simple heuristic - in practice you'd want something more sophisticated
    if "Error" in result_text:
        return 10  # Attack completely broke the AI's ability to process
    
    # For transcription prompts
    if prompt_type == "transcription":
        if len(result_text) < 50:
            return 9  # Almost nothing transcribed
        elif "unable to" in result_text.lower() or "cannot" in result_text.lower():
            return 8  # AI acknowledged difficulty
        elif len(result_text) < 200:
            return 6  # Very short response
        
    # For solving prompts
    if prompt_type == "solving":
        if "cannot solve" in result_text.lower() or "unable to solve" in result_text.lower():
            return 8  # AI acknowledged it can't solve
        if "unclear" in result_text.lower() or "difficult to read" in result_text.lower():
            return 7  # AI had difficulty
            
    # For explanation prompts
    if prompt_type == "explanation":
        if "cannot explain" in result_text.lower() or "unable to explain" in result_text.lower():
            return 8  # AI acknowledged it can't explain
    
    # Default - assume moderate effectiveness
    return 4
    
def benchmark_pdfs(pdf_folder, output_file):
    """
    Run benchmark tests on all PDFs in the folder against available models
    """
    # Find all PDFs in the folder
    pdfs = list(Path(pdf_folder).glob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs to benchmark")
    
    # Get available models
    models = get_available_models()
    if not models:
        print("No models available to test!")
        return
    
    # Create results structure
    benchmark_results = []
    
    # Process each PDF
    for pdf_path in pdfs:
        pdf_name = pdf_path.name
        print(f"\n--- Benchmarking {pdf_name} ---")
        
        # Extract attack name from filename pattern
        attack_name = "unknown"
        if "_" in pdf_name:
            parts = pdf_name.split("_")
            if len(parts) >= 2:
                attack_name = parts[1]
        
        # Test with each model
        for model in models:
            print(f"Testing with model: {model}")
            
            # Test with each prompt type
            for prompt_name, prompt_text in PROMPTS.items():
                print(f"  Running {prompt_name} test...")
                
                start_time = time.time()
                result = run_test_suite(
                    pdf_path=str(pdf_path),
                    model_name=model,
                    prompt=prompt_text
                )
                elapsed = time.time() - start_time
                
                # Extract the AI response
                ai_response = result.get("test_results", {}).get("image_input", "")
                
                # Score effectiveness
                effectiveness = score_attack_effectiveness(ai_response, prompt_name)
                
                # Record result
                benchmark_entry = {
                    "pdf": pdf_name,
                    "attack": attack_name,
                    "model": model,
                    "prompt": prompt_name,
                    "effectiveness_score": effectiveness,
                    "response_time": elapsed,
                    "response_length": len(ai_response),
                    "timestamp": time.time()
                }
                
                benchmark_results.append(benchmark_entry)
                
                # Save incrementally
                with open(output_file, "a") as f:
                    f.write(json.dumps(benchmark_entry) + "\n")
                
                print(f"  Effectiveness score: {effectiveness}/10")
    
    return benchmark_results

def analyze_results(results_file):
    """Analyze benchmark results and generate a summary report"""
    if not os.path.exists(results_file):
        print(f"Results file {results_file} not found!")
        return
        
    # Load results
    results = []
    with open(results_file, "r") as f:
        for line in f:
            results.append(json.loads(line))
    
    print(f"\n=== Benchmark Analysis ({len(results)} test runs) ===")
    
    # Calculate average effectiveness by attack type
    attack_scores = {}
    for r in results:
        attack = r["attack"]
        score = r["effectiveness_score"]
        
        if attack not in attack_scores:
            attack_scores[attack] = []
        attack_scores[attack].append(score)
    
    print("\nAttack Effectiveness (higher = more effective):")
    for attack, scores in attack_scores.items():
        avg = sum(scores) / len(scores)
        print(f"- {attack}: {avg:.1f}/10")
    
    # Effectiveness by model
    model_scores = {}
    for r in results:
        model = r["model"]
        score = r["effectiveness_score"]
        
        if model not in model_scores:
            model_scores[model] = []
        model_scores[model].append(score)
    
    print("\nAttack Effectiveness by Model:")
    for model, scores in model_scores.items():
        avg = sum(scores) / len(scores)
        print(f"- {model}: {avg:.1f}/10")
    
    # Effectiveness by prompt type
    prompt_scores = {}
    for r in results:
        prompt = r["prompt"]
        score = r["effectiveness_score"]
        
        if prompt not in prompt_scores:
            prompt_scores[prompt] = []
        prompt_scores[prompt].append(score)
    
    print("\nAttack Effectiveness by Prompt Type:")
    for prompt, scores in prompt_scores.items():
        avg = sum(scores) / len(scores)
        print(f"- {prompt}: {avg:.1f}/10")
    
    # Find most effective attacks
    attack_avgs = {a: sum(s)/len(s) for a, s in attack_scores.items()}
    best_attack = max(attack_avgs.items(), key=lambda x: x[1])
    print(f"\nMost effective attack: {best_attack[0]} ({best_attack[1]:.1f}/10)")
    
    # Save analysis to file
    analysis = {
        "attack_scores": {a: sum(s)/len(s) for a, s in attack_scores.items()},
        "model_scores": {m: sum(s)/len(s) for m, s in model_scores.items()},
        "prompt_scores": {p: sum(s)/len(s) for p, s in prompt_scores.items()},
        "best_attack": best_attack[0],
        "best_attack_score": best_attack[1]
    }
    
    with open("benchmark_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\nDetailed analysis saved to benchmark_analysis.json")

def main():
    """Run benchmark tests on generated PDFs"""
    output_file = "attack_benchmarks.jsonl"
    
    # Clear previous results if they exist
    if os.path.exists(output_file):
        os.rename(output_file, f"{output_file}.{int(time.time())}.bak")
    
    # Run benchmarks
    print("Starting benchmark tests...")
    benchmark_pdfs("/Users/memo/Documents/act", output_file)
    
    # Analyze results
    analyze_results(output_file)

if __name__ == "__main__":
    main()
