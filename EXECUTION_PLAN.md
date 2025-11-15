# EXECUTION PLAN
## Infinite Backrooms - Production Readiness Implementation

**Version**: 1.0 - Operational Document
**Created**: 2025-11-14
**Status**: READY FOR EXECUTION
**Approach**: Five-Tier Orchestrated Architecture with Just-In-Time Skill Creation

---

## 📋 QUICK REFERENCE

**Total Estimated Time**: 32-47 hours (2 weeks)
**Phases**: 3 phases across 5 tiers
**Custom Skills to Create**: 12+ specialized skills
**Quality Gates**: 15+ validation checkpoints
**Final Deliverables**: Complete enterprise-grade suite

---

## 🏗️ ARCHITECTURE OVERVIEW

```
TIER 1 (Strategic)    → Claude (Me) - Overall coordination
TIER 2 (Orchestration) → project-supervisor-orchestrator agents
TIER 3 (Skill Creation) → skill-creator agent (creates custom skills)
TIER 4 (Execution)     → Specialist agents (equipped with skills)
TIER 5 (Capabilities)  → Custom + Generic skills layer
```

---

## ⚡ PRE-EXECUTION SETUP

### Preparation Checklist
- [ ] Review this entire execution plan
- [ ] Confirm understanding of five-tier architecture
- [ ] Verify all required agents are available
- [ ] Confirm skill-creator agent is accessible
- [ ] Establish git branch: `feature/production-readiness-ultimate`
- [ ] Set up progress tracking mechanism

### Git Branch Setup
```bash
git checkout -b feature/production-readiness-ultimate
git push -u origin feature/production-readiness-ultimate
```

---

## 🎯 PHASE 1: FOUNDATION (Days 1-3, 10-15 hours)

**Objective**: Fix test infrastructure, consolidate clients, optimize async patterns

### Phase 1 Orchestrator Deployment

- [ ] **Deploy Phase 1 Orchestrator**
  ```
  Deploy: project-supervisor-orchestrator
  Instruction: "Execute Phase 1 foundation tasks with just-in-time skill creation.
  Deploy three teams: (1) Test Infrastructure, (2) Client Consolidation,
  (3) Event Loop Optimization. Create custom skills before each team deployment.
  Enforce quality gates. Tasks 1 and 2 run in parallel, task 3 sequential."
  ```

---

### ⚡ TASK 1.1: FIX TEST SUITE (6-8 hours)

**Priority**: P0 - CRITICAL BLOCKER

#### STEP 1: Create Custom Skill (30-45 min)

- [ ] **Invoke skill-creator to create "pytest-streamlit-async-fixer"**
  ```
  Deploy: skill-creator agent

  Skill Specification:
  Name: pytest-streamlit-async-fixer
  Purpose: Fix pytest infrastructure for Streamlit apps with async components
  Domain Knowledge:
    - pytest configuration for Streamlit applications
    - Async test fixture patterns with AsyncMock
    - Import resolution strategies for Streamlit modules
    - Coverage reporting setup and configuration
    - Mock strategies for async Ollama clients
  Workflow:
    1. Run pytest -v to diagnose all failures
    2. Analyze import errors in conftest.py
    3. Fix imports to match actual codebase structure
    4. Update async mock fixtures with proper patterns
    5. Fix test file imports across all test files
    6. Run tests incrementally, validating each fix
    7. Generate coverage baseline report
  Tools: Read, Edit, Write, Bash, Grep, Glob
  Best Practices:
    - Use AsyncMock(spec=ClassName) for type safety
    - Proper pytest.mark.asyncio decorators
    - Incremental fixing with validation after each change
    - Document import paths in comments
  Success Criteria:
    - pytest runs without import errors
    - At least 50% of tests pass
    - Coverage baseline established and documented
    - All fixtures properly typed and mocked
  ```

- [ ] **Validate Skill Creation**
  - Skill file created in `.claude/skills/` directory
  - Skill specification complete and readable
  - Skill ready for agent deployment

#### STEP 2: Deploy Agent Team with Custom Skill (5-7 hours)

- [ ] **Deploy debugger agent**
  ```
  Task: Diagnose root causes of test failures
  Tools: Read, Bash, Grep
  Output: Comprehensive diagnostic report of all import errors
  ```

- [ ] **Deploy test-engineer agent with custom skill**
  ```
  Task: Fix test infrastructure using custom skill workflow
  Skills to Equip:
    - pytest-streamlit-async-fixer (custom, just created)
    - git-commit-helper (generic)
  Tools: Read, Edit, Write, Bash, Grep
  Workflow: Follow pytest-streamlit-async-fixer skill's encoded workflow
  Output: Fixed test suite with proper structure
  ```

- [ ] **Deploy code-reviewer agent**
  ```
  Task: Validate test quality and fixture structure
  Tools: Read, Grep
  Output: Test quality review report
  ```

#### STEP 3: Quality Gate Validation

- [ ] **Run validation commands**
  ```bash
  # Verify tests run without import errors
  pytest --collect-only

  # Run test suite
  pytest -v

  # Generate coverage report
  pytest --cov=src --cov-report=term --cov-report=html
  ```

- [ ] **Quality Gate Checklist**
  - [ ] All import errors resolved
  - [ ] pytest runs without errors
  - [ ] At least 50% of tests pass
  - [ ] Coverage baseline documented (record %: ______)
  - [ ] All fixtures properly mocked
  - [ ] Git commits well-documented

#### DELIVERABLES CHECKLIST

- [ ] Fixed `tests/conftest.py` with correct imports
- [ ] All test files updated with correct imports
- [ ] Async mocks properly configured
- [ ] Coverage baseline report (HTML + terminal)
- [ ] Custom skill: `pytest-streamlit-async-fixer` created and saved
- [ ] Git commits with descriptive messages
- [ ] Diagnostic report from debugger

---

### ⚡ TASK 1.2: CONSOLIDATE OLLAMA CLIENTS (5-7 hours) [PARALLEL WITH 1.1]

