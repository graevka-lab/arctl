# Contributing to ARCTL

Thank you for considering contributing to ARCTL! This document provides guidelines and best practices.

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Be respectful, constructive, and collaborative.

---

## Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/graevka-lab/arctl.git
cd arctl
pip install -e .
```

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b bugfix/issue-description
```

### 3. Make Your Changes

Follow the guidelines below, then test locally:

```bash
python run_tests.py
```

---

## Code Style & Standards

### Python Style

- **PEP 8** for all code
- **4 spaces** for indentation (no tabs)
- **Type hints** on all public functions
- **Docstrings** in Google format for all functions

Example:

```python
def calculate_repetition(tokens: List[str], window: int = 50) -> float:
    """
    Calculate repetition score from a token sequence.
    
    Uses trigram overlap to detect looping patterns.
    
    Args:
        tokens: Input token list
        window: Analysis window size (tokens)
    
    Returns:
        Repetition score (0.0 = diverse, 1.0 = highly repetitive)
    
    Example:
        >>> tokens = ["the", "the", "the"]
        >>> score = calculate_repetition(tokens)
        >>> score > 0.8
        True
    """
    # Implementation...
```

### Naming Conventions

- **Functions**: `snake_case` (e.g., `calculate_entropy`)
- **Classes**: `PascalCase` (e.g., `SystemState`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_ENERGY`)
- **Private**: prefix with `_` (e.g., `_internal_method`)

### Type Hints

Always use complete type hints:

```python
# Good
def step(metrics: RawMetrics, state: SystemState, now: float) -> SystemState:
    ...

# Bad
def step(metrics, state, now):
    ...

# Also good (Optional types)
def get_config(name: str, default: Optional[str] = None) -> Optional[ControllerConfig]:
    ...
```

### Documentation

- Every public function must have a docstring
- Every public class must have a docstring
- Complex algorithms must have inline comments explaining the logic
- Use examples in docstrings for user-facing functions

---

## Testing Requirements

### Unit Tests

Add unit tests for all new functionality:

```python
# tests/test_my_feature.py
import unittest
from arctl.core.my_module import MyClass

class TestMyFeature(unittest.TestCase):
    def setUp(self):
        self.obj = MyClass()
    
    def test_basic_functionality(self):
        result = self.obj.do_something()
        self.assertEqual(result, expected_value)
    
    def test_edge_case(self):
        with self.assertRaises(ValueError):
            self.obj.do_something(invalid_input)
```

### Run Tests Locally

```bash
# Run all tests
python run_tests.py

# Run specific test file
python -m unittest tests.test_my_feature -v

# Run with coverage (if pytest-cov installed)
pytest --cov=arctl tests/
```

### Benchmark Expectations

For performance-critical code, add a benchmark:

```python
# tests/benchmarks.py
def benchmark_my_feature():
    def func():
        my_expensive_operation()
    
    return Benchmarker.benchmark("My feature", func, iterations=10000)
```

Target: Single operations should complete in < 1μs.

---

## Git Workflow

### Commit Messages

Follow conventional commits:

```
feat: Add repetition detection
fix: Handle edge case in energy restoration
docs: Update QUICKSTART.md with examples
test: Add unit tests for chronos module
refactor: Extract common logic into helper function
chore: Update dependencies
```

Format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:

```
fix(kernel): Prevent energy overflow on reset

Energy restoration after 24h gap now properly clamps to max_energy.
Previously would exceed max due to conservative reset logic.

Fixes #42
```

### Pull Requests

1. **Describe the change** — What problem does this solve?
2. **Reference issues** — Link to related GitHub issues
3. **Add tests** — All new code must be tested
4. **Update docs** — If behavior changes, update documentation
5. **Keep it focused** — One feature per PR

Template:

```markdown
## Description
Briefly describe what this PR does.

## Problem
What issue does this solve? Link to #issue_number

## Changes
- List the key changes
- Use bullet points

## Testing
- [ ] Unit tests added
- [ ] Integration tests pass
- [ ] Benchmarks show acceptable performance

## Checklist
- [ ] Code follows style guidelines
- [ ] Docstrings added/updated
- [ ] No breaking changes
- [ ] Ready for review
```

---

## Architecture Decisions

### When Modifying Core Logic

The kernel (`arctl/core/kernel.py`) is the most critical component.

**Before changing:**
1. Understand the existing state machine thoroughly
2. Check the formal spec: `spec/kernel.tla`
3. Run the full test suite (especially integration tests)
4. Consider backward compatibility

**Guidelines:**
- Never remove modes or transitions
- Energy values are immutable once committed
- Time model changes need Chronos updates
- All changes must preserve determinism

### Adding New Modules

For new components:

1. **Create minimal interface** — Keep it small and focused
2. **Write tests first** — TDD approach recommended
3. **Document philosophy** — Why does this module exist?
4. **Add examples** — Show how to use it

Structure:

```python
# arctl/domain/my_module.py
"""
Module docstring explaining purpose and philosophy.

Usage:
    from arctl.domain.my_module import MyClass
    obj = MyClass()
    result = obj.do_something()
"""

class MyClass:
    """Docstring with examples and guarantees."""
    
    def do_something(self) -> str:
        """Docstring with Args, Returns, Examples."""
        ...
```

---

## Documentation

### Updating Docs

When adding features:

1. **Update ARCHITECTURE.md** if design changes
2. **Update QUICKSTART.md** if it's user-facing
3. **Add docstrings** to code
4. **Update TESTING.md** if test patterns change

### Documentation Style

- Be clear and concise
- Use examples liberally
- Explain the "why", not just the "what"
- Link related documentation

---

## Performance Considerations

### Optimization Guidelines

1. **Measure before optimizing** — Use benchmarks
2. **Preserve clarity** — Don't sacrifice readability for speed
3. **Document trade-offs** — Explain why you chose this approach
4. **Test thoroughly** — Optimizations often introduce bugs

### Acceptable Performance Ranges

| Operation | Target | Acceptable |
|-----------|--------|-----------|
| `step()` | < 1μs | 500-2000 ns |
| State transitions | < 3μs | 1500-5000 ns |
| Metric calculation | < 50μs | 10-100 μs |
| Verification | < 100ms | 50-200ms |

---

## Dependency Management

### Adding Dependencies

Keep dependencies minimal. Before adding:

1. **Is it necessary?** Can we implement it ourselves?
2. **Is it maintained?** Active development and issue response?
3. **Is it light?** Check file size and transitive dependencies
4. **Is it compatible?** Works with Python 3.8+?

Update both `pyproject.toml` and `install` docs.

### Optional Dependencies

Heavy dependencies (e.g., `sentence-transformers`) should be optional:

```toml
# pyproject.toml
[project.optional-dependencies]
verification = ["sentence-transformers"]

# In code
try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
```

---

## Reporting Issues

### Bug Reports

Include:
- Python version
- Full error traceback
- Minimal reproduction script
- Expected vs actual behavior
- Environment details (OS, installed packages)

### Feature Requests

Include:
- Use case — Why do you need this?
- Proposed solution — How would it work?
- Alternatives — Other approaches considered?
- Examples — Show usage

---

## Review Process

### What We Look For

1. **Correctness** — Does it work as intended?
2. **Tests** — Is it well-tested?
3. **Documentation** — Is it clear and complete?
4. **Style** — Does it follow guidelines?
5. **Performance** — Is it efficient?
6. **Architecture** — Does it fit the system design?

### Getting Reviewed

- Be patient — Maintainers volunteer their time
- Respond to feedback — Iterate on suggestions
- Ask questions — If feedback is unclear, ask for clarification

---

## Release Process

Releases follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Example: `1.0.0` → `1.1.0` (new feature) → `1.1.1` (bug fix)

---

## Useful Resources

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design
- [TESTING.md](docs/TESTING.md) — Test guide
- [kernel.tla](spec/kernel.tla) — Formal specification
- [PEP 8](https://pep8.org/) — Python style guide

---

## Questions?

- **GitHub Issues** — For bugs and feature requests
- **Discussions** — For questions and ideas
- **Email** — graevka@example.com

---

Thank you for contributing! Your help makes ARCTL better. 🚀
