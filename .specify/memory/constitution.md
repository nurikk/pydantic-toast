<!--
  SYNC IMPACT REPORT
  ==================
  Version change: N/A → 1.0.0 (initial ratification)
  
  Modified principles: N/A (initial version)
  
  Added sections:
  - Core Principles (4 principles)
    - I. Code Quality Standards
    - II. Testing Standards
    - III. User Experience Consistency
    - IV. Performance Requirements
  - Quality Gates
  - Development Workflow
  - Governance
  
  Removed sections: N/A (initial version)
  
  Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (Constitution Check section compatible)
  - .specify/templates/spec-template.md ✅ (Success Criteria aligns with performance/UX principles)
  - .specify/templates/tasks-template.md ✅ (Test-first workflow compatible)
  
  Follow-up TODOs: None
-->

# Pydantic Toast Constitution

## Core Principles

### I. Code Quality Standards

All code MUST adhere to strict quality standards to ensure maintainability and reliability.

- **Type Safety**: All functions MUST have complete type annotations. No `Any` types unless
  explicitly justified in code review.
- **Single Responsibility**: Each module, class, and function MUST have one clearly defined
  purpose. Functions exceeding 50 lines require justification.
- **Explicit Over Implicit**: Avoid magic methods and hidden behavior. Dependencies MUST be
  explicitly injected, not globally imported or auto-discovered.
- **No Dead Code**: Unused imports, variables, and functions MUST be removed before merge.
- **Consistent Naming**: Follow Python conventions (snake_case for functions/variables,
  PascalCase for classes). Names MUST be descriptive and unambiguous.
- **Error Handling**: All external calls (I/O, network, parsing) MUST have explicit error
  handling with typed exceptions. Never silently swallow exceptions.

**Rationale**: Consistent, readable code reduces cognitive load for maintainers and minimizes
defect introduction rates.

### II. Testing Standards

Testing is mandatory and MUST follow established patterns to ensure reliability.

- **Function-Based Tests Only**: All tests MUST be simple functions. No class-based test
  structures (no `TestCase` classes, no `unittest.TestCase`).
- **No Mocks**: Tests MUST NOT use mocks, patches, or monkeypatching. Use real implementations
  or existing fixtures. If a test cannot be written without mocks, reconsider the design.
- **Module-Scoped Imports**: Test files MUST use module-level imports only. No function-scoped
  imports or inline imports within test functions.
- **Meaningful Assertions**: Each test MUST have clear, specific assertions. Avoid generic
  "assert True" or overly broad exception catches.
- **Test Naming**: Test functions MUST follow `test_<behavior>_<condition>_<expected>` pattern
  (e.g., `test_parse_empty_input_raises_value_error`).
- **Coverage Requirements**: New code MUST have test coverage. Critical paths require both
  happy path and error case tests.

**Rationale**: Simple, mock-free tests are more maintainable, less brittle, and provide
higher confidence in actual system behavior.

### III. User Experience Consistency

All user-facing interfaces MUST provide predictable, coherent experiences.

- **Consistent Error Messages**: All error outputs MUST follow a standard format with
  actionable guidance. Errors MUST be written for the end user, not the developer.
- **Predictable Behavior**: Similar operations MUST behave similarly. No surprising side
  effects or inconsistent return types for equivalent operations.
- **Progressive Disclosure**: Simple use cases MUST remain simple. Advanced options MUST
  NOT complicate the default experience.
- **Clear Documentation**: Every public API MUST have docstrings explaining purpose,
  parameters, return values, and exceptions. Examples required for complex APIs.
- **Graceful Degradation**: Systems MUST handle edge cases gracefully. Prefer partial
  success with clear reporting over complete failure.

**Rationale**: Users develop mental models based on experience. Inconsistency forces
users to re-learn behavior, increasing friction and errors.

### IV. Performance Requirements

Performance MUST be considered from design phase, not as an afterthought.

- **Baseline Metrics**: Every feature MUST document expected performance characteristics
  (time complexity, memory usage, I/O patterns) in the design phase.
- **No Premature Optimization**: Optimize only when metrics demonstrate need. All
  optimizations MUST include before/after benchmarks.
- **Resource Awareness**: Code MUST be conscious of resource consumption. Large data
  structures MUST use streaming/iteration where possible.
- **Async by Default**: I/O-bound operations SHOULD use async patterns. Blocking calls
  in async contexts MUST be wrapped appropriately.
- **Startup Time**: Application startup MUST remain responsive. Lazy loading required
  for heavy dependencies.
- **Regression Prevention**: Performance-critical paths MUST have benchmark tests to
  detect regressions.

**Rationale**: Performance issues are expensive to fix after deployment. Early awareness
prevents architectural decisions that preclude optimization.

## Quality Gates

All code changes MUST pass these gates before merge:

| Gate | Requirement | Enforcement |
|------|-------------|-------------|
| Type Check | `mypy --strict` passes | CI required |
| Lint | No linter errors (ruff) | CI required |
| Format | Code formatted (ruff format) | CI required |
| Tests | All tests pass | CI required |
| Coverage | No decrease in coverage | CI required |
| Review | At least one approval | PR required |

## Development Workflow

All development MUST follow this workflow:

1. **Design First**: Document requirements and approach before implementation.
2. **Tests Before Code**: Write failing tests that define expected behavior.
3. **Incremental Commits**: Each commit MUST be atomic and pass all quality gates.
4. **Review Required**: All changes require code review before merge.
5. **No Direct Main Commits**: All changes MUST go through pull requests.

## Governance

This constitution supersedes all other development practices and guidelines.

- **Amendments**: Changes to this constitution require documented justification,
  team review, and explicit approval. All amendments MUST include migration plans
  for existing code if applicable.
- **Compliance**: All pull requests and code reviews MUST verify compliance with
  these principles. Violations require explicit justification or refactoring.
- **Exceptions**: Temporary exceptions MUST be documented with issue tracking and
  remediation timeline. No permanent exceptions without constitution amendment.
- **Versioning**: Constitution follows semantic versioning:
  - MAJOR: Principle removal or backward-incompatible redefinition
  - MINOR: New principle or section addition
  - PATCH: Clarifications and wording improvements

**Version**: 1.0.0 | **Ratified**: 2025-12-23 | **Last Amended**: 2025-12-23
