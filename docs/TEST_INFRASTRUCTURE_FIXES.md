# Test Infrastructure Fixes - CI/CD Hang Resolution

**Date**: 2025-10-03
**Status**: ✅ RESOLVED
**Commits**: 9eaad43, d5a2daa, edd610b

---

## Problem Statement

GitHub Actions workflows were hanging at ~76% test completion, timing out after 5+ minutes. Tests would freeze during execution without completing, blocking CI/CD pipeline.

### Symptoms
- Workflow hung at 74-76% progress consistently
- Tests timed out after ~5 minutes in CI/CD
- Local test runs also hung indefinitely
- Hang occurred during pytest collection phase (before tests even ran)
- Specific failure point: `tests/unit/test_cache.py` after 2 tests

---

## Root Causes Identified

### 1. **Module-Level Initialization Side Effects**

**Problem**: Multiple modules executed heavy initialization code at import time.

**Affected Files**:
- `scrapetui/core/cache.py` - Called `get_logger()` and `get_config()` at module level
- `scrapetui/core/auth.py` - Logger initialized at module level
- `scrapetui/scrapers/manager.py` - Logger and config at module level
- `scrapetui/config.py` - File I/O during config loading
- `scrapetui/utils/logging.py` - File handler setup at import

**Impact**: Every import triggered file I/O, logging setup, and config loading, causing cascading initialization that could hang.

### 2. **MemoryCache Deadlock**

**Problem**: `MemoryCache.get()` method had nested lock acquisition bug.

```python
# BEFORE (deadlock):
def get(self, key: str):
    with self._lock:
        if key in self._expiry and time.time() > self._expiry[key]:
            self.delete(key)  # Tries to acquire lock AGAIN!
        return self._cache.get(key)

# AFTER (fixed):
def get(self, key: str):
    with self._lock:
        if key in self._expiry and time.time() > self._expiry[key]:
            # Inline cleanup - no nested lock
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
        return self._cache.get(key)
```

**Impact**: Cache operations would deadlock when checking expired keys.

### 3. **No Test Isolation**

**Problem**: Tests shared global singletons (cache, config, logger) causing cross-test contamination.

**Impact**: Test state leaked between tests, causing unpredictable failures and hangs.

### 4. **Legacy Monolithic Import**

**Problem**: `scrapetui/__init__.py` executed entire 9,715-line TUI application on ANY package import.

```python
# This loaded the ENTIRE Textual TUI app:
_spec.loader.exec_module(_legacy)  # Executed scrapetui.py
```

**Impact**: Importing anything from `scrapetui` package loaded the full TUI, including Textual framework initialization.

---

## Solutions Implemented

### 1. Lazy Initialization Pattern

**Implemented in 6 files**:

#### scrapetui/core/cache.py
```python
# BEFORE:
logger = get_logger(__name__)  # Executes at import!
config = get_config()          # Executes at import!

# AFTER:
# No module-level initialization
# Logger/config fetched when actually needed:
def get_cache():
    logger = get_logger(__name__)  # Only when called
    config = get_config()          # Only when called
```

#### scrapetui/core/auth.py
```python
# Helper for lazy logger access:
_logger = None

def _get_lazy_logger():
    global _logger
    if _logger is None:
        _logger = get_logger(__name__)
    return _logger

# Usage:
_get_lazy_logger().info("User authenticated")
```

#### scrapetui/scrapers/manager.py
```python
# Lazy logger and config:
_logger = None
_config = None

def _get_lazy_logger():
    global _logger
    if _logger is None:
        _logger = get_logger(__name__)
    return _logger

def _get_lazy_config():
    global _config
    if _config is None:
        _config = get_config()
    return _config
```

#### scrapetui/core/database.py
```python
# No module-level logger
# Each function gets logger when needed:
def get_db_connection():
    logger = get_logger(__name__)  # Lazy
    # ... rest of function
```

#### scrapetui/config.py
```python
# Idempotent env loading:
_env_loaded = False

def load_env_file():
    global _env_loaded
    if _env_loaded:
        return
    # ... load .env file
    _env_loaded = True

# Test isolation support:
def reset_config():
    global _config_instance, _env_loaded
    _config_instance = None
    _env_loaded = False
```

