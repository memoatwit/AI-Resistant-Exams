# exam_test.py
#
# This script is responsible for testing a single generated PDF exam variant
# against a local AI model using two different methods:
#   1. Direct PDF Input: Simulates an AI with internal PDF parsing capabilities.
#   2. Image Input: Simulates a student taking a photo of a physical exam.
#
# It is designed to be called by a master orchestrator script.

import os
import subprocess
import base64
import ollama
from pdf2image import convert_from_path

# --- Configuration ---
# Use the model you have running, e.g., 'gemma3:4b', 'llava'
DEFAULT_MODEL = 'gemma3:4b'  # Updated to gemma3:4b which is confirmed working
DEFAULT_VISION_MODEL = 'gemma3:4b'  # Use the same model for vision
# Different prompts for the AI
DEFAULT_PROMPT = "Transcribe the text from the document."
SOLVE_PROMPT = "Identify the main math or coding problem in this document and solve it. Show your work and explain your solution."
EXPLAIN_PROMPT = "Explain the concept being tested in this document and provide a detailed explanation of the problem and solution."

IMAGE_DPI = 300 # Simulates a decent quality phone camera resolution

def check_vision_capability(model_name: str) -> bool:
    """
    Check if a model supports vision by looking at known vision models
    """
    vision_models = ['llava', 'bakllava', 'llava-phi3', 'llava-llama3', 'moondream', 'cogvlm', 'gemma']
    return any(vm in model_name.lower() for vm in vision_models)

def test_direct_pdf(pdf_path: str, model_name: str, prompt: str) -> str:
    """
    Tests the AI by feeding it the PDF file directly via the command line.
    This method bypasses visual OCR for models that can parse PDF structure.
    """
    print(f"  [TESTING] Direct PDF input for: {pdf_path}")
    if not os.path.exists(pdf_path):
        return "Error: PDF file not found."

    try:
        # We use subprocess here to replicate the user's command `ollama run model "prompt" /path/to/file`
        # as the Python library doesn't have a direct file path argument in the same way.
        command = ['ollama', 'run', model_name, prompt, pdf_path]
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120 # Add a timeout to prevent hangs
        )
        if process.returncode == 0:
            print("  [SUCCESS] Direct PDF test completed.")
            return process.stdout.strip()
        else:
            print(f"  [ERROR] Ollama CLI returned an error: {process.stderr}")
            return f"Error from Ollama CLI: {process.stderr.strip()}"
    except FileNotFoundError:
        return "Error: 'ollama' command not found. Is Ollama installed and in your PATH?"
    except Exception as e:
        print(f"  [ERROR] An unexpected error occurred during direct PDF test: {e}")
        return f"Error: {e}"

