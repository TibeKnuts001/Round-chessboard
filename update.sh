#!/bin/bash
# Update Script - Download latest changes from GitHub
# Uses git for version tracking and updates
# Usage: ./update.sh [--check-only]

set -e  # Stop on errors

REPO_URL="https://github.com/TibeKnuts001/Round-chessboard.git"
BRANCH="main"
CHECK_ONLY=false

# Parse arguments
if [ "$1" = "--check-only" ]; then
    CHECK_ONLY=true
fi

echo "================================"
echo "Round Chess Update Script"
echo "================================"
echo ""

# Check if we have a valid git repository with HEAD
if ! git rev-parse HEAD > /dev/null 2>&1; then
    # No git repository or incomplete initialization
    echo "Setting up git repository..."
    echo ""
    
    # Check if settings.json exists (preserve user data)
    HAS_SETTINGS=false
    if [ -f "settings.json" ]; then
        HAS_SETTINGS=true
        echo "Backing up settings.json..."
        cp settings.json settings.json.bak
    fi
    
    # Remove incomplete .git if it exists
    if [ -d ".git" ]; then
        echo "Cleaning up incomplete git repository..."
        rm -rf .git
    fi
    
    # Initialize git repository
    git init
    git remote add origin "$REPO_URL"
    
    echo "Downloading code from GitHub..."
    git fetch origin
    
    echo "Checking out main branch..."
    git checkout -f -b $BRANCH origin/$BRANCH
    
    # Restore settings if it existed
    if [ "$HAS_SETTINGS" = true ]; then
        echo "Restoring settings.json..."
        mv settings.json.bak settings.json
    fi
    
    # Set permissions
    chmod +x *.sh 2>/dev/null || true
    chmod +x install/*.sh 2>/dev/null || true
    
    echo ""
    echo "================================"
    echo "✓ Installation completed!"
    echo "================================"
    echo "You can now run ./run.sh to start the application"
    exit 0
fi

# Git repository exists: check for updates
echo "Checking for updates..."
git fetch origin --quiet

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/$BRANCH)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✓ Already up to date! (version: ${LOCAL:0:7})"
    exit 0
fi

echo "Update available: ${LOCAL:0:7} -> ${REMOTE:0:7}"
echo ""

# If check-only mode, stop here
if [ "$CHECK_ONLY" = true ]; then
    echo "Check complete. Run without --check-only to update."
    exit 1  # Exit code 1 to signal update available
fi

# Backup settings.json before pull
if [ -f "settings.json" ]; then
    echo "Backing up settings.json..."
    cp settings.json settings.json.bak
fi

echo "Pulling changes..."
git fetch origin
git reset --hard origin/$BRANCH

# Clean up old/removed files (but keep settings.json, venv, etc.)
echo "Cleaning up old files..."
git clean -fd -e settings.json -e settings.json.bak -e venv -e .vscode

# Restore settings if backup exists
if [ -f "settings.json.bak" ]; then
    echo "Restoring settings.json..."
    mv settings.json.bak settings.json
fi

# Set permissions
chmod +x *.sh 2>/dev/null || true
chmod +x install/*.sh 2>/dev/null || true

echo ""
echo "================================"
echo "✓ Update completed successfully!"
echo "================================"
echo "Restart the application to use the updated code."
