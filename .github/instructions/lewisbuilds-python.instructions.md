description: 'lewisbuilds Python coding standards and best practices - mandatory compliance required'
applyTo: '**/*.py'
---

# lewisbuilds Python Coding Standards

## Mission Statement

You are an expert Python developer working within the lewisbuilds team. All code you generate, review, or refactor must strictly adhere to lewisbuilds Python coding standards. These standards are mandatory and non-negotiable for all lewisbuilds Python projects, tools, automations, APIs, and services.

## Precedence of Standards

When conflicts exist between standards, follow this precedence order:

1. **lewisbuilds Overrides** (this document)
2. **Google Python Style Guide**
3. **PEP 8** (Style Guide for Python Code)
4. **PEP 257** (Docstring Conventions)

## Language Version Requirements

### Python 3.10+ (Mandatory)

All lewisbuilds projects must use **Python 3.10 or later**. You must leverage modern Python features including:

- **Type hints** (mandatory for all functions and methods)
- **Dataclasses** for data structures where appropriate
- **Structural pattern matching** (`match` statements)
- **Modern typing improvements** (`Final`, `Protocol`, `TypedDict`)
- **Context managers** for resource management

```python
# ✅ CORRECT: Modern Python 3.10+ with type hints
from typing import Final
from dataclasses import dataclass

MAX_RETRIES: Final[int] = 3

@dataclass
class User:
    user_id: int
    username: str
    email: str

def get_user(user_id: int) -> User | None:
    """Retrieve user by ID."""
    # Implementation
    pass

# ❌ INCORRECT: Missing type hints
def get_user(user_id):
    # Implementation
    pass
```

## Project Structure Standards

### Repository and Module Naming

- **Repository names**: Use `kebab-case`
- **Python modules**: Use `snake_case`
- Module directory must be at the top level of the repository

### Required Project Layout

```
<repo-name>/
│
├── pyproject.toml          # REQUIRED
├── README.md               # REQUIRED
├── <module_name>/          # Main package (kebab-case → snake_case)
│   ├── __init__.py
│   ├── module1.py
│   └── module2.py
│
└── tests/                  # REQUIRED
    └── test_module1.py
```

### Project Structure Requirements

✅ **MUST:**
- Include `pyproject.toml` in every project
- Place all importable code inside the module directory
- Place tests under `tests/` directory
- Use CLI entry points in dedicated module (e.g., `cli.py` or `cli/`)

❌ **MUST NOT:**
- Use namespace packages (unless explicitly justified)
- Place importable code at repository root
- Mix test code with production code

## Import Standards (Mandatory)

### Import Rules

lewisbuilds uses **isort** to automatically enforce import ordering. All projects must include isort configuration.

✅ **MUST:**
- Place imports at the top of the file (after module docstring)
- Use **absolute imports only**
- Follow isort grouping and ordering
- Separate import groups with single blank line

❌ **MUST NOT:**
- Use wildcard imports (`from x import *`)
- Use relative imports
- Place imports inside functions (except justified cases)

### Import Grouping Order

Imports must be grouped in this order:

1. **Standard library**
2. **Third-party packages**
3. **Internal shared lewisbuilds libraries**
4. **Local project modules**

```python
# ✅ CORRECT: Proper import grouping and ordering
import datetime
import logging
from typing import Dict, List

import requests
from pydantic import BaseModel

from lewisbuilds.utils.retry import RetryPolicy

from myproject.core import processor
from myproject.models import User

# ❌ INCORRECT: Mixed grouping, no separation
from myproject.core import processor
import requests
import logging
from lewisbuilds.utils.retry import RetryPolicy
```

### Exceptions for Function-Level Imports

Imports inside functions are permitted **only** for:

1. **Avoiding circular imports**
2. **Reducing startup time** (heavy dependencies)
3. **Optional dependencies** (feature-specific)

```python
# ✅ ACCEPTABLE: Local import to avoid circular dependency
def process_data(data: dict) -> Result:
    """Process data with heavy dependency."""
    # Heavy ML library loaded only when needed
    import torch

    return torch.process(data)
```

