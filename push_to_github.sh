#!/bin/bash
# Script to push the project to GitHub

# Set default remote name and branch
REMOTE="origin"
BRANCH="main"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --remote=*)
      REMOTE="${1#*=}"
      shift
      ;;
    --branch=*)
      BRANCH="${1#*=}"
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      echo "Usage: ./push_to_github.sh [--remote=REMOTE_NAME] [--branch=BRANCH_NAME]"
      exit 1
      ;;
  esac
done

echo "===== AI-RESISTANT MATH DOCUMENT FRAMEWORK GITHUB PUSH ====="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed or not in PATH."
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    
    # Prompt for GitHub repository URL
    read -p "Enter GitHub repository URL (e.g., https://github.com/username/repo.git): " REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        echo "Error: No repository URL provided."
        exit 1
    fi
    
    echo "Adding remote repository..."
    git remote add $REMOTE $REPO_URL
else
    echo "Git repository already initialized."
    
    # Check if remote exists
    if ! git remote get-url $REMOTE &> /dev/null; then
        read -p "Remote '$REMOTE' not found. Enter GitHub repository URL: " REPO_URL
        
        if [ -z "$REPO_URL" ]; then
            echo "Error: No repository URL provided."
            exit 1
        fi
        
        git remote add $REMOTE $REPO_URL
    fi
fi

# List of important files to track
IMPORTANT_FILES=(
    # Core scripts
    "exam_attack_v3.py"
    "exam_test.py"
    "run_experiment_v3.py"
    "analyze_overnight_detailed.py"
    "analyze_top_attacks.py"
    
    # New scripts
    "run_top_attacks.py"
    "generate_top_attack_pdfs.py"
    "test_uploaded_images.py"
    "run_top_attacks_experiment.sh"
    "run_physical_attack_test.sh"
    
    # Documentation and setup
    "README.md"
    "requirements.txt"
    "ai_resistant_math_paper.tex"
    
    # LaTeX templates
    "exam_template.tex"
    "ex0.tex"
    "ex1.tex"
)

# Check which files exist and add them
for file in "${IMPORTANT_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Adding file: $file"
        git add "$file"
    else
        echo "Warning: File '$file' not found, skipping."
    fi
done

# Add any other Python files that might be relevant
echo "Adding other Python files..."
git add *.py

# Add shell scripts
echo "Adding shell scripts..."
git add *.sh

# Prompt for commit message
read -p "Enter commit message (default: 'Initial commit of AI-resistant math framework'): " COMMIT_MSG
COMMIT_MSG=${COMMIT_MSG:-"Initial commit of AI-resistant math framework"}

# Commit the changes
echo "Committing changes..."
git commit -m "$COMMIT_MSG"

# Push to GitHub
echo "Pushing to GitHub ($REMOTE/$BRANCH)..."
git push -u $REMOTE $BRANCH

# Check if the push was successful
if [ $? -eq 0 ]; then
    echo "===== SUCCESSFULLY PUSHED TO GITHUB ====="
    echo "Repository URL: $(git remote get-url $REMOTE)"
    echo "Branch: $BRANCH"
else
    echo "===== ERROR PUSHING TO GITHUB ====="
    echo "Please check your internet connection and repository permissions."
    echo "You might need to authenticate with GitHub."
fi
