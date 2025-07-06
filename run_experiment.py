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
    from exam_test import run_test_suite, DEFAULT_MODEL, DEFAULT_PROMPT, SOLVE_PROMPT, EXPLAIN_PROMPT
except ImportError:
    # Fallback in case the constants aren't defined in exam_test.py
    from exam_test import run_test_suite
    DEFAULT_MODEL = "gemma3:4b"
    DEFAULT_PROMPT = "Transcribe the text from the document."
    SOLVE_PROMPT = "Identify the main math or coding problem in this document and solve it. Show your work and explain your solution."
    EXPLAIN_PROMPT = "Explain the concept being tested in this document and provide a detailed explanation of the problem and solution."

def run_full_experiment():
    """
    Manages the entire experiment from PDF generation to testing and logging.
    """
    # --- 1. Define the NEW, MORE ADVANCED Adversarial Attacks to Test ---
    attacks_to_run = [
        # --- BASELINE ---
        {
            'name': 'baseline_clean',
            'type': 'none',
            'params': {}
        },
        # --- TIER 1: SINGLE, IMPROVED ATTACKS ---
        {
            'name': 'A1_watermark_tiled_math',
            'type': 'watermark_tiled',
            'params': {'text': r"f'(x)", 'color': 'gray!15', 'size': 8, 'angle': 20, 'x_step': 4, 'y_step': 3}
        },
        {
            'name': 'A2_texture_wave_pattern',
            'type': 'texture',
            'params': {'pattern': 'wave', 'color': 'gray!20', 'density': 0.4}
        },
        {
            'name': 'A3_layout_targeted_kerning',
            'type': 'kerning',
            'params': {'amount': -0.08, 'target': 'e^{x^2}'} # Target the part that was misread
        },
        {
            'name': 'A3b_kerning_on_sin',
            'type': 'kerning',
            'params': {'amount': -0.08, 'target': 'sin(3x)'}
        },
        {
            'name': 'A4_font_symbol_swap',
            'type': 'font_swap',
            'params': {'symbol_to_swap': '=', 'font_name': 'Comic Sans MS'}
        },
        # --- TIER 2: POWERFUL COMBINATION ATTACKS ---
        {
            'name': 'B1_combo_kerning_and_dense_lines',
            'type': 'combo',
            'params': {
                'sub_attacks': [
                    {'type': 'kerning', 'params': {'amount': -0.08, 'target': 'e^{x^2}'}},
                    {'type': 'texture', 'params': {'pattern': 'lines', 'density': 0.5, 'color': 'gray!18'}}
                ]
            }
        },
        {
            'name': 'B2_combo_tiledwatermark_and_waves',
            'type': 'combo',
            'params': {
                'sub_attacks': [
                    {'type': 'watermark_tiled', 'params': {'text': 'sin(3x)', 'color': 'gray!12', 'angle': -15, 'x_step': 5, 'y_step': 4}},
                    {'type': 'texture', 'params': {'pattern': 'wave', 'density': 0.5, 'color': 'gray!20'}}
                ]
            }
        },
        # --- TIER 3: KITCHEN SINK ---
        {
            'name': 'C1_combo_kitchen_sink',
            'type': 'combo',
            'params': {
                'sub_attacks': [
                    {'type': 'kerning', 'params': {'amount': -0.07, 'target': 'sin(3x)'}},
                    {'type': 'watermark_tiled', 'params': {'text': 'f(x)', 'color': 'gray!15', 'angle': 25, 'x_step': 6, 'y_step': 5}},
                    {'type': 'texture', 'params': {'pattern': 'dots', 'density': 1.0, 'color': 'gray!12'}}
                ]
            }
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
        backup_name = f"{log_filename}.{int(time.time())}.bak"
        os.rename(log_filename, backup_name)
        print(f"Backed up existing log file to {backup_name}")

    for attack in attacks_to_run:
        variant_name = f"variant_{attack['name']}"
        print(f"\n\n{'='*20} PROCESSING ATTACK: {variant_name.upper()} {'='*20}")

        pdf_path = create_exam_variant(
            template_path='exam_template.tex',
            output_name=variant_name,
            attack_params=attack
        )

        if not pdf_path or not os.path.exists(pdf_path):
            print(f"!!!!!! FAILED to generate PDF for {variant_name}. Skipping. !!!!!!")
            continue

        print(f"Successfully generated PDF: {pdf_path}")

        for prompt_name, prompt_text in prompts_to_test.items():
            print(f"\n--- Testing '{variant_name}' with prompt: '{prompt_name.upper()}' ---")
            result_data = run_test_suite(pdf_path=pdf_path, model_name=DEFAULT_MODEL, prompt=prompt_text)

            log_entry = {
                "attack_details": attack,
                "prompt_type": prompt_name,
                "test_run_output": result_data
            }

            with open(log_filename, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

            print(f"--- Completed test for '{prompt_name}'. Master log updated. ---")

    print(f"\n\n{'*'*20} EXPERIMENT COMPLETE {'*'*20}")
    print(f"All attacks processed. Individual results are in '.txt' files.")
    print(f"A complete, structured log for analysis is saved to: {log_filename}")


if __name__ == "__main__":
    if not os.path.exists('exam_template.tex'):
        print("ERROR: 'exam_template.tex' not found. Please create it.")
    else:
        run_full_experiment()