#!/bin/bash

# Comprehensive test runner for AI Research Agent
set -e

echo "🧪 Starting comprehensive test suite for AI Research Agent"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $2 -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

# Function to run command with status
run_test() {
    echo -e "\n${YELLOW}Running: $1${NC}"
    echo "----------------------------------------"
    
    if eval "$2"; then
        print_status "$1" 0
        return 0
    else
        print_status "$1" 1
        return 1
    fi
}

# Initialize counters
TOTAL_TESTS=0
PASSED_TESTS=0

# Frontend Tests
echo -e "\n🎨 FRONTEND TESTS"
echo "=================="

cd frontend

# Frontend unit tests
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Frontend Unit Tests" "npm run test:unit -- --passWithNoTests"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi

# Frontend integration tests
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Frontend Integration Tests" "npm run test:integration -- --passWithNoTests"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi

# Frontend coverage
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Frontend Coverage Report" "npm run test:coverage -- --passWithNoTests"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi

# Frontend linting
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Frontend Linting" "npm run lint"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi

cd ..

# Backend Tests
echo -e "\n🔧 BACKEND TESTS"
echo "================"

cd backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Backend unit tests
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Backend Unit Tests" "python -m pytest tests/ -v --tb=short -m 'not integration'"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi

# Backend integration tests
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Backend Integration Tests" "python -m pytest tests/test_integration_workflow.py -v"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi

# Backend coverage
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Backend Coverage Report" "python -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi

# Backend main app tests
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Backend Main App Tests" "python -m pytest tests/test_main_app.py -v"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi

cd ..

# Summary
echo -e "\n📊 TEST SUMMARY"
echo "================"
echo "Total test suites: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $((TOTAL_TESTS - PASSED_TESTS))"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "\n${GREEN}🎉 All test suites passed!${NC}"
    
    # Generate combined coverage report
    echo -e "\n📈 COVERAGE REPORTS"
    echo "==================="
    echo "Frontend coverage: frontend/coverage/"
    echo "Backend coverage: backend/htmlcov/"
    
    exit 0
else
    echo -e "\n${RED}💥 Some test suites failed!${NC}"
    echo "Check the output above for details."
    exit 1
fi