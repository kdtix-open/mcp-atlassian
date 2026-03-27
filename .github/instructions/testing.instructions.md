---
applyTo: "**/*.test.*,**/*.spec.*,**/*_test.*,**/*Test.*"
---
# Testing Standards

- Test method names MUST follow `{MethodName}_{Scenario}_{ExpectedOutcome}`
- Tests MUST be fully deterministic — no random data without explicit seeding
- Tests MUST be isolated — each sets up and tears down its own state
- Tests MUST NOT duplicate production business logic
- Every bug fix MUST begin with a failing regression test first (TDD: Red → Green → Refactor)
- New code requires ≥ 80% coverage; critical paths (auth, security, mutations) require 100%

For full details, see `.github/docs/standards/testing-requirements.md`
