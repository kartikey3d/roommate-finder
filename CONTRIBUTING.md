# Contributing to Roommate Finder

First off, thank you for considering contributing to Roommate Finder! It's people like you that make this project better.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected behavior** vs. actual behavior
- **Environment details** (OS, Python version, etc.)
- **Error messages** or logs (if applicable)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - why is this enhancement needed?
- **Proposed solution** (if you have one)
- **Alternative solutions** you've considered

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the code style** (PEP 8, type hints, docstrings)
3. **Add tests** for any new functionality
4. **Update documentation** if needed
5. **Ensure all tests pass** before submitting
6. **Write a clear commit message**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/kartikey3d/roommate-finder.git
cd roommate-finder

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up pre-commit hooks (optional)
pre-commit install

# Run tests
pytest
```

## Code Style

### Python Style Guide

- Follow **PEP 8** conventions
- Use **type hints** for all function parameters and returns
- Write **docstrings** for classes and functions
- Keep functions **under 50 lines** when possible
- Use **meaningful variable names**

### Example:

```python
async def create_user_profile(
    db: AsyncSession,
    user_id: int,
    profile_data: UserProfileCreate
) -> UserProfileResponse:
    """
    Create a new user profile.
    
    Args:
        db: Database session
        user_id: ID of the user
        profile_data: Profile data to create
    
    Returns:
        Created profile response
    
    Raises:
        HTTPException: If user not found or profile exists
    """
    # Implementation...
```

### Code Formatting

Use these tools before committing:

```bash
# Format code
black app/

# Sort imports
isort app/

# Check types
mypy app/

# Lint
flake8 app/
```

## Testing Guidelines

### Writing Tests

- **Unit tests** for pure functions (in `tests/unit/`)
- **Integration tests** for API endpoints (in `tests/integration/`)
- **Test file naming**: `test_*.py`
- **Test function naming**: `test_*`

### Test Structure

```python
def test_feature_name():
    # Arrange - set up test data
    user_data = {"email": "test@example.com"}
    
    # Act - perform the action
    result = create_user(user_data)
    
    # Assert - verify the result
    assert result.email == "test@example.com"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest tests/unit/
```

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```
feat(matching): add distance-based filtering

Implement radius-based location filtering in matching algorithm
to reduce irrelevant matches.

Closes #123
```

```
fix(auth): resolve JWT token expiration issue

Fixed issue where tokens were expiring prematurely due to
incorrect timezone handling.

Fixes #456
```

## Branch Naming

- `feature/description` - for new features
- `fix/description` - for bug fixes
- `docs/description` - for documentation
- `refactor/description` - for refactoring

Examples:
- `feature/add-photo-upload`
- `fix/profile-validation-error`
- `docs/update-api-examples`

## Pull Request Process

1. **Update documentation** for any API changes
2. **Add tests** for new functionality
3. **Ensure CI passes** (all tests, linting)
4. **Request review** from maintainers
5. **Address feedback** if requested
6. **Squash commits** if requested before merge

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
```

## Questions?

Feel free to:
- Open an issue for discussion
- Ask in GitHub Discussions
- Reach out to maintainers

Thank you for contributing! 🎉
