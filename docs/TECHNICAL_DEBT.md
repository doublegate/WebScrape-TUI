# Technical Debt Tracker

**Last Updated**: 2025-10-03
**Project Version**: v2.1.0-alpha.3
**Status**: 🟡 Active Development

---

## Overview

This document tracks known technical debt in the WebScrape-TUI project. Technical debt represents work that was deferred to meet deadlines or avoid blocking progress, but should be addressed in future development cycles.

### Current Test Status

- ✅ **Working Tests**: 199/199 passing (100%)
  - `tests/unit/`: 135 tests
  - `tests/api/`: 64 tests
- 🟡 **Legacy Tests**: ~150+ tests requiring migration (20 files)
- ✅ **CI/CD Pipeline**: Passing on Python 3.11 and 3.12

---

## High Priority Technical Debt

### 1. Legacy Test Suite Migration

**Status**: 🔴 Blocked
**Priority**: High
**Estimated Effort**: 4-6 hours
**Assigned**: Unassigned

#### Problem Statement

The project was refactored from a monolithic `scrapetui.py` file (9,715 lines) to a modular package structure. Legacy tests written for the monolithic architecture are currently failing due to:

1. **Import Errors**: Package `__init__.py` sets legacy managers to `None` to prevent loading the monolithic TUI (which hangs tests)
2. **UNIQUE Constraint Violations**: Tests insert duplicate data (links, scraper names)
3. **Database Isolation Issues**: Tests share database state instead of using temporary isolated databases

#### Affected Test Files (20 files)

| File | Test Count | Primary Issue | Status |
|------|-----------|---------------|--------|
| `test_analytics.py` | 16 | AnalyticsManager = None | 🟡 In Progress |
| `test_performance.py` | 6 | UNIQUE constraints | 🔴 Blocked |
| `test_scheduling.py` | 12 | ScheduleManager = None | 🔴 Blocked |
| `test_v2_auth_phase1.py` | 25 | Database isolation | 🔴 Blocked |
| `test_v2_ui_phase2.py` | 20 | Database isolation | 🔴 Blocked |
| `test_v2_phase3_isolation.py` | 23 | Database isolation | 🔴 Blocked |
| `test_scraping.py` | ~15 | Import errors | 🔴 Blocked |
| `test_utils.py` | ~10 | Import errors | 🔴 Blocked |
| `test_bulk_operations.py` | ~8 | UNIQUE constraints | 🔴 Blocked |
| `test_json_export.py` | ~5 | Import errors | 🔴 Blocked |
| `test_ai_providers.py` | ~12 | Import errors | 🔴 Blocked |
| `test_database.py` | ~10 | Database isolation | 🔴 Blocked |
| `test_config_and_presets.py` | ~8 | Import errors | 🔴 Blocked |
| `test_enhanced_export.py` | ~6 | Import errors | 🔴 Blocked |
| `test_topic_modeling.py` | ~10 | Import errors | 🔴 Blocked |
| `test_question_answering.py` | ~8 | Import errors | 🔴 Blocked |
| `test_duplicate_detection.py` | ~6 | Import errors | 🔴 Blocked |
| `test_summary_quality.py` | ~8 | Import errors | 🔴 Blocked |
| `test_advanced_ai.py` | ~10 | Import errors | 🔴 Blocked |
| `test_entity_relationships.py` | ~8 | Import errors | 🔴 Blocked |

**Total**: ~226 legacy test cases requiring migration

#### Work Completed

- ✅ Created `temp_db` fixture for isolated test databases (commit 30c12c0)
- ✅ Created `unique_link` fixture to avoid UNIQUE constraints (commit 30c12c0)
- ✅ Created `unique_scraper_name` fixture (commit 30c12c0)
- 🟡 Started migrating `test_analytics.py` (partial, commit 30c12c0)

#### Required Work

