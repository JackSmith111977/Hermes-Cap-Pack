---
type: concept
domain: devops-monitor
keywords: [docker, containerization, image, container, orchestration, isolation]
created: 2026-05-14
---

# Docker Containerization

## Definition
Docker containerization packages applications and their dependencies into lightweight, portable containers that run consistently across any environment. Containers share the host OS kernel but provide filesystem, network, and process isolation.

## Core Concepts
- **Docker Image**: A read-only template with layers of filesystem snapshots. Images are built from Dockerfiles and stored in registries (Docker Hub, ECR, GCR).
- **Docker Container**: A runnable instance of an image, with its own filesystem, network interfaces, and process tree. Containers can be started, stopped, moved, and deleted.
- **Dockerfile**: A declarative script defining the build steps — base image, dependencies, configuration, and entrypoint. Each instruction creates a cacheable layer.
- **Volume Mounts**: Persistent data storage outside the container's ephemeral filesystem, enabling stateful workloads like databases.
- **Docker Compose**: A multi-container orchestration tool using YAML to define services, networks, and volumes for local development environments.

## Relationships
- Provides the runtime environment for **CI/CD Pipeline** build and test stages
- Enables consistent **Deployment** across dev, staging, and production
- Integrates with **Monitoring** stacks via container-level metrics and log collection
