#!/bin/bash
# run_overnight_experiment.sh
# Script to start the overnight experiment with enhanced attack types

echo "Starting overnight experiment with enhanced attack types..."

# Define which models to test against
# You can add more models separated by commas
MODELS="gemma3:4b,claude-3.5-sonnet"

# Define the template to use
TEMPLATE="ex1.tex"

# Define the output log file
LOG_FILE="full_experiment_overnight_v3.jsonl"

echo "This will run a comprehensive test of all attack types with parameter optimization."
echo "Models to test: $MODELS"
echo "Template: $TEMPLATE"
echo "Log file: $LOG_FILE"
echo

# Execute the experiment
python run_experiment_v3.py --template "$TEMPLATE" \
                           --log-file "$LOG_FILE" \
                           --model "$MODELS" \
                           --multi-model \
                           --optimize \
                           --overnight

echo "Experiment started. You can go to bed now, results will be available in the morning."
echo "To monitor progress, you can use: tail -f $LOG_FILE"
