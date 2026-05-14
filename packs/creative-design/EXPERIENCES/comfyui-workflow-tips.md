---
type: tutorial
skill_ref: comfyui
keywords: [comfyui, workflow, nodes]
created: 2026-05-14
---

# ComfyUI Workflow Setup Guide

> ComfyUI 节点式工作流搭建指南 — 从基础架构到高级技巧的完整实践

## 1. 节点组织原则

### 工作流分层架构

```
┌─────────────────────────────────────────────────┐
│                  Input Layer                      │
│  (Load Checkpoint → Load LoRA → Load VAE)        │
├─────────────────────────────────────────────────┤
│              Processing Pipeline                  │
│  (CLIP Text Encode → KSampler → VAE Decode)     │
├─────────────────────────────────────────────────┤
│                 Output Layer                      │
│  (Save Image → Preview → Upscale)                │
└─────────────────────────────────────────────────┘
```

### 节点命名规范

```markdown
# 推荐分组前缀
[IN]   → Input nodes (checkpoint, image, text)
[PROC] → Processing nodes (sampler, latent, mask)
[CTRL] → ControlNet / IP-Adapter nodes
[OUT]  → Output nodes (preview, save, upscale)
[UTIL] → Utility nodes (primitive, logic, math)
```

### 节点布局最佳实践

- **从左到右布局**: 文件加载在最左，输出在最右
- **使用 Reroute 节点**: 减少连线交叉，保持界面整洁
- **分组框 (Group nodes)**: 用颜色区分功能模块
  - 蓝色: 模型加载
  - 绿色: 图像处理
  - 红色: ControlNet
  - 黄色: 后处理
- **最小化 crossover**: 各模块之间保持垂直对齐

## 2. Model Loading 工作流

### Checkpoint 加载配置

```yaml
# 推荐配置
Load Checkpoint:
  model: "sd_xl_base_1.0.safetensors"
  vae: "sdxl_vae.safetensors"       # 单独加载 VA格式E 防止色彩失真
  clip_skip: -2                     # 跳过最后2层 CLIP 层

# 错误做法
Load Checkpoint (default VAE):
  # 使用 checkpoint 内置 VAE 可能导致色彩偏移
  # 应加载独立 VAE 文件
```

### LoRA 与 Embedding 加载顺序

```
1. Load Checkpoint (base)
2. Load VAE (separate file)
3. Load LoRA(s) → 权重从 0.4 开始调试
4. Load Embedding / Textual Inversion (如有)
5. CLIP Text Encode (positive + negative)
```

### 模型卸载策略

| 场景 | 策略 | 命令/操作 |
|:-----|:------|:----------|
| **切换 checkpoint** | 清除 GPU 缓存 | `Load Checkpoint` 自动卸载旧模型 |
| **OOM 错误** | 低显存模式 | `--lowvram` 启动参数 |
| **批量生成** | 固定模型不卸载 | 使用 `Keep Alive` 保持模型加载 |
| **多模型对比** | 交替加载 | 使用 `Checkpoint Loader Switch` |

## 3. Batch Processing 批量处理

### 批量生成设置

```python
# 批量参数配置
batch_config = {
    "batch_size":     4,    # 每批次并行生成数（受显存限制）
    "batch_count":   10,    # 总批次数
    "seed_offset":    1,    # 每次批次 seed 递增
    "variation_seed": True  # 每次随机 seed
}
```

### 批量输入处理

```markdown
# 批量处理工作流类型
1. **Text → Image 批量**: 多个 prompt 同一 seed
   - 使用 `文本输入` + `Primitive List` + `循环节点`
   
2. **Image → Image 批量**: 同一 prompt 多张原图
   - 输入目录通过 `Folder Walker` 自动遍历
   
3. **参数扫描**: 遍历 CFG / Steps / Denoise
   - `Primitive Float Range` + `KSampler` 参数输入
```

### 输出管理

- **文件名模板**: `{workflow_name}_{prompt_hash}_{seed}_{index}`
- **子目录分类**: `outputs/batch_{datetime}/{seed_range}/`
- **元数据写入**: 在每个 PNG 中写入 workflow 元数据
- **自动删除失败**: `failed/` 子目录隔离异常输出

## 4. 常见 Pitfalls

### Pitfall 1: VAE 不匹配

**问题**: 使用 checkpoint 内置 VAE 或加载错误 VAE 导致色彩严重偏色

**解决**: 
- 始终显式加载独立 VAE 文件
- SDXL 使用 `sdxl_vae.safetensors`
- SD1.5 使用 `vae-ft-mse-840000-ema-pruned.safetensors`

### Pitfall 2: 显存溢出 (OOM)

| 显存 | 安全配置 | 极限配置 |
|:-----|:---------|:---------|
| 4GB | 512×512, batch=1 | 768×768, batch=1 |
| 8GB | 768×768, batch=2 | 1024×1024, batch=1 |
| 12GB | 1024×1024, batch=2 | 1280×1280, batch=1 |
| 24GB | 1024×1024, batch=8 | 2048×2048, batch=2 |

**解决方案**:
- `--lowvram`: 每个节点用完即卸载（降速 30% 但省显存）
- `--medvram`: 半精度缓存（推荐平衡）
- Tiled VAE: 分块解码大图
- 减少 `batch_size` 至 1

### Pitfall 3: 节点类型不兼容

```markdown
# 常见不兼容模式
- ❌ Load Checkpoint (SDXL) + VAE (SD1.5) → 尺寸/结构错误
- ❌ ControlNet (SD1.5) + Base model (SDXL) → 无效果
- ❌ LoRA (SD1.5) + Checkpoint (SDXL) → 加载失败
- ✅ 始终匹配 base model 版本
```

### Pitfall 4: Workflow 脆弱性

- **绝对路径**: 不要用 `/home/user/...` — 使用 `ComfyUI/input/` 相对路径
- **缺失节点**: 用 `Missing Nodes` 窗口一键安装自定义节点
- **版本锁定**: 关键 workflow 导出时附带 `requirements.txt`
- **备份策略**: 每次重大修改前复制 workflow 为 `*.bak.json`

## 5. 性能优化

### 推理加速

| 方法 | 加速比 | 质量影响 |
|:-----|:-------|:---------|
| `--force-fp16` | 1.5x | 几乎无 |
| Turbo scheduler | 3-5x | 轻微降低 |
| Model quantization (8-bit) | 1.8x | 几乎无 |
| xformers | 1.3x | 无 |
| Batch size increase | 线性 | 无（显存够） |

### 缓存策略

- **CLIP cache**: 复用相同 prompt 的 text embedding
- **Model cache**: 频繁切换模型时保留在显存
- **Latent cache**: 图生图时复用 noise latents
