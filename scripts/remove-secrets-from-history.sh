#!/bin/bash

# Script to Remove Secrets from Git History
# WARNING: This rewrites git history and changes commit hashes
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_prompt() {
    echo -e "${BLUE}[INPUT]${NC} $1"
}

echo "🔒 Git History Secret Removal Tool"
echo "=================================="
echo

print_warning "This script will PERMANENTLY remove sensitive files from git history"
print_warning "This operation:"
print_warning "1. Rewrites ALL commit history"
print_warning "2. Changes ALL commit hashes"
print_warning "3. Requires force push to GitHub"
print_warning "4. May break existing pull requests"
print_warning "5. Other contributors will need to re-clone"

echo
print_prompt "Are you absolutely sure you want to proceed? (type 'YES' to continue): "
read -r confirmation

if [[ "$confirmation" != "YES" ]]; then
    print_status "Operation cancelled."
    exit 0
fi

print_status "Creating backup branch..."
git branch backup-before-history-rewrite 2>/dev/null || true

print_status "Removing sensitive files from git history..."

# Files to remove from history
SENSITIVE_FILES=(
    "backend/.env.development"
    "backend/.env.production" 
    "backend/.env.staging"
)

# Use git filter-branch to remove files from all history
for file in "${SENSITIVE_FILES[@]}"; do
    print_status "Removing $file from all commits..."
    git filter-branch --force --index-filter \
        "git rm --cached --ignore-unmatch '$file'" \
        --prune-empty --tag-name-filter cat -- --all
done

print_status "Cleaning up git references..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

print_status "Verifying removal..."
echo
echo "Checking if sensitive files still exist in history..."

FOUND_SECRETS=false
for file in "${SENSITIVE_FILES[@]}"; do
    if git log --all --full-history -- "$file" | grep -q "commit"; then
        print_error "❌ $file still found in history!"
        FOUND_SECRETS=true
    else
        print_status "✅ $file successfully removed from history"
    fi
done

if [[ "$FOUND_SECRETS" == true ]]; then
    print_error "Some files were not completely removed. Manual intervention required."
    exit 1
fi

print_status "✅ All sensitive files removed from git history!"

echo
print_warning "IMPORTANT: Next steps to complete the process:"
echo "1. Force push to GitHub (this will rewrite remote history):"
echo "   git push --force-with-lease origin main"
echo
echo "2. Notify all contributors that they need to:"
echo "   - Delete their local clones"
echo "   - Re-clone the repository"
echo "   - Any existing pull requests will need to be recreated"
echo
echo "3. Consider rotating the exposed API keys as a security precaution"

echo
print_prompt "Do you want to force push to GitHub now? (y/N): "
read -r push_confirmation

if [[ "$push_confirmation" =~ ^[Yy]$ ]]; then
    print_status "Force pushing to GitHub..."
    git push --force-with-lease origin main
    
    if [[ $? -eq 0 ]]; then
        print_status "✅ Successfully pushed cleaned history to GitHub!"
        print_status "🔒 API keys have been completely removed from the public repository"
    else
        print_error "❌ Failed to push to GitHub. You may need to run:"
        print_error "git push --force origin main"
    fi
else
    print_warning "History cleaned locally but not pushed to GitHub yet."
    print_warning "Run 'git push --force-with-lease origin main' when ready."
fi

echo
print_status "Backup branch 'backup-before-history-rewrite' created for safety"
print_status "You can delete it later with: git branch -D backup-before-history-rewrite"