1. **Fix Import Strategy**:
   - Option A: Import managers directly from `scrapetui.py` (legacy monolithic file)
   - Option B: Refactor tests to use new modular imports from `scrapetui.core.*`
   - **Recommended**: Option B for long-term maintainability

2. **Apply Test Fixtures**: Update all 20 test files to use `temp_db`, `unique_link`, and `unique_scraper_name` fixtures

3. **Database Isolation**: Ensure all tests use temporary databases via `DATABASE_PATH` environment variable

4. **UNIQUE Constraint Fixes**: Replace all hardcoded URLs/names with unique values

5. **Update Workflow**: Once all tests pass, restore full test suite in `.github/workflows/python-package.yml`:
   ```yaml
   pytest tests/ --timeout=30 --timeout-method=thread --tb=short
   ```

#### Acceptance Criteria

- [ ] All 20 legacy test files pass locally
- [ ] Total test count: ~425 tests passing (199 current + 226 legacy)
- [ ] GitHub Actions workflow tests entire `tests/` directory
- [ ] Zero test failures, zero test errors
- [ ] No tests disabled, removed, or stubbed

#### References

- **GitHub Actions Logs**:
  - Run 18234569611: Shows UNIQUE constraint errors
  - Run 18234478769: Shows import errors
- **Related Commits**:
  - 30c12c0: Test fixtures for migration
  - 5725c8e: Workflow updated to skip legacy tests

---

## Medium Priority Technical Debt

### 2. Deprecation Warnings

**Status**: 🟡 Known Issue
**Priority**: Medium
**Estimated Effort**: 2-3 hours
**Assigned**: Unassigned

#### Issues

1. **datetime.utcnow() Deprecation** (Python 3.12+)
   - Files: `scrapetui/api/dependencies.py`, `scrapetui/api/auth.py`
   - Warning: "datetime.utcnow() is deprecated"
   - Fix: Replace with `datetime.now(datetime.UTC)`
   - Count: ~8 occurrences

2. **Pydantic v2 ConfigDict Migration**
   - Files: Various model files
   - Warning: "Support for class-based `config` is deprecated"
   - Fix: Migrate to ConfigDict
   - Count: ~4 occurrences

3. **FastAPI Lifespan Events**
   - File: `scrapetui/api/app.py`
   - Warning: "on_event is deprecated, use lifespan event handlers"
   - Fix: Migrate to lifespan context manager
   - Count: 3 occurrences (@app.on_event)

#### Work Required

- [ ] Replace all `datetime.utcnow()` with `datetime.now(datetime.UTC)`
- [ ] Migrate Pydantic models to ConfigDict
- [ ] Refactor FastAPI app to use lifespan handlers
- [ ] Verify no new warnings in CI/CD

### 3. Code Quality Improvements

**Status**: 🟢 Non-Critical
**Priority**: Low
**Estimated Effort**: 4-6 hours
**Assigned**: Unassigned

#### Flake8 Issues (730 non-critical)

Current flake8 output shows 730 style issues:
- 551 E501: Line too long (82 > 79 characters)
- 90 F401: Imported but unused (check_database_exists in multiple files)
- 50 E302: Expected 2 blank lines, found 1
- 10 F841: Local variable assigned but never used
- 8 E402: Module level import not at top of file
- 4 W291: Trailing whitespace
- 4 E712: Comparison to True should be 'if cond is True:' or 'if cond:'
- 3 E722: Do not use bare 'except'
- 3 F811: Redefinition of unused imports
- Other minor issues

**Note**: Critical errors (E9,F63,F7,F82) are already at zero ✅

#### Work Required

- [ ] Fix all E501 line length issues (wrap long lines)
- [ ] Remove all unused imports (F401)
- [ ] Add blank lines per PEP 8 (E302, E305)
- [ ] Remove trailing whitespace (W291)
- [ ] Fix boolean comparisons (E712)
- [ ] Add specific exception types to bare except blocks (E722)
- [ ] Organize imports properly (E402)