**Priority**: P0 - CRITICAL BLOCKER

#### STEP 1: Create Custom Skill (30-45 min)

- [ ] **Invoke skill-creator to create "python-async-client-consolidator"**
  ```
  Deploy: skill-creator agent

  Skill Specification:
  Name: python-async-client-consolidator
  Purpose: Consolidate multiple async Python client implementations
  Domain Knowledge:
    - Async Python client patterns (aiohttp, httpx)
    - Connection pooling strategies for performance
    - Context manager patterns for resource cleanup
    - Error handling best practices for async clients
    - API design principles for async operations
  Workflow:
    1. Audit all client implementations (10+ files)
    2. Create feature comparison matrix
    3. Identify best features from each implementation
    4. Design unified client API with all features
    5. Implement canonical OllamaClient
    6. Update imports throughout codebase
    7. Remove duplicate implementations
    8. Run tests to validate functionality
  Tools: Read, Write, Edit, Grep, Glob, MultiEdit
  Best Practices:
    - async with context manager pattern
    - Connection pooling for performance
    - Comprehensive type hints
    - Detailed docstrings with examples
    - Proper resource cleanup in __aexit__
  Success Criteria:
    - Single canonical client implementation
    - All features from duplicates preserved
    - No duplicate files remain
    - All imports updated
    - Tests pass with unified client
  ```

- [ ] **Validate Skill Creation**
  - Skill file created
  - Specification complete
  - Ready for deployment

#### STEP 2: Deploy Agent Team with Custom Skill (4-6 hours)

- [ ] **Deploy architecture-modernizer agent**
  ```
  Task: Analyze client duplication, recommend consolidation strategy
  Skills to Equip: mcp-builder (for API design principles)
  Tools: Read, Grep, Glob
  Output: Client comparison matrix and consolidation recommendation
  ```

- [ ] **Deploy backend-architect agent with custom skill**
  ```
  Task: Design unified client API
  Skills to Equip:
    - python-async-client-consolidator (custom, just created)
    - canvas-design (for API diagrams)
  Tools: Read, Write
  Output: Unified API design with diagrams
  ```

- [ ] **Deploy python-pro agent with custom skill**
  ```
  Task: Implement canonical OllamaClient
  Skills to Equip:
    - python-async-client-consolidator (custom)
    - git-commit-helper (generic)
  Tools: Read, Write, Edit, Grep, Glob
  Workflow: Follow python-async-client-consolidator skill's workflow
  Output: Implemented src/services/ollama_client.py (canonical)
  ```

- [ ] **Deploy unused-code-cleaner agent**
  ```
  Task: Remove duplicate client implementations
  Tools: Read, Write, Bash, Grep, Glob
  Output: Duplicate files removed, codebase cleaned
  ```

- [ ] **Deploy architect-reviewer agent**
  ```
  Task: Validate architecture consistency
  Tools: Read, Grep
  Output: Architecture review report
  ```

#### STEP 3: Quality Gate Validation

- [ ] **Run validation commands**
  ```bash
  # Find all ollama client imports
  grep -r "ollama_client" --include="*.py" src/ tests/ *.py

  # Verify old files deleted
  ls -la src/services/ollama_client*.py
  ls -la src/services/*ollama*.py

  # Run tests with unified client
  pytest tests/test_ollama_client.py -v

  # Test import
  python -c "from src.services.ollama_client import OllamaClient; print('Success')"
  ```

- [ ] **Quality Gate Checklist**
  - [ ] Single canonical `src/services/ollama_client.py` exists
  - [ ] All duplicate files deleted (list verified empty)
  - [ ] All imports updated throughout codebase
  - [ ] Tests pass with unified client
  - [ ] API diagrams generated
  - [ ] Architecture review passed

#### DELIVERABLES CHECKLIST

- [ ] Canonical `src/services/ollama_client.py` implemented
- [ ] All duplicate client files deleted
- [ ] All imports updated in codebase
- [ ] API architecture diagram created
- [ ] Feature comparison matrix documented
- [ ] Custom skill: `python-async-client-consolidator` created
- [ ] Git commits documenting consolidation
- [ ] Architecture review report

---

### 🔥 TASK 1.3: IMPROVE EVENT LOOP MANAGEMENT (4-5 hours) [AFTER 1.2]

**Priority**: P1 - HIGH

#### STEP 1: Create Custom Skill (30-45 min)

- [ ] **Invoke skill-creator to create "streamlit-async-pattern-optimizer"**
  ```
  Deploy: skill-creator agent

  Skill Specification:
  Name: streamlit-async-pattern-optimizer
  Purpose: Optimize async patterns for Streamlit avoiding event loop conflicts
  Domain Knowledge:
    - Streamlit event loop model and limitations
    - st.experimental_singleton for resource management
    - asyncio.run() vs thread-based execution tradeoffs
    - Proper resource cleanup in Streamlit context
    - Error handling for event loop conflicts
  Workflow:
    1. Research Streamlit async best practices
    2. Design singleton client management pattern
    3. Implement get_ollama_client() with singleton
    4. Implement safe_async_call() with fallback
    5. Update all async operation call sites
    6. Add comprehensive error handling
    7. Test for event loop errors
    8. Profile performance before/after
  Tools: Read, Edit, Write, Bash, Grep
  Best Practices:
    - Use st.experimental_singleton for client caching
    - Prefer asyncio.run() with try-except for RuntimeError
    - Keep thread-based fallback for edge cases
    - Comprehensive logging for debugging
    - Performance profiling validation
  Success Criteria:
    - No event loop creation errors
    - Resource cleanup verified
    - Performance maintained or improved
    - All tests pass
    - No "Event loop is closed" errors
  ```

- [ ] **Validate Skill Creation**
  - Skill file created
  - Specification complete
  - Ready for deployment

#### STEP 2: Deploy Agent Team with Custom Skill (3-4 hours)

