# Testing Documentation

This document describes the comprehensive testing suite for the AI Research Agent application.

## Overview

The testing suite includes:
- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test complete workflows and component interactions
- **Coverage Reports**: Ensure adequate test coverage (80% minimum)
- **Quality Gates**: Automated quality checks and thresholds
- **CI/CD Integration**: Automated testing in GitHub Actions

## Test Structure

### Frontend Tests (`frontend/src/__tests__/`)

```
__tests__/
├── fixtures/
│   └── mockData.ts          # Mock data for consistent testing
├── utils/
│   └── testUtils.tsx        # Test utilities and custom render
├── integration/
│   ├── research-workflow.test.tsx
│   └── api-state-management.test.tsx
├── api-integration.test.tsx
├── navigation.integration.test.tsx
├── pages-structure.test.tsx
└── routing.test.tsx
```

### Backend Tests (`backend/tests/`)

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_integration_workflow.py
├── test_main_app.py
├── test_api_structure.py
├── test_cache_service.py
├── test_database.py
├── test_error_handling.py
├── test_google_books_service.py
├── test_google_scholar_service.py
├── test_research_orchestrator.py
└── test_sciencedirect_service.py
```

## Running Tests

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run unit tests only
npm run test:unit

# Run integration tests only
npm run test:integration

# Run tests in watch mode
npm run test:watch

# Run tests for CI
npm run test:ci
```

### Backend Tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Run integration tests only
python -m pytest tests/test_integration_workflow.py -v

# Run unit tests only (exclude integration)
python -m pytest tests/ -v -m "not integration"

# Run with HTML coverage report
python -m pytest tests/ --cov=. --cov-report=html

# Use the comprehensive test runner
python run_tests.py
```

### Run All Tests

```bash
# Run comprehensive test suite for both frontend and backend
./run_all_tests.sh
```

## Test Configuration

### Frontend Configuration

**Jest Configuration** (`frontend/jest.config.js`):
- Uses Next.js Jest configuration
- JSDOM test environment
- Coverage thresholds: 80% for all metrics
- Custom module name mapping
- Comprehensive setup file

**Setup File** (`frontend/jest.setup.js`):
- Testing Library DOM matchers
- Next.js router mocks
- React Query mocks
- Global mocks (fetch, matchMedia, etc.)

### Backend Configuration

**Pytest Configuration** (`backend/pytest.ini`):
- Async test support
- Coverage reporting
- Test markers for categorization
- Strict configuration

**Coverage Configuration** (`backend/.coveragerc`):
- Source code coverage
- Exclusion patterns
- HTML and XML report generation

## Test Fixtures and Mocks

### Frontend Fixtures (`frontend/src/__tests__/fixtures/mockData.ts`)

- `mockResearchQuery`: Sample research query data
- `mockScholarResult`: Google Scholar result mock
- `mockBooksResult`: Google Books result mock
- `mockScienceDirectResult`: ScienceDirect result mock
- `mockResearchResult`: Complete research result
- `mockApiResponses`: API response mocks
- `createMockFetch`: Utility for mocking fetch calls

### Backend Fixtures (`backend/tests/conftest.py`)

- Database mocks (MongoDB collections)
- External API mocks (HTTP clients)
- Test data generators
- Async test helpers
- Environment setup

## Integration Tests

### Frontend Integration Tests

1. **Research Workflow** (`research-workflow.test.tsx`):
   - Complete user journey from query to results
   - Error handling and retry functionality
   - Navigation between pages
   - Offline state handling

2. **API State Management** (`api-state-management.test.tsx`):
   - React Query integration
   - Cache management
   - Background refetching
   - Optimistic updates
   - Error recovery

### Backend Integration Tests

1. **Research Workflow** (`test_integration_workflow.py`):
   - End-to-end API testing
   - Database integration
   - External API mocking
   - Error resilience
   - Concurrent request handling

2. **Main Application** (`test_main_app.py`):
   - FastAPI application lifecycle
   - Middleware functionality
   - CORS configuration
   - Error handling
   - Security headers

## Coverage Requirements

### Minimum Coverage Thresholds

- **Frontend**: 80% for branches, functions, lines, and statements
- **Backend**: 80% overall coverage

### Coverage Reports

- **Frontend**: `frontend/coverage/` (HTML), `frontend/coverage/lcov.info` (LCOV)
- **Backend**: `backend/htmlcov/` (HTML), `backend/coverage.xml` (XML)

## Quality Gates

### Automated Checks

1. **Code Coverage**: Minimum 80% coverage required
2. **Test Execution**: All tests must pass
3. **Linting**: Code must pass linting rules
4. **Security**: No high-severity vulnerabilities
5. **Performance**: Tests must complete within reasonable time

### CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/test.yml`) includes:

1. **Frontend Tests**:
   - Node.js matrix testing (18.x, 20.x)
   - Linting, unit tests, integration tests
   - Coverage reporting to Codecov

2. **Backend Tests**:
   - Python matrix testing (3.9, 3.10, 3.11)
   - MongoDB service for integration tests
   - Comprehensive test execution
   - Coverage reporting to Codecov

3. **Quality Gates**:
   - Coverage threshold enforcement
   - Code quality checks
   - Security scanning

## Test Data Management

### Mock Data Strategy

- **Consistent Fixtures**: Reusable mock data across tests
- **Realistic Data**: Mock data reflects actual API responses
- **Edge Cases**: Include error conditions and edge cases
- **Isolation**: Each test uses isolated mock data

### Database Testing

- **Test Database**: Separate MongoDB database for testing
- **Data Cleanup**: Automatic cleanup between tests
- **Transaction Isolation**: Tests don't interfere with each other

## Best Practices

### Writing Tests

1. **Descriptive Names**: Test names should clearly describe what is being tested
2. **Arrange-Act-Assert**: Follow the AAA pattern
3. **Single Responsibility**: Each test should test one specific behavior
4. **Independent Tests**: Tests should not depend on each other
5. **Mock External Dependencies**: Mock all external services and APIs

### Test Organization

1. **Logical Grouping**: Group related tests in describe blocks
2. **Setup and Teardown**: Use proper setup and cleanup
3. **Shared Utilities**: Extract common test utilities
4. **Documentation**: Comment complex test scenarios

### Performance

1. **Fast Execution**: Tests should run quickly
2. **Parallel Execution**: Use parallel test execution where possible
3. **Efficient Mocking**: Mock only what's necessary
4. **Resource Cleanup**: Clean up resources after tests

## Troubleshooting

### Common Issues

1. **Async Test Failures**: Ensure proper async/await usage
2. **Mock Leakage**: Clear mocks between tests
3. **Environment Variables**: Set test environment variables
4. **Database Connections**: Ensure test database is available

### Debugging Tests

1. **Verbose Output**: Use `-v` flag for detailed output
2. **Single Test**: Run individual tests for debugging
3. **Console Logging**: Add temporary console.log statements
4. **Debugger**: Use debugger statements in tests

## Continuous Improvement

### Metrics to Monitor

1. **Test Coverage**: Track coverage trends
2. **Test Execution Time**: Monitor test performance
3. **Flaky Tests**: Identify and fix unstable tests
4. **Test Maintenance**: Keep tests up to date with code changes

### Regular Reviews

1. **Test Effectiveness**: Review test quality regularly
2. **Coverage Gaps**: Identify areas needing more tests
3. **Test Refactoring**: Refactor tests as code evolves
4. **Tool Updates**: Keep testing tools and dependencies updated