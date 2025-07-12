#!/usr/bin/env python3
"""
Script to generate PDFs for the top 10 most effective attacks without running AI tests.
This allows for physical testing - printing the PDFs, taking photos, and testing those images.
"""

import os
import argparse
import sys
from datetime import datetime

# Try to import the required modules
try:
    from exam_attack_v3 import create_exam_variant
except ImportError:
    print("ERROR: Could not import exam_attack_v3 module. Make sure it exists in the current directory.")
    sys.exit(1)

def generate_attack_pdfs(template_path='exam_template.tex', output_dir='attack_pdfs'):
    """
    Generate PDFs for the top 10 most effective attacks.
    
    Args:
        template_path (str): Path to the LaTeX template file to use as a base
        output_dir (str): Directory to save the generated PDFs
    """
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
         'params': {'pattern': 'grid', 'color': 'gray!12', 'density': 0.5, 'line_width': 0.2}},
        
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
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting PDF generation for top 10 attacks on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using template: {template_path}")
    print(f"Saving PDFs to: {output_dir}")
    
    # Generate PDFs for each attack
    for attack in all_attacks:
        print(f"\n--- Generating PDF for attack: {attack['name']} ({attack['type']}) ---")
        
        try:
            # Create the attack variant
            # Make sure we don't add .tex twice
            attack_name_clean = attack['name'].replace('.tex', '')
            variant_filename = f"{output_dir}/variant_{attack_name_clean}.tex"
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
            
            # Compile the LaTeX file
            print(f"Compiling {variant_filename}...")
            compile_cmd = f"lualatex -interaction=nonstopmode -output-directory={output_dir} {variant_filename}"
            os.system(compile_cmd)
            
            # Run twice for proper cross-references
            os.system(compile_cmd)
            
            if not os.path.exists(pdf_path):
                print(f"Error: Failed to create PDF for {variant_filename}")
                continue
            
            print(f"Successfully generated: {pdf_path}")
            
        except Exception as e:
            print(f"Error with attack {attack['name']}: {str(e)}")
    
    # Create a manifest file listing all generated PDFs and their attack types
    manifest_path = f"{output_dir}/pdf_manifest.txt"
    with open(manifest_path, 'w') as f:
        f.write("Generated Attack PDFs Manifest\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Template used: {template_path}\n")
        f.write("-" * 60 + "\n\n")
        
        for attack in all_attacks:
            pdf_name = f"variant_{attack['name']}.pdf"
            f.write(f"File: {pdf_name}\n")
            f.write(f"Attack Name: {attack['name']}\n")
            f.write(f"Attack Type: {attack['type']}\n")
            if attack['type'] != 'none':
                f.write(f"Attack Parameters: {str(attack['params'])}\n")
            f.write("\n")
    
    print("\nAll PDFs generated!")
    print(f"PDFs and manifest saved to the '{output_dir}' directory")
    print(f"Manifest file: {manifest_path}")
    print("\nNext steps for physical testing:")
    print("1. Print the generated PDFs")
    print("2. Take photos of the printed pages")
    print("3. Use test_uploaded_images.py to test these photos")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate PDFs for top 10 most effective AI-resistant exam attacks')
    parser.add_argument('--template', type=str, default='exam_template.tex', 
                        help='LaTeX template file path')
    parser.add_argument('--output-dir', type=str, default='attack_pdfs',
                        help='Directory to save the generated PDFs')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.template):
        print(f"ERROR: Template file '{args.template}' not found.")
    else:
        generate_attack_pdfs(
            template_path=args.template,
            output_dir=args.output_dir
        )