- [ ] **Deploy backend-architect agent with custom skill**
  ```
  Task: Design async pattern using Streamlit best practices
  Skills to Equip: streamlit-async-pattern-optimizer (custom, just created)
  Tools: Read, Write
  Output: Async pattern design document
  ```

- [ ] **Deploy python-pro agent with custom skill**
  ```
  Task: Implement async patterns
  Skills to Equip:
    - streamlit-async-pattern-optimizer (custom)
    - git-commit-helper (generic)
  Tools: Read, Edit, Write, Bash
  Workflow: Follow streamlit-async-pattern-optimizer skill's workflow
  Output: Implemented async patterns in streamlit_backroom.py
  ```

- [ ] **Deploy performance-engineer agent**
  ```
  Task: Validate performance and profile
  Tools: Bash, Read
  Output: Performance comparison report
  ```

- [ ] **Deploy debugger agent**
  ```
  Task: Test for event loop errors
  Tools: Bash, Read, Grep
  Output: Event loop validation report
  ```

#### STEP 3: Quality Gate Validation

- [ ] **Run validation commands**
  ```bash
  # Search for old pattern usage
  grep -n "run_async_in_thread" streamlit_backroom.py

  # Run integration tests
  pytest tests/test_integration_real.py -v

  # Run app and monitor logs
  streamlit run streamlit_backroom.py &
  sleep 10
  # Check for event loop errors in logs
  grep -i "event loop" logs/ || echo "No errors found"
  pkill -f streamlit
  ```

- [ ] **Quality Gate Checklist**
  - [ ] Singleton pattern implemented
  - [ ] safe_async_call() function created
  - [ ] All async calls updated
  - [ ] No event loop errors in testing
  - [ ] Performance maintained/improved (record: ______)
  - [ ] Integration tests pass
  - [ ] Resource cleanup verified

#### DELIVERABLES CHECKLIST

- [ ] Singleton pattern for client management implemented
- [ ] safe_async_call() with fallback implemented
- [ ] All async call sites updated
- [ ] No event loop errors in testing
- [ ] Performance comparison report
- [ ] Custom skill: `streamlit-async-pattern-optimizer` created
- [ ] Git commits documenting async changes
- [ ] Event loop validation report

---

### 📊 PHASE 1 COMPLETION GATE

**Before Proceeding to Phase 2, Validate All Items:**

- [ ] **All Phase 1 Tasks Complete**
  - [ ] Task 1.1: Test suite fixed ✓
  - [ ] Task 1.2: Clients consolidated ✓
  - [ ] Task 1.3: Event loop optimized ✓

- [ ] **All Quality Gates Passed**
  - [ ] Tests run without import errors ✓
  - [ ] Single canonical client exists ✓
  - [ ] No event loop errors ✓

- [ ] **Custom Skills Created** (3 skills)
  - [ ] pytest-streamlit-async-fixer ✓
  - [ ] python-async-client-consolidator ✓
  - [ ] streamlit-async-pattern-optimizer ✓

- [ ] **Foundation Validated**
  - [ ] Coverage baseline: ______%
  - [ ] All tests passing: ______/______ tests
  - [ ] Git branch clean and up to date

**PROCEED TO PHASE 2**: YES / NO

---

## 🏗️ PHASE 2: ARCHITECTURE & TESTING (Days 4-8, 12-18 hours)

**Objective**: Refactor to modular architecture, achieve 80% test coverage

### Phase 2 Orchestrator Deployment

- [ ] **Deploy Phase 2 Orchestrator**
  ```
  Deploy: project-supervisor-orchestrator
  Instruction: "Execute Phase 2 architecture and testing tasks with custom skills.
  Deploy two teams: (1) Architecture Refactoring, (2) Test Coverage. Create
  4 custom skills. Smart parallelization: testing team starts gap analysis
  during architecture design phase. Enforce quality gates."
  ```

---

### 🔥 TASK 2.1: ARCHITECTURE REFACTORING (10-14 hours)

**Priority**: P1 - HIGH

#### STEP 1: Create Custom Skills (75-90 min for 2 skills)

- [ ] **Invoke skill-creator to create "streamlit-monolith-to-modular-refactorer"**
  ```
  Deploy: skill-creator agent

  Skill Specification:
  Name: streamlit-monolith-to-modular-refactorer
  Purpose: Refactor monolithic Streamlit apps into modular architecture
  Domain Knowledge:
    - Streamlit application architecture patterns
    - Service layer extraction (orchestrators, managers)
    - UI component separation patterns
    - Session state management best practices
    - SOLID principles for Python
    - Module organization strategies
  Workflow:
    1. Analyze monolithic file, identify boundaries
    2. Extract ConversationOrchestrator service
    3. Extract UI components (display, persona management)
    4. Extract SessionManager for state
    5. Refactor main app to orchestration layer
    6. Test each module independently
    7. Validate integration
    8. Ensure main file <300 lines
  Tools: Read, Write, Edit, MultiEdit, Grep, Glob
  Best Practices:
    - Extract one module at a time
    - Test after each extraction
    - Single responsibility per module
    - Dependency injection
    - Type hints and docstrings
    - Keep functions <50 lines
  Success Criteria:
    - Main file <300 lines
    - All modules tested independently
    - Clear separation of concerns
    - All tests pass after integration
  ```

- [ ] **Invoke skill-creator to create "python-architecture-diagram-generator"**
  ```
  Deploy: skill-creator agent

  Skill Specification:
  Name: python-architecture-diagram-generator
  Purpose: Generate professional architecture diagrams from Python code
  Domain Knowledge:
    - System architecture visualization
    - Component relationship diagrams
    - Data flow visualization
    - Mermaid diagram syntax
    - Professional diagram styling
  Workflow:
    1. Analyze codebase structure
    2. Identify components and relationships
    3. Generate system overview diagram
    4. Generate component interaction diagrams
    5. Generate data flow diagrams
    6. Export multiple formats (SVG, PNG, Mermaid)
  Tools: Read, Write, Bash
  Best Practices:
    - Use canvas-design for styling
    - Clear component boundaries
    - Labeled relationships
    - Multiple diagram types
  Success Criteria:
    - Complete architecture documentation
    - Professional visual quality
    - Multiple formats available
  ```

