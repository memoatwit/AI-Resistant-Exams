# run_experiment_v3.py
"""
Enhanced experiment runner for AI-resistant exam testing.
This script orchestrates the creation of various exam variants with different attack types
and tests them against specified AI models using different prompt strategies.
"""

import os
import json
import time
import sys
import itertools

from exam_attack_v3 import create_exam_variant

# Define default prompts that will be used if not available from exam_test
DEFAULT_PROMPT = "Transcribe the text from the document."
SOLVE_PROMPT = "Identify the main math or coding problem in this document and solve it. Show your work and explain your solution."
EXPLAIN_PROMPT = "Explain the concept being tested in this document and provide a detailed explanation of the problem and solution."

# Import the test suite and any available prompts
try:
    from exam_test import run_test_suite
    # Try to import prompts, but keep defaults if they're not defined there
    try:
        from exam_test import DEFAULT_PROMPT, SOLVE_PROMPT, EXPLAIN_PROMPT
    except ImportError:
        pass  # Use the defaults defined above
except ImportError:
    print("ERROR: Could not import exam_test module. Make sure it exists in the current directory.")
    sys.exit(1)

def run_full_experiment(template_path='exam_template.tex', log_file='full_experiment_log_v3.jsonl', 
                 model_name='gemma3:4b', attack_subset='all', optimization_mode=False, 
                 multi_model=False, auto_attack_selection=False, overnight_run=False):
    """
    Run a comprehensive experiment testing various AI-resistance techniques on LaTeX documents.
    
    Args:
        template_path (str): Path to the LaTeX template file to use as a base
        log_file (str): Path where the experiment results will be logged in JSONL format
        model_name (str): Name of the AI model to test against (or comma-separated list if multi_model=True)
        attack_subset (str): Category of attacks to run, or 'all' to run all attacks
        optimization_mode (bool): Whether to run parameter optimization (fine-tuning of parameters)
        multi_model (bool): Whether to test against multiple AI models
        auto_attack_selection (bool): Whether to use automated attack selection based on content
        overnight_run (bool): Set up for extended overnight run with more variations
        
    Returns:
        None: Results are saved to log file and individual result files
    """
    # Define all attacks
    all_attacks = [
        # --- BASELINE ---
        {'name': 'baseline_clean', 'type': 'none', 'params': {}},

        # --- EXPANDED WATERMARK TESTS ---
        {'name': 'A1a_watermark_light_text', 'type': 'watermark_tiled', 'params': {'text': 'CONFIDENTIAL', 'color': 'gray!10', 'size': 10, 'angle': 30, 'x_step': 6, 'y_step': 5}},
        {'name': 'A1b_watermark_dense_math', 'type': 'watermark_tiled', 'params': {'text': r'\int_0^\infty x^2 e^{-x} dx', 'color': 'gray!15', 'size': 6, 'angle': 15, 'x_step': 4, 'y_step': 3}},
        {'name': 'A1c_watermark_subtle_symbols', 'type': 'watermark_tiled', 'params': {'text': r'\alpha \beta \gamma', 'color': 'gray!8', 'size': 12, 'angle': 45, 'x_step': 5, 'y_step': 4}},

        # --- FINE-TUNING WATERMARK ATTACK ---
        # Varying Color (Contrast)
        {'name': 'F1a_watermark_color_vlight', 'type': 'watermark_tiled', 'params': {'text': 'DRAFT', 'color': 'gray!5', 'size': 10, 'angle': 30, 'x_step': 6, 'y_step': 5}},
        {'name': 'F1b_watermark_color_light', 'type': 'watermark_tiled', 'params': {'text': 'DRAFT', 'color': 'gray!10', 'size': 10, 'angle': 30, 'x_step': 6, 'y_step': 5}},
        {'name': 'F1c_watermark_color_medium', 'type': 'watermark_tiled', 'params': {'text': 'DRAFT', 'color': 'gray!15', 'size': 10, 'angle': 30, 'x_step': 6, 'y_step': 5}},
        # Varying Size
        {'name': 'F2a_watermark_size_small', 'type': 'watermark_tiled', 'params': {'text': 'DRAFT', 'color': 'gray!10', 'size': 6, 'angle': 30, 'x_step': 6, 'y_step': 5}},
        {'name': 'F2b_watermark_size_medium', 'type': 'watermark_tiled', 'params': {'text': 'DRAFT', 'color': 'gray!10', 'size': 10, 'angle': 30, 'x_step': 6, 'y_step': 5}},
        {'name': 'F2c_watermark_size_large', 'type': 'watermark_tiled', 'params': {'text': 'DRAFT', 'color': 'gray!10', 'size': 14, 'angle': 30, 'x_step': 6, 'y_step': 5}},

        # --- TEXT-BASED ATTACKS ---
        {'name': 'E1_homoglyph_attack', 'type': 'homoglyph', 'params': {'target': 'derivative'}},
        {'name': 'E2_ligature_disruption', 'type': 'ligature', 'params': {'target': 'function'}},
        {'name': 'E3_low_contrast_text', 'type': 'low_contrast', 'params': {'target': 'calculus', 'color': 'gray!75'}},

        # --- OTHER ATTACKS FROM V2 ---
        {'name': 'A2_texture_wave_pattern', 'type': 'texture', 'params': {'pattern': 'wave', 'color': 'gray!20', 'density': 0.4}},
        {'name': 'A3_layout_targeted_kerning', 'type': 'kerning', 'params': {'amount': -0.08, 'target': 'e^{x^2}'}},
        {'name': 'A4_font_symbol_swap', 'type': 'font_swap', 'params': {'symbol_to_swap': '=', 'font_name': 'Comic Sans MS'}},
        {'name': 'D1_stretch_equals', 'type': 'symbol_stretch', 'params': {'target': '=', 'stretch_amount': 2.0}},
        
        # --- NEW ADVANCED ATTACKS (SYMBOL STRETCHING) ---
        {'name': 'S1_stretch_integral', 'type': 'symbol_stretch', 'params': {'target': '\\int', 'stretch_amount': 1.8}},
        {'name': 'S2_stretch_sum', 'type': 'symbol_stretch', 'params': {'target': '\\sum', 'stretch_amount': 1.5}},
        {'name': 'S3_vertical_stretch_fraction', 'type': 'symbol_stretch', 'params': {'target': '\\frac', 'stretch_amount': 1.3, 'direction': 'vertical'}},
        
        # --- NEW MATH-SPECIFIC FONT SUBSTITUTIONS ---
        {'name': 'M1_calligraphy_variables', 'type': 'math_font', 'params': {'target_type': 'variables', 'font_style': '\\mathcal'}},
        {'name': 'M2_blackboard_numbers', 'type': 'math_font', 'params': {'target_type': 'numbers', 'font_style': '\\mathbb'}},
        {'name': 'M3_fraktur_operators', 'type': 'math_font', 'params': {'target_type': 'operators', 'font_style': '\\mathfrak'}},
        
        # --- CUSTOM ENVIRONMENT TARGETING ---
        {'name': 'E1_equation_border', 'type': 'custom_env', 'params': {'env': 'equation', 'effect': 'border', 'color': 'gray!30'}},
        {'name': 'E2_align_background', 'type': 'custom_env', 'params': {'env': 'align', 'effect': 'background', 'color': 'gray!5'}},
        {'name': 'E3_matrix_spacing', 'type': 'custom_env', 'params': {'env': 'matrix', 'effect': 'spacing', 'amount': 1.2}},
        
        # --- TARGETED NOISE INJECTION ---
        {'name': 'N1_noise_near_equals', 'type': 'noise_injection', 'params': {'target': '=', 'noise_density': 0.3, 'noise_radius': 0.15}},
        {'name': 'N2_noise_around_integrals', 'type': 'noise_injection', 'params': {'target': '\\int', 'noise_density': 0.5, 'noise_radius': 0.2}},
        {'name': 'N3_noise_at_subscripts', 'type': 'noise_injection', 'params': {'target': '_', 'noise_density': 0.4, 'noise_radius': 0.1}},
        
        # --- PARAMETER-OPTIMIZED ATTACKS ---
        {'name': 'O1_optimized_watermark', 'type': 'watermark_tiled', 'params': {'text': r'\nabla^2 f', 'color': 'gray!7.5', 'size': 8, 'angle': 22, 'x_step': 5, 'y_step': 4}},
        {'name': 'O2_optimized_texture', 'type': 'texture', 'params': {'pattern': 'wave', 'color': 'gray!18', 'density': 0.35}},
        {'name': 'O3_optimized_kerning', 'type': 'kerning', 'params': {'amount': -0.075, 'target': '\\lim_{x \\to \\infty}'}},

        # --- COMBINATION ATTACKS ---
        {'name': 'B1_combo_kerning_and_dense_lines', 'type': 'combo', 'params': {'sub_attacks': [
            {'type': 'kerning', 'params': {'amount': -0.08, 'target': 'e^{x^2}'}}, 
            {'type': 'texture', 'params': {'pattern': 'lines', 'density': 0.5, 'color': 'gray!18'}}
        ]}},
        {'name': 'C1_combo_kitchen_sink', 'type': 'combo', 'params': {'sub_attacks': [
            {'type': 'kerning', 'params': {'amount': -0.07, 'target': 'sin(3x)'}}, 
            {'type': 'watermark_tiled', 'params': {'text': 'f(x)', 'color': 'gray!15', 'angle': 25, 'x_step': 6, 'y_step': 5}}, 
            {'type': 'texture', 'params': {'pattern': 'dots', 'density': 1.0, 'color': 'gray!12'}}
        ]}},
        
        # --- NEW COMBINATIONS WITH NEW ATTACK TYPES ---
        {'name': 'C2_combo_stretch_and_noise', 'type': 'combo', 'params': {'sub_attacks': [
            {'type': 'symbol_stretch', 'params': {'target': '\\int', 'stretch_amount': 1.8}},
            {'type': 'noise_injection', 'params': {'target': '=', 'noise_density': 0.3, 'noise_radius': 0.15}}
        ]}},
        {'name': 'C3_combo_env_and_font', 'type': 'combo', 'params': {'sub_attacks': [
            {'type': 'custom_env', 'params': {'env': 'equation', 'effect': 'background', 'color': 'gray!8'}},
            {'type': 'math_font', 'params': {'target_type': 'variables', 'font_style': '\\mathcal'}}
        ]}},
        {'name': 'C4_combo_triple_threat', 'type': 'combo', 'params': {'sub_attacks': [
            {'type': 'watermark_tiled', 'params': {'text': r'\partial f/\partial x', 'color': 'gray!12', 'size': 9, 'angle': 33, 'x_step': 7, 'y_step': 5}},
            {'type': 'kerning', 'params': {'amount': -0.06, 'target': '\\lim'}},
            {'type': 'noise_injection', 'params': {'target': '^', 'noise_density': 0.25, 'noise_radius': 0.12}}
        ]}}
    ]
    
    # Add parameter optimization attacks if in optimization mode
    if optimization_mode or overnight_run:
        # Create fine-tuning combinations for watermarks
        watermark_texts = [r'\nabla \cdot F', r'\oint_C F \cdot ds', r'\mathbb{R}^n', r'\forall \epsilon > 0']
        watermark_colors = ['gray!6', 'gray!8', 'gray!10', 'gray!12']
        watermark_sizes = [7, 9, 11, 13]
        watermark_angles = [18, 27, 36, 45]
        
        opt_counter = 1
        for text, color, size, angle in itertools.product(watermark_texts[:2], watermark_colors[:2], watermark_sizes[:2], watermark_angles[:2]):
            if overnight_run or opt_counter <= 5:  # Limit to 5 combinations if not overnight
                all_attacks.append({
                    'name': f'OPT{opt_counter}_watermark_tuned',
                    'type': 'watermark_tiled',
                    'params': {
                        'text': text,
                        'color': color,
                        'size': size,
                        'angle': angle,
                        'x_step': 5,
                        'y_step': 4
                    }
                })
                opt_counter += 1
                
        # Create fine-tuning combinations for textures
        texture_patterns = ['dots', 'lines', 'wave']
        texture_colors = ['gray!8', 'gray!12', 'gray!16', 'gray!20']
        texture_densities = [0.3, 0.5, 0.7, 0.9]
        
        opt_counter = 1
        for pattern, color, density in itertools.product(texture_patterns, texture_colors[:2], texture_densities[:2]):
            if overnight_run or opt_counter <= 5:  # Limit to 5 combinations if not overnight
                all_attacks.append({
                    'name': f'OPT{opt_counter + 10}_texture_tuned',
                    'type': 'texture',
                    'params': {
                        'pattern': pattern,
                        'color': color,
                        'density': density
                    }
                })
                opt_counter += 1
    
    # Filter attacks based on subset
    if attack_subset != 'all':
        filtered_attacks = []
        # Always include baseline
        filtered_attacks.append(all_attacks[0])
        
        # Filter by type
        for attack in all_attacks[1:]:  # Skip baseline which we already added
            if attack_subset == 'watermark' and 'watermark' in attack['type']:
                filtered_attacks.append(attack)
            elif attack_subset == 'texture' and attack['type'] == 'texture':
                filtered_attacks.append(attack)
            elif attack_subset == 'kerning' and attack['type'] == 'kerning':
                filtered_attacks.append(attack)
            elif attack_subset == 'font' and (attack['type'] == 'font_swap' or attack['type'] == 'math_font'):
                filtered_attacks.append(attack)
            elif attack_subset == 'text' and attack['type'] in ['homoglyph', 'ligature', 'low_contrast']:
                filtered_attacks.append(attack)
            elif attack_subset == 'stretch' and attack['type'] == 'symbol_stretch':
                filtered_attacks.append(attack)
            elif attack_subset == 'noise' and attack['type'] == 'noise_injection':
                filtered_attacks.append(attack)
            elif attack_subset == 'env' and attack['type'] == 'custom_env':
                filtered_attacks.append(attack)
            elif attack_subset == 'opt' and attack['name'].startswith('OPT'):
                filtered_attacks.append(attack)
            elif attack_subset == 'combo' and attack['type'] == 'combo':
                filtered_attacks.append(attack)
            elif attack_subset == 'new' and attack['type'] in ['symbol_stretch', 'math_font', 'custom_env', 'noise_injection']:
                filtered_attacks.append(attack)
        
        attacks_to_run = filtered_attacks
        print(f"Running subset of attacks: {attack_subset} ({len(attacks_to_run)} attacks)")
    else:
        # For overnight runs, include all attacks
        if overnight_run:
            attacks_to_run = all_attacks
            print(f"OVERNIGHT RUN: Running all attacks ({len(attacks_to_run)} attacks)")
        else:
            # For normal runs, exclude optimization attacks unless specifically requested
            if not optimization_mode:
                attacks_to_run = [attack for attack in all_attacks if not attack['name'].startswith('OPT')]
                print(f"Running standard attacks ({len(attacks_to_run)} attacks)")
            else:
                attacks_to_run = all_attacks
                print(f"Running all attacks including optimization variants ({len(attacks_to_run)} attacks)")

    prompts_to_test = {
        "transcription": DEFAULT_PROMPT,
        "solving": SOLVE_PROMPT,
        "explanation": EXPLAIN_PROMPT,
    }
    
    # If testing multiple models, split the model string by commas
    models_to_test = [model_name]
    if multi_model and ',' in model_name:
        models_to_test = [model.strip() for model in model_name.split(',')]
        print(f"Testing against multiple models: {models_to_test}")

    # For automated attack selection, analyze the template content
    attack_recommendations = {}
    if auto_attack_selection:
        try:
            print("Analyzing template content for automated attack selection...")
            with open(template_path, 'r') as f:
                template_content = f.read()
                
            # Simple content analysis to recommend attacks
            # This is a basic implementation - a more sophisticated one would use NLP/ML
            if '\\int' in template_content or '\\sum' in template_content:
                attack_recommendations['calculus'] = ['watermark_tiled', 'symbol_stretch']
            if '\\frac' in template_content:
                attack_recommendations['fractions'] = ['math_font', 'kerning']
            if '\\begin{equation}' in template_content or '\\begin{align}' in template_content:
                attack_recommendations['equations'] = ['custom_env', 'noise_injection']
                
            print(f"Automated attack recommendations: {attack_recommendations}")
        except Exception as e:
            print(f"Error in automated attack selection: {str(e)}")

    log_filename = log_file
    if os.path.exists(log_filename):
        backup_name = f"{log_filename}.{int(time.time())}.bak"
        os.rename(log_filename, backup_name)
        print(f"Backed up existing log file to {backup_name}")
        
    # Setup progress tracking for overnight runs
    total_attacks = len(attacks_to_run)
    total_models = len(models_to_test)
    total_prompts = len(prompts_to_test)
    total_tests = total_attacks * total_models * total_prompts
    test_counter = 0
    start_time = time.time()
    
    print(f"\n{'='*60}")
    if overnight_run:
        print("OVERNIGHT RUN CONFIGURED")
        print(f"Total tests to run: {total_tests} ({total_attacks} attacks × {total_models} models × {total_prompts} prompts)")
        print("Estimated completion time will be calculated after first test...")
    print(f"{'='*60}\n")

    for attack in attacks_to_run:
        variant_name = f"variant_{attack['name']}"
        print(f"\n\n{'='*20} PROCESSING ATTACK: {variant_name.upper()} {'='*20}")

        try:
            pdf_path = create_exam_variant(
                template_path=template_path,
                output_name=variant_name,
                attack_params=attack
            )

            if not pdf_path or not os.path.exists(pdf_path):
                print(f"!!!!!! FAILED to generate PDF for {variant_name}. Skipping. !!!!!!")
                # Log the failure to the experiment log
                error_entry = {
                    "attack_details": attack,
                    "status": "failed",
                    "error": "PDF generation failed",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(log_file, 'a') as f:
                    f.write(json.dumps(error_entry) + '\n')
                continue
        except Exception as e:
            print(f"!!!!!! EXCEPTION during PDF generation for {variant_name}: {str(e)} !!!!!!")
            # Log the exception to the experiment log
            error_entry = {
                "attack_details": attack,
                "status": "error",
                "error": f"Exception: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(log_file, 'a') as f:
                f.write(json.dumps(error_entry) + '\n')
            continue

        print(f"Successfully generated PDF: {pdf_path}")
        
        # Test against all selected models
        for current_model in models_to_test:
            print(f"\n--- Testing with model: {current_model} ---")
            
            for prompt_name, prompt_text in prompts_to_test.items():
                test_counter += 1  # Increment test counter
                
                # Calculate and display progress for overnight runs
                if overnight_run and test_counter > 1:
                    elapsed_time = time.time() - start_time
                    time_per_test = elapsed_time / (test_counter - 1)
                    tests_remaining = total_tests - test_counter + 1
                    est_remaining_time = tests_remaining * time_per_test
                    
                    # Convert to hours, minutes, seconds
                    hours, remainder = divmod(est_remaining_time, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    progress_pct = (test_counter - 1) / total_tests * 100
                    print(f"\nProgress: {progress_pct:.1f}% complete ({test_counter-1}/{total_tests})")
                    print(f"Estimated time remaining: {int(hours)}h {int(minutes)}m {int(seconds)}s")
                
                print(f"\n--- Testing '{variant_name}' with model '{current_model}' and prompt: '{prompt_name.upper()}' ---")
                try:
                    result_data = run_test_suite(pdf_path=pdf_path, model_name=current_model, prompt=prompt_text)

                    log_entry = {
                        "attack_details": attack,
                        "model": current_model,
                        "prompt_type": prompt_name,
                        "test_run_output": result_data,
                        "status": "success",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }

                    with open(log_filename, 'a') as f:
                        f.write(json.dumps(log_entry) + '\n')

                    print(f"--- Completed test for '{prompt_name}' with model '{current_model}'. Master log updated. ---")
                    
                    # For overnight runs, add a small delay between tests to avoid API rate limits
                    if overnight_run:
                        time.sleep(2)
                        
                except Exception as e:
                    print(f"!!! ERROR running test suite for '{prompt_name}' with model '{current_model}': {str(e)} !!!")
                    error_entry = {
                        "attack_details": attack,
                        "model": current_model,
                        "prompt_type": prompt_name,
                        "status": "error",
                        "error_message": str(e),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    with open(log_filename, 'a') as f:
                        f.write(json.dumps(error_entry) + '\n')

    # Calculate total run time
    total_run_time = time.time() - start_time
    hours, remainder = divmod(total_run_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    print(f"\n\n{'*'*20} EXPERIMENT COMPLETE {'*'*20}")
    print(f"Total runtime: {int(hours)}h {int(minutes)}m {int(seconds)}s")
    print(f"Completed {test_counter} test combinations across {len(attacks_to_run)} attacks")
    print("All attacks processed. Individual results are in '.txt' files.")
    print(f"A complete, structured log for analysis is saved to: {log_filename}")
    
    # Provide basic analysis of results for overnight runs
    if overnight_run:
        try:
            print("\n--- Quick Results Analysis ---")
            attack_effectiveness = {}
            
            with open(log_filename, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    if 'status' in entry and entry['status'] == 'success':
                        attack_name = entry['attack_details']['name']
                        if 'test_run_output' in entry and 'success_rate' in entry['test_run_output']:
                            success_rate = entry['test_run_output']['success_rate']
                            
                            if attack_name not in attack_effectiveness:
                                attack_effectiveness[attack_name] = []
                            
                            attack_effectiveness[attack_name].append(success_rate)
            
            # Calculate average success rate for each attack
            for attack_name, rates in attack_effectiveness.items():
                avg_rate = sum(rates) / len(rates) if rates else 0
                print(f"{attack_name}: Average AI Success Rate = {avg_rate:.2f}%")
                
            print("\nLower success rates indicate more effective attacks at preventing AI from reading content.")
            print("For detailed analysis, run analyze_generalized_results_v2.py on the log file.")
        except Exception as e:
            print(f"Error during results analysis: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run enhanced AI-resistant exam experiments')
    parser.add_argument('--template', type=str, default='exam_template.tex', 
                        help='LaTeX template file path')
    parser.add_argument('--log-file', type=str, default='full_experiment_log_v3.jsonl',
                        help='Path to the output log file')
    parser.add_argument('--model', type=str, default='gemma3:4b',
                        help='AI model to use for testing (comma-separated for multiple models)')
    parser.add_argument('--subset', choices=['watermark', 'texture', 'kerning', 'font', 'text', 'combo', 
                                           'stretch', 'noise', 'env', 'opt', 'new', 'all'], 
                        default='all', help='Only run a subset of attacks')
    parser.add_argument('--optimize', action='store_true',
                        help='Run parameter optimization (fine-tuning) attacks')
    parser.add_argument('--multi-model', action='store_true',
                        help='Test against multiple AI models specified in --model (comma-separated)')
    parser.add_argument('--auto-select', action='store_true',
                        help='Use automated attack selection based on content type')
    parser.add_argument('--overnight', action='store_true',
                        help='Set up for extended overnight run with more variations')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.template):
        print(f"ERROR: Template file '{args.template}' not found.")
    else:
        # Run the experiment with all specified options
        run_full_experiment(
            template_path=args.template,
            log_file=args.log_file,
            model_name=args.model,
            attack_subset=args.subset,
            optimization_mode=args.optimize,
            multi_model=args.multi_model,
            auto_attack_selection=args.auto_select,
            overnight_run=args.overnight
        )