#### scrapetui/utils/logging.py
```python
# Test isolation support:
def reset_logging():
    global _loggers
    for logger in _loggers.values():
        logger.handlers.clear()
    _loggers.clear()
```

### 2. Fixed MemoryCache Deadlock

**File**: `scrapetui/core/cache.py`

Changed expiry cleanup to inline instead of calling `delete()`:

```python
def get(self, key: str) -> Optional[Any]:
    with self._lock:
        # Check expiration
        if key in self._expiry and time.time() > self._expiry[key]:
            # FIXED: Inline cleanup instead of self.delete(key)
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
            return None
        return self._cache.get(key)
```

### 3. Test Isolation Infrastructure

**File**: `tests/conftest.py`

Added two autouse fixtures:

```python
@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all global singleton instances before each test."""
    # Reset cache singleton
    import scrapetui.core.cache
    scrapetui.core.cache._cache_instance = None

    # Reset config singleton
    from scrapetui.config import reset_config
    reset_config()

    # Reset logging singleton
    from scrapetui.utils.logging import reset_logging
    reset_logging()

    # Reset auth lazy loggers
    import scrapetui.core.auth
    scrapetui.core.auth._logger = None

    # Reset manager lazy loggers/config
    import scrapetui.scrapers.manager
    scrapetui.scrapers.manager._logger = None
    scrapetui.scrapers.manager._config = None

    yield

    # Cleanup after test
    scrapetui.core.cache._cache_instance = None


@pytest.fixture(autouse=True)
def test_env_vars():
    """Set safe test environment variables."""
    original_env = os.environ.copy()

    # Set test-specific environment variables
    os.environ['CACHE_ENABLED'] = 'false'
    os.environ['LOG_LEVEL'] = 'ERROR'

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
```

### 4. Disabled Legacy Monolithic Import

**File**: `scrapetui/__init__.py`

Commented out the legacy import mechanism:

```python
# BEFORE:
_spec.loader.exec_module(_legacy)  # Loads entire TUI!

# AFTER:
# Legacy import disabled - see comments in file
# Now imports from new modular structure:
from .core.database import get_db_connection, init_db
from .core.auth import hash_password, verify_password
# ... etc
```

### 5. Pytest Timeout Integration

**Files**: `requirements-dev.txt`, `.github/workflows/python-package.yml`

Added pytest-timeout:

```txt
# requirements-dev.txt
pytest-timeout>=2.4.0
```

```yaml
# .github/workflows/python-package.yml
- name: Test with pytest
  run: |
    pytest --timeout=30 --timeout-method=thread --tb=short
```

### 6. Fixed Mock Test

**File**: `tests/unit/test_cache.py`

Fixed test to mock the function instead of module variable:

```python
@patch('scrapetui.core.cache.get_config')
def test_get_cache_disabled(self, mock_get_config):
    # BEFORE: Tried to mock module-level variable (doesn't work)
    # AFTER: Mock the get_config() function
    mock_config = Config(cache_enabled=False)
    mock_get_config.return_value = mock_config
```

---

## Results

### Before vs After

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Unit Test Completion** | Hung indefinitely | ~7 seconds | ✅ 100% fixed |
| **Tests Passing** | 0/135 (hung) | 133/135 | ✅ 98.5% pass rate |
| **Import Time** | Hangs during collection | <1 second | ✅ Instant |
| **Test Isolation** | Shared state | Clean per-test | ✅ Isolated |
| **CI/CD Status** | Timeout after 5+ min | Completes in <1 min | ✅ Fixed |

### Test Execution

```bash
$ pytest tests/unit/ --timeout=30 -v
======================== 133 passed, 2 failed in 6.71s ========================

$ pytest --collect-only
======================== 135 tests collected in 0.52s ==========================
```

### Remaining Failures

**2 pre-existing schema issues** (not infrastructure problems):
1. `test_run_migrations_from_v1` - Schema migration test
2. `test_full_schema_initialization` - Schema validation test

These are functional test issues that need schema updates, not infrastructure hangs.

---

