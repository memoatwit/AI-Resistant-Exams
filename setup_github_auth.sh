#!/bin/bash
# Script to help with GitHub authentication

echo "===== GITHUB AUTHENTICATION HELPER ====="
echo "This script will guide you through setting up authentication for GitHub"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed or not in PATH."
    exit 1
fi

echo "GitHub now requires personal access tokens instead of passwords for command-line authentication."
echo ""
echo "Follow these steps to create a personal access token:"
echo ""
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Click 'Generate new token' > 'Generate new token (classic)'"
echo "3. Give it a name (e.g., 'AI-Resistant Math Project')"
echo "4. Set an expiration date"
echo "5. Select the following scopes:"
echo "   - repo (Full control of private repositories)"
echo "   - workflow (optional, if you plan to use GitHub Actions)"
echo "6. Click 'Generate token'"
echo "7. COPY THE TOKEN IMMEDIATELY - GitHub will only show it once!"
echo ""

read -p "Have you created and copied the token? (y/n): " TOKEN_READY
if [[ ! "$TOKEN_READY" =~ ^[Yy]$ ]]; then
    echo "Please create a token first and run this script again."
    exit 0
fi

echo ""
echo "There are two ways to authenticate:"
echo ""
echo "OPTION 1: Configure Git credentials helper (recommended)"
echo "This will save your token securely so you don't have to enter it each time."
echo ""
echo "OPTION 2: Use the token as your password when prompted"
echo "Git will prompt for username and password when you push."
echo ""

read -p "Which option do you prefer? (1/2): " AUTH_OPTION

if [ "$AUTH_OPTION" == "1" ]; then
    echo ""
    echo "Setting up Git credential helper..."
    
    # For macOS, use the osxkeychain helper
    if [[ "$OSTYPE" == "darwin"* ]]; then
        git config --global credential.helper osxkeychain
        echo "Configured Git to use osxkeychain for credential storage."
        
    # For Linux, use the cache helper
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        git config --global credential.helper cache
        git config --global credential.helper 'cache --timeout=3600'
        echo "Configured Git to cache credentials for 1 hour."
        
    # For Windows, use the manager helper
    elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "win32" ]]; then
        git config --global credential.helper manager
        echo "Configured Git to use the Windows credential manager."
    else
        git config --global credential.helper store
        echo "Configured Git to store credentials (less secure but works everywhere)."
    fi
    
    echo ""
    echo "Next time you push to GitHub, enter your username and use the personal access token"
    echo "as the password when prompted. Git will remember it after that."
    
elif [ "$AUTH_OPTION" == "2" ]; then
    echo ""
    echo "When prompted during git push:"
    echo "- Enter your GitHub username"
    echo "- Use the personal access token as the password (paste it)"
else
    echo "Invalid option selected."
fi

echo ""
echo "===== AUTHENTICATION SETUP COMPLETE ====="
echo "Now try running ./push_to_github.sh again"
echo ""
echo "If you continue to have issues, you can also try:"
echo "git push https://YOUR-USERNAME:YOUR-TOKEN@github.com/username/repository.git"