- [ ] **Validate Skills Creation**
  - Both skill files created
  - Specifications complete
  - Ready for deployment

#### STEP 2: Deploy Agent Team with Custom Skills (9-13 hours)

- [ ] **Deploy architecture-modernizer agent with custom skill**
  ```
  Task: Analyze monolith, create decomposition plan
  Skills to Equip:
    - streamlit-monolith-to-modular-refactorer (custom, just created)
    - mcp-builder (generic, API design principles)
  Tools: Read, Grep, Glob
  Output: Decomposition plan with module boundaries
  ```

- [ ] **Deploy backend-architect agent with custom skills**
  ```
  Task: Design module APIs and generate diagrams
  Skills to Equip:
    - streamlit-monolith-to-modular-refactorer (custom)
    - python-architecture-diagram-generator (custom, just created)
    - canvas-design (generic)
    - skill-creator (for understanding modular design)
  Tools: Read, Write
  Output: Module API designs + architecture diagrams
  ```

- [ ] **Deploy python-pro agents (3 instances in parallel)**
  ```
  Instance 1 - ConversationOrchestrator:
    Task: Implement ConversationOrchestrator module
    Skills: streamlit-monolith-to-modular-refactorer, git-commit-helper, docx
    Output: src/services/conversation_orchestrator.py

  Instance 2 - UI Components:
    Task: Implement UI component modules
    Skills: streamlit-monolith-to-modular-refactorer, git-commit-helper, docx
    Output: src/ui/conversation_display.py, src/ui/persona_manager.py

  Instance 3 - SessionManager:
    Task: Implement SessionManager module
    Skills: streamlit-monolith-to-modular-refactorer, git-commit-helper, docx
    Output: src/state/session_manager.py
  ```

- [ ] **Deploy test-engineer agent (incremental testing)**
  ```
  Task: Test each module as implemented
  Skills to Equip: pytest-streamlit-async-fixer (from Phase 1)
  Tools: Read, Write, Bash
  Output: Module test reports
  ```

- [ ] **Deploy architect-reviewer agent**
  ```
  Task: Validate architecture consistency
  Tools: Read, Grep
  Output: Architecture review report
  ```

- [ ] **Deploy code-reviewer agent**
  ```
  Task: Comprehensive code review
  Tools: Read, Grep
  Output: Code quality review report
  ```

#### STEP 3: Quality Gate Validation

- [ ] **Run validation commands**
  ```bash
  # Count lines in main file
  wc -l streamlit_backroom.py
  # Target: <300 lines

  # Count function sizes
  grep -n "^def " streamlit_backroom.py
  # Validate: all functions <50 lines

  # Run all tests
  pytest -v

  # Check module structure
  ls -la src/services/
  ls -la src/ui/
  ls -la src/state/

  # Run linting
  ruff check src/ streamlit_backroom.py
  ```

- [ ] **Quality Gate Checklist**
  - [ ] Main file streamlit_backroom.py <300 lines (actual: ______ lines)
  - [ ] All functions <50 lines
  - [ ] ConversationOrchestrator module created
  - [ ] UI component modules created
  - [ ] SessionManager module created
  - [ ] All modules tested independently
  - [ ] Integration tests pass
  - [ ] Architecture diagrams generated
  - [ ] Architecture review passed
  - [ ] Code review passed

#### DELIVERABLES CHECKLIST

- [ ] Modular architecture (<300 line main file)
- [ ] src/services/conversation_orchestrator.py created
- [ ] src/ui/conversation_display.py created
- [ ] src/ui/persona_manager.py created
- [ ] src/state/session_manager.py created
- [ ] Refactored streamlit_backroom.py
- [ ] Architecture diagrams (system, component, data flow)
- [ ] Module-level documentation
- [ ] Custom skills: 2 new skills created
- [ ] Git commits documenting each extraction
- [ ] Architecture review report
- [ ] Code review report

---

### 🔥 TASK 2.2: ACHIEVE 80% TEST COVERAGE (8-12 hours) [SMART PARALLEL WITH 2.1]

**Priority**: P1 - HIGH

#### STEP 1: Create Custom Skills (75-90 min for 2 skills)

- [ ] **Invoke skill-creator to create "streamlit-comprehensive-test-generator"**
  ```
  Deploy: skill-creator agent

  Skill Specification:
  Name: streamlit-comprehensive-test-generator
  Purpose: Generate comprehensive test suites for Streamlit applications
  Domain Knowledge:
    - Streamlit testing patterns
    - pytest best practices
    - Unit test patterns for services, UI, state
    - Integration test patterns
    - Security test patterns (XSS, injection, path traversal)
    - Mock strategies for Streamlit components
    - Coverage analysis and gap identification
  Workflow:
    1. Analyze codebase and current coverage
    2. Identify coverage gaps by module
    3. Generate unit tests for models (target 90%)
    4. Generate unit tests for services (target 80%)
    5. Generate unit tests for state (target 85%)
    6. Generate unit tests for utilities (target 95%)
    7. Generate integration tests
    8. Generate security tests
    9. Generate test metrics dashboard
  Tools: Read, Write, Bash, Grep, Glob
  Best Practices:
    - Proper async test patterns
    - Comprehensive fixtures
    - Parametrized tests for edge cases
    - Security test scenarios
    - Test data factories
  Success Criteria:
    - 80%+ overall coverage
    - All critical paths tested
    - Security tests comprehensive
    - Test metrics dashboard created
  ```

