---
type: best-practice
skill_ref: image-generation
keywords: [ai-image, prompt-engineering, best-practices]
created: 2026-05-14
---

# AI Image Generation Best Practices

> 高质量 AI 图像生成工作流实践指南 — 从提示词工程到模型选择的完整方法论

## 1. Prompt Engineering 核心原则

### 结构化提示词模板

```
[Subject] + [Action/Pose] + [Environment] + [Lighting] + [Style] + [Quality Modifiers]
```

| 组件 | 描述 | 示例 |
|:-----|:------|:------|
| **Subject** | 主体描述（具体到细节） | "a cyberpunk samurai woman with neon katana" |
| **Action/Pose** | 姿势与动作 | "standing on a rain-soaked rooftop, looking down" |
| **Environment** | 背景与环境 | "futuristic Tokyo skyline, holographic billboards" |
| **Lighting** | 光源与氛围 | "volumetric lighting, neon glow, dramatic shadows" |
| **Style** | 艺术风格 | "anime style by Makoto Shinkai, detailed linework" |
| **Quality** | 质量修饰词 | "8K, highly detailed, sharp focus, cinematic composition" |

### 负提示词策略

```markdown
# 常见负提示词分类
- **解剖学问题**: deformed hands, extra fingers, bad anatomy, mutated
- **质量问题**: blurry, low quality, jpeg artifacts, pixelated
- **风格冲突**: watermark, text, signature, frame
- **构图问题**: cropped, out of frame, cut off, distorted
```

### 提示词迭代工作流

1. **基础构图** → 写核心主体 + 环境（3-5个关键描述词）
2. **风格注入** → 添加风格参考 + 艺术家引用
3. **质量提升** → 添加质量修饰词 + 光照描述
4. **负优化** → 根据输出添加针对性负提示词
5. **种子锁定** → 找到满意的构图后固定 seed 做微调

## 2. Model Selection 模型选择策略

| 场景 | 推荐模型 | 优势 |
|:-----|:---------|:------|
| **写实摄影** | SDXL + RealVisXL / Juggernaut XL | 照片级真实感 |
| **二次元动漫** | Niji Journey / Anything V5 | 专业动漫风格 |
| **概念设计** | Midjourney V6 / DALL-E 3 | 创意自由度高 |
| **产品渲染** | SDXL + 特定 LoRA | 精确控制 |
| **速度优先** | Turbo models (SDXL Turbo) | 1-2步推理 |

### Checkpoint 选择要点

- **Base model 匹配**: LoRA/ControlNet 必须与 base model 版本匹配
- **VAE 兼容性**: 使用与 checkpoint 配对的 VAE 避免色彩失真
- **CLIP skip**: 部分模型需要 CLIP skip 2 来获得更好 prompt 遵循度

## 3. Resolution & Aspect Ratio 设置

### 分辨率最佳实践

```python
# 推荐的初始分辨率（基于 base model）
resolution_map = {
    "SD 1.5":      (512, 512),   # base: 512x512
    "SDXL":        (1024, 1024), # base: 1024x1024
    "SDXL Turbo":  (1024, 1024),
    "SVD":         (576, 1024),  # 视频模型
}
```

### 宽高比选择

| 用途 | 宽高比 | 分辨率 |
|:-----|:-------|:-------|
| 社交媒体帖图 | 1:1 | 1024×1024 |
| 横幅/Banner | 16:9 | 1456×816 |
| 手机壁纸 | 9:16 | 816×1456 |
| 打印海报 | 3:4 | 1152×1536 |
| 产品展示 | 4:3 | 1152×864 |

### Upscaling 策略

1. **Latent upscale** (SD upscale) → 保持风格一致但可能模糊
2. **ESRGAN / 4x-UltraSharp** → 最佳画质提升
3. **Tiled upscale** → 超大图（>4096px）时分块处理
4. **Hires.fix** → 两步法：低分辨率生图 + 高分辨率重绘

## 4. Iteration 迭代技巧

### 高效迭代工作流

```
Prompt A (粗构图) → seed=1234 → 满意构图方向
  ├─ 微调 prompt → seed=1234 → 优化细节
  ├─ 换 style modifier → seed=1234 → 风格探索
  └─ 换 model/checkpoint → seed=1234 → 模型对比
```

### Seed 控制策略

- **固定 seed 做 prompt 消融实验**: 同一 seed 下加/删每个修饰词看效果
- **Seed hunting**: 批量生成 10-20 个 seed，精选后再深入
- **变体生成**: 锁定构图满意的 seed，调整 CFG scale / denoising

### CFG Scale 调参

| CFG Scale | 效果 | 适用场景 |
|:----------|:-----|:---------|
| 3-5 | 高创意、艺术化 | 概念设计、风格化 |
| 7-9 | 平衡（推荐默认） | 大部分场景 |
| 10-15 | 高 prompt 遵循度 | 精确控制、产品图 |
| >15 | 色彩过饱和、伪影 | 不推荐 |

## 5. 常见陷阱与解决方案

| 陷阱 | 现象 | 解决方案 |
|:-----|:------|:---------|
| **六指/畸形手** | 手部变形 | 负提示词 + hands restoration LoRA |
| **提示词稀释** | 输出忽略部分 prompt | 减少 prompt 长度，加权重 (token weighting) |
| **色彩偏色** | 整体色调偏某色 | 换 VAE 或调整 CFG |
| **重复构图** | 每张图过于相似 | 提高 CFG 或换 seed |
| **过度渲染** | 细节过多变杂乱 | 降低 CFG，简化 prompt |
