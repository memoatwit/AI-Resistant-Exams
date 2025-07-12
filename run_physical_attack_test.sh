#!/bin/bash
# run_physical_attack_test.sh
# Script to orchestrate physical attack testing - generating PDFs, guiding through the photo taking process,
# testing the photos, and analyzing the results

# Set default values
TEMPLATE="exam_template.tex"
MODEL="gemma3:4b"
PDF_DIR="attack_pdfs_0712"
IMG_DIR="attack_images_0712"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --template=*)
      TEMPLATE="${1#*=}"
      shift
      ;;
    --model=*)
      MODEL="${1#*=}"
      shift
      ;;
    --pdf-dir=*)
      PDF_DIR="${1#*=}"
      shift
      ;;
    --img-dir=*)
      IMG_DIR="${1#*=}"
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      echo "Usage: ./run_physical_attack_test.sh [--template=TEMPLATE.tex] [--model=MODEL_NAME] [--pdf-dir=DIR] [--img-dir=DIR]"
      exit 1
      ;;
  esac
done

# Make scripts executable if needed
chmod +x run_top_attacks.py
chmod +x fix_and_compile_pdfs.sh
chmod +x test_uploaded_images.py
chmod +x analyze_top_attacks.py

# Create required directories
mkdir -p "$PDF_DIR"
mkdir -p "$IMG_DIR"

# STEP 1: Generate PDFs
echo "===== STEP 1: GENERATING ATTACK PDFs ====="
echo "Using template: $TEMPLATE"
echo "Output directory: $PDF_DIR"
echo "========================================"

# First generate the LaTeX files using the new script
python run_top_attacks.py --template "$TEMPLATE" --output-dir "$PDF_DIR" --log-file "${PDF_DIR}/results.jsonl"

# Then compile the PDFs using the fix script
./fix_and_compile_pdfs.sh --pdf-dir="$PDF_DIR" --template="$TEMPLATE"

# Check if the PDF generation was successful
if [ $? -ne 0 ]; then
  echo "Error generating PDFs!"
  exit 1
fi

# STEP 2: Guide user through the physical testing process
echo -e "\n\n===== STEP 2: PHYSICAL TESTING INSTRUCTIONS ====="
echo "Please follow these steps for physical testing:"
echo "1. Print the generated PDFs from the '$PDF_DIR' directory"
echo "2. Take clear photos of the printed pages"
echo "3. Transfer the photos to your computer"
echo "4. Place the photos in the '$IMG_DIR' directory"
echo "5. Try to name the photos to correspond with the attack name if possible"
echo "   (e.g., photo_baseline_clean.jpg, photo_C4_combo_triple_threat.jpg)"
echo "======================================================="

# Ask user to confirm when they've placed photos in the directory
read -p "Have you placed photos in the '$IMG_DIR' directory? (y/n): " RESPONSE
if [[ ! "$RESPONSE" =~ ^[Yy]$ ]]; then
  echo "Please place your photos in the '$IMG_DIR' directory and run the script again."
  exit 0
fi

# Count images in the directory
IMG_COUNT=$(find "$IMG_DIR" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" \) | wc -l)
if [ $IMG_COUNT -eq 0 ]; then
  echo "No images found in $IMG_DIR directory!"
  echo "Please place your photos (JPG, JPEG, or PNG format) in this directory and run the script again."
  exit 1
fi

echo "Found $IMG_COUNT images to test."

# STEP 3: Test the uploaded images
echo -e "\n\n===== STEP 3: TESTING UPLOADED IMAGES ====="
echo "Testing $IMG_COUNT images with model: $MODEL"
echo "============================================="

python test_uploaded_images.py --images-dir "$IMG_DIR" --output-file "physical_test_results.jsonl" --model "$MODEL" --manifest "$PDF_DIR/pdf_manifest.txt"

# Check if the testing was successful
if [ $? -ne 0 ]; then
  echo "Error testing images!"
  exit 1
fi

# STEP 4: Analyze the results
echo -e "\n\n===== STEP 4: ANALYZING RESULTS ====="
echo "Analyzing physical test results..."
echo "====================================="

python analyze_top_attacks.py --log-file "physical_test_results.jsonl" --output-prefix "physical_attack"

# Check if analysis was successful
if [ $? -ne 0 ]; then
  echo "Error analyzing the results!"
  exit 1
fi

echo -e "\n\n===== PHYSICAL TESTING EXPERIMENT COMPLETE ====="
echo "Results saved to:"
echo "- physical_test_results.jsonl (raw test data)"
echo "- physical_attack_detailed_results.csv (processed data)"
echo "- physical_attack_effectiveness.png (effectiveness chart)"
echo "- physical_attack_by_prompt_type.png (prompt type analysis)"
echo ""
echo "You can compare these results with the digital tests to see if physical printing and photography affects the attack effectiveness."