- [ ] **Invoke skill-creator to create "playwright-streamlit-e2e-tester"**
  ```
  Deploy: skill-creator agent

  Skill Specification:
  Name: playwright-streamlit-e2e-tester
  Purpose: Create E2E test suites for Streamlit apps using Playwright
  Domain Knowledge:
    - Playwright for Python
    - Streamlit component selectors
    - Async test patterns with Playwright
    - Screenshot comparison testing
    - Form interaction testing
  Workflow:
    1. Set up Playwright for Streamlit
    2. Create E2E test scenarios for workflows
    3. Test persona management
    4. Test conversation workflows
    5. Test settings and configuration
    6. Capture screenshots for visual regression
    7. Test error scenarios
  Tools: Bash, Read, Write
  Best Practices:
    - Page object pattern
    - Reliable selectors
    - Wait strategies
    - Screenshot comparison
  Success Criteria:
    - All user workflows covered
    - Visual regression suite
    - Tests run reliably
  ```

- [ ] **Validate Skills Creation**
  - Both skill files created
  - Specifications complete
  - Ready for deployment

#### STEP 2: Deploy Agent Team with Custom Skills (6-10 hours)

- [ ] **Deploy test-engineer agent (analysis)**
  ```
  Task: Analyze coverage gaps, create test plan
  Skills to Equip: streamlit-comprehensive-test-generator (custom, just created)
  Tools: Bash, Read, Write
  Output: Test plan with gap analysis
  ```

- [ ] **Deploy test-automator agents (3 instances in parallel)**
  ```
  Instance 1 - Unit Tests:
    Task: Generate comprehensive unit tests
    Skills: streamlit-comprehensive-test-generator, git-commit-helper
    Output: Unit tests for models, services, utils, state

  Instance 2 - Integration Tests:
    Task: Generate integration tests
    Skills: streamlit-comprehensive-test-generator, git-commit-helper
    Output: Integration test suite

  Instance 3 - E2E & Security Tests:
    Task: Generate E2E and security tests
    Skills: streamlit-comprehensive-test-generator,
            playwright-streamlit-e2e-tester,
            webapp-testing,
            git-commit-helper
    Output: E2E and security test suites
  ```

- [ ] **Deploy test-engineer agent (validation)**
  ```
  Task: Validate test quality and coverage
  Skills to Equip: xlsx (for metrics dashboard)
  Tools: Bash, Read, Write
  Output: Test coverage report and metrics dashboard
  ```

- [ ] **Deploy code-reviewer agent**
  ```
  Task: Review test code quality
  Tools: Read, Grep
  Output: Test quality review report
  ```

#### STEP 3: Quality Gate Validation

- [ ] **Run validation commands**
  ```bash
  # Run full test suite with coverage
  pytest --cov=src --cov-report=html --cov-report=term-missing

  # Check coverage percentage
  pytest --cov=src --cov-report=term | grep "TOTAL"

  # Run only unit tests
  pytest -m unit --cov=src

  # Run integration tests
  pytest -m integration

  # Run security tests
  pytest -m security

  # Open coverage report
  open htmlcov/index.html
  ```

- [ ] **Quality Gate Checklist**
  - [ ] Overall coverage ≥80% (actual: ______%)
  - [ ] Models coverage ≥90% (actual: ______%)
  - [ ] Services coverage ≥80% (actual: ______%)
  - [ ] State coverage ≥85% (actual: ______%)
  - [ ] Utils coverage ≥95% (actual: ______%)
  - [ ] All critical paths tested
  - [ ] Integration tests pass
  - [ ] E2E tests pass
  - [ ] Security tests pass
  - [ ] Test metrics dashboard created
  - [ ] Test quality review passed

#### DELIVERABLES CHECKLIST

- [ ] Comprehensive unit test suite
- [ ] Integration test suite
- [ ] E2E test suite with Playwright
- [ ] Security test suite
- [ ] Test coverage ≥80%
- [ ] Test metrics dashboard (XLSX)
- [ ] Visual regression screenshots
- [ ] Custom skills: 2 new skills created
- [ ] Git commits for all test additions
- [ ] Test quality review report

---

### 📊 PHASE 2 COMPLETION GATE

**Before Proceeding to Phase 3, Validate All Items:**

- [ ] **All Phase 2 Tasks Complete**
  - [ ] Task 2.1: Architecture refactored ✓
  - [ ] Task 2.2: 80% test coverage achieved ✓

- [ ] **All Quality Gates Passed**
  - [ ] Main file <300 lines ✓
  - [ ] All tests pass ✓
  - [ ] Coverage ≥80% ✓

- [ ] **Custom Skills Created** (Total: 7 skills)
  - [ ] streamlit-monolith-to-modular-refactorer ✓
  - [ ] python-architecture-diagram-generator ✓
  - [ ] streamlit-comprehensive-test-generator ✓
  - [ ] playwright-streamlit-e2e-tester ✓

- [ ] **Architecture Validated**
  - [ ] Main file lines: ______ (<300)
  - [ ] Test coverage: ______% (≥80%)
  - [ ] Architecture review: PASSED / FAILED
  - [ ] Code review: PASSED / FAILED

**PROCEED TO PHASE 3**: YES / NO

---

## 🚀 PHASE 3: PRODUCTION READINESS (Days 9-10, 10-14 hours)

**Objective**: Security hardening, production validation, professional documentation

### Phase 3 Orchestrator Deployment

- [ ] **Deploy Phase 3 Orchestrator**
  ```
  Deploy: project-supervisor-orchestrator
  Instruction: "Execute Phase 3 production readiness with custom skills.
  Deploy THREE PARALLEL STREAMS: (1) Security Hardening, (2) Production
  Validation, (3) Documentation Suite. Create 5 custom skills total.
  Maximum parallelization for final push. Enforce quality gates."
  ```

---

### 🛡️ TASK 3.1: SECURITY HARDENING (6-8 hours)

**Priority**: P2 - MEDIUM

#### STEP 1: Create Custom Skill (45-60 min)

