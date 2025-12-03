# Testing Guide

This document explains how to run tests for both backend and frontend without Docker.

## Backend Tests

### Prerequisites

Install test dependencies:

```bash
cd backend/api
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Running Tests

**Run all tests:**
```bash
python run_tests.py
```

**Run with verbose output:**
```bash
python run_tests.py -v
```

**Run specific test file:**
```bash
python run_tests.py tests/test_auth.py
```

**Run specific test:**
```bash
python run_tests.py -k test_hash_password
```

**Run with coverage:**
```bash
python run_tests.py --cov
```

**Generate HTML coverage report:**
```bash
python run_tests.py --cov --cov-report=html
# Open htmlcov/index.html in browser
```

### Test Structure

```
backend/api/tests/
├── conftest.py          # Pytest fixtures and configuration
├── test_config.py       # Configuration tests
├── test_models.py       # Database model tests
└── test_auth.py         # Authentication tests
```

### What's Tested

- ✅ Configuration loading and validation
- ✅ User model creation and constraints
- ✅ InferenceRequest model
- ✅ Password hashing and verification
- ✅ JWT token creation and validation
- ✅ User authentication flow

## Frontend Tests

### Prerequisites

Install dependencies:

```bash
cd frontend
npm install
```

### Running Tests

**Run all tests:**
```bash
npm test
```

**Run in watch mode:**
```bash
npm test -- --watch
```

**Run with UI:**
```bash
npm run test:ui
```

**Run with coverage:**
```bash
npm run test:coverage
```

**Run specific test file:**
```bash
npm test -- Login.test.tsx
```

### Test Structure

```
frontend/src/tests/
├── setup.ts             # Test setup and configuration
├── Login.test.tsx       # Login component tests
└── App.test.tsx         # App component tests
```

### What's Tested

- ✅ Login form rendering
- ✅ Input field updates
- ✅ Form validation
- ✅ Loading states
- ✅ App authentication flow
- ✅ Token management

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          cd backend/api
          pip install -r requirements.txt -r requirements-test.txt
          python run_tests.py
  
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: |
          cd frontend
          npm install
          npm test
```

## Writing New Tests

### Backend Test Example

```python
# tests/test_example.py
import pytest
from app.models import User

class TestExample:
    def test_something(self, test_db):
        """Test description."""
        # Arrange
        user = User(id="1", username="test")
        
        # Act
        test_db.add(user)
        test_db.commit()
        
        # Assert
        assert user.username == "test"
```

### Frontend Test Example

```typescript
// src/tests/Example.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MyComponent from '../components/MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

## Troubleshooting

### Backend

**Import errors:**
```bash
# Make sure you're in the backend/api directory
cd backend/api
# Install dependencies
pip install -r requirements.txt -r requirements-test.txt
```

**Database errors:**
Tests use in-memory SQLite, no external database needed.

### Frontend

**Module not found:**
```bash
# Install dependencies
npm install
```

**jsdom errors:**
```bash
# Reinstall jsdom
npm install --save-dev jsdom
```

## Best Practices

1. **Write tests before fixing bugs** - Helps prevent regressions
2. **Keep tests focused** - One test should test one thing
3. **Use descriptive names** - Test names should explain what they test
4. **Mock external dependencies** - Don't make real API calls in tests
5. **Maintain test coverage** - Aim for >80% coverage
6. **Run tests before committing** - Catch issues early
