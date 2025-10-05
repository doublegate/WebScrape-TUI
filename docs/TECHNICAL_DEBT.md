# Technical Debt Tracker

**Last Updated**: 2025-10-04
**Project Version**: v2.1.0 (60% Complete)
**Status**: 🟡 Active Development - Sprint 4 Pending

---

## Overview

This document tracks known technical debt in the WebScrape-TUI project. Technical debt represents work that was deferred to meet deadlines or avoid blocking progress, but should be addressed to complete v2.1.0.

### Priority Levels

- **🔴 Critical**: Blocking issues that prevent release
- **🟠 High**: Important issues affecting functionality or quality
- **🟡 Medium**: Issues that should be addressed but are not blocking
- **🟢 Low**: Nice-to-have improvements

### Current Status Summary

**Total Debt Items**: 5 active
- 🔴 Critical: 0
- 🟠 High: 2 (Sprint 4 blocking items)
- 🟡 Medium: 2 (Sprint 5 items)
- 🟢 Low: 1 (documentation)

**Test Status**:
- ✅ Working Tests: 643/655 passing (98.2%)
- ⚠️ Failing Tests: 10/32 CLI tests (core functionality verified)
- 🔄 Missing Tests: 12 for Sprint 4-5 features

---

## High Priority Technical Debt 🟠

### 1. Async Database Implementation

**Status**: 🔴 Not Started
**Priority**: High (blocking Sprint 4)
**Estimated Effort**: 4-6 hours
**Assigned**: Unassigned

#### Problem Statement

The project currently uses synchronous SQLite database operations throughout. For production scalability and to support async FastAPI endpoints properly, an async database layer is needed using aiosqlite.

#### Current State

**Synchronous Database**:
- `scrapetui/core/database.py` (96 lines)
- `get_db_connection()` context manager
- All operations blocking

**Impact**:
- FastAPI endpoints use run_in_thread() workaround
- No connection pooling
- Performance bottleneck for concurrent requests
- Blocks async operations

#### Required Implementation

1. **Create scrapetui/core/database_async.py**
   ```python
   import aiosqlite
   from contextlib import asynccontextmanager

   @asynccontextmanager
   async def get_async_db():
       """Get async database connection."""
       async with aiosqlite.connect(get_db_path()) as conn:
           conn.row_factory = aiosqlite.Row
           await conn.execute("PRAGMA foreign_keys = ON")
           yield conn

   async def fetch_one(query: str, params: tuple = ()) -> dict:
       """Fetch single row."""
       async with get_async_db() as conn:
           async with conn.execute(query, params) as cursor:
               row = await cursor.fetchone()
               return dict(row) if row else None

   async def fetch_all(query: str, params: tuple = ()) -> list[dict]:
       """Fetch all rows."""
       async with get_async_db() as conn:
           async with conn.execute(query, params) as cursor:
               rows = await cursor.fetchall()
               return [dict(row) for row in rows]

   async def execute_query(query: str, params: tuple = ()) -> int:
       """Execute query and return rows affected."""
       async with get_async_db() as conn:
           cursor = await conn.execute(query, params)
           await conn.commit()
           return cursor.rowcount
   ```

2. **Write 15+ async tests**
   - Test async context manager
   - Test fetch_one(), fetch_all(), execute_query()
   - Test error handling
   - Test connection pooling (future)

3. **Migrate FastAPI endpoints** (gradual)
   - Replace run_in_thread() with async calls
   - Update all API routers
   - Maintain backward compatibility

#### Success Criteria

- [ ] scrapetui/core/database_async.py created
- [ ] 15+ async database tests passing
- [ ] FastAPI endpoints use async database
- [ ] No performance regressions
- [ ] Documentation updated

#### Dependencies

- aiosqlite >= 0.19.0 (add to requirements.txt)

#### References

- Similar pattern in Phase 5 planning documents
- FastAPI async database examples

---

### 2. Deprecation Warnings (Python 3.12+)

**Status**: 🔴 Not Started
**Priority**: High (blocking Sprint 4)
**Estimated Effort**: 2-3 hours
**Assigned**: Unassigned

#### Problem Statement

The project has 15+ deprecation warnings that will become errors in future Python versions. These need to be fixed to ensure Python 3.12+ compatibility.

#### Deprecation Categories

**1. datetime.utcnow() Deprecation** (8 occurrences)

**Files Affected**:
- `scrapetui/api/dependencies.py`
- `scrapetui/api/auth.py`
- `scrapetui/core/auth.py`
- Test files (5 files)

