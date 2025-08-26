#!/bin/bash

# SSL Certificate Generation Script for AI Research Agent
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Create nginx/ssl directory if it doesn't exist
mkdir -p nginx/ssl

print_status "Generating self-signed SSL certificate for development..."
print_warning "This certificate is for development/testing only!"
print_warning "For production, use certificates from a trusted CA."

# Generate private key
openssl genrsa -out nginx/ssl/key.pem 2048

# Generate certificate signing request
openssl req -new -key nginx/ssl/key.pem -out nginx/ssl/cert.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate self-signed certificate
openssl x509 -req -days 365 -in nginx/ssl/cert.csr -signkey nginx/ssl/key.pem -out nginx/ssl/cert.pem

# Clean up CSR file
rm nginx/ssl/cert.csr

# Set appropriate permissions
chmod 600 nginx/ssl/key.pem
chmod 644 nginx/ssl/cert.pem

print_status "SSL certificate generated successfully!"
print_status "Certificate: nginx/ssl/cert.pem"
print_status "Private key: nginx/ssl/key.pem"
print_warning "Valid for 365 days from today"

echo
print_status "To use HTTPS in production:"
echo "1. Obtain certificates from a trusted CA (Let's Encrypt, etc.)"
echo "2. Replace the generated files with your production certificates"
echo "3. Update nginx configuration if needed"