---
type: pitfall
skill_ref: docker-management
keywords: [docker, ops, pitfalls]
created: 2026-05-14
---

# Common Docker Operations Pitfalls

> Docker 运维实战避坑指南 — 卷挂载、网络、资源限制与日志管理核心经验

## 1. Volume Mounts 卷挂载陷阱

### Pitfall 1: 绝对路径与权限问题

```yaml
# ❌ 错误：权限不足导致容器无写入权限
volumes:
  - /home/user/data:/app/data   # 主机目录权限 755，容器用户非 root 时无法写入

# ✅ 正确：显式设置权限或使用 Docker-managed volumes
volumes:
  - app_data:/app/data           # Docker 自动管理
  - /home/user/data:/app/data:ro # 只读挂载更安全

# ✅ 或者在运行时指定 UID 匹配
services:
  app:
    user: "${UID:-1000}:${GID:-1000}"
```

### Pitfall 2: 绑定挂载覆盖容器目录

```bash
# 陷阱：将空目录绑定到已有内容的容器目录
docker run -v /empty/host/dir:/app/config myimage
# → 容器 /app/config 原有文件被隐藏（被空目录覆盖）

# 预防方案
# 1. 优先使用 COPY 而非 volume 初始化配置
# 2. 挂载前确保主机目录有初始化脚本
# 3. 使用 docker-entrypoint 检测空 volume 并初始化
```

### Pitfall 3: Volume 泄漏与孤儿数据

```bash
# 容器删除后 volume 仍然存在
docker rm mycontainer           # ← 不删除 volumes
docker volume ls                # ← 遗留 dangling volumes

# 清理策略
docker rm -v mycontainer        # 删除容器时一并删除匿名 volumes
docker volume prune             # 清理所有未使用的 volumes
docker system prune --volumes   # 完整系统清理
```

## 2. Networking 网络配置

### Bridge 网络默认限制

```markdown
# Docker 默认 bridge 网络限制
- ❌ 容器间无法通过 container_name 互相访问
- ❌ 无内置 DNS 解析
- ❌ 需通过 `--link`（已废弃）或 IP 地址访问

# ✅ 推荐：使用自定义 bridge 网络
docker network create mynet
docker run --net mynet --name app1 myimage
docker run --net mynet --name app2 myimage
# app1 可通过主机名 "app1" 访问 app2
```

### 端口映射陷阱

```yaml
# ❌ 错误：动态端口映射导致服务发现失败
ports:
  - "8080"                  # 随机分配主机端口

# ✅ 正确：固定端口映射
ports:
  - "8080:8080"

# ✅ 生产环境：使用反向代理而非端口暴露
services:
  nginx:
    ports:
      - "443:443"
  app:
    expose:
      - "3000"              # 仅内部网络可访问
```

### DNS 与 host 解析

```bash
# DNS 配置最佳实践
docker run --dns 1.1.1.1 --dns 8.8.8.8 myimage

# 自定义 hosts
docker run --add-host host.docker.internal:host-gateway myimage

# Docker Compose DNS 解析
# 默认 service 名称即可相互解析
# 注意：network_mode: host 时失去 Docker DNS
```

## 3. Resource Limits 资源限制

### 内存限制配置

```yaml
services:
  app:
    # 硬限制与软限制
    mem_limit: 512m          # 硬限制: 超出即 OOM kill
    mem_reservation: 256m    # 软限制: 尽力保障
    oom_kill_disable: false  # 允许 OOM killer（推荐）
    
    # Swap 限制
    mem_swappiness: 0        # 禁止使用 swap（性能敏感型服务）
```

### CPU 限制策略

```yaml
services:
  worker:
    # 精确分配 CPU 核心
    cpus: "1.5"               # 最多使用 1.5 核
    cpuset: "0-3"            # 绑定到 CPU 0-3
    
    # CPU 共享权重（非限制）
    cpu_shares: 1024          # 默认权重，资源竞争时按比例分配
```

### OOM 排查流程

```bash
# Step 1: 检查容器退出状态
docker inspect <container> --format '{{.State.ExitCode}}'

# Step 2: 查看 OOM 日志
docker logs <container> | grep -i "killed\|OOM\|out of memory"
dmesg | grep -i "killed\|OOM" | tail -5

# Step 3: 检查主机内存
free -h
docker stats --no-stream

# Step 4: 调整限制
docker update --memory 1g --memory-swap 1g <container>
```

## 4. Cleanup Strategies 清理策略

### 分层清理命令

```bash
# 安全清理（不影响运行中容器）
docker container prune           # 删除已停止容器
docker image prune               # 删除 dangling 镜像
docker volume prune              # 删除未使用 volume
docker network prune             # 删除未使用网络

# 激进清理
docker system prune -a --volumes # 删除所有未使用的资源
docker rmi $(docker images -q)   # 删除所有本地镜像（慎用！）
```

### 日志文件清理

```bash
# Log 文件膨胀是 Docker 运维的首要问题
# 方案 1: 容器运行时限制日志大小
docker run --log-opt max-size=10m --log-opt max-file=3 myimage

# 方案 2: Docker Compose 全局配置
version: "3.8"
services:
  app:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

# 方案 3: daemon.json 全局设置
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## 5. Log Management 日志管理

### 日志驱动选择

| 驱动 | 适合场景 | 注意事项 |
|:-----|:---------|:---------|
| `json-file` | 默认，单机调试 | 磁盘占用大，需配合 log rotation |
| `local` | 性能敏感 | 不保证持久性，重启丢失 |
| `syslog` | 集中日志 | 需运行 syslog 服务 |
| `journald` | systemd 集成系统 | 与系统日志一起管理 |
| `gelf` | Graylog 集中管理 | 结构化日志支持好 |
| `fluentd` | 日志管道 | 适合大规模集群 |

### 日志轮转配置

```bash
# daemon.json 全局日志配置
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3",
    "compress": "true"
  },
  "storage-driver": "overlay2"
}

# 手动清理（紧急情况）
truncate -s 0 $(docker inspect --format='{{.LogPath}}' <container>)
```

### 日志排查命令速查

```bash
# 常用日志排查
docker logs --tail 100 -f <container>            # 实时跟踪最后 100 行
docker logs --since 2024-01-01T00:00:00 <container>
docker logs --until 2024-01-02T00:00:00 <container>
docker logs --details <container>                 # 显示额外标签

# 结合 grep
docker logs <container> 2>&1 | grep "ERROR"      # 过滤错误
docker logs <container> 2>&1 | head -100          # 只看开头

# 批量日志（多容器）
docker-compose logs --tail=50 -f
```

## 6. 综合 Checklist

### 生产环境 Docker 部署自查

- [ ] Volume 使用命名卷而非绑定挂载（除非必要）
- [ ] 非 root 用户运行容器（Dockerfile 中 USER 指令）
- [ ] 日志限制已配置（max-size + max-file）
- [ ] 内存/CPU 资源限制已设置
- [ ] 健康检查已配置（HEALTHCHECK）
- [ ] 容器重启策略合适（unless-stopped / always）
- [ ] 敏感信息使用 secrets 而非环境变量
- [ ] 镜像使用具体版本标签（避免 latest）
- [ ] 网络使用自定义 bridge（非默认 bridge）
- [ ] 定时清理策略已建立（cron + docker system prune）