#### Acceptance Criteria

- [ ] Flake8 with default settings shows zero errors
- [ ] Code passes `flake8 . --max-line-length=79`

---

## Low Priority Technical Debt

### 4. Database Schema Cleanup

**Status**: 🟢 Non-Critical
**Priority**: Low
**Estimated Effort**: 1-2 hours

#### Issues

1. **Unused check_database_exists Import**: Imported in 90+ files but rarely used
2. **Inconsistent Timestamp Fields**: Some use TIMESTAMP, others TEXT
3. **Missing Indexes**: Some foreign keys lack indexes for performance

### 5. Documentation Updates

**Status**: 🟢 Non-Critical
**Priority**: Low
**Estimated Effort**: 2-3 hours

#### Issues

- [ ] Update API documentation for v2.1.0 endpoints
- [ ] Document new modular architecture in README
- [ ] Create migration guide from v2.0.0 to v2.1.0
- [ ] Update contribution guidelines for new structure

---

## Tracking Metrics

### Current Status (2025-10-03)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Working Tests | 199/199 (100%) | 100% | ✅ |
| Legacy Tests | 0/226 (0%) | 100% | 🔴 |
| Total Tests | 199/425 (47%) | 100% | 🟡 |
| CI/CD Status | ✅ Passing | Passing | ✅ |
| Flake8 Critical | 0 | 0 | ✅ |
| Flake8 Total | 730 | 0 | 🔴 |
| Deprecations | 15+ | 0 | 🟡 |

### Progress Tracking

#### Completed ✅
- [x] Core test infrastructure fixes (test hangs resolved)
- [x] Database migration v2.0.0 → v2.0.1
- [x] API test suite (64 tests, 100% passing)
- [x] Unit test suite (135 tests, 100% passing)
- [x] Flake8 critical errors fixed
- [x] GitHub Actions workflow operational
- [x] Test fixture infrastructure created

#### In Progress 🟡
- [ ] Legacy test migration (0/20 files complete)
- [ ] test_analytics.py migration (partial)

#### Not Started 🔴
- [ ] Deprecation warnings (15+ instances)
- [ ] Code quality improvements (730 flake8 issues)
- [ ] Documentation updates

---

## Action Items

### Immediate (Sprint 1)
1. Complete `test_analytics.py` migration
2. Migrate 5 highest-priority legacy test files
3. Document migration patterns for team

### Short-term (Sprint 2-3)
1. Migrate remaining 15 legacy test files
2. Restore full test suite in GitHub Actions
3. Fix datetime deprecation warnings

### Long-term (Future Sprints)
1. Fix all flake8 style issues
2. Migrate Pydantic to ConfigDict
3. Refactor FastAPI to lifespan handlers
4. Update documentation

---

## Notes

### Why Legacy Tests Were Deferred

The legacy test migration was deferred to unblock the CI/CD pipeline and v2.1.0 development. The decision was made because:

1. **Working tests are comprehensive**: 199 tests cover all critical v2.1.0 functionality
2. **Legacy tests are non-critical**: They test the old monolithic structure
3. **Time constraints**: Proper migration requires 4-6 hours of focused work
4. **Migration complexity**: Requires careful refactoring, not simple fixes

### Migration Strategy

When resuming legacy test work:

1. Use existing fixtures: `temp_db`, `unique_link`, `unique_scraper_name`
2. Follow pattern from `test_analytics.py` (partial work completed)
3. Test each file individually: `pytest tests/test_[file].py -v`
4. Commit after each file is fixed
5. Update workflow only when all files pass

### Contact

For questions about technical debt or migration work:
- GitHub Issues: https://github.com/doublegate/WebScrape-TUI/issues
- Project Maintainer: See CONTRIBUTING.md

---

**Last Review**: 2025-10-03
**Next Review**: When legacy test migration resumes
**Status**: 🟡 Active tracking
