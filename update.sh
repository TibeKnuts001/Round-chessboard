#!/bin/bash
# Update Script - Download latest changes from GitHub
# Works for both git repositories and direct installations
# Usage: ./update.sh

set -e  # Stop on errors

REPO_URL="https://github.com/TibeKnuts001/Round-chessboard"
BRANCH="main"

echo "================================"
echo "Round Chess Update Script"
echo "================================"
echo ""

# Check if we're in a valid git repository
if git rev-parse --git-dir > /dev/null 2>&1; then
    # Git repository: use git to check for updates
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
    echo "Pulling changes..."
    git pull origin $BRANCH
    
    echo ""
    echo "✓ Update completed successfully!"
    echo "Restart the application to use the updated code."
    exit 0
fi

# Non-git installation: download from GitHub
echo "Non-git installation detected"
echo ""

# Check current version (if available)
CURRENT_VERSION=""
if [ -f ".version" ]; then
    CURRENT_VERSION=$(cat .version)
    echo "Current version: ${CURRENT_VERSION:0:7}"
fi

# Get latest version from GitHub
echo "Checking for updates..."
LATEST_VERSION=$(curl -s "https://api.github.com/repos/TibeKnuts001/Round-chessboard/commits/$BRANCH" | grep '"sha"' | head -1 | cut -d'"' -f4)

if [ -z "$LATEST_VERSION" ]; then
    echo "Warning: Could not check latest version from GitHub"
    read -p "Continue with update anyway? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Update cancelled"
        exit 0
    fi
elif [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
    echo "✓ Already up to date! (version: ${LATEST_VERSION:0:7})"
    exit 0
else
    if [ -n "$CURRENT_VERSION" ]; then
        echo "Update available: ${CURRENT_VERSION:0:7} -> ${LATEST_VERSION:0:7}"
    else
        echo "Installing latest version: ${LATEST_VERSION:0:7}"
    fi
fi
echo ""

echo "Downloading latest code..."
TEMP_DIR=$(mktemp -d)

if command -v git >/dev/null 2>&1; then
    git clone --depth 1 --branch $BRANCH "$REPO_URL.git" "$TEMP_DIR"
    rm -rf "$TEMP_DIR/.git"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$REPO_URL/archive/refs/heads/$BRANCH.zip" -O "$TEMP_DIR/repo.zip"
    unzip -q "$TEMP_DIR/repo.zip" -d "$TEMP_DIR"
    mv "$TEMP_DIR/Round-chessboard-$BRANCH"/* "$TEMP_DIR/"
    rm -rf "$TEMP_DIR/Round-chessboard-$BRANCH" "$TEMP_DIR/repo.zip"
elif command -v curl >/dev/null 2>&1; then
    curl -sL "$REPO_URL/archive/refs/heads/$BRANCH.zip" -o "$TEMP_DIR/repo.zip"
    unzip -q "$TEMP_DIR/repo.zip" -d "$TEMP_DIR"
    mv "$TEMP_DIR/Round-chessboard-$BRANCH"/* "$TEMP_DIR/"
    rm -rf "$TEMP_DIR/Round-chessboard-$BRANCH" "$TEMP_DIR/repo.zip"
else
    echo "Error: No download tool available (git/wget/curl)"
    exit 1
fi

echo "Updating files..."
rsync -a --exclude='settings.json' --exclude='venv' --exclude='.version' --exclude='*.pyc' --exclude='__pycache__' "$TEMP_DIR/" ./
rm -rf "$TEMP_DIR"

# Save version for next check
if [ -n "$LATEST_VERSION" ]; then
    echo "$LATEST_VERSION" > .version
fi

chmod +x *.sh 2>/dev/null || true
chmod +x install/*.sh 2>/dev/null || true

echo ""
echo "================================"
echo "✓ Update completed successfully!"
echo "================================"
echo "Restart the application to use the updated code."
