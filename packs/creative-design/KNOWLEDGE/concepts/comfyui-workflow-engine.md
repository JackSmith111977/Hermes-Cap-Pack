---
type: concept
domain: creative-design
keywords: [comfyui, workflow, nodes, stable-diffusion, pipeline]
created: 2026-05-14
---

# ComfyUI Workflow Engine

## Definition

ComfyUI is a node-based workflow engine for Stable Diffusion and other diffusion models. It provides a visual programming interface where users construct image generation pipelines by connecting nodes — each node representing a model, operation, or data transformation. The graph-based architecture enables precise control over every step of the generation process.

## Core Concepts

### Node Types and Roles

| Node Category | Function | Examples |
|:--------------|:---------|:---------|
| **Loaders** | Load models and resources | CheckpointLoader, LoraLoader, VaeLoader |
| **Encoders** | Convert text/images to latent representations | CLIPTextEncode, VAEEncode |
| **Samplers** | Core diffusion process | KSampler, KSamplerAdvanced |
| **Decoders** | Convert latents back to images | VAEDecode |
| **Conditioning** | Control generation via spatial inputs | ControlNetApply, IPAdapterApply |
| **Post-process** | Upscale, filter, composite | ImageUpscale, ImageComposite |
| **Utility** | Flow control, math, logic | PrimitiveNode, Switch, Reroute |

### Graph Architecture Principles

- **Data flow**: Directed acyclic graph (DAG) — data flows left to right
- **Latent tensor**: The primary data type passed between nodes (compressed image representation)
- **Model sharing**: Models loaded once and referenced by multiple downstream nodes
- **Batching**: Batch dimension flows through the entire graph automatically

### Key Concepts

- **Latent space**: The compressed representation where diffusion operates (typically 8× downscaled)
- **CFG Scale**: Classifier-Free Guidance scale — how strongly the output follows the prompt
- **Denoising strength**: How much of the original image to retain (0=preserve, 1=full regenerate)
- **Seed**: Random number seed for reproducibility — same seed + same workflow = same output

## Relationships

- **Companion to**: `image-generation` (same domain, tool-specific workflow)
- **Requires**: Understanding of diffusion models and latent spaces
- **Used with**: Custom nodes (ControlNet, IP-Adapter, LoRA) for advanced pipelines
- **Input to**: Batch processing scripts, animation workflows (SVD, AnimateDiff)
- **Related to**: `image-prompt-guide` for crafting effective prompts within node parameters
