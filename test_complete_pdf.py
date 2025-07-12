#!/usr/bin/env python3
"""
A test script to verify that the complete template is being used in the generated PDFs
"""

import os
import sys
import shutil
from exam_attack_v3 import create_exam_variant

def test_complete_pdf(template_path='ex1_shorter.tex', 
                     output_dir='test_pdf_output'):
    """
    Test that the complete template with all problems is rendered correctly
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Define a simple texture attack
    test_attack = {
        'name': 'O2_optimized_texture_test',
        'type': 'texture', 
        'params': {
            'pattern': 'grid', 
            'color': 'gray!40', 
            'density': 0.6, 
            'line_width': 0.4
        }
    }
    
    # Copy all resource directories needed for figures
    dirname = os.path.dirname(template_path)
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
                # If symlink fails, try copying
                print(f"Symlink failed: {e}. Attempting to copy directory.")
                if os.path.isdir(src_dir):
                    shutil.copytree(src_dir, dst_dir)
    
    # Create the attack variant
    output_path = os.path.join(output_dir, 'test_complete_template')
    print(f"\nTesting with template: {template_path}")
    print(f"Output will be saved to: {output_path}.pdf")
    
    # Create the attack variant
    pdf_path = create_exam_variant(
        template_path=template_path,
        output_name=output_path,
        attack_params=test_attack
    )
    
    if pdf_path:
        print(f"Success! Generated PDF: {pdf_path}")
        print("Please open this PDF and verify that ALL problems from the template appear.")
    else:
        print("Failed to generate PDF.")

if __name__ == "__main__":
    # Use ex1_shorter.tex as the default template if available
    default_template = 'ex1_shorter.tex'
    if len(sys.argv) > 1:
        template_path = sys.argv[1]
    else:
        template_path = default_template if os.path.exists(default_template) else 'exam_template.tex'
    
    test_complete_pdf(template_path=template_path)
