#!/bin/bash

# AI Research Agent Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
BUILD_FRESH=false
PULL_IMAGES=false

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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Set environment (development|staging|production)"
    echo "  -f, --fresh             Build images from scratch (no cache)"
    echo "  -p, --pull              Pull latest base images before building"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e development        Deploy to development environment"
    echo "  $0 -e production -f      Deploy to production with fresh build"
    echo "  $0 -e staging -p         Deploy to staging and pull latest images"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--fresh)
            BUILD_FRESH=true
            shift
            ;;
        -p|--pull)
            PULL_IMAGES=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    print_error "Must be one of: development, staging, production"
    exit 1
fi

print_status "Starting deployment for environment: $ENVIRONMENT"

# Set compose file based on environment
COMPOSE_FILE="docker-compose.yml"
if [[ "$ENVIRONMENT" == "staging" ]]; then
    COMPOSE_FILE="docker-compose.staging.yml"
elif [[ "$ENVIRONMENT" == "production" ]]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

# Check if compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    print_error "Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Check if .env file exists for production/staging
if [[ "$ENVIRONMENT" != "development" ]] && [[ ! -f ".env" ]]; then
    print_warning ".env file not found. Please create one based on .env.example"
    print_warning "Some services may fail to start without proper environment variables"
fi

# Pull latest images if requested
if [[ "$PULL_IMAGES" == true ]]; then
    print_status "Pulling latest base images..."
    docker-compose -f "$COMPOSE_FILE" pull
fi

# Build arguments
BUILD_ARGS=""
if [[ "$BUILD_FRESH" == true ]]; then
    BUILD_ARGS="--no-cache"
    print_status "Building images from scratch (no cache)..."
else
    print_status "Building images..."
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down

# Build and start services
print_status "Building and starting services..."
docker-compose -f "$COMPOSE_FILE" build $BUILD_ARGS
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 10

# Check service health
print_status "Checking service health..."
if docker-compose -f "$COMPOSE_FILE" ps | grep -q "unhealthy\|Exit"; then
    print_error "Some services are not healthy. Check logs:"
    docker-compose -f "$COMPOSE_FILE" ps
    docker-compose -f "$COMPOSE_FILE" logs --tail=50
    exit 1
fi

print_status "Deployment completed successfully!"
print_status "Services are running on:"

if [[ "$ENVIRONMENT" == "development" ]]; then
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8000"
    echo "  MongoDB:  mongodb://localhost:27017"
fi

print_status "Use 'docker-compose -f $COMPOSE_FILE logs -f' to view logs"
print_status "Use 'docker-compose -f $COMPOSE_FILE down' to stop services"