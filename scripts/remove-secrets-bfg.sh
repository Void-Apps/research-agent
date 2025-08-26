#!/bin/bash

# Script to Remove Secrets using BFG Repo-Cleaner (Recommended Method)
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

echo "🔒 BFG Repo-Cleaner Secret Removal Tool"
echo "======================================="
echo

# Check if BFG is installed
if ! command -v bfg &> /dev/null; then
    print_error "BFG Repo-Cleaner is not installed!"
    echo
    echo "Install BFG Repo-Cleaner:"
    echo "  macOS: brew install bfg"
    echo "  Or download from: https://rtyley.github.io/bfg-repo-cleaner/"
    echo
    exit 1
fi

print_status "BFG Repo-Cleaner found: $(bfg --version)"

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
git branch backup-before-bfg-clean 2>/dev/null || true

print_status "Creating list of files to remove..."
cat > files-to-delete.txt << EOF
backend/.env.development
backend/.env.production
backend/.env.staging
EOF

print_status "Running BFG Repo-Cleaner..."
bfg --delete-files files-to-delete.txt

print_status "Cleaning up git references..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

print_status "Removing temporary files..."
rm -f files-to-delete.txt

print_status "Verifying removal..."
echo
echo "Checking if sensitive files still exist in history..."

SENSITIVE_FILES=(
    "backend/.env.development"
    "backend/.env.production" 
    "backend/.env.staging"
)

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
print_status "Backup branch 'backup-before-bfg-clean' created for safety"
print_status "You can delete it later with: git branch -D backup-before-bfg-clean"