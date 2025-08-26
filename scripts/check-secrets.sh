#!/bin/bash

# Security Check Script - Detect potential secrets in git
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

ISSUES_FOUND=false

echo "AI Research Agent - Security Check"
echo "================================="
echo

print_status "Checking for potential secrets in git repository..."

# Check for tracked environment files
echo "Checking for tracked environment files..."
TRACKED_ENV_FILES=$(git ls-files | grep -E "\\.env" | grep -v "\\.env\\.example" || true)
if [[ -n "$TRACKED_ENV_FILES" ]]; then
    print_error "Found tracked environment files (potential secret leak):"
    echo "$TRACKED_ENV_FILES" | while read -r file; do
        echo "  - $file"
    done
    print_error "Run: git rm --cached <file> to untrack these files"
    ISSUES_FOUND=true
else
    print_status "No tracked environment files found"
fi

# Check for API key patterns in tracked files
echo
echo "Checking for API key patterns in tracked files..."
API_KEY_PATTERNS=(
    "AIza[0-9A-Za-z_-]{35}"  # Google API keys
    "[0-9a-f]{32,64}"        # Generic hex keys
    "sk-[0-9A-Za-z]{48}"     # OpenAI API keys
    "xoxb-[0-9]+-[0-9]+-[0-9A-Za-z]+" # Slack tokens
)

for pattern in "${API_KEY_PATTERNS[@]}"; do
    MATCHES=$(git grep -E "$pattern" -- '*.py' '*.js' '*.ts' '*.tsx' '*.json' '*.yml' '*.yaml' '*.md' 2>/dev/null || true)
    if [[ -n "$MATCHES" ]]; then
        print_error "Found potential API key pattern: $pattern"
        echo "$MATCHES" | head -5  # Show first 5 matches
        ISSUES_FOUND=true
    fi
done

if [[ "$ISSUES_FOUND" == false ]]; then
    print_status "No API key patterns found in tracked files"
fi

# Check for common secret keywords
echo
echo "Checking for common secret keywords..."
SECRET_KEYWORDS=(
    "password.*=.*[^_here]"
    "secret.*=.*[^_here]"
    "token.*=.*[^_here]"
    "key.*=.*[^_here]"
)

for keyword in "${SECRET_KEYWORDS[@]}"; do
    MATCHES=$(git grep -iE "$keyword" -- '*.py' '*.js' '*.ts' '*.tsx' '*.json' '*.yml' '*.yaml' 2>/dev/null | grep -v "example\|template\|placeholder\|your_.*_here" || true)
    if [[ -n "$MATCHES" ]]; then
        print_warning "Found potential secret keyword: $keyword"
        echo "$MATCHES" | head -3
    fi
done

# Check .env files in working directory
echo
echo "Checking for .env files in working directory..."
ENV_FILES=$(find . -name ".env*" -not -name "*.example" -not -path "./.git/*" 2>/dev/null || true)
if [[ -n "$ENV_FILES" ]]; then
    print_warning "Found .env files in working directory:"
    echo "$ENV_FILES" | while read -r file; do
        echo "  - $file"
        # Check if file contains placeholder values
        if grep -q "your_.*_here\|please_change" "$file" 2>/dev/null; then
            print_warning "    Contains placeholder values - needs configuration"
        fi
    done
    print_status "These files are properly ignored by git"
else
    print_warning "No .env files found - you may need to configure environment"
fi

# Check git hooks for pre-commit security
echo
echo "Checking git hooks..."
if [[ -f ".git/hooks/pre-commit" ]]; then
    print_status "Pre-commit hook found"
else
    print_warning "No pre-commit hook found - consider adding secret detection"
fi

echo
echo "Security Check Summary:"
echo "======================"

if [[ "$ISSUES_FOUND" == true ]]; then
    print_error "SECURITY ISSUES FOUND!"
    echo
    echo "Immediate actions required:"
    echo "1. Remove tracked environment files: git rm --cached <file>"
    echo "2. Review and remove any exposed secrets"
    echo "3. Rotate any compromised API keys"
    echo "4. Commit the .gitignore changes"
    echo
    exit 1
else
    print_status "No critical security issues found"
    echo
    echo "Recommendations:"
    echo "1. Run this check before each commit"
    echo "2. Use environment variables for all secrets"
    echo "3. Never commit .env files"
    echo "4. Regularly rotate API keys"
    echo
    exit 0
fi