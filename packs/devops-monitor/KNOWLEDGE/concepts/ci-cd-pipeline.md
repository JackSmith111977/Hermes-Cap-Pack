---
type: concept
domain: devops-monitor
keywords: [ci-cd, pipeline, automation, deployment, integration, delivery]
created: 2026-05-14
---

# CI/CD Pipeline

## Definition
A CI/CD (Continuous Integration / Continuous Delivery) pipeline automates the build, test, and deployment lifecycle of software. Every code commit triggers a sequence of stages that verify quality and deliver artifacts to target environments.

## Core Concepts
- **Continuous Integration (CI)**: Developers merge code changes frequently into a shared branch. Each merge triggers automated builds and tests to detect integration issues early.
- **Continuous Delivery (CD)**: Every passing CI build produces a deployable artifact that can be released to staging or production with manual approval.
- **Pipeline Stages**: Typical stages include checkout, lint, build, unit test, integration test, security scan, artifact publish, and deploy.
- **Artifact Repository**: Build outputs (Docker images, JARs, npm packages) are stored in registries with version tags, enabling rollback and traceability.
- **Gates and Approvals**: Manual or automated quality gates (test coverage thresholds, vulnerability scans) must pass before promotion to the next environment.

## Relationships
- Executes tests produced by **TDD Cycle** and **Code Review** workflows
- Builds and ships **Docker Containerization** images as deployment artifacts
- Feeds **Monitoring** and alerting systems with deployment events and pipeline metrics
