---
type: concept
domain: creative-design
keywords: [comfyui, pipeline, workflow, node-graph, image-generation, automation]
created: 2026-05-14
---

# ComfyUI Pipeline

## Definition
ComfyUI is a node-based visual workflow system for AI image generation. Pipelines are directed graphs where each node performs a specific transformation — loading models, encoding prompts, sampling latents, or post-processing images — connected by data-flow edges.

## Core Concepts
- **Node Graph Architecture**: Each node is a self-contained operation with typed inputs and outputs. Graphs can be saved as JSON workflows for reproducibility.
- **Model Loading Nodes**: Checkpoint loaders, LoRA loaders, and VAE loaders initialize model weights into memory for the pipeline.
- **Latent Flow**: The core data type is the latent tensor, which flows from the sampler through decoders to output images.
- **Queue and Batch Execution**: Workflows can be queued sequentially or executed in batch, with automatic GPU memory management.
- **Custom Nodes**: The ecosystem extends via community custom nodes for ControlNet, video generation, upscaling, and more.

## Relationships
- Executes **AI Image Generation** models as its core pipeline stage
- Can be controlled programmatically via **API Integration** for automated production workflows
- Outputs feed into **Visual Design Principles** review cycles for quality assessment