def test_image_from_pdf(pdf_path: str, model_name: str, prompt: str) -> str:
    """
    Tests the AI by converting the PDF to an image first.
    This correctly simulates the real-world threat model of a student taking a photo.
    """
    print(f"  [TESTING] Image input for: {pdf_path}")
    if not os.path.exists(pdf_path):
        return "Error: PDF file not found."

    temp_image_path = "temp_exam_page_for_testing.png"
    
    try:
        # 1. Convert PDF to image
        images = convert_from_path(pdf_path, dpi=IMAGE_DPI)
        if not images:
            return "Error: pdf2image failed to convert the PDF."
        
        images[0].save(temp_image_path, "PNG")
        print(f"  [INFO] Image saved to {temp_image_path} ({images[0].size})")
        
        # 2. Enhanced prompt for vision models
        vision_prompt = f"{prompt} I am providing you with an image of a document. Please analyze the visual content of this image."
        
        # 3. Call Ollama with the image - using the working format for gemma3:4b
        try:
            # Using the format that's confirmed to work with gemma3:4b
            response = ollama.chat(
                model=model_name,
                messages=[{
                    'role': 'user',
                    'content': vision_prompt,
                    'images': [temp_image_path]  # Pass the image path directly
                }]
            )
            print("  [SUCCESS] Image test completed.")
            return response['message']['content']
        except Exception as api_error:
            print(f"  [WARNING] Vision API failed with {model_name}: {api_error}")
            
            # Try command line approach as fallback
            try:
                print("  [INFO] Trying command line approach...")
                cmd = ['ollama', 'run', model_name, f"{vision_prompt}: {temp_image_path}"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print("  [SUCCESS] Image test completed via command line.")
                    return result.stdout.strip()
                else:
                    return f"Error: Command line approach failed: {result.stderr}"
            except Exception as cmd_error:
                return f"Error: All approaches failed. API error: {api_error}. Command line error: {cmd_error}"

    except Exception as e:
        print(f"  [ERROR] An unexpected error occurred during image test: {e}")
        return f"Error: {e}"
    finally:
        # 4. We don't remove the temporary image for debugging purposes
        if os.path.exists(temp_image_path):
            print(f"  [INFO] Temporary image saved at {temp_image_path}")
            # If you want to automatically clean up, uncomment the code below
            # os.remove(temp_image_path)

def run_test_suite(pdf_path: str, model_name: str = DEFAULT_MODEL, prompt: str = DEFAULT_PROMPT) -> dict:
    """
    Runs an image-based test on a single PDF file.
    
    Returns a dictionary containing the results and metadata.
    """
    print(f"\n--- Starting Test Suite for: {os.path.basename(pdf_path)} ---")
    print(f"Using model: {model_name}")
    
    # Check if the model supports vision
    is_vision_model = check_vision_capability(model_name)
    print(f"Vision capability detected for {model_name}: {is_vision_model}")
    
    # Run the image-based test (use vision model if current model doesn't support vision)
    image_model = model_name if is_vision_model else DEFAULT_VISION_MODEL
    if image_model != model_name:
        print(f"  [INFO] Using {image_model} for image processing as {model_name} may not support vision")
    
    image_result = test_image_from_pdf(pdf_path, image_model, prompt)
    
    results = {
        "pdf_variant": os.path.basename(pdf_path),
        "model_used": model_name,
        "image_model_used": image_model,
        "prompt": prompt,
        "test_results": {
            "image_input": image_result
        },
        "analysis": {
            "image_test_failed": "Error:" in image_result,
            "image_output_length": len(image_result)
        }
    }
    
    print(f"--- Test Suite for {os.path.basename(pdf_path)} Finished ---")
    
    # Save the results to a file - use a prompt-specific name
    prompt_type = "transcription"
    if "solve" in prompt.lower():
        prompt_type = "solving"
    elif "explain" in prompt.lower():
        prompt_type = "explanation"
        
    results_filename = f"results_{os.path.splitext(os.path.basename(pdf_path))[0]}_{prompt_type}.txt"
    with open(results_filename, "w") as f:
        f.write(f"Test Results for {pdf_path}\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Prompt: {prompt}\n")
        f.write("-" * 50 + "\n\n")
        f.write("IMAGE ANALYSIS RESULTS:\n\n")
        f.write(image_result)
    
    print(f"Results saved to {results_filename}")
    
    return results

# This block allows you to run this script directly to test a single file
if __name__ == '__main__':
    # --- Execute the test suite ---
    # Define the PDF file to test
    TEST_PDF = 'ex0.pdf'
    
    if not os.path.exists(TEST_PDF):
        print(f"Error: PDF file '{TEST_PDF}' does not exist.")
        exit(1)
    
    # Run different prompts to get a range of outputs
    print("\n=== RUNNING TRANSCRIPTION TEST ===")
    transcription_results = run_test_suite(TEST_PDF, DEFAULT_MODEL, DEFAULT_PROMPT)
    
    print("\n=== RUNNING PROBLEM SOLVING TEST ===")
    solving_results = run_test_suite(TEST_PDF, DEFAULT_MODEL, SOLVE_PROMPT)
    
    print("\n=== RUNNING EXPLANATION TEST ===")
    explanation_results = run_test_suite(TEST_PDF, DEFAULT_MODEL, EXPLAIN_PROMPT)
    
    # --- Print a summary of the results ---
    print("\n\n" + "="*20 + " TEST SUMMARY " + "="*20)
    print(f"File Tested: {TEST_PDF}")
    print(f"Model Used: {DEFAULT_MODEL}")
    print("-" * 54)
    print("TRANSCRIPTION OUTPUT:")
    print("-" * 20)
    print(transcription_results['test_results']['image_input'][:500] + "..." if len(transcription_results['test_results']['image_input']) > 500 else transcription_results['test_results']['image_input'])
    print("\nSOLVING OUTPUT:")
    print("-" * 20)
    print(solving_results['test_results']['image_input'][:500] + "..." if len(solving_results['test_results']['image_input']) > 500 else solving_results['test_results']['image_input'])
    print("\nEXPLANATION OUTPUT:")
    print("-" * 20)
    print(explanation_results['test_results']['image_input'][:500] + "..." if len(explanation_results['test_results']['image_input']) > 500 else explanation_results['test_results']['image_input'])
    print("="*54)
    
    print("\nDetailed results have been saved to:")
    print(f"- results_{os.path.splitext(os.path.basename(TEST_PDF))[0]}_transcription.txt")
    print(f"- results_{os.path.splitext(os.path.basename(TEST_PDF))[0]}_solving.txt")
    print(f"- results_{os.path.splitext(os.path.basename(TEST_PDF))[0]}_explanation.txt")