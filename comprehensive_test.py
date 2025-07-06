#!/usr/bin/env python3
# comprehensive_test.py
#
# This script tests the generalized attack framework against all sample exams
# to evaluate effectiveness across different exam types

import os
import subprocess
from glob import glob
import json
import time
from pathlib import Path
from generalized_attack import create_exam_variant, DocumentAnalyzer

# Test configuration
CONTEXT_LEVEL = 3  # Use highest context awareness level
TEST_ATTACKS = [
    {'name': 'watermark_tiled', 'type': 'watermark_tiled', 'params': {}},
    {'name': 'texture_wave', 'type': 'texture', 'params': {'pattern': 'wave'}},
    {'name': 'kerning', 'type': 'kerning', 'params': {}},
    {'name': 'font_swap', 'type': 'font_swap', 'params': {}},
    {'name': 'background_color', 'type': 'background_color', 'params': {'color': 'blue!2'}},
    {'name': 'combo_kitchen_sink', 'type': 'combo', 'params': {
        'sub_attacks': [
            {'type': 'kerning', 'params': {'amount': -0.07}},
            {'type': 'watermark_tiled', 'params': {'text': 'f(x)', 'color': 'gray!15', 'angle': 25}},
            {'type': 'texture', 'params': {'pattern': 'dots', 'density': 0.8, 'color': 'gray!12'}}
        ]
    }}
]

def analyze_tex_file(tex_path):
    """Analyze a TeX file and return summary of its contents"""
    print(f"\nAnalyzing {tex_path}...")
    with open(tex_path, 'r') as f:
        content = f.read()
    
    analyzer = DocumentAnalyzer(content)
    subject = analyzer.get_subject_hint()
    
    print(f"- Subject detected: {subject}")
    print(f"- Has figures: {analyzer.has_figures}")
    print(f"- Has complex math: {analyzer.has_complex_math}")
    print(f"- Math environments found: {len(analyzer.math_environments)}")
    print(f"- Math expressions found: {len(analyzer.math_expressions)}")
    
    return {
        "path": tex_path,
        "subject": subject,
        "has_figures": analyzer.has_figures,
        "has_complex_math": analyzer.has_complex_math,
        "math_env_count": len(analyzer.math_environments),
        "math_expr_count": len(analyzer.math_expressions),
        "targets": analyzer.get_target_math_for_attacks()
    }

def find_all_tex_files():
    """Find all TeX files in the exam folders"""
    exams = [
        "/Users/memo/Documents/act/CoF AI paper exam 1 (ML)",
        "/Users/memo/Documents/act/CoF AI paper exam 2 (Multivariable calculus)",
        "/Users/memo/Documents/act/CoF AI paper exam 4 (Discrete math)",
        "/Users/memo/Documents/act/CoFAI paper exam 3 (Complex analysis)"
    ]
    
    tex_files = []
    for exam_folder in exams:
        # Find all .tex files in the exam folder
        tex_files.extend(glob(f"{exam_folder}/*.tex"))
    
    # Add our ex1.tex file
    tex_files.append("/Users/memo/Documents/act/ex1.tex")
    return tex_files

def test_attack_on_file(tex_path, attack, context_level=3):
    """Test a specific attack on a TeX file"""
    output_name = f"test_{Path(tex_path).stem}_{attack['name']}"
    print(f"\nTesting {attack['name']} on {tex_path}...")
    
    result = create_exam_variant(
        template_path=tex_path,
        output_name=output_name,
        attack_params=attack,
        context_level=context_level
    )
    
    success = result is not None and os.path.exists(result)
    print(f"Attack successful: {success}")
    return {
        "tex_file": tex_path,
        "attack": attack['name'],
        "success": success,
        "output": result,
        "context_level": context_level
    }

def main():
    """Run comprehensive tests on all TeX files"""
    results_file = "comprehensive_test_results.jsonl"
    
    # Find all TeX files
    tex_files = find_all_tex_files()
    print(f"Found {len(tex_files)} TeX files to test")
    
    # Analyze each file
    analyses = []
    for tex_path in tex_files:
        analysis = analyze_tex_file(tex_path)
        analyses.append(analysis)
    
    # Save analyses
    with open("tex_file_analyses.json", "w") as f:
        json.dump(analyses, f, indent=2)
    
    print("\n--- Starting Attack Tests ---")
    results = []
    
    for tex_path in tex_files:
        for attack in TEST_ATTACKS:
            result = test_attack_on_file(tex_path, attack, CONTEXT_LEVEL)
            results.append(result)
            
            # Write results incrementally to avoid data loss
            with open(results_file, "a") as f:
                f.write(json.dumps(result) + "\n")
    
    # Count successes
    success_count = sum(1 for r in results if r['success'])
    print(f"\nTest Summary: {success_count}/{len(results)} attacks successful")
    print(f"Detailed results saved to: {results_file}")

if __name__ == "__main__":
    main()
