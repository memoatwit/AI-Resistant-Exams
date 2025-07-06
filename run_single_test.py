#!/usr/bin/env python3

import os
from exam_attack import create_exam_variant
from exam_test import run_test_suite, DEFAULT_PROMPT

def run_single_test():
    """Run a single test to validate the experiment setup."""
    # Create just the baseline variant
    attack_params = {'type': 'none', 'params': {}}
    output_name = 'variant_test_baseline'
    
    print(f"\n=== Creating {output_name} PDF ===")
    pdf_path = create_exam_variant(
        template_path='exam_template.tex',
        output_name=output_name,
        attack_params=attack_params
    )
    
    if not pdf_path or not os.path.exists(pdf_path):
        print(f"Failed to generate PDF. Exiting.")
        return
    
    print(f"Successfully created: {pdf_path}")
    
    # Run a simple transcription test
    print(f"\n=== Testing with transcription prompt ===")
    result = run_test_suite(pdf_path=pdf_path, prompt=DEFAULT_PROMPT)
    
    print(f"\n=== Test Results ===")
    print(result)
    print("\nTest completed successfully.")

if __name__ == "__main__":
    run_single_test()
