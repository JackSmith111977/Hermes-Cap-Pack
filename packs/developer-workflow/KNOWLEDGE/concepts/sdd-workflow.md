---
type: concept
domain: developer-workflow
keywords: [sdd, specification-driven-development, requirements, architecture, design-doc]
created: 2026-05-14
---

# SDD Workflow (Specification-Driven Development)

## Definition
Specification-Driven Development (SDD) is a methodology where comprehensive specifications are written before implementation begins. The spec defines requirements, architecture, interfaces, and acceptance criteria, serving as the single source of truth throughout development.

## Core Concepts
- **Specification Document**: A structured document covering purpose, scope, functional requirements, non-functional requirements, API contracts, data models, and edge cases.
- **Review Gate**: The spec undergoes peer and stakeholder review before any code is written, catching design flaws early at minimal cost.
- **Acceptance Criteria**: Each requirement includes explicit, testable conditions that must be met for the feature to be considered complete.
- **Traceability**: Requirements flow from spec → implementation → tests, ensuring every feature is verified and no untested code is shipped.
- **Living Document**: The spec is updated during implementation as discoveries are made, maintaining alignment between design and code.

## Relationships
- Provides the requirements input for **TDD Cycle** test case authoring
- Establishes the design context for **Code Review** evaluation criteria
- Integrates with **Project Management** workflows for task breakdown and estimation
