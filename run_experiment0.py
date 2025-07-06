# run_experiment.py
#
# This is the master orchestrator for the AI-resistant exam project.
# It coordinates the generation of adversarial exam papers and their subsequent testing.
#
# Workflow:
# 1. Defines a list of "attacks" (e.g., watermarks, textures).
# 2. For each attack:
#    a. Calls `exam_attack.py` to generate a unique PDF variant.
# 3. For each generated PDF:
#    a. Calls `exam_test.py` multiple times, once for each prompt (transcribe, solve, explain).
# 4. Aggregates all structured results into a single `full_experiment_log.jsonl` file
#    for comprehensive analysis.

import os
import json
import time

# Import the necessary components from your other scripts
from exam_attack import create_exam_variant 
# Import test module with the updated prompts
try:
    from exam_test import run_test_suite, DEFAULT_PROMPT, SOLVE_PROMPT, EXPLAIN_PROMPT
except ImportError:
    # Fallback in case the constants aren't defined in exam_test.py
    from exam_test import run_test_suite
    DEFAULT_PROMPT = "Transcribe the text from the document."
    SOLVE_PROMPT = "Identify the main math or coding problem in this document and solve it. Show your work and explain your solution."
    EXPLAIN_PROMPT = "Explain the concept being tested in this document and provide a detailed explanation of the problem and solution."

def run_full_experiment():
    """
    Manages the entire experiment from PDF generation to testing and logging.
    """
    # --- 1. Define the Adversarial Attacks to Test ---
    # Each dictionary defines one experiment. Add new attacks here.
    attacks_to_run = [
        {
            'name': 'baseline_clean',
            'type': 'none', 
            'params': {}
        },
        {
            'name': 'watermark_light_text',
            'type': 'watermark',
            'params': {'text': "DO NOT COPY - PROPERTY OF UNIVERSITY", 'color': 'gray!15', 'size': 10, 'angle': 30}
        },
        {
            'name': 'watermark_dense_math',
            'type': 'watermark',
            'params': {'text': r"\(\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}\) " * 3, 'color': 'gray!12', 'size': 8, 'angle': -25}
        },
        {
            'name': 'texture_low_density_dots',
            'type': 'texture', 
            'params': {'pattern': 'dots', 'density': 0.7, 'color': 'gray!10'}
        },
        {
            'name': 'texture_high_density_lines',
            'type': 'texture', 
            'params': {'pattern': 'lines', 'density': 0.4, 'color': 'gray!18'}
        },
        {
            'name': 'layout_kerning_disrupt',
            'type': 'kerning',
            'params': {'amount': -0.08} # Make this a negative value
        },
        {
            'name': 'combo_watermark_texture',
            'type': 'combo',
            'params': {'attacks': ['watermark', 'texture']} # Example for a future combo attack
        }
    ]

    # --- 2. Define the Prompts for Testing ---
    prompts_to_test = {
        "transcription": DEFAULT_PROMPT,
        "solving": SOLVE_PROMPT,
        "explanation": EXPLAIN_PROMPT,
    }

    # --- 3. Run the Experiment Loop ---
    log_filename = 'full_experiment_log.jsonl'
    if os.path.exists(log_filename):
        # Prevent accidentally appending to an old experiment log
        os.rename(log_filename, f"{log_filename}.{int(time.time())}.bak")
        print(f"Backed up existing log file.")

    for attack in attacks_to_run:
        variant_name = f"variant_{attack['name']}"
        print(f"\n\n{'='*20} PROCESSING ATTACK: {variant_name.upper()} {'='*20}")

        # STEP A: Generate the PDF using your attack script
        # The `create_exam_variant` function in exam_attack.py needs to accept these params.
        pdf_path = create_exam_variant(
            template_path='exam_template.tex',
            output_name=variant_name,
            attack_params=attack
        )

        if not pdf_path or not os.path.exists(pdf_path):
            print(f"!!!!!! FAILED to generate PDF for {variant_name}. Skipping. !!!!!!")
            continue

        print(f"Successfully generated PDF: {pdf_path}")
        
        # STEP B: Test the generated PDF with each prompt
        for prompt_name, prompt_text in prompts_to_test.items():
            print(f"\n--- Testing '{variant_name}' with prompt: '{prompt_name.upper()}' ---")
            
            # This function now runs the test and saves its own .txt file
            result_data = run_test_suite(pdf_path=pdf_path, prompt=prompt_text)
            
            # STEP C: Aggregate data for the master log file
            log_entry = {
                "attack_details": attack,
                "prompt_type": prompt_name,
                "test_run_output": result_data # This contains the AI's response and other metadata
            }
            
            # Save the structured result to our comprehensive log
            with open(log_filename, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            print(f"--- Completed test for '{prompt_name}'. Master log updated. ---")

    print(f"\n\n{'*'*20} EXPERIMENT COMPLETE {'*'*20}")
    print(f"All attacks processed. Individual results are in '.txt' files.")
    print(f"A complete, structured log for analysis is saved to: {log_filename}")


if __name__ == "__main__":
    # You will need to create a basic `exam_attack.py` and `exam_template.tex`
    # for this to run without errors.
    run_full_experiment()