- [ ] **Invoke skill-creator to create "streamlit-security-hardener"**
  ```
  Deploy: skill-creator agent

  Skill Specification:
  Name: streamlit-security-hardener
  Purpose: Comprehensive security hardening for Streamlit applications
  Domain Knowledge:
    - Streamlit security best practices
    - Input validation patterns
    - XSS prevention in Streamlit
    - Rate limiting implementation
    - CSP headers configuration
    - Secure session management
    - Path traversal prevention
  Workflow:
    1. Audit current security posture
    2. Implement SecureAIPersona with validation
    3. Add rate limiting to endpoints
    4. Configure security headers
    5. Complete input validation with length limits
    6. Add sanitization layers
    7. Run security scans (bandit, safety)
    8. Test with attack simulation
  Tools: Read, Edit, Write, Bash
  Best Practices:
    - Defense in depth
    - Whitelist over blacklist
    - Fail securely
    - Comprehensive logging
  Success Criteria:
    - All security scans pass
    - Rate limiting functional
    - Input validation complete
    - Attack simulation validates measures
  ```

- [ ] **Validate Skill Creation**
  - Skill file created
  - Specification complete
  - Ready for deployment

#### STEP 2: Deploy Agent Team with Custom Skill (5-7 hours)

- [ ] **Deploy security-engineer agent with custom skill**
  ```
  Task: Audit and implement security hardening
  Skills to Equip:
    - streamlit-security-hardener (custom, just created)
    - webapp-testing (generic, for attack simulation)
    - git-commit-helper (generic)
  Tools: Read, Edit, Write, Bash
  Output: Hardened security implementation
  ```

- [ ] **Deploy test-engineer agent**
  ```
  Task: Create security tests
  Skills to Equip:
    - streamlit-comprehensive-test-generator (from Phase 2)
    - playwright-streamlit-e2e-tester (from Phase 2)
  Tools: Read, Write, Bash
  Output: Security test suite
  ```

- [ ] **Deploy code-reviewer agent**
  ```
  Task: Security-focused code review
  Tools: Read, Grep
  Output: Security code review report
  ```

#### STEP 3: Quality Gate Validation

- [ ] **Run validation commands**
  ```bash
  # Run security scans
  bandit -r src/ -ll
  bandit -r src/ -f json -o security-report.json

  # Run dependency vulnerability check
  safety check

  # Test security measures (manual)
  # - Try XSS injection in persona description
  # - Try path traversal in file operations
  # - Test rate limiting with rapid requests

  # Run security tests
  pytest -m security -v
  ```

- [ ] **Quality Gate Checklist**
  - [ ] Bandit scan passes (no critical/high issues)
  - [ ] Safety check passes (no vulnerable dependencies)
  - [ ] SecureAIPersona integrated
  - [ ] Rate limiting implemented and tested
  - [ ] Security headers configured
  - [ ] Input validation complete
  - [ ] Security tests pass
  - [ ] Attack simulation validates measures
  - [ ] Security code review passed

#### DELIVERABLES CHECKLIST

- [ ] SecureAIPersona integrated
- [ ] Rate limiting implemented
- [ ] Security headers configured
- [ ] Input validation complete with length limits
- [ ] Security scan reports (bandit, safety)
- [ ] Security test suite
- [ ] Attack simulation report
- [ ] Custom skill: `streamlit-security-hardener` created
- [ ] Git commits documenting security changes
- [ ] Security code review report

---

### 🚀 TASK 3.2: PRODUCTION VALIDATION (8-10 hours) [PARALLEL WITH 3.3]

**Priority**: P2 - MEDIUM

#### STEP 1: Create Custom Skills (75-90 min for 2 skills)

- [ ] **Invoke skill-creator to create "streamlit-production-validator"**
  ```
  Deploy: skill-creator agent

  Skill Specification:
  Name: streamlit-production-validator
  Purpose: Comprehensive production readiness validation for Streamlit apps
  Domain Knowledge:
    - Staging deployment strategies
    - E2E testing in production-like environments
    - Performance benchmarking methodologies
    - Load testing with Streamlit
    - Production monitoring setup
  Workflow:
    1. Deploy to staging environment
    2. Run comprehensive E2E test suite
    3. Execute performance benchmarks
    4. Run load testing scenarios
    5. Test error recovery
    6. Validate monitoring and alerting
    7. Generate production readiness report
  Tools: Bash, Read, Write
  Best Practices:
    - Test in production-like environment
    - Realistic load scenarios
    - Monitor during testing
  Success Criteria:
    - All E2E tests pass in staging
    - Performance targets met (<2s p95)
    - Load testing successful
    - Monitoring operational
  ```

- [ ] **Invoke skill-creator to create "executive-production-readiness-reporter"**
  ```
  Deploy: skill-creator agent

  Skill Specification:
  Name: executive-production-readiness-reporter
  Purpose: Generate executive-level production readiness reports
  Domain Knowledge:
    - Executive reporting formats
    - Metrics visualization
    - Risk assessment presentation
    - Go/no-go decision frameworks
  Workflow:
    1. Analyze test and validation results
    2. Generate metrics dashboard (XLSX)
    3. Create executive presentation (PPTX)
    4. Create production readiness report (DOCX/PDF)
    5. Document risks and mitigations
    6. Provide go/no-go recommendation
  Tools: Read, Write
  Best Practices:
    - Clear visualizations
    - Executive summaries
    - Data-driven recommendations
  Success Criteria:
    - Professional presentation
    - Comprehensive metrics
    - Clear go/no-go recommendation
  ```

- [ ] **Validate Skills Creation**
  - Both skill files created
  - Specifications complete
  - Ready for deployment

#### STEP 2: Deploy Agent Team with Custom Skills (6-8 hours)

- [ ] **Deploy devops-engineer agent**
  ```
  Task: Deploy to staging environment
  Tools: Bash, Read, Write
  Output: Staging deployment report
  ```

- [ ] **Deploy test-engineer agent with custom skills**
  ```
  Task: Run E2E validation suite
  Skills to Equip:
    - streamlit-production-validator (custom, just created)
    - playwright-streamlit-e2e-tester (from Phase 2)
    - webapp-testing (generic)
    - executive-production-readiness-reporter (custom, just created)
    - pptx (generic)
    - xlsx (generic)
  Tools: Bash, Read, Write
  Output: E2E validation results + executive reporting suite
  ```

