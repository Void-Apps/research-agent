# AI Research Agent

A comprehensive AI-powered research application that aggregates academic content from multiple sources including Google Scholar, Google Books, and ScienceDirect, providing AI-synthesized research summaries.

## 🚀 Features

- **Multi-Source Research**: Searches across Google Scholar, Google Books, and ScienceDirect
- **AI-Powered Synthesis**: Uses Agno AI to provide intelligent research summaries
- **Real-time Results**: Asynchronous processing with live status updates
- **Research History**: Persistent storage and retrieval of past research queries
- **Caching System**: Intelligent caching to improve performance and reduce API calls
- **Responsive UI**: Modern React/Next.js frontend with Tailwind CSS
- **Error Handling**: Comprehensive error handling and user feedback
- **Offline Support**: Graceful degradation when offline

## 🏗️ Architecture

### Frontend (Next.js 15 + React 19)
- **Framework**: Next.js 15 with App Router
- **UI Library**: React 19 with Tailwind CSS
- **State Management**: TanStack Query (React Query) for server state
- **HTTP Client**: Axios for API communication
- **Notifications**: React Hot Toast for user feedback

### Backend (FastAPI + Python)
- **Framework**: FastAPI with async/await support
- **Database**: MongoDB with Motor (async driver)
- **AI Integration**: Agno AI for research synthesis
- **External APIs**: Google Scholar, Google Books, ScienceDirect
- **Caching**: Redis-compatible caching system
- **Monitoring**: Built-in performance and error monitoring

## 🧪 Testing Suite

This project includes a comprehensive testing suite with high coverage standards and automated quality gates.

### Testing Infrastructure

**Frontend Testing:**
- **Framework**: Jest + React Testing Library
- **Coverage**: 80% minimum threshold for all metrics
- **Test Types**: Unit tests, integration tests, component tests
- **Mocking**: Comprehensive mocks for APIs, Next.js router, and browser APIs

**Backend Testing:**
- **Framework**: Pytest with async support
- **Coverage**: 80% minimum threshold
- **Test Types**: Unit tests, integration tests, API tests
- **Mocking**: Database mocks, external API mocks, service mocks

### Running Tests

**Frontend Tests:**
```bash
cd frontend

# Run all tests
npm test

# Run with coverage report
npm run test:coverage

# Run only unit tests
npm run test:unit

# Run only integration tests
npm run test:integration

# Run tests in watch mode
npm run test:watch
```

**Backend Tests:**
```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=. --cov-report=html

# Run integration tests only
python -m pytest tests/test_integration_workflow.py -v

# Run comprehensive test suite
python run_tests.py
```

**Run All Tests:**
```bash
# Run complete test suite for both frontend and backend
./run_all_tests.sh
```

### Test Coverage Reports

- **Frontend Coverage**: `frontend/coverage/index.html`
- **Backend Coverage**: `backend/htmlcov/index.html`
- **CI/CD Reports**: Automatically uploaded to Codecov

### Quality Gates

- ✅ **Code Coverage**: Minimum 80% for both frontend and backend
- ✅ **Test Execution**: All tests must pass
- ✅ **Linting**: ESLint for frontend, automated formatting
- ✅ **Security**: Automated vulnerability scanning
- ✅ **CI/CD**: GitHub Actions workflow with matrix testing

## 📦 Installation

### Prerequisites

- **Node.js**: 18.x or 20.x
- **Python**: 3.9, 3.10, or 3.11
- **MongoDB**: 6.0 or later
- **API Keys**: Google Scholar, Google Books, ScienceDirect, Agno AI

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
# Configure environment variables
npm run dev
```

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Configure environment variables
python -m uvicorn main:app --reload
```

### Environment Variables

**Frontend (.env.local):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend (.env):**
```env
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=ai_research_agent
GOOGLE_SCHOLAR_API_KEY=your_key_here
GOOGLE_BOOKS_API_KEY=your_key_here
SCIENCEDIRECT_API_KEY=your_key_here
AGNO_API_KEY=your_key_here
```

## 🚀 Development

### Project Structure

```
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── lib/             # Utility libraries
│   │   └── __tests__/       # Test files
│   ├── jest.config.js       # Jest configuration
│   └── package.json
├── backend/                  # FastAPI backend application
│   ├── services/            # Business logic services
│   ├── routers/             # API route handlers
│   ├── models/              # Data models
│   ├── database/            # Database connection and utilities
│   ├── tests/               # Test files
│   ├── pytest.ini          # Pytest configuration
│   └── requirements.txt
├── .github/workflows/       # GitHub Actions CI/CD
├── TESTING.md              # Comprehensive testing documentation
└── run_all_tests.sh        # Test runner script
```

### Development Workflow

1. **Feature Development**: Create feature branches from `develop`
2. **Testing**: Write tests for new features (maintain 80% coverage)
3. **Code Review**: Submit pull requests with comprehensive tests
4. **CI/CD**: Automated testing and quality checks on all PRs
5. **Deployment**: Merge to `main` triggers deployment pipeline

### Code Quality Standards

- **TypeScript**: Strict mode enabled for frontend
- **Python**: Type hints and async/await patterns
- **Testing**: Comprehensive unit and integration tests
- **Documentation**: Inline comments and README updates
- **Error Handling**: Graceful error handling throughout

## 🔧 API Documentation

The backend provides a comprehensive REST API:

- **POST /api/research/query**: Submit research query
- **GET /api/research/results/{query_id}**: Get research results
- **GET /api/research/history**: Get research history
- **GET /api/research/status/{query_id}**: Check query status
- **GET /api/health**: Health check endpoint

API documentation is available at `http://localhost:8000/docs` when running the backend.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write comprehensive tests for your changes
4. Ensure all tests pass (`./run_all_tests.sh`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Testing Requirements

- All new features must include comprehensive tests
- Maintain minimum 80% code coverage
- Include both unit and integration tests
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Agno AI**: For providing AI synthesis capabilities
- **Academic APIs**: Google Scholar, Google Books, ScienceDirect
- **Open Source**: Built with amazing open-source technologies

## 📞 Support

For support and questions:
- Create an issue in this repository
- Check the [TESTING.md](TESTING.md) for testing documentation
- Review the API documentation at `/docs`
