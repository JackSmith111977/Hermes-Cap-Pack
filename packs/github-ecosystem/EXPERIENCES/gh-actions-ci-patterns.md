---
type: best-practice
skill_ref: github-project-ops
keywords: [github-actions, ci, patterns]
created: 2026-05-14
---

# GitHub Actions CI Configuration Patterns

> GitHub Actions CI 配置最佳实践 — 矩阵构建、缓存、密钥管理与工作流优化

## 1. Matrix Builds 矩阵构建

### 多维度矩阵策略

```yaml
# 基础矩阵：多版本 + 多平台
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [18, 20, 22]
        # 排除不需要的组合
        exclude:
          - os: macos-latest
            node-version: 18
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

### 动态矩阵（从文件读取）

```yaml
# 高级：从 JSON 文件中动态生成矩阵
jobs:
  load-matrix:
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - id: set-matrix
        run: |
          echo 'matrix={"include":[
            {"project":"frontend","dir":"frontend","build":"npm"},
            {"project":"backend","dir":"backend","build":"gradle"},
            {"project":"docs","dir":"docs","build":"mkdocs"}
          ]}' >> $GITHUB_OUTPUT
  
  build:
    needs: load-matrix
    strategy:
      matrix: ${{ fromJSON(needs.load-matrix.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - run: cd ${{ matrix.dir }} && ${{ matrix.build }} build
```

### 矩阵优化技巧

```markdown
# 矩阵最佳实践
1. **fail-fast: false** — 一个平台失败不中断其他平台
2. **max-parallel: 5** — 控制并发数避免 API 限流
3. **include/exclude 精确控制** — 避免无效组合
4. **job 输出传递** — 矩阵 job 通过 outputs 传递结果给下游
5. **条件矩阵** — 根据分支/标签动态选择矩阵范围
```

## 2. Caching 缓存策略

### 依赖缓存配置

```yaml
# npm 缓存
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-

# pip 缓存
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}

# Gradle 缓存
- uses: actions/cache@v4
  with:
    path: |
      ~/.gradle/caches
      ~/.gradle/wrapper
    key: ${{ runner.os }}-gradle-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
```

### 缓存失效策略

```yaml
# 分层缓存：精确匹配 + fallback
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: node_modules
    key: deps-node-${{ runner.os }}-${{ hashFiles('yarn.lock') }}
    restore-keys: |
      deps-node-${{ runner.os }}-    # 无 lockfile 变化时复用
      deps-node-                     # 最终 fallback

# 构建缓存（monorepo 场景）
- name: Cache build outputs
  uses: actions/cache@v4
  with:
    path: packages/*/dist
    key: build-${{ github.sha }}     # 精确到 commit
    restore-keys: |
      build-${{ github.ref_name }}-  # 按分支回退
```

### 缓存大小与配额管理

```markdown
# GitHub Actions 缓存限制
- 单个仓库缓存上限: 10 GB
- 单个缓存条目: 最大 512 MB（压缩后）
- 超过 7 天未访问的缓存自动过期
- 分支被删除后关联缓存也删除

# 优化建议
- 拆分大缓存: 依赖缓存 + 构建缓存分离
- 定期清理: 手动删除陈旧缓存条目
- 压缩监控: 在 workflow 中输出缓存大小日志
```

## 3. Secret Management 密钥管理

### GitHub Secrets 最佳实践

```yaml
# ✅ 正确：使用 Repository Secrets / Environment Secrets
jobs:
  deploy:
    environment: production
    steps:
      - name: Deploy to production
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_SSH_KEY }}
          API_TOKEN: ${{ secrets.PROD_API_TOKEN }}
        run: |
          echo "$DEPLOY_KEY" > deploy_key
          chmod 600 deploy_key
          ./deploy.sh

# ❌ 错误：硬编码或打印密钥
- run: echo "API_KEY=abc123" >> .env       # 泄露风险
- run: echo ${{ secrets.API_KEY }}         # 日志暴露
```

### 环境级别密钥隔离

```yaml
# 环境隔离配置
name: Deploy
on:
  push:
    branches: [main, staging, develop]

jobs:
  deploy:
    environment: ${{ github.ref_name == 'main' && 'production' || 'staging' }}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: ./deploy.sh
        env:
          # 自动匹配当前环境的 secrets
          API_URL: ${{ vars.API_URL }}
```

### OIDC 替代长期密钥

```yaml
# 使用 OIDC 避免存储云厂商密钥
jobs:
  aws-deploy:
    permissions:
      id-token: write    # 必须：请求 OIDC token
      contents: read
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/GitHubActions
          aws-region: us-east-1
      - run: aws s3 sync ./dist s3://my-bucket
```

## 4. Workflow Optimization 工作流优化

### 条件执行与跳过

```yaml
# 基于路径的条件触发
on:
  push:
    paths:
      - 'src/**'
      - 'tests/**'
      - '!docs/**'              # 文档变更不触发 CI
      - '!**/*.md'              # Markdown 变更不触发

# Job 级别的条件跳过
jobs:
  lint:
    if: github.event_name == 'pull_request' || github.ref == 'refs/heads/main'
  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

### 并行与依赖编排

```yaml
# 并行 lint + test，然后合并部署
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: [run: npm run lint]

  test:
    runs-on: ubuntu-latest
    steps: [run: npm test]

  build:
    if: ${{ always() }}          # 即使 lint/test 失败也尝试 build
    needs: [lint, test]
    steps: [run: npm run build]

  deploy:
    needs: [build]
    if: ${{ github.ref == 'refs/heads/main' && needs.build.result == 'success' }}
    steps: [run: ./deploy.sh]
```

### 性能优化清单

```markdown
# GitHub Actions 性能优化清单
- [ ] 合并多个 run 步骤（减少 container 启动开销）
- [ ] 使用 actions/checkout 的 fetch-depth: 1（浅克隆）
- [ ] 启用 actions/setup-node 的 cache: npm
- [ ] 使用 larger runner（如 ubuntu-22.04-4core）减少排队
- [ ] GitHub-hosted runner 优于自托管（维护成本）
- [ ] 使用 concurrency 取消陈旧的工作流
- [ ] 定期归档老的 workflow artifacts
```

### Concurrency 控制

```yaml
# 取消重复工作流
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# 环境级部署串行
concurrency:
  group: production-deploy
  cancel-in-progress: false      # 不允许中断部署中环境
```

## 5. 常见模式模板

### 语义化版本发布

```yaml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  release:
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: npm run build
      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          files: |
            dist/*.zip
            dist/*.tar.gz
```

### Dependabot 自动合并

```yaml
name: Dependabot auto-merge
on: pull_request_target

jobs:
  auto-merge:
    if: github.actor == 'dependabot[bot]'
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: write
    steps:
      - uses: dependabot/fetch-metadata@v2
      - name: Enable auto-merge
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
```
