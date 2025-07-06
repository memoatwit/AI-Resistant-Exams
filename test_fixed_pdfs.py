#!/usr/bin/env python3
# test_fixed_pdfs.py
#
# This script tests the PDFs that were fixed by fix_attacks.py

import os
import json
import time
from pathlib import Path
import re
import subprocess

# Import the test module
try:
    from exam_test import run_test_suite, DEFAULT_MODEL, DEFAULT_PROMPT, SOLVE_PROMPT, EXPLAIN_PROMPT
except ImportError:
    # Fallback defaults
    print("Warning: Could not import from exam_test.py, using defaults")
    DEFAULT_MODEL = "gemma3:4b"
    DEFAULT_PROMPT = "Transcribe the text from the document."
    SOLVE_PROMPT = "Identify the main math or coding problem in this document and solve it. Show your work and explain your solution."
    EXPLAIN_PROMPT = "Explain the concept being tested in this document and provide a detailed explanation of the problem and solution."
    
    # Define a minimal run_test_suite function
    def run_test_suite(pdf_path, model_name, prompt):
        """Run test on PDF using the Ollama command line"""
        result = {
            "model": model_name,
            "prompt": prompt,
            "test_results": {}
        }
        
        try:
            # Convert PDF to image
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, dpi=300)
            temp_image = "temp_test_image.png"
            images[0].save(temp_image, "PNG")
            
            # Use subprocess to call ollama
            cmd = ["ollama", "run", model_name, prompt, temp_image]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if process.returncode == 0:
                result["test_results"]["image_input"] = process.stdout
            else:
                result["test_results"]["image_input"] = f"Error: {process.stderr}"
        except Exception as e:
            result["test_results"]["image_input"] = f"Exception: {str(e)}"
        
        return result

def test_pdf(pdf_path):
    """Test a single PDF with all prompt types"""
    print(f"\n--- Testing {pdf_path} ---")
    
    prompts = {
        "transcription": DEFAULT_PROMPT,
        "solving": SOLVE_PROMPT,
        "explanation": EXPLAIN_PROMPT
    }
    
    results = {}
    
    for prompt_name, prompt_text in prompts.items():
        print(f"  Running {prompt_name} test...")
        
        result = run_test_suite(
            pdf_path=str(pdf_path),
            model_name=DEFAULT_MODEL,
            prompt=prompt_text
        )
        
        # Save result to file
        base_name = os.path.basename(pdf_path)
        base_name = os.path.splitext(base_name)[0]
        result_file = f"results_{base_name}_{prompt_name}_fixed.txt"
        
        with open(result_file, "w") as f:
            f.write(f"Test Results for {pdf_path}\n")
            f.write(f"Model: {DEFAULT_MODEL}\n")
            f.write(f"Prompt: {prompt_text}\n")
            f.write("-" * 50 + "\n\n")
            f.write("IMAGE ANALYSIS RESULTS:\n\n")
            f.write(result["test_results"].get("image_input", "No result"))
        
        print(f"  Results saved to {result_file}")
        results[prompt_name] = result
    
    return results

def find_fixed_pdfs():
    """Find all the PDFs that were fixed"""
    # Look for PDFs with kerning, font_swap, combo, or kitchen_sink in the name
    kerning_pdfs = list(Path('.').glob("*kerning*.pdf"))
    font_swap_pdfs = list(Path('.').glob("*font_swap*.pdf")) 
    combo_pdfs = list(Path('.').glob("*combo*.pdf"))
    
    all_pdfs = kerning_pdfs + font_swap_pdfs + combo_pdfs
    return [pdf for pdf in all_pdfs if os.path.exists(pdf)]

def update_experiment_log(pdf_path, results):
    """Update the experiment log with the new results"""
    log_file = "generalized_experiment_log.jsonl"
    if not os.path.exists(log_file):
        print(f"Warning: Log file {log_file} not found")
        return
    
    # Extract attack details from filename
    base_name = os.path.basename(pdf_path)
    match = re.search(r"gen_variant_(.+?)\.pdf", base_name)
    if not match:
        print(f"Warning: Could not extract attack name from {base_name}")
        return
    
    attack_name = match.group(1)
    
    # Read existing log to find attack details
    attack_details = None
    with open(log_file, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if "attack_details" in entry and entry["attack_details"].get("name") == attack_name.replace("_level2", ""):
                    attack_details = entry["attack_details"]
                    break
            except:
                pass
    
    if not attack_details:
        print(f"Warning: Could not find attack details for {attack_name}")
        attack_details = {"name": attack_name, "type": "unknown"}
    
    # Append new entries to log
    with open(log_file, "a") as f:
        for prompt_type, result in results.items():
            log_entry = {
                "attack_details": attack_details,
                "context_level": 2,
                "prompt_type": prompt_type,
                "test_run_output": result,
                "fixed": True
            }
            f.write(json.dumps(log_entry) + "\n")
    
    print(f"Updated log file with results for {base_name}")

def main():
    # Find all fixed PDFs
    pdfs = find_fixed_pdfs()
    print(f"Found {len(pdfs)} fixed PDFs to test")
    
    if not pdfs:
        print("No fixed PDFs found. Run fix_attacks.py first.")
        return
    
    # Test each PDF
    for pdf in pdfs:
        results = test_pdf(pdf)
        update_experiment_log(pdf, results)
    
    print("\nAll tests completed. Run analyze_generalized_results_v2.py to generate an updated report.")

if __name__ == "__main__":
    main()
