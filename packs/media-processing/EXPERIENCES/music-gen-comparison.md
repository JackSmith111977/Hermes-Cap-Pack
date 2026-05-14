---
type: decision-tree
skill_ref: heartmula
keywords: [music-generation, heartmula, suno, audiocraft, tts, song]
---

# 音乐生成选型决策

## 场景 vs 工具

| 场景 | 推荐工具 | 理由 |
|:-----|:---------|:------|
| 一句话生成歌曲 | Suno (在线) | 开箱即用，质量最高 |
| 本地生成（有 GPU） | HeartMuLa | 开源，可控歌词+标签 |
| 纯音乐（无歌词） | Audiocraft (MusicGen) | 更轻量，无需歌词 |
| 音色/音效 | 开源社区模型 | HeartMuLa 偏歌曲 |

## HeartMuLa 注意事项

### 硬件需求
| 配置 | 模式 | 显存峰值 |
|:-----|:-----|:--------:|
| 8GB VRAM | `--lazy_load true` | ~6.2GB |
| 16GB+ VRAM | 默认 | ~8GB |
| 无 GPU | CPU 模式 | 极慢（30-60min/首） |

### 已知问题
1. **HeartCodec 必须用 fp32** — bf16 严重劣化音质
2. **标签可能被忽略** — Issue #90，歌词优先于标签
3. **RTX 5080 不兼容** — 上游报告
4. **macOS 无 Triton** — 仅 Linux/CUDA

### 依赖修复（必做）
安装后必须执行：
```
uv pip install --upgrade datasets transformers
```
并打两个 source patch（见 SKILL.md）