### Required isort Configuration

Include this in `pyproject.toml`:

```toml
[tool.isort]
profile = "black"
known_first_party = ["my_project"]
src_paths = ["my_project"]
line_length = 88
```

## Naming Conventions (Mandatory)

| Item               | Convention         | Example              | Rule     |
|--------------------|--------------------|----------------------|----------|
| Modules            | `snake_case`       | `data_loader.py`     | MUST     |
| Functions          | `snake_case`       | `load_data()`        | MUST     |
| Variables          | `snake_case`       | `retry_count`        | MUST     |
| Classes            | `PascalCase`       | `DataClient`         | MUST     |
| Constants          | `UPPER_SNAKE_CASE` | `MAX_CONNECTIONS`    | MUST     |
| Private functions  | `_snake_case`      | `_serialize()`       | MUST     |
| Private variables  | `_snake_case`      | `_internal_state`    | MUST     |

```python
# ✅ CORRECT: Proper naming conventions
from typing import Final

MAX_RETRIES: Final[int] = 3
DEFAULT_TIMEOUT: Final[int] = 30

class DataProcessor:
    """Process data from multiple sources."""

    def __init__(self) -> None:
        self._retry_count: int = 0

    def process_data(self, input_data: dict) -> dict:
        """Process input data."""
        return self._transform_data(input_data)

    def _transform_data(self, data: dict) -> dict:
        """Internal transformation logic."""
        return data

# ❌ INCORRECT: Inconsistent naming
class dataProcessor:  # Should be PascalCase
    def ProcessData(self, InputData):  # Should be snake_case
        return self.__TransformData(InputData)  # Double underscore inappropriate
```

## Type Hints (Mandatory)

### Type Hint Requirements

✅ **MUST:**
- Use type hints for **all** function parameters
- Use type hints for **all** function return values
- Use type hints for class attributes
- Use `typing` module for complex types

❌ **MUST NOT:**
- Omit type hints from any function signature
- Use dynamic typing without explicit `Any` annotation

```python
# ✅ CORRECT: Complete type hints
from typing import Dict, List, Optional, Final

def load_user(user_id: int) -> Optional[Dict[str, str]]:
    """Load user data by ID."""
    # Implementation
    pass

def process_items(items: List[str], max_count: int = 10) -> Dict[str, int]:
    """Process list of items."""
    result: Dict[str, int] = {}
    # Implementation
    return result

# ❌ INCORRECT: Missing type hints
def load_user(user_id):
    # Implementation
    pass

def process_items(items, max_count=10):
    result = {}
    return result
```

### Complex Type Examples

```python
from typing import Dict, List, Optional, Union, Final, Protocol
from dataclasses import dataclass

# Type aliases for clarity
UserId = int
UserData = Dict[str, Union[str, int]]

# Protocol for structural typing
class DataSource(Protocol):
    def fetch(self, id: int) -> Optional[dict]:
        ...

# Dataclass with type hints
@dataclass
class Configuration:
    api_url: str
    timeout: int
    max_retries: Final[int] = 3

def fetch_users(
    source: DataSource,
    user_ids: List[UserId]
) -> Dict[UserId, Optional[UserData]]:
    """Fetch multiple users from data source."""
    # Implementation
    pass
```

## Constants and Immutability

### Constant Declaration

Python does not have true compile-time constants. lewisbuilds uses two approaches:

1. **Convention**: `UPPER_SNAKE_CASE` (PEP 8)
2. **Type annotation**: `typing.Final` (type checker enforcement)

```python
# ✅ CORRECT: Constants with Final annotation
from typing import Final

DEFAULT_TIMEOUT: Final[int] = 5
API_BASE_URL: Final[str] = "https://example.com"
MAX_CONNECTIONS: Final[int] = 100

# ✅ ACCEPTABLE: Convention-based constants (when Final is impractical)
RETRY_DELAYS = [1, 2, 5, 10]  # List is mutable, but intent is clear

# ❌ INCORRECT: No type hint or capitalization
default_timeout = 5
ApiBaseUrl = "https://example.com"
```

### Important Notes About `Final`

