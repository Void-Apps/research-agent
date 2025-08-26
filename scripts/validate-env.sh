#!/bin/bash

# Environment Validation Script for AI Research Agent
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Validation results
VALIDATION_PASSED=true

# Function to validate environment variable
validate_env_var() {
    local var_name="$1"
    local var_value="$2"
    local is_required="$3"
    local min_length="${4:-1}"
    
    if [[ -z "$var_value" ]]; then
        if [[ "$is_required" == "true" ]]; then
            print_error "$var_name is required but not set"
            VALIDATION_PASSED=false
        else
            print_warning "$var_name is not set (optional)"
        fi
    elif [[ ${#var_value} -lt $min_length ]]; then
        print_error "$var_name is too short (minimum $min_length characters)"
        VALIDATION_PASSED=false
    elif [[ "$var_value" == *"your_"*"_here" ]] || [[ "$var_value" == *"please_change"* ]]; then
        print_error "$var_name contains placeholder value - please set actual value"
        VALIDATION_PASSED=false
    else
        print_status "$var_name is properly configured"
    fi
}

# Function to validate API key format
validate_api_key() {
    local var_name="$1"
    local var_value="$2"
    local expected_prefix="$3"
    
    if [[ -z "$var_value" ]]; then
        print_error "$var_name is required but not set"
        VALIDATION_PASSED=false
    elif [[ "$var_value" == *"your_"*"_here" ]]; then
        print_error "$var_name contains placeholder value - please set actual API key"
        VALIDATION_PASSED=false
    elif [[ -n "$expected_prefix" ]] && [[ ! "$var_value" == "$expected_prefix"* ]]; then
        print_warning "$var_name may have incorrect format (expected to start with '$expected_prefix')"
    else
        print_status "$var_name is configured"
    fi
}

echo "AI Research Agent Environment Validation"
echo "========================================"
echo

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    print_error ".env file not found"
    print_error "Run './scripts/setup-env.sh' to create environment configuration"
    exit 1
fi

print_status ".env file found"

# Load environment variables
set -a
source .env
set +a

echo
echo "Validating API Keys:"
echo "-------------------"

# Validate API keys
validate_api_key "GOOGLE_SCHOLAR_API_KEY" "$GOOGLE_SCHOLAR_API_KEY" "AIza"
validate_api_key "GOOGLE_BOOKS_API_KEY" "$GOOGLE_BOOKS_API_KEY" "AIza"
validate_api_key "SCIENCEDIRECT_API_KEY" "$SCIENCEDIRECT_API_KEY"

echo
echo "Validating Database Configuration:"
echo "---------------------------------"

# Validate database configuration
validate_env_var "MONGODB_ROOT_USERNAME" "$MONGODB_ROOT_USERNAME" true 3
validate_env_var "MONGODB_ROOT_PASSWORD" "$MONGODB_ROOT_PASSWORD" true 8
validate_env_var "MONGODB_USERNAME" "$MONGODB_USERNAME" true 3
validate_env_var "MONGODB_PASSWORD" "$MONGODB_PASSWORD" true 8
validate_env_var "MONGODB_HOST" "$MONGODB_HOST" true
validate_env_var "MONGODB_PORT" "$MONGODB_PORT" true

echo
echo "Validating Application Configuration:"
echo "------------------------------------"

# Validate application configuration
validate_env_var "NEXT_PUBLIC_API_URL" "$NEXT_PUBLIC_API_URL" true
validate_env_var "SECRET_KEY" "$SECRET_KEY" true 32
validate_env_var "ALLOWED_ORIGINS" "$ALLOWED_ORIGINS" true

echo
echo "Validating Optional Configuration:"
echo "---------------------------------"

# Validate optional configuration
validate_env_var "REDIS_URL" "$REDIS_URL" false

echo
echo "Security Checks:"
echo "---------------"

# Check file permissions
if [[ -f ".env" ]]; then
    ENV_PERMS=$(stat -c "%a" .env 2>/dev/null || stat -f "%A" .env 2>/dev/null || echo "unknown")
    if [[ "$ENV_PERMS" == "600" ]]; then
        print_status ".env file has secure permissions (600)"
    else
        print_warning ".env file permissions are $ENV_PERMS (recommended: 600)"
        print_warning "Run: chmod 600 .env"
    fi
fi

# Check for common security issues
if [[ -f ".env" ]] && git ls-files --error-unmatch .env >/dev/null 2>&1; then
    print_error ".env file is tracked by git - this is a security risk!"
    print_error "Run: git rm --cached .env"
    VALIDATION_PASSED=false
else
    print_status ".env file is not tracked by git"
fi

echo
echo "Docker Configuration:"
echo "--------------------"

# Check Docker files
if [[ -f "frontend/Dockerfile" ]]; then
    print_status "Frontend Dockerfile found"
else
    print_error "Frontend Dockerfile missing"
    VALIDATION_PASSED=false
fi

if [[ -f "backend/Dockerfile" ]]; then
    print_status "Backend Dockerfile found"
else
    print_error "Backend Dockerfile missing"
    VALIDATION_PASSED=false
fi

if [[ -f "docker-compose.yml" ]]; then
    print_status "Docker Compose configuration found"
else
    print_error "docker-compose.yml missing"
    VALIDATION_PASSED=false
fi

echo
echo "Validation Summary:"
echo "=================="

if [[ "$VALIDATION_PASSED" == true ]]; then
    print_status "All validations passed! Environment is properly configured."
    echo
    echo "Next steps:"
    echo "1. Run: ./scripts/deploy.sh -e development"
    echo "2. Access your application at http://localhost:3000"
    exit 0
else
    print_error "Validation failed! Please fix the issues above."
    echo
    echo "Common solutions:"
    echo "1. Run: ./scripts/setup-env.sh (to reconfigure environment)"
    echo "2. Check API key formats and ensure they're valid"
    echo "3. Ensure all required fields are filled"
    exit 1
fi