#!/bin/bash
# run_top_attacks_experiment.sh
# Script to run the top attacks experiment and analyze the results

# Set the model to use (can be changed via command line argument)
MODEL="gemma3:4b"
TEMPLATE="exam_template.tex"
LOG_FILE="top_attacks_results.jsonl"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --model=*)
      MODEL="${1#*=}"
      shift
      ;;
    --template=*)
      TEMPLATE="${1#*=}"
      shift
      ;;
    --log-file=*)
      LOG_FILE="${1#*=}"
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      echo "Usage: ./run_top_attacks_experiment.sh [--model=MODEL_NAME] [--template=TEMPLATE.tex] [--log-file=OUTPUT.jsonl]"
      exit 1
      ;;
  esac
done

# Make scripts executable if needed
chmod +x run_top_attacks.py
chmod +x analyze_top_attacks.py

# Print experiment information
echo "===== RUNNING TOP ATTACKS EXPERIMENT ====="
echo "Using model: $MODEL"
echo "Template file: $TEMPLATE"
echo "Log file: $LOG_FILE"
echo "========================================"

# Run the top attacks experiment
echo "Running experiment..."
python run_top_attacks.py --model "$MODEL" --template "$TEMPLATE" --log-file "$LOG_FILE"

# Check if the experiment was successful
if [ $? -ne 0 ]; then
  echo "Error running the experiment!"
  exit 1
fi

# Analyze the results
echo -e "\n===== ANALYZING RESULTS ====="
python analyze_top_attacks.py --log-file "$LOG_FILE" --output-prefix "top_attacks"

# Check if analysis was successful
if [ $? -ne 0 ]; then
  echo "Error analyzing the results!"
  exit 1
fi

echo -e "\n===== EXPERIMENT COMPLETE ====="
echo "Results saved to:"
echo "- $LOG_FILE (raw data)"
echo "- top_attacks_detailed_results.csv (processed data)"
echo "- top_attacks_effectiveness.png (effectiveness chart)"
echo "- top_attacks_by_prompt_type.png (prompt type analysis)"
