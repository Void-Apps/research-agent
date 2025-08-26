#!/bin/bash

# Install Git Hooks for Security
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_status "Installing git hooks for AI Research Agent..."

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# Pre-commit hook to check for secrets
echo "Running security checks..."

# Run the security check script
if [[ -f "scripts/check-secrets.sh" ]]; then
    ./scripts/check-secrets.sh
    if [[ $? -ne 0 ]]; then
        echo "❌ Security check failed! Commit blocked."
        echo "Fix the security issues above before committing."
        exit 1
    fi
else
    echo "⚠️  Security check script not found, skipping..."
fi

# Check for .env files being committed
if git diff --cached --name-only | grep -E "\.env$|\.env\." | grep -v "\.env\.example"; then
    echo "❌ Attempting to commit .env files!"
    echo "These files may contain secrets and should not be committed."
    echo "Files:"
    git diff --cached --name-only | grep -E "\.env$|\.env\." | grep -v "\.env\.example"
    exit 1
fi

echo "✅ Security checks passed"
EOF

# Make the hook executable
chmod +x .git/hooks/pre-commit

print_status "Pre-commit hook installed successfully!"
print_status "This hook will:"
echo "  - Check for potential secrets before each commit"
echo "  - Prevent .env files from being committed"
echo "  - Run security validation"

print_warning "To bypass the hook (not recommended): git commit --no-verify"

# Create commit-msg hook for commit message validation
cat > .git/hooks/commit-msg << 'EOF'
#!/bin/bash

# Commit message hook
commit_regex='^(feat|fix|docs|style|refactor|test|chore|security)(\(.+\))?: .{1,50}'

error_msg="Invalid commit message format!
Format: <type>(<scope>): <description>
Types: feat, fix, docs, style, refactor, test, chore, security
Example: feat(auth): add user authentication"

if ! grep -qE "$commit_regex" "$1"; then
    echo "$error_msg" >&2
    exit 1
fi
EOF

chmod +x .git/hooks/commit-msg

print_status "Commit message hook installed!"
print_status "Enforces conventional commit format"

echo
print_status "Git hooks installation complete!"
print_status "Your repository is now protected against accidental secret commits."