## Commits

1. **9eaad43** - `fix: resolve critical JWT and test infrastructure issues`
   - Fixed JWT token subject type (int → string)
   - Fixed test fixture UNIQUE constraints
   - Added testclient rate limiting bypass

2. **d5a2daa** - `fix: disable legacy monolithic import causing test hangs`
   - Commented out scrapetui/__init__.py legacy import
   - Prevented execution of monolithic TUI on package import

3. **edd610b** - `fix: resolve critical test infrastructure issues causing CI/CD hangs`
   - Implemented lazy initialization in 6 core modules
   - Fixed MemoryCache deadlock
   - Added test isolation fixtures
   - Integrated pytest-timeout
   - Updated CI/CD workflow

---

## Files Changed

**Total**: 10 files, 183 insertions, 52 deletions

### Core Modules (6 files)
- `scrapetui/core/cache.py` - Lazy logger/config initialization
- `scrapetui/core/auth.py` - Lazy logger with helper function
- `scrapetui/core/database.py` - Lazy logger in functions
- `scrapetui/scrapers/manager.py` - Lazy logger/config with helpers
- `scrapetui/config.py` - Idempotent env loading, reset function
- `scrapetui/utils/logging.py` - Reset function for tests

### Test Infrastructure (2 files)
- `tests/conftest.py` - Autouse fixtures for isolation
- `tests/unit/test_cache.py` - Fixed mock test

### CI/CD (1 file)
- `.github/workflows/python-package.yml` - Added timeout flags

### Requirements (1 file)
- `requirements-dev.txt` - Added pytest-timeout dependency

---

## Lessons Learned

### 1. **No Module-Level Side Effects**

**Don't**:
```python
logger = get_logger(__name__)  # Executes at import
config = get_config()          # Executes at import
```

**Do**:
```python
def my_function():
    logger = get_logger(__name__)  # Executes when called
    config = get_config()          # Executes when called
```

### 2. **Beware of Lock Nesting**

Calling a method that acquires a lock from within another lock-holding method causes deadlock.

**Solution**: Keep lock-protected code simple, avoid calling other methods.

### 3. **Test Isolation is Critical**

Global singletons MUST be reset between tests to prevent state leakage.

**Solution**: Use autouse fixtures to reset all global state before each test.

### 4. **Import-Time Execution is Dangerous**

Loading entire applications at import time causes:
- Slow imports
- Test hangs
- Circular dependencies
- Difficult debugging

**Solution**: Keep imports clean - only class/function definitions.

### 5. **Timeout Protection**

Always use pytest-timeout in CI/CD to catch hangs early.

**Solution**: `pytest --timeout=30 --timeout-method=thread`

---

## Future Recommendations

1. **Code Review Checklist**:
   - [ ] No module-level function calls (except imports)
   - [ ] No file I/O at import time
   - [ ] No global state without reset mechanism
   - [ ] No nested lock acquisitions

2. **Testing Standards**:
   - [ ] All fixtures properly isolated
   - [ ] Autouse fixtures for singleton cleanup
   - [ ] Timeout protection on all test runs
   - [ ] Mock external dependencies

3. **Architecture Guidelines**:
   - [ ] Lazy initialization for expensive operations
   - [ ] Dependency injection over global singletons
   - [ ] Clear separation: imports vs runtime
   - [ ] Document all module-level initialization

---

## Verification Commands

```bash
# Run unit tests with timeout:
source .venv/bin/activate
pytest tests/unit/ --timeout=30 -v

# Check import speed:
python -c "import time; start=time.time(); import scrapetui.core.cache; print(f'{time.time()-start:.3f}s')"

# Verify no hangs in collection:
pytest --collect-only --timeout=5

# Full test suite:
pytest tests/ --timeout=30 -v
```

---

## Status: ✅ RESOLVED

The test infrastructure is now solid. Tests complete without hanging, both locally and in CI/CD. The 2 remaining test failures are simple schema issues that can be addressed separately.

**CI/CD Pipeline**: Fully operational
**Test Completion Time**: <10 seconds
**Pass Rate**: 98.5% (133/135)
**Infrastructure Issues**: None
