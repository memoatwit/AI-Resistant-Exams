#!/usr/bin/env python3
"""
Script to run the top 10 most effective attacks based on previous experiment results.
This script selects the attacks that showed the highest effectiveness
in reducing AI model output across various tests.
"""

import os
import json
import argparse
import sys
import shutil
from datetime import datetime

# Try to import the required modules
try:
    from exam_attack_v3 import create_exam_variant
except ImportError:
    print("ERROR: Could not import exam_attack_v3 module. Make sure it exists in the current directory.")
    sys.exit(1)

try:
    from exam_test import run_test_suite, DEFAULT_PROMPT, SOLVE_PROMPT, EXPLAIN_PROMPT
except ImportError:
    print("ERROR: Could not import exam_test module. Make sure it exists in the current directory.")
    print("Using default prompts instead.")
    DEFAULT_PROMPT = "Transcribe the text from the document."
    SOLVE_PROMPT = "Identify the main math or coding problem in this document and solve it. Show your work and explain your solution."
    EXPLAIN_PROMPT = "Explain the concept being tested in this document and provide a detailed explanation of the problem and solution."

def run_top_attacks(template_path='exam_template.tex', 
                   log_file='top_attacks_results.jsonl',
                   model_name='gemma3:4b',
                   output_dir='attack_pdfs_0712'):
    """
    Run the top 10 most effective attacks based on previous experiment results.
    
    Args:
        template_path (str): Path to the LaTeX template file to use as a base
        log_file (str): Path where the experiment results will be logged in JSONL format
        model_name (str): Name of the AI model to test against
        output_dir (str): Directory to store output PDFs
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Define the top 10 attacks based on effectiveness
    top_attacks = [
        # Attacks that performed best for "solving" prompt type
        {'name': 'C4_combo_triple_threat', 'type': 'combo', 'params': {
            'attacks': [
                {'type': 'watermark_tiled', 'params': {'text': 'DRAFT', 'color': 'gray!10', 'size': 8}},
                {'type': 'kerning', 'params': {'amount': -0.08, 'target': 'x^2'}},
                {'type': 'symbol_stretch', 'params': {'target': '\\int', 'stretch_amount': 1.5}}
            ]
        }},
        
        {'name': 'A1c_watermark_subtle_symbols', 'type': 'watermark_tiled', 
         'params': {'text': r'\alpha \beta \gamma', 'color': 'gray!8', 'size': 12, 'angle': 45, 'x_step': 5, 'y_step': 4}},
        
        {'name': 'B1_combo_kerning_and_dense_lines', 'type': 'combo', 'params': {
            'attacks': [
                {'type': 'kerning', 'params': {'amount': -0.1, 'target': 'derivative'}},
                {'type': 'texture', 'params': {'pattern': 'lines', 'density': 0.6, 'color': 'gray!15'}}
            ]
        }},
        
        {'name': 'F1b_watermark_color_light', 'type': 'watermark_tiled', 
         'params': {'text': 'DRAFT', 'color': 'gray!10', 'size': 10, 'angle': 30, 'x_step': 6, 'y_step': 5}},
        
        {'name': 'S2_stretch_sum', 'type': 'symbol_stretch', 
         'params': {'target': '\\sum', 'stretch_amount': 1.5}},
        
        {'name': 'M3_fraktur_operators', 'type': 'math_font', 
         'params': {'target_type': 'operators', 'font_style': '\\mathfrak'}},
        
        {'name': 'O2_optimized_texture', 'type': 'texture', 
         'params': {'pattern': 'grid', 'color': 'gray!40', 'density': 0.6, 'line_width': 0.4}},
        
        # Attacks that had some positive effectiveness
        {'name': 'OPT21_texture_tuned', 'type': 'texture', 
         'params': {'pattern': 'wave', 'color': 'gray!18', 'density': 0.45, 'line_width': 0.25}},
        
        {'name': 'F1a_watermark_color_vlight', 'type': 'watermark_tiled', 
         'params': {'text': 'DRAFT', 'color': 'gray!5', 'size': 10, 'angle': 30, 'x_step': 6, 'y_step': 5}},
        
        {'name': 'C1_combo_kitchen_sink', 'type': 'combo', 'params': {
            'attacks': [
                {'type': 'watermark_tiled', 'params': {'text': 'CONFIDENTIAL', 'color': 'gray!7', 'size': 8}},
                {'type': 'texture', 'params': {'pattern': 'dots', 'density': 0.4, 'color': 'gray!10'}},
                {'type': 'kerning', 'params': {'amount': -0.05, 'target': 'calculus'}},
                {'type': 'symbol_stretch', 'params': {'target': '=', 'stretch_amount': 1.2}}
            ]
        }}
    ]
    
    # Add the baseline for comparison
    baseline = {'name': 'baseline_clean', 'type': 'none', 'params': {}}
    all_attacks = [baseline] + top_attacks
    
    # Create a log file and record setup
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
    
    print(f"Starting experiment with top 10 attacks on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using template: {template_path}")
    print(f"Using model: {model_name}")
    print(f"Results will be logged to: {log_file}")
    print(f"PDFs will be saved to: {output_dir}")
    
    # Define prompt types to test
    prompt_types = [
        {"name": "transcription", "prompt": DEFAULT_PROMPT},
        {"name": "solving", "prompt": SOLVE_PROMPT},
        {"name": "explanation", "prompt": EXPLAIN_PROMPT}
    ]
    
    # Run all combinations of attacks and prompt types
    for attack in all_attacks:
        print(f"\n--- Running attack: {attack['name']} ({attack['type']}) ---")
        
        try:
            # Create the attack variant
            variant_filename = os.path.join(output_dir, f"variant_{attack['name']}.tex")
            pdf_path = os.path.splitext(variant_filename)[0] + ".pdf"
            
            if attack['type'] == 'none':
                # Just copy the template for baseline
                with open(template_path, 'r') as f:
                    template_content = f.read()
                
                with open(variant_filename, 'w') as f:
                    f.write(template_content)
            else:
                # Create the attack variant
                create_exam_variant(
                    template_path=template_path,
                    output_name=variant_filename,
                    attack_params=attack
                )
            
            # Copy all resource directories needed for figures
            dirname = os.path.dirname(template_path)
            if dirname != output_dir and dirname != '':
                # List of possible resource directories used in templates
                resource_dirs = [
                    "CoF AI paper exam 4 (Discrete math)",
                    "CoF AI paper exam 2 (Multivariable calculus)",
                    "CoF AI paper exam 3 (Complex analysis)",
                    "CoF AI paper exam"
                ]
                
                for resource_dir in resource_dirs:
                    src_dir = os.path.join(os.path.abspath(dirname or '.'), resource_dir)
                    dst_dir = os.path.join(os.path.abspath(output_dir), resource_dir)
                    
                    if os.path.exists(src_dir) and not os.path.exists(dst_dir):
                        print(f"Creating symbolic link from {src_dir} to {dst_dir}")
                        try:
                            os.symlink(src_dir, dst_dir)
                        except OSError as e:
                            # If symlink fails (e.g. on some Windows systems), try copying
                            print(f"Symlink failed: {e}. Attempting to copy directory.")
                            if os.path.isdir(src_dir):
                                shutil.copytree(src_dir, dst_dir)
            
            # Compile the LaTeX file with output directory specified
            print(f"Compiling {variant_filename}...")
            os.system(f"lualatex -interaction=nonstopmode -output-directory={output_dir} {variant_filename}")
            
            if not os.path.exists(pdf_path):
                print(f"Error: Failed to create PDF for {variant_filename}")
                continue
            
            # Test each prompt type
            for pt in prompt_types:
                print(f"Testing with {pt['name']} prompt...")
                
                results = run_test_suite(pdf_path, model_name, pt['prompt'])
                
                # Add metadata
                entry = {
                    "attack_details": attack,
                    "context_level": 2,
                    "prompt_type": pt["name"],
                    "model": model_name,
                    "test_run_output": results,
                    "status": "success",
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Log the results
                with open(log_file, 'a') as f:
                    f.write(json.dumps(entry) + '\n')
            
        except Exception as e:
            print(f"Error with attack {attack['name']}: {str(e)}")
            
            # Log the error
            error_entry = {
                "attack_details": attack,
                "context_level": 2,
                "model": model_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(error_entry) + '\n')
    
    print("\nAll attacks completed!")
    print(f"Results have been logged to {log_file}")
    print(f"PDFs have been saved to {output_dir}")
    print("To analyze results, run analyze_overnight_detailed.py on the log file.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run top 10 most effective AI-resistant exam attacks')
    parser.add_argument('--template', type=str, default='exam_template.tex', 
                        help='LaTeX template file path')
    parser.add_argument('--log-file', type=str, default='top_attacks_results.jsonl',
                        help='Path to the output log file')
    parser.add_argument('--model', type=str, default='gemma3:4b',
                        help='AI model to use for testing')
    parser.add_argument('--output-dir', type=str, default='attack_pdfs_0712',
                        help='Directory to store output PDFs')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.template):
        print(f"ERROR: Template file '{args.template}' not found.")
    else:
        run_top_attacks(
            template_path=args.template,
            log_file=args.log_file,
            model_name=args.model,
            output_dir=args.output_dir
        )