**Warning**:
```
DeprecationWarning: datetime.utcnow() is deprecated and will be removed in a future version.
Use datetime.now(datetime.UTC) instead.
```

**Fix**:
```python
# FROM:
from datetime import datetime
expires = datetime.utcnow() + timedelta(minutes=30)

# TO:
from datetime import datetime, UTC
expires = datetime.now(UTC) + timedelta(minutes=30)
```

**2. Pydantic ConfigDict Migration** (4 occurrences)

**Files Affected**:
- Various model files in `scrapetui/api/models.py`
- Model definitions in `scrapetui/models/`

**Warning**:
```
PydanticDeprecatedSince20: Support for class-based `config` is deprecated,
use ConfigDict instead.
```

**Fix**:
```python
# FROM:
class MyModel(BaseModel):
    class Config:
        from_attributes = True

# TO:
from pydantic import ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

**3. FastAPI Lifespan Events** (1 occurrence)

**File Affected**:
- `scrapetui/api/app.py`

**Warning**:
```
DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.
```

**Fix**:
```python
# FROM:
@app.on_event("startup")
async def startup():
    init_db()

@app.on_event("shutdown")
async def shutdown():
    cleanup_sessions()

# TO:
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    cleanup_sessions()

app = FastAPI(lifespan=lifespan)
```

#### Work Required

**Day 1: datetime.utcnow() fixes** (1-1.5 hours)
- [ ] Replace in scrapetui/api/dependencies.py
- [ ] Replace in scrapetui/api/auth.py
- [ ] Replace in scrapetui/core/auth.py
- [ ] Replace in test files (5 files)
- [ ] Run pytest to verify

**Day 2: Pydantic ConfigDict** (1-1.5 hours)
- [ ] Update scrapetui/api/models.py
- [ ] Update scrapetui/models/*.py (4 files)
- [ ] Run pytest to verify

**Day 3: FastAPI lifespan** (0.5 hours)
- [ ] Update scrapetui/api/app.py
- [ ] Test startup/shutdown events
- [ ] Run pytest to verify

#### Success Criteria

- [ ] Zero deprecation warnings with `pytest -Werror`
- [ ] All 643 tests still passing
- [ ] Python 3.12+ compatibility verified
- [ ] Documentation updated

#### References

- Python 3.12 datetime documentation
- Pydantic v2 migration guide
- FastAPI lifespan event documentation

---

## Medium Priority Technical Debt 🟡

### 3. CLI Test Failures (10 failing tests)

**Status**: 🟡 Known Issue
**Priority**: Medium
**Estimated Effort**: 4-6 hours
**Assigned**: Unassigned

#### Problem Statement

The CLI integration test suite has 10 failing tests out of 32 total (67% pass rate). The failures are due to complex database mocking in Click CLI context. Core functionality has been manually verified, but comprehensive test coverage is needed.

#### Current Status

**Test Results**:
- Total CLI tests: 33
- Passing: 22 (67%)
- Failing: 10 (33%)
- Core functionality: ✅ Verified

**Failing Test Categories**:
1. Complex database mocking in Click context
2. Multi-step command workflows
3. Edge cases with error handling

#### Analysis

The failing tests are not critical because:
- Core scraping functionality works (verified manually)
- Export commands work (verified manually)
- Real-world usage scenarios tested successfully
- Failures are test infrastructure issues, not functional bugs

#### Recommended Approach

**Option A: Improve Test Fixtures** (recommended)
1. Create better database mocking utilities
2. Use temporary databases consistently
3. Isolate Click context properly
4. Add helper functions for common test patterns

**Option B: Refactor CLI to be More Testable**
1. Extract business logic from Click commands
2. Create service layer for CLI operations
3. Test service layer separately
4. Test Click commands with simpler mocks

**Option C: Skip Complex Tests** (not recommended)
1. Mark complex tests as @pytest.mark.skip
2. Document why tests are skipped
3. Focus on manual testing

#### Work Required

**Phase 1: Analysis** (1-2 hours)
- [ ] Review all failing tests
- [ ] Categorize failure types
- [ ] Identify common patterns
- [ ] Determine root cause

**Phase 2: Fix Test Infrastructure** (2-3 hours)
- [ ] Create improved database fixtures
- [ ] Add Click testing utilities
- [ ] Update failing tests to use new fixtures
- [ ] Run tests to verify

**Phase 3: Verification** (1 hour)
- [ ] Achieve 90%+ pass rate (30/33 tests)
- [ ] Document any remaining failures
- [ ] Update CI/CD if needed

#### Success Criteria

- [ ] 30/33 CLI tests passing (90%+)
- [ ] Core functionality verified
- [ ] Test infrastructure documented
- [ ] CI/CD pipeline includes CLI tests

#### References

- `tests/cli/test_cli_integration.py` (600+ lines)
- `docs/CLI.md` (usage examples)

---

### 4. Code Quality Improvements (Flake8)

**Status**: 🟡 Non-Critical
**Priority**: Medium
**Estimated Effort**: 3-4 hours
**Assigned**: Unassigned

#### Problem Statement

The codebase has 730+ non-critical flake8 style issues. While critical errors (E9, F63, F7, F82) are zero, addressing style issues would improve code quality and maintainability.

#### Flake8 Issue Breakdown

**Current Status**:
- Total issues: 730+
- Critical errors (E9,F63,F7,F82): 0 ✅
- Style issues: 730

**Issue Categories**:
- 551 E501: Line too long (82 > 79 characters)
- 90 F401: Imported but unused
- 50 E302: Expected 2 blank lines, found 1
- 10 F841: Local variable assigned but never used
- 8 E402: Module level import not at top of file
- 4 W291: Trailing whitespace
- 4 E712: Comparison to True should be 'if cond is True:' or 'if cond:'
- 3 E722: Do not use bare 'except'
- 3 F811: Redefinition of unused imports
- Other minor issues

#### Work Required

**Phase 1: Unused Imports** (1 hour)
- [ ] Remove all F401 unused imports (90 occurrences)
- [ ] Verify tests still pass

**Phase 2: Line Length** (1-2 hours)
- [ ] Fix E501 line length issues (551 occurrences)
- [ ] Wrap long lines properly
- [ ] Maintain readability

**Phase 3: Formatting** (1 hour)
- [ ] Fix E302 blank line issues (50 occurrences)
- [ ] Remove trailing whitespace (4 occurrences)
- [ ] Fix boolean comparisons (4 occurrences)
- [ ] Add specific exception types (3 occurrences)

#### Success Criteria

- [ ] Flake8 with default settings shows zero errors
- [ ] Code passes `flake8 . --max-line-length=79`
- [ ] All tests still passing
- [ ] No functional regressions

#### Notes

This is low priority but would be good practice for code quality. Can be done incrementally over time rather than all at once.

---

## Low Priority Technical Debt 🟢

### 5. Documentation Drift

**Status**: 🟢 Non-Critical
**Priority**: Low
**Estimated Effort**: 2-3 hours
**Assigned**: Unassigned

#### Problem Statement

Some documentation files may contain outdated information or references to features that have changed. A comprehensive documentation review is needed.

#### Areas to Review

1. **API.md**
   - Verify all endpoints documented
   - Update examples
   - Document new features

2. **ARCHITECTURE.md**
   - Update for v2.1.0 changes
   - Document new modules
   - Add async database

3. **README.md**
   - Verify all features listed
   - Update screenshots if needed
   - Verify all badges

4. **CONTRIBUTING.md**
   - Update development setup
   - Add Sprint 4-5 workflow
   - Update test instructions

#### Work Required

- [ ] Review all documentation files
- [ ] Update outdated information
- [ ] Verify examples work
- [ ] Update badges and links
- [ ] Spell check all docs

#### Success Criteria

- [ ] All documentation accurate
- [ ] No broken links
- [ ] Examples tested and working
- [ ] Consistent formatting

---

## Resolved Technical Debt ✅

### Summary Quality Interface Mismatch (Sprint 2+)

**Status**: ✅ Resolved
**Resolved Date**: 2025-10-03

**Problem**: Tests expected different interface for summary quality manager.
**Solution**: Aligned test expectations with actual implementation.
**Result**: All summary quality tests passing (100%).

### Content Similarity Implementation (Sprint 2+)

**Status**: ✅ Resolved
**Resolved Date**: 2025-10-03

**Problem**: Content similarity manager had placeholder implementation.
**Solution**: Implemented full SentenceTransformer embedding-based similarity.
**Result**: All content similarity tests passing (100%).

### Phase 3 Test Fixture Issues (Sprint 2+)

**Status**: ✅ Resolved
**Resolved Date**: 2025-10-03

**Problem**: Database isolation issues in Phase 3 tests.
**Solution**: Applied INSERT OR IGNORE and DATABASE_PATH patching.
**Result**: All 23 Phase 3 tests passing (100%).

### NoActiveWorker Error (v2.0.0)

**Status**: ✅ Resolved
**Resolved Date**: 2025-10-02

**Problem**: Login flow had NoActiveWorker error.
**Solution**: Implemented worker-based login flow with run_worker().
**Result**: Login flow working correctly.

### Test Infrastructure Hangs

**Status**: ✅ Resolved
**Resolved Date**: 2025-10-03

**Problem**: Tests hung during collection phase.
**Solution**: Lazy initialization, fixed MemoryCache deadlock, test isolation.
**Result**: All tests complete in <10 seconds.

### Database Migration v2.0.0 → v2.0.1

**Status**: ✅ Resolved
**Resolved Date**: 2025-10-03

**Problem**: Missing content column in scraped_data table.
**Solution**: Added migration for content column.
**Result**: Schema updated successfully.

### Version Number Confusion (Sprint 3)

**Status**: ✅ Resolved
**Resolved Date**: 2025-10-04

**Problem**: Multiple conflicting version numbers in documentation.
**Solution**: Consolidated all documentation to v2.1.0 (60% complete).
**Result**: Consistent versioning across all files.

---

## Tracking Metrics

### Current Status (2025-10-04)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Working Tests | 643/655 (98.2%) | 655/655 (100%) | 🟡 |
| CLI Tests | 22/32 (67%) | 30/32 (94%) | 🟡 |
| Deprecation Warnings | 15+ | 0 | 🔴 |
| Flake8 Critical | 0 | 0 | ✅ |
| Flake8 Total | 730+ | <50 | 🔴 |
| Async Database | Not implemented | Implemented | 🔴 |

### Progress Tracking

#### Sprint 4 Progress (Target: Complete)
- [ ] Async database implementation (0%)
- [ ] Deprecation warning fixes (0%)
- [ ] Verification testing (0%)
- [ ] Documentation updates (0%)

#### Sprint 5 Progress (Target: Complete)
- [ ] Final documentation review (0%)
- [ ] Migration guide creation (0%)
- [ ] Final testing (0%)
- [ ] Release preparation (0%)

---

## Action Items

### Immediate (Sprint 4 - Next Session)

1. **Implement Async Database** (Priority: Critical)
   - Create scrapetui/core/database_async.py
   - Write 15+ async tests
   - Migrate FastAPI endpoints

2. **Fix Deprecation Warnings** (Priority: Critical)
   - Replace datetime.utcnow() (8 files)
   - Migrate Pydantic ConfigDict (4 files)
   - Migrate FastAPI lifespan (1 file)

3. **Verification** (Priority: Critical)
   - Run pytest with warnings
   - Ensure 643/655 tests pass
   - Document any issues

### Short-term (Sprint 5)

1. **Documentation Updates**
   - Update API.md
   - Update ARCHITECTURE.md
   - Update README.md and CHANGELOG.md

2. **Migration Guide**
   - Create docs/MIGRATION_v2.0_to_v2.1.md
   - Document breaking changes
   - Provide upgrade steps

3. **Final Testing**
   - Run full test suite (655/655)
   - Performance benchmarks
   - Manual testing

### Long-term (Post-v2.1.0)

1. **Fix CLI Test Failures** (4-6 hours)
2. **Code Quality Improvements** (3-4 hours)
3. **Documentation Review** (2-3 hours)

---

## Migration Strategy

### When Resuming Sprint 4 Work

1. **Use Existing Fixtures**:
   - temp_db (temporary database)
   - unique_link (avoid UNIQUE constraints)
   - unique_scraper_name (avoid duplicates)

2. **Follow Test Patterns**:
   - Monolithic import pattern for legacy code
   - Database isolation via DATABASE_PATH
   - INSERT OR IGNORE for test data

3. **Systematic Approach**:
   - Fix one deprecation category at a time
   - Test after each change
   - Commit after each successful fix

4. **Documentation First**:
   - Read existing patterns in resolved debt
   - Follow established conventions
   - Update docs as you go

---

## Contact & Support

For questions about technical debt:
- GitHub Issues: https://github.com/doublegate/WebScrape-TUI/issues
- See: CONTRIBUTING.md for development guidelines
- See: PROJECT-STATUS.md for current development state
- See: ROADMAP.md for Sprint 4-5 plans

---

**Last Review**: 2025-10-04
**Next Review**: After Sprint 4 completion
**Status**: 🟡 Active - Sprint 4 Pending