- `Final` is enforced by static type checkers (`mypy`, `pylance`)
- Python runtime **does not** prevent reassignment
- Use for code clarity and tooling support
- Combine with `UPPER_SNAKE_CASE` for maximum clarity

## Docstring Standards (Mandatory)

### Google-Style Docstrings

lewisbuilds adopts **Google-style docstrings** as defined in the Google Python Style Guide.

```python
# ✅ CORRECT: Complete Google-style docstring
def load_user(user_id: int, include_inactive: bool = False) -> Optional[User]:
    """Load a user from the database.

    This function retrieves a user by their unique identifier. If the user
    does not exist or is inactive (and include_inactive is False), returns None.

    Args:
        user_id: The unique identifier of the user.
        include_inactive: Whether to include inactive users in the search.
            Defaults to False.

    Returns:
        A populated User object if found, None otherwise.

    Raises:
        DatabaseError: If the database connection fails.
        ValueError: If user_id is negative.

    Example:
        >>> user = load_user(12345)
        >>> if user:
        ...     print(user.username)
    """
    # Implementation
    pass

# ❌ INCORRECT: Missing or inadequate docstring
def load_user(user_id: int, include_inactive: bool = False) -> Optional[User]:
    # Implementation
    pass
```

### Docstring Requirements

✅ **MUST:**
- Include docstring for all public functions, methods, and classes
- Use Google-style format consistently
- Document all parameters in `Args:` section
- Document return value in `Returns:` section
- Document exceptions in `Raises:` section
- Include usage examples for complex functions

❌ **MUST NOT:**
- Use inconsistent docstring formats
- Omit docstrings from public APIs
- Document private functions with same detail (summary line sufficient)

### Module-Level Docstrings

```python
"""Data processing utilities for lewisbuilds projects.

This module provides utilities for loading, transforming, and validating
data from multiple sources. It includes support for retry logic, caching,
and error handling.

Typical usage example:

    processor = DataProcessor(config)
    result = processor.process_file("input.json")
"""

from typing import Final
# ... rest of module
```

## Security Requirements (Mandatory)

### Prohibited Practices

❌ **MUST NEVER:**
- Use `exec()` or `eval()` with user input
- Use `shell=True` in subprocess calls
- Store secrets in the repository
- Use `yaml.load()` (use `yaml.safe_load()` instead)
- Accept untrusted data without validation

### Required Security Practices

✅ **MUST:**
- Validate all external input with `pydantic` or validators
- Use HTTPS only for outbound requests
- Store secrets in environment variables or secret management systems
- Sanitize user input before using in queries or commands
- Use parameterized queries for database operations

```python
# ✅ CORRECT: Secure practices
import os
from pydantic import BaseModel, validator

API_KEY = os.environ.get("API_KEY")  # From environment

class UserInput(BaseModel):
    """Validated user input."""
    email: str
    age: int

    @validator("email")
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v:
            raise ValueError("Invalid email")
        return v

# ✅ CORRECT: Parameterized query
def get_user(conn, user_id: int) -> dict:
    """Get user with parameterized query."""
    return conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

# ❌ INCORRECT: Security vulnerabilities
API_KEY = "sk_hardcoded_secret_12345"  # Never hardcode secrets

def get_user_unsafe(conn, user_id: str) -> dict:
    # SQL injection vulnerability
    return conn.execute(
        f"SELECT * FROM users WHERE id = {user_id}"
    ).fetchone()

def execute_command(user_input: str) -> None:
    # Command injection vulnerability
    subprocess.run(user_input, shell=True)
```

## Performance Best Practices

### Preferred Patterns

✅ **PREFER:**
- List/dict/set comprehensions over `map()`/`filter()`
- Generators for large datasets
- `dataclasses` for lightweight objects
- `functools.lru_cache` for expensive computations
- Avoid unnecessary copying of data structures

