---
type: concept
domain: developer-workflow
keywords: [tdd, test-driven-development, red-green-refactor, unit-testing, test-first]
created: 2026-05-14
---

# TDD Cycle (Test-Driven Development)

## Definition
Test-Driven Development (TDD) is a software development practice where tests are written before the implementation code. The cycle follows a strict Red-Green-Refactor rhythm: write a failing test, make it pass with minimal code, then improve the design.

## Core Concepts
- **Red Phase**: Write a test that defines a desired behavior or function. The test fails because the implementation does not yet exist — this validates the test is meaningful.
- **Green Phase**: Write the simplest possible implementation code to make the test pass. No optimization or refactoring — just pass the test.
- **Refactor Phase**: Clean up the code while keeping all tests green. Improve design, remove duplication, and optimize without changing external behavior.
- **Test Granularity**: Unit tests target individual functions, integration tests verify component interactions, and acceptance tests validate end-to-end workflows.
- **Test Coverage**: TDD naturally produces high coverage, but the focus is on behavioral coverage — testing what the code does, not how it does it.

## Relationships
- Implements requirements from **SDD Workflow** specifications as executable tests
- Produces well-tested code that passes **Code Review** with higher confidence
- Feeds into **CI/CD Pipeline** as the automated test suite executed on every commit
