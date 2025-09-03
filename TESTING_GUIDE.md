# Testing Guide for FPL Application

## Overview

This guide outlines the testing strategy and best practices for the FPL application. Our goal is to maintain high code quality and prevent regressions through comprehensive testing.

## Testing Pyramid

```
    /\
   /  \     E2E Tests (Few, High-Level)
  /____\    
 /      \   Integration Tests (Some, Medium-Level)
/________\  Unit Tests (Many, Low-Level)
```

## 1. Unit Tests

### What to Test
- Individual functions and methods
- Model validation and business logic
- Database operations
- Service layer functions
- Utility functions

### Test Structure
```python
@pytest.mark.unit
class TestPlayerService:
    """Test cases for PlayerService"""
    
    @pytest.fixture(autouse=True)
    def setup_service(self, db_manager):
        """Set up service with test database"""
        self.player_service = PlayerService(db_manager)
    
    def test_get_all_players(self, db_manager):
        """Test getting all players"""
        # Arrange
        # Act
        # Assert
```

### Best Practices
- Use descriptive test names that explain the scenario
- Follow AAA pattern (Arrange, Act, Assert)
- Test both happy path and edge cases
- Mock external dependencies
- Use fixtures for common setup

### Running Unit Tests
```bash
# Run all unit tests
pytest backend/tests/ -m unit -v

# Run specific test file
pytest backend/tests/test_models.py -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

## 2. Integration Tests

### What to Test
- API endpoints
- Database integration
- Service layer integration
- External API interactions

### Test Structure
```python
@pytest.mark.integration
class TestAPIEndpoints:
    """Test all API endpoints comprehensively"""
    
    def test_api_players(self, client):
        """Test /api/players endpoint"""
        resp = client.get("/api/players")
        assert resp.status_code == 200
        # ... more assertions
```

### Best Practices
- Use test database with real schema
- Test full request/response cycle
- Verify database state changes
- Test error conditions and edge cases

### Running Integration Tests
```bash
# Run all integration tests
pytest backend/tests/ -m integration -v

# Run specific integration test
pytest backend/tests/test_endpoints.py -v
```

## 3. End-to-End Tests

### What to Test
- User workflows
- Page rendering
- Interactive elements
- Cross-browser compatibility

### Test Structure (Playwright)
```typescript
test('search filters rows', async ({ page }) => {
  // Navigate to page
  await page.goto('/players2');
  
  // Wait for elements to load
  await expect(page.locator('#players2Table')).toBeVisible();
  
  // Perform actions
  await searchInput.fill('salah');
  
  // Verify results
  expect(after).toBeLessThanOrEqual(before);
});
```

### Best Practices
- Use reliable selectors (IDs over classes)
- Wait for elements to be ready
- Test on multiple viewport sizes
- Handle async operations properly
- Use page object pattern for complex pages

### Running E2E Tests
```bash
# Run all E2E tests
npm run test:e2e

# Run specific test file
npx playwright test tests/e2e/players2.spec.ts

# Run in headed mode for debugging
npx playwright test --headed
```

## 4. Test-Driven Development (TDD)

### TDD Cycle
1. **Red**: Write a failing test
2. **Green**: Write minimal code to pass the test
3. **Refactor**: Clean up the code while keeping tests green

### Example TDD Workflow
```python
# 1. Write failing test
def test_player_price_validation():
    """Test that player price must be positive"""
    with pytest.raises(ValueError):
        Player(name="Test", price=-5.0, ...)

# 2. Run test (should fail)
# 3. Implement minimal validation
# 4. Run test (should pass)
# 5. Refactor if needed
```

### When to Use TDD
- New features
- Bug fixes
- Refactoring
- API changes

## 5. Test Data Management

### Test Database
- Use temporary SQLite database for tests
- Populate with realistic test data
- Clean up after each test
- Use fixtures for common data

### Test Data Fixtures
```python
@pytest.fixture
def sample_player_data():
    """Sample player data for testing"""
    return {
        'id': 999,
        'name': 'Test Player',
        'position': 'Midfielder',
        'team': 'Test Team',
        'price': 8.0,
        # ... other fields
    }
```

### Mocking External Services
```python
@patch('backend.services.live_fpl_service.requests.get')
def test_fpl_api_integration(mock_get, db_manager):
    """Test FPL API integration with mocked responses"""
    mock_get.return_value.json.return_value = {'players': []}
    # ... test implementation
```

## 6. Test Coverage

### Coverage Goals
- **Unit Tests**: 90%+
- **Integration Tests**: 80%+
- **Overall Coverage**: 85%+

### Coverage Reports
```bash
# Generate coverage report
pytest --cov=backend --cov-report=html

# View in browser
open htmlcov/index.html
```

### Coverage Exclusions
- Configuration files
- Database migration scripts
- CLI entry points
- Error handling edge cases

## 7. Continuous Integration

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### CI Pipeline
- Tests run on every PR
- Coverage reports generated
- Quality checks enforced
- Security scans performed

### Branch Protection
- Tests must pass before merge
- Code review required
- Coverage thresholds enforced
- No force pushes to main

## 8. Debugging Tests

### Common Issues
1. **Flaky Tests**: Add proper waits and assertions
2. **Database State**: Use transaction rollbacks
3. **Async Operations**: Wait for completion
4. **Selector Issues**: Use reliable selectors

### Debug Commands
```bash
# Run single test with verbose output
pytest test_file.py::test_function -v -s

# Run with debugger
pytest --pdb

# Run with coverage and stop on first failure
pytest --cov=backend --maxfail=1
```

### Playwright Debugging
```bash
# Run in headed mode
npx playwright test --headed

# Run with debug mode
npx playwright test --debug

# Show trace
npx playwright show-trace trace.zip
```

## 9. Performance Testing

### Load Testing
- Test API endpoints under load
- Monitor database performance
- Check memory usage
- Verify response times

### Tools
- Locust for API load testing
- Playwright for UI performance
- Database query analysis
- Memory profiling

## 10. Security Testing

### What to Test
- SQL injection prevention
- XSS protection
- CSRF protection
- Authentication/authorization
- Input validation

### Security Tools
- Bandit for Python security
- Safety for dependency checks
- CodeQL for vulnerability scanning
- OWASP ZAP for web security

## 11. Test Maintenance

### Regular Tasks
- Update test data
- Review and update mocks
- Clean up test files
- Update test dependencies
- Review coverage reports

### Test Review Checklist
- [ ] Tests are descriptive and clear
- [ ] Edge cases are covered
- [ ] Mocks are appropriate
- [ ] Test data is realistic
- [ ] Assertions are specific
- [ ] No hardcoded values
- [ ] Proper cleanup is done

## 12. Resources

### Documentation
- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)

### Tools
- Pytest for Python testing
- Playwright for E2E testing
- Coverage.py for coverage
- Pre-commit for hooks
- GitHub Actions for CI/CD

### Team Contacts
- Backend Team: @backend-team
- Frontend Team: @frontend-team
- QA Team: @qa-team
- DevOps Team: @devops-team

---

**Remember**: Good tests are the foundation of reliable software. Write tests first, keep them simple, and maintain them regularly.
