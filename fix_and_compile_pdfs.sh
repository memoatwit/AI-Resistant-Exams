#!/bin/bash
# Script to fix the file extension issue and compile the PDFs

# Default values
PDF_DIR="attack_pdfs_0712"
TEMPLATE="exam_template.tex"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --pdf-dir=*)
      PDF_DIR="${1#*=}"
      shift
      ;;
    --template=*)
      TEMPLATE="${1#*=}"
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      echo "Usage: ./fix_and_compile_pdfs.sh [--pdf-dir=DIR] [--template=TEMPLATE.tex]"
      exit 1
      ;;
  esac
done

# Clean up the directory
rm -rf "$PDF_DIR"/* 2>/dev/null
mkdir -p "$PDF_DIR"

# First create the baseline and save it
echo "Creating baseline..."
python run_top_attacks.py --template="$TEMPLATE" --output-dir="$PDF_DIR" --log-file="$PDF_DIR/results.jsonl"

# Fix the file extensions (rename .tex.tex to .tex)
echo "Fixing file extensions..."
for file in "$PDF_DIR"/*.tex.tex; do
    if [ -f "$file" ]; then
        new_name=$(echo $file | sed 's/\.tex\.tex$/.tex/')
        mv "$file" "$new_name"
        echo "Renamed $file to $new_name"
    fi
done

# Compile each tex file with lualatex using -output-directory option
echo "Compiling files with lualatex..."
for texfile in "$PDF_DIR"/*.tex; do
    echo "Compiling $texfile..."
    # Get just the filename without the directory
    filename=$(basename "$texfile")
    
    # Compile with output directory specified
    lualatex -interaction=nonstopmode -output-directory="$PDF_DIR" "$texfile"
    
    # Check if PDF was created in the output directory
    pdf_name="$PDF_DIR/${filename%.tex}.pdf"
    if [ -f "$pdf_name" ]; then
        echo "Successfully created $pdf_name"
    else
        echo "Error: Failed to create PDF for $texfile"
    fi
done

echo "All PDFs saved to $PDF_DIR directory"
echo "Use these PDFs for physical testing."