- [ ] **Deploy performance-engineer agent with custom skill**
  ```
  Task: Performance and load testing
  Skills to Equip: streamlit-production-validator (custom)
  Tools: Bash, Read, Write
  Output: Performance benchmark report
  ```

#### STEP 3: Quality Gate Validation

- [ ] **Run validation commands**
  ```bash
  # Deploy to staging (platform-specific)
  # Railway: railway up
  # Or manual deployment to staging

  # Run E2E tests against staging
  STAGING_URL=https://staging.example.com pytest tests/test_e2e/ -v

  # Run performance benchmarks
  python scripts/benchmark_performance.py

  # Check staging health
  curl https://staging.example.com/health
  ```

- [ ] **Quality Gate Checklist**
  - [ ] Staging deployment successful
  - [ ] All E2E tests pass in staging
  - [ ] Performance targets met:
    - [ ] Response time <2s p95 (actual: ______)
    - [ ] Memory usage <512MB (actual: ______)
  - [ ] Load testing passed
  - [ ] Error rate <0.1% (actual: ______)
  - [ ] Monitoring operational
  - [ ] Executive presentation created
  - [ ] Metrics dashboard created
  - [ ] Production readiness report generated
  - [ ] Go/no-go recommendation: GO / NO-GO

#### DELIVERABLES CHECKLIST

- [ ] Staging deployment validated
- [ ] Comprehensive E2E validation in staging
- [ ] Performance benchmark report
- [ ] Load testing report
- [ ] Executive presentation (PPTX)
- [ ] Metrics dashboard (XLSX)
- [ ] Production readiness report (DOCX/PDF)
- [ ] Custom skills: 2 new skills created
- [ ] Go/no-go recommendation document

---

### 📚 TASK 3.3: DOCUMENTATION SUITE (5-6 hours) [PARALLEL WITH 3.2]

**Priority**: P2 - MEDIUM

#### STEP 1: Create Custom Skill (45-60 min)

- [ ] **Invoke skill-creator to create "streamlit-professional-documenter"**
  ```
  Deploy: skill-creator agent

  Skill Specification:
  Name: streamlit-professional-documenter
  Purpose: Create comprehensive professional documentation for Streamlit apps
  Domain Knowledge:
    - Technical documentation best practices
    - Streamlit documentation patterns
    - API documentation standards
    - Architecture documentation
    - Multi-format documentation (MD, DOCX, PDF)
  Workflow:
    1. Audit codebase for documentation needs
    2. Update README.md with current architecture
    3. Create ARCHITECTURE.md with diagrams
    4. Generate API_REFERENCE.md
    5. Create DEPLOYMENT_GUIDE.md
    6. Create CONTRIBUTING.md
    7. Generate PDF versions
    8. Create architecture presentation
    9. Apply consistent styling
  Tools: Read, Write, Edit, Grep, Glob
  Best Practices:
    - Clear structure
    - Visual aids (diagrams)
    - Multiple formats
    - Validated instructions
  Success Criteria:
    - All documentation complete
    - Multiple formats available
    - Professional appearance
    - Setup instructions validated
  ```

- [ ] **Validate Skill Creation**
  - Skill file created
  - Specification complete
  - Ready for deployment

#### STEP 2: Deploy Agent Team with Custom Skill (4-5 hours)

- [ ] **Deploy documentation-expert agent with custom skill**
  ```
  Task: Create technical documentation suite
  Skills to Equip:
    - streamlit-professional-documenter (custom, just created)
    - python-architecture-diagram-generator (from Phase 2)
    - docx (generic)
    - pdf-anthropic (generic)
    - canvas-design (generic)
    - theme-factory (generic)
    - pptx (generic)
  Tools: Read, Write, Edit, Grep, Glob
  Output: Complete professional documentation suite
  ```

- [ ] **Deploy technical-writer agent with custom skill**
  ```
  Task: Write narrative documentation and guides
  Skills to Equip:
    - streamlit-professional-documenter (custom)
    - brand-guidelines (generic)
  Tools: Read, Write, Edit
  Output: User-friendly narratives and guides
  ```

#### STEP 3: Quality Gate Validation

- [ ] **Run validation commands**
  ```bash
  # Test setup instructions on fresh machine
  # (Manual validation recommended)

  # Check all documentation files exist
  ls -la README.md ARCHITECTURE.md API_REFERENCE.md DEPLOYMENT_GUIDE.md CONTRIBUTING.md

  # Check for broken links
  grep -r "](http" *.md | grep -v ".png\|.jpg\|.svg"

  # Validate PDF generation
  ls -la docs/*.pdf
  ```

- [ ] **Quality Gate Checklist**
  - [ ] README.md updated and comprehensive
  - [ ] ARCHITECTURE.md created with diagrams
  - [ ] API_REFERENCE.md generated
  - [ ] DEPLOYMENT_GUIDE.md created
  - [ ] CONTRIBUTING.md created
  - [ ] PDF versions generated
  - [ ] Architecture presentation created (PPTX)
  - [ ] All diagrams included and professional
  - [ ] Consistent styling and branding
  - [ ] Setup instructions validated
  - [ ] No broken links

#### DELIVERABLES CHECKLIST

- [ ] Updated README.md
- [ ] ARCHITECTURE.md with diagrams
- [ ] API_REFERENCE.md
- [ ] DEPLOYMENT_GUIDE.md
- [ ] CONTRIBUTING.md
- [ ] PDF documentation suite
- [ ] Architecture presentation (PPTX)
- [ ] Professional diagrams throughout
- [ ] Consistent branding applied
- [ ] Custom skill: `streamlit-professional-documenter` created

---

### 📊 PHASE 3 COMPLETION GATE

**Before Final Production Approval, Validate All Items:**

- [ ] **All Phase 3 Tasks Complete**
  - [ ] Task 3.1: Security hardened ✓
  - [ ] Task 3.2: Production validated ✓
  - [ ] Task 3.3: Documentation complete ✓

