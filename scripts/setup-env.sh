#!/bin/bash

# Environment Setup Script for AI Research Agent
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to generate random secret key
generate_secret_key() {
    openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "please_change_this_secret_key_$(date +%s)"
}

# Function to prompt for input with default
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    if [[ -n "$default" ]]; then
        print_prompt "$prompt (default: $default): "
    else
        print_prompt "$prompt: "
    fi
    
    read -r input
    if [[ -z "$input" && -n "$default" ]]; then
        input="$default"
    fi
    
    eval "$var_name='$input'"
}

# Function to prompt for sensitive input (hidden)
prompt_sensitive() {
    local prompt="$1"
    local var_name="$2"
    
    print_prompt "$prompt (input hidden): "
    read -rs input
    echo
    eval "$var_name='$input'"
}

print_status "AI Research Agent Environment Setup"
print_status "This script will help you configure environment variables securely."
echo

# Check if .env already exists
if [[ -f ".env" ]]; then
    print_warning ".env file already exists!"
    print_prompt "Do you want to overwrite it? (y/N): "
    read -r overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        print_status "Exiting without changes."
        exit 0
    fi
fi

print_status "Setting up API keys..."
print_warning "You'll need to obtain these API keys from the respective services:"
print_warning "- Google Scholar API: https://developers.google.com/custom-search"
print_warning "- Google Books API: https://developers.google.com/books"
print_warning "- ScienceDirect API: https://dev.elsevier.com/"
echo

# Collect API keys
prompt_sensitive "Enter your Google Scholar API key" GOOGLE_SCHOLAR_API_KEY
prompt_sensitive "Enter your Google Books API key" GOOGLE_BOOKS_API_KEY
prompt_sensitive "Enter your ScienceDirect API key" SCIENCEDIRECT_API_KEY

print_status "Setting up database configuration..."

# Database configuration
prompt_with_default "MongoDB root username" "admin" MONGODB_ROOT_USERNAME
prompt_sensitive "MongoDB root password" MONGODB_ROOT_PASSWORD
prompt_with_default "MongoDB application username" "ai_research_user" MONGODB_USERNAME
prompt_sensitive "MongoDB application password" MONGODB_PASSWORD
prompt_with_default "MongoDB host" "mongodb" MONGODB_HOST
prompt_with_default "MongoDB port" "27017" MONGODB_PORT

print_status "Setting up application configuration..."

# Application configuration
prompt_with_default "Frontend API URL" "http://localhost:8000" NEXT_PUBLIC_API_URL
prompt_with_default "Allowed CORS origins" "http://localhost:3000,https://yourdomain.com" ALLOWED_ORIGINS

# Generate secret key
SECRET_KEY=$(generate_secret_key)
print_status "Generated secure secret key"

# Optional Redis
prompt_with_default "Redis URL (optional)" "redis://redis:6379" REDIS_URL

print_status "Creating .env file..."

# Create .env file
cat > .env << EOF
# AI Research Agent Environment Configuration
# Generated on $(date)
# WARNING: Keep this file secure and never commit it to version control

# API Keys
GOOGLE_SCHOLAR_API_KEY=$GOOGLE_SCHOLAR_API_KEY
GOOGLE_BOOKS_API_KEY=$GOOGLE_BOOKS_API_KEY
SCIENCEDIRECT_API_KEY=$SCIENCEDIRECT_API_KEY

# Database Configuration
MONGODB_ROOT_USERNAME=$MONGODB_ROOT_USERNAME
MONGODB_ROOT_PASSWORD=$MONGODB_ROOT_PASSWORD
MONGODB_USERNAME=$MONGODB_USERNAME
MONGODB_PASSWORD=$MONGODB_PASSWORD
MONGODB_HOST=$MONGODB_HOST
MONGODB_PORT=$MONGODB_PORT

# Frontend Configuration
NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Security
SECRET_KEY=$SECRET_KEY

# CORS Configuration
ALLOWED_ORIGINS=$ALLOWED_ORIGINS

# Optional Services
REDIS_URL=$REDIS_URL
EOF

# Set secure permissions
chmod 600 .env

print_status "Environment configuration completed!"
print_warning "Important security notes:"
print_warning "1. The .env file has been created with restricted permissions (600)"
print_warning "2. Never commit the .env file to version control"
print_warning "3. Keep your API keys secure and rotate them regularly"
print_warning "4. Use different credentials for different environments"
echo

print_status "Next steps:"
echo "1. Review the generated .env file"
echo "2. Run: ./scripts/deploy.sh -e development"
echo "3. Access your application at http://localhost:3000"