```python
# ✅ CORRECT: Efficient comprehension
numbers = [x * 2 for x in range(1000) if x % 2 == 0]

# ✅ CORRECT: Generator for large dataset
def process_large_file(filepath: str):
    """Process file line by line without loading into memory."""
    with open(filepath) as f:
        for line in f:
            yield process_line(line)

# ✅ CORRECT: Caching expensive computation
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(n: int) -> int:
    """Calculate Fibonacci with caching."""
    if n < 2:
        return n
    return expensive_calculation(n - 1) + expensive_calculation(n - 2)

# ❌ INCORRECT: Inefficient patterns
numbers = list(map(lambda x: x * 2, filter(lambda x: x % 2 == 0, range(1000))))

def load_entire_file(filepath: str) -> list:
    """Loads entire file into memory - inefficient for large files."""
    with open(filepath) as f:
        return f.readlines()  # Loads everything at once
```

## Error Handling Standards

### Exception Handling

✅ **MUST:**
- Catch specific exceptions, not bare `except:`
- Provide meaningful error messages
- Log errors with context
- Re-raise exceptions when appropriate

```python
# ✅ CORRECT: Specific exception handling
import logging

logger = logging.getLogger(__name__)

def load_config(filepath: str) -> dict:
    """Load configuration from file."""
    try:
        with open(filepath) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {filepath}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        raise ValueError(f"Configuration file {filepath} contains invalid JSON") from e

# ❌ INCORRECT: Bare except and swallowed exceptions
def load_config_bad(filepath: str) -> dict:
    try:
        with open(filepath) as f:
            return json.load(f)
    except:  # Too broad
        return {}  # Swallows error without logging
```

## Versioning Standards

lewisbuilds projects follow **Semantic Versioning** (SemVer 2.0.0): `MAJOR.MINOR.PATCH`

### Version Increment Rules

**MAJOR (X.0.0)** - Breaking changes:
- Added features that break existing usage
- Changed behavior that is not backward compatible
- Removed functionality of any kind

**MINOR (0.X.0)** - Backward-compatible additions:
- Added features that are fully backward compatible
- Changed functionality that expands behavior without breaking existing usage
- Deprecated features (still accessible, scheduled for removal)

**PATCH (0.0.X)** - Backward-compatible fixes:
- Fixed bugs or issues
- Security improvements
- Performance optimizations
- Internal maintenance

```python
# Version must be defined in __init__.py or version.py
__version__ = "1.2.3"
```

## Code Review Checklist

Before submitting code for review, verify:

- [ ] Python 3.10+ features used appropriately
- [ ] All functions have type hints
- [ ] All public functions have Google-style docstrings
- [ ] Imports are organized with isort
- [ ] Naming conventions followed (snake_case, PascalCase, UPPER_SNAKE_CASE)
- [ ] Constants use `Final` annotation and UPPER_SNAKE_CASE
- [ ] No security vulnerabilities (no hardcoded secrets, no `eval()`, etc.)
- [ ] No wildcard imports (`from x import *`)
- [ ] Exception handling is specific, not bare `except:`
- [ ] Tests exist for new functionality
- [ ] Project structure follows lewisbuilds standards
- [ ] `pyproject.toml` is present and configured

## Tooling Requirements

### Required Tools

lewisbuilds projects must use these tools:

- **isort**: Import sorting and organization
- **mypy**: Static type checking
- **pylint** or **ruff**: Linting and code quality
- **black**: Code formatting
- **pytest**: Unit testing

### Recommended pyproject.toml Configuration

```toml
[tool.isort]
profile = "black"
line_length = 88
known_first_party = ["my_project"]
src_paths = ["my_project"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.black]
line-length = 88
target-version = ["py310"]
```

## References

- **Google Python Style Guide**: https://google.github.io/styleguide/pyguide.html
- **PEP 8**: https://peps.python.org/pep-0008/
- **PEP 257**: https://peps.python.org/pep-0257/
- **Python Typing**: https://docs.python.org/3/library/typing.html
- **Semantic Versioning**: https://semver.org/spec/v2.0.0.html

---

## Enforcement

These standards are **mandatory** for all lewisbuilds Python projects. Code that does not comply with these standards will not be accepted in code reviews. Use automated tooling (isort, mypy, black, pylint/ruff) to ensure compliance before submitting code for review.
