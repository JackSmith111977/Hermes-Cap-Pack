---
type: concept
domain: developer-workflow
keywords: [tdd, testing, test-driven-development, red-green-refactor]
created: 2026-05-14
---

# Test-Driven Development

## Definition

Test-Driven Development (TDD) is a software development methodology where tests are written before the implementation code. The process follows a strict Red-Green-Refactor cycle: write a failing test (Red), write the minimum code to make it pass (Green), then refactor for quality (Refactor). TDD drives design through testability and produces a comprehensive regression suite as a byproduct.

## Core Concepts

### The Red-Green-Refactor Cycle

```
RED   → Write a test that fails (defines the expected behavior)
         ↓
GREEN → Write the minimum code to pass the test
         ↓
REFACTOR → Clean up both code and test without changing behavior
         ↓
         (Repeat for next requirement)
```

### TDD Benefits

- **Design forcing**: Writing tests first encourages modular, loosely coupled code with clear interfaces
- **Regression safety**: The accumulated test suite catches regressions instantly
- **Documentation**: Tests serve as executable documentation of expected behavior
- **Confidence**: Enables aggressive refactoring with immediate feedback
- **Focused development**: Each test defines a single, concrete objective

### Testing Levels with TDD

| Level | Scope | Speed | Tooling |
|:------|:------|:------|:--------|
| **Unit** | Single function/class | Milliseconds | pytest, vitest, JUnit |
| **Integration** | Component interaction | Seconds | pytest + fixtures, supertest |
| **Acceptance** | End-to-end feature | Minutes | playwright, cypress, selenium |

### Key Practices

1. **Test one thing per test** — Single assertion or cohesive behavior group
2. **Arrange-Act-Assert** pattern — Setup, execute, verify
3. **Keep tests independent** — No shared state between tests
4. **Test behavior, not implementation** — Focus on what, not how
5. **Run tests frequently** — Before every commit, ideally on every save

## Relationships

- **Works with**: `systematic-debugging` (debugging methodology complements TDD)
- **Related to**: `writing-plans` (plan-driven development), `one-three-one-rule` (effort allocation)
- **Prerequisite for**: CI/CD pipelines that enforce test coverage gates
- **Supported by**: `python-env-guide`, `node-inspect-debugger` for environment setup
