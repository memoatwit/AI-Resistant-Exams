#!/usr/bin/env python3
"""
Script to test uploaded images of printed attack PDFs against AI models.
This allows for physical testing - analyzing photos of printed attack pages.
"""

import os
import json
import argparse
import sys
from datetime import datetime
import glob

# Try to import the required modules
try:
    from exam_test import test_image_from_pdf, run_test_suite, DEFAULT_PROMPT, SOLVE_PROMPT, EXPLAIN_PROMPT
except ImportError:
    print("ERROR: Could not import exam_test module. Make sure it exists in the current directory.")
    sys.exit(1)
    
def test_uploaded_images(images_dir='attack_images', output_file='physical_test_results.jsonl', 
                        model_name='gemma3:4b', manifest_file=None):
    """
    Test uploaded images of printed attack PDFs against an AI model.
    
    Args:
        images_dir (str): Directory containing the uploaded images
        output_file (str): Path where the test results will be logged in JSONL format
        model_name (str): Name of the AI model to test against
        manifest_file (str): Optional path to a manifest file mapping image names to attack types
    """
    # Find all images in the specified directory
    image_extensions = ['*.jpg', '*.jpeg', '*.png']
    images = []
    for ext in image_extensions:
        images.extend(glob.glob(os.path.join(images_dir, ext)))
    
    if not images:
        print(f"No images found in directory: {images_dir}")
        print("Please place your images (jpg, jpeg, png) in this directory.")
        return
    
    # Load manifest if provided
    attack_mapping = {}
    if manifest_file and os.path.exists(manifest_file):
        print(f"Loading attack details from manifest: {manifest_file}")
        with open(manifest_file, 'r') as f:
            lines = f.readlines()
            
            current_file = None
            current_attack = {}
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('-'):
                    continue
                    
                if line.startswith('File:'):
                    # Save previous entry if exists
                    if current_file and current_attack:
                        base_name = os.path.splitext(current_file)[0]
                        attack_mapping[base_name] = current_attack
                    
                    # Start new entry
                    current_file = line.replace('File:', '').strip()
                    current_attack = {}
                elif line.startswith('Attack Name:'):
                    current_attack['name'] = line.replace('Attack Name:', '').strip()
                elif line.startswith('Attack Type:'):
                    current_attack['type'] = line.replace('Attack Type:', '').strip()
            
            # Save the last entry
            if current_file and current_attack:
                base_name = os.path.splitext(current_file)[0]
                attack_mapping[base_name] = current_attack
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    print(f"Starting image testing with model {model_name} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing {len(images)} images from: {images_dir}")
    print(f"Results will be logged to: {output_file}")
    
    # Define prompt types to test
    prompt_types = [
        {"name": "transcription", "prompt": DEFAULT_PROMPT},
        {"name": "solving", "prompt": SOLVE_PROMPT},
        {"name": "explanation", "prompt": EXPLAIN_PROMPT}
    ]
    
    # Test each image with each prompt type
    for image_path in images:
        image_name = os.path.basename(image_path)
        image_base = os.path.splitext(image_name)[0]
        
        print(f"\n--- Testing image: {image_name} ---")
        
        # Try to match with manifest
        attack_details = None
        for key in attack_mapping:
            if key in image_base or image_base in key:
                attack_details = attack_mapping[key]
                print(f"Matched image to attack: {attack_details['name']} ({attack_details['type']})")
                break
        
        if not attack_details:
            print(f"No attack mapping found for {image_name}. Using filename as identifier.")
            attack_details = {
                'name': image_base,
                'type': 'unknown'
            }
        
        for pt in prompt_types:
            print(f"Testing with {pt['name']} prompt...")
            
            try:
                # Test the image
                image_result = test_image_from_pdf(image_path, model_name, pt['prompt'])
                
                # Prepare results
                results = {
                    "pdf_variant": image_name,
                    "model_used": model_name,
                    "image_model_used": model_name,
                    "prompt": pt['prompt'],
                    "test_results": {
                        "image_input": image_result
                    },
                    "analysis": {
                        "image_test_failed": "Error:" in image_result,
                        "image_output_length": len(image_result)
                    }
                }
                
                # Add metadata
                entry = {
                    "attack_details": attack_details,
                    "context_level": 2,
                    "prompt_type": pt["name"],
                    "model": model_name,
                    "test_run_output": results,
                    "status": "success",
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "physical_test": True,
                    "image_path": image_path
                }
                
                # Save results to a dedicated file for this image
                results_filename = f"results_{image_base}_{pt['name']}.txt"
                with open(results_filename, "w") as f:
                    f.write(f"Test Results for {image_path}\n")
                    f.write(f"Model: {model_name}\n")
                    f.write(f"Prompt: {pt['prompt']}\n")
                    f.write("-" * 50 + "\n\n")
                    f.write("IMAGE ANALYSIS RESULTS:\n\n")
                    f.write(image_result)
                
                # Log the results
                with open(output_file, 'a') as f:
                    f.write(json.dumps(entry) + '\n')
                    
            except Exception as e:
                print(f"Error testing image {image_name} with {pt['name']} prompt: {str(e)}")
                
                # Log the error
                error_entry = {
                    "attack_details": attack_details,
                    "context_level": 2,
                    "prompt_type": pt["name"],
                    "model": model_name,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "physical_test": True,
                    "image_path": image_path
                }
                
                with open(output_file, 'a') as f:
                    f.write(json.dumps(error_entry) + '\n')
    
    print("\nAll image tests completed!")
    print(f"Results have been logged to {output_file}")
    print("To analyze results, run analyze_top_attacks.py on the log file.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test uploaded images of printed attack PDFs')
    parser.add_argument('--images-dir', type=str, default='attack_images',
                        help='Directory containing the uploaded images')
    parser.add_argument('--output-file', type=str, default='physical_test_results.jsonl',
                        help='Path where the test results will be logged')
    parser.add_argument('--model', type=str, default='gemma3:4b',
                        help='AI model to use for testing')
    parser.add_argument('--manifest', type=str, default='attack_pdfs/pdf_manifest.txt',
                        help='Path to a manifest file mapping image names to attack types')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.images_dir):
        print(f"WARNING: Images directory '{args.images_dir}' not found. Creating it now.")
        os.makedirs(args.images_dir, exist_ok=True)
        print(f"Please place your images in the '{args.images_dir}' directory and run this script again.")
    else:
        test_uploaded_images(
            images_dir=args.images_dir,
            output_file=args.output_file,
            model_name=args.model,
            manifest_file=args.manifest
        )
