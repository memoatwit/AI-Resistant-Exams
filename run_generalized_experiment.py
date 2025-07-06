#!/usr/bin/env python3
# run_generalized_experiment.py
#
# Enhanced orchestrator for AI-resistant exam project with generalized attacks.
# Builds on the original run_experiment.py but uses the context-aware attack framework.

import os
import json
import time

# Import the enhanced attack framework
from generalized_attack import create_exam_variant

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

def run_full_experiment(template_path='ex1.tex', context_level=2):
    """
    Manages the entire experiment from PDF generation to testing and logging.
    
    Args:
        template_path: Path to the LaTeX template file
        context_level: Level of context awareness for attacks (0-3)
    """
    # --- 1. Define Advanced Adversarial Attacks ---
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
            'params': {'amount': -0.08} # Let the context awareness select targets
        },
        {
            'name': 'A4_font_symbol_swap',
            'type': 'font_swap',
            'params': {'symbol_to_swap': '=', 'font_name': 'Comic Sans MS'}
        },
        # --- TIER 2: NEW ADVANCED ATTACKS ---
        {
            'name': 'A5_background_color',
            'type': 'background_color',
            'params': {'color': 'yellow!3', 'mode': 'full'}
        },
        {
            'name': 'A6_line_spacing',
            'type': 'line_spacing',
            'params': {'factor': 1.08}
        },
        # --- TIER 3: POWERFUL COMBINATION ATTACKS ---
        {
            'name': 'B1_combo_kerning_and_texture',
            'type': 'combo',
            'params': {
                'sub_attacks': [
                    {'type': 'kerning', 'params': {'amount': -0.08}},
                    {'type': 'texture', 'params': {'pattern': 'lines', 'density': 0.5, 'color': 'gray!18'}}
                ]
            }
        },
        {
            'name': 'B2_combo_watermark_and_font',
            'type': 'combo',
            'params': {
                'sub_attacks': [
                    {'type': 'watermark_tiled', 'params': {'text': 'sin(x)', 'color': 'gray!12', 'angle': -15}},
                    {'type': 'font_swap', 'params': {'symbol_to_swap': '=', 'font_name': 'Comic Sans MS'}}
                ]
            }
        },
        {
            'name': 'B3_combo_background_and_kerning',
            'type': 'combo',
            'params': {
                'sub_attacks': [
                    {'type': 'background_color', 'params': {'color': 'blue!2', 'mode': 'full'}},
                    {'type': 'kerning', 'params': {'amount': -0.07}}
                ]
            }
        },
        # --- TIER 4: KITCHEN SINK ---
        {
            'name': 'C1_combo_kitchen_sink',
            'type': 'combo',
            'params': {
                'sub_attacks': [
                    {'type': 'kerning', 'params': {'amount': -0.07}},
                    {'type': 'watermark_tiled', 'params': {'text': 'f(x)', 'color': 'gray!15', 'angle': 25}},
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
    log_filename = 'generalized_experiment_log.jsonl'
    if os.path.exists(log_filename):
        backup_name = f"{log_filename}.{int(time.time())}.bak"
        os.rename(log_filename, backup_name)
        print(f"Backed up existing log file to {backup_name}")

    for attack in attacks_to_run:
        variant_name = f"gen_variant_{attack['name']}_level{context_level}"
        print(f"\n\n{'='*20} PROCESSING ATTACK: {variant_name.upper()} {'='*20}")

        pdf_path = create_exam_variant(
            template_path=template_path,
            output_name=variant_name,
            attack_params=attack,
            context_level=context_level
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
                "context_level": context_level,
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Run generalized adversarial exam experiments')
    parser.add_argument('--template', type=str, default='ex1.tex', help='LaTeX template file path')
    parser.add_argument('--context-level', type=int, default=2, choices=[0, 1, 2, 3],
                        help='Context awareness level (0-3)')
    args = parser.parse_args()
    
    if not os.path.exists(args.template):
        print(f"ERROR: Template file '{args.template}' not found.")
    else:
        run_full_experiment(args.template, args.context_level)
