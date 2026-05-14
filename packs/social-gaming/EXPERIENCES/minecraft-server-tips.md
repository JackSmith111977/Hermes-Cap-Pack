---
type: pitfall
skill_ref: minecraft-modpack-server
keywords: [minecraft, server, modded, java, performance]
---

# Minecraft 服务器搭建陷阱

## Java 版本
| Minecraft 版本 | Java 版本 |
|:---------------|:----------|
| 1.21+ | Java 21 |
| 1.18-1.20 | Java 17 |
| 1.16 及以下 | Java 8 |

## 关键配置
```properties
# 模组服必开！
allow-flight=true       # 否则飞行模组玩家会被踢
max-tick-time=180000    # 模组加载慢，默认 60000 不够
spawn-protection=0      # 让所有人能在出生点建造
enforce-secure-profile=false  # offline-mode=true 时必须设置
```

## 性能调优
- 模组数量 → RAM 分配：100-200 模组 6-12GB，200+ 模组 12-24GB
- 视距：8-16 取决于玩家数量和硬件
- 首次启动非常慢（大包可能几分钟）— 正常现象

## 备份
每小时自动备份 world 目录，保留最近 24 个备份