- [ ] **All Quality Gates Passed**
  - [ ] Security scans pass ✓
  - [ ] Staging validation successful ✓
  - [ ] Documentation complete ✓

- [ ] **Custom Skills Created** (Total: 12 skills)
  - [ ] streamlit-security-hardener ✓
  - [ ] streamlit-production-validator ✓
  - [ ] executive-production-readiness-reporter ✓
  - [ ] streamlit-professional-documenter ✓

- [ ] **Production Readiness Validated**
  - [ ] Security: All scans PASSED
  - [ ] Performance: Targets MET
  - [ ] Testing: All tests PASSED
  - [ ] Documentation: COMPLETE
  - [ ] Executive recommendation: GO / NO-GO

**PROCEED TO PRODUCTION**: YES / NO

---

## ✅ FINAL PRODUCTION READINESS CHECKLIST

### CRITICAL REQUIREMENTS ⚡
- [ ] Test suite runs without errors
- [ ] Single canonical Ollama client
- [ ] Event loop stable (no errors)
- [ ] Architecture refactored (<300 line main)
- [ ] 80%+ test coverage achieved
- [ ] All security scans pass
- [ ] Staging validated successfully
- [ ] Performance targets met

### SECURITY REQUIREMENTS 🔐
- [ ] XSS prevention validated
- [ ] Path traversal prevention tested
- [ ] Rate limiting functional
- [ ] Input validation complete
- [ ] Security headers configured
- [ ] Attack simulation successful
- [ ] SecureAIPersona integrated

### PERFORMANCE REQUIREMENTS ⚡
- [ ] Response time <2s p95 (actual: ______)
- [ ] Memory usage <512MB (actual: ______)
- [ ] No memory leaks detected
- [ ] Connection pooling active
- [ ] Load testing passed

### RELIABILITY REQUIREMENTS 📊
- [ ] Error rate <0.1% (actual: ______)
- [ ] All errors handled gracefully
- [ ] Comprehensive logging operational
- [ ] Monitoring operational
- [ ] Health checks working

### DOCUMENTATION REQUIREMENTS 📚
- [ ] README accurate and complete
- [ ] Architecture documented with diagrams
- [ ] API documented
- [ ] Deployment guides validated
- [ ] Contributing guidelines complete
- [ ] Executive presentations ready

---

## 📊 EXECUTION METRICS

### Time Tracking

| Phase | Estimated | Actual | Status |
|-------|-----------|--------|--------|
| Phase 1 | 10-15h | ______h | ⬜ |
| Phase 2 | 12-18h | ______h | ⬜ |
| Phase 3 | 10-14h | ______h | ⬜ |
| **TOTAL** | **32-47h** | **______h** | **⬜** |

### Custom Skills Library

| # | Skill Name | Phase | Status |
|---|------------|-------|--------|
| 1 | pytest-streamlit-async-fixer | 1 | ⬜ |
| 2 | python-async-client-consolidator | 1 | ⬜ |
| 3 | streamlit-async-pattern-optimizer | 1 | ⬜ |
| 4 | streamlit-monolith-to-modular-refactorer | 2 | ⬜ |
| 5 | python-architecture-diagram-generator | 2 | ⬜ |
| 6 | streamlit-comprehensive-test-generator | 2 | ⬜ |
| 7 | playwright-streamlit-e2e-tester | 2 | ⬜ |
| 8 | streamlit-security-hardener | 3 | ⬜ |
| 9 | streamlit-production-validator | 3 | ⬜ |
| 10 | executive-production-readiness-reporter | 3 | ⬜ |
| 11 | streamlit-professional-documenter | 3 | ⬜ |
| 12+ | [Ad-hoc skills as needed] | All | ⬜ |

### Quality Gate Tracking

| Gate | Criteria | Status | Notes |
|------|----------|--------|-------|
| Foundation | Tests run, client unified, async stable | ⬜ | |
| Architecture | Main <300 lines, modular structure | ⬜ | |
| Testing | 80%+ coverage, all tests pass | ⬜ | |
| Security | All scans pass, hardening complete | ⬜ | |
| Production | Staging validated, targets met | ⬜ | |
| Documentation | Complete suite, multiple formats | ⬜ | |

---

## 🎯 NEXT STEPS AFTER COMPLETION

### Immediate Post-Execution
1. [ ] Merge feature branch to main
2. [ ] Tag release version
3. [ ] Deploy to production
4. [ ] Monitor production metrics
5. [ ] Archive all documentation

### Skill Library Management
1. [ ] Catalog all 12+ created skills
2. [ ] Document skill purposes and usage
3. [ ] Establish skill maintenance procedures
4. [ ] Plan skill reuse strategy for future projects

### Continuous Improvement
1. [ ] Conduct execution retrospective
2. [ ] Identify process improvements
3. [ ] Update skill library documentation
4. [ ] Refine orchestration patterns

---

## 📞 EXECUTION SUPPORT

### Commands Reference

```bash
# Git workflow
git checkout -b feature/production-readiness-ultimate
git add .
git commit -m "Description"
git push

# Testing
pytest -v
pytest --cov=src --cov-report=html
pytest -m integration
pytest -m security

# Security scanning
bandit -r src/ -ll
safety check

# Linting
ruff check src/

# Application
streamlit run streamlit_backroom.py
```

### Contact & Escalation
- Questions: Ask during execution
- Blockers: Escalate immediately
- Reviews: Request at quality gates

---

## 🚀 EXECUTION AUTHORIZATION

**Plan Status**: READY FOR EXECUTION
**Review Status**: PENDING USER APPROVAL
**Authorization**: PENDING

**Authorized By**: ________________
**Date**: ________________
**Signature**: ________________

---

**READY TO BEGIN EXECUTION ON YOUR COMMAND** 🎯

*This execution plan is comprehensive, machine-readable, and designed for step-by-step execution with clear validation at every stage.*
