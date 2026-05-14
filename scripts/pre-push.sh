#!/usr/bin/env bash
# pre-push.sh — 推送前本地门禁检查
# 在 git push 前运行，发现问题本地拦截，避免 CI 失败
# 用法: ./scripts/pre-push.sh  (手动运行)
#       在 .git/hooks/pre-push 中: exec scripts/pre-push.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

FAILED=0
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║       🔒 推送前门禁检查                        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ─── Gate 1: README 对齐 ───
echo -n "📖 README 对齐 ... "
if python3 scripts/validate-readme.py > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    python3 scripts/validate-readme.py | grep -E "🔴|🟡|结果"
    FAILED=1
fi

# ─── Gate 2: 项目状态一致性 ───
echo -n "📋 项目状态一致性 ... "
if python3 scripts/project-state.py verify > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    python3 scripts/project-state.py verify 2>&1 | grep -E "🔴|❌|不一致"
    FAILED=1
fi

# ─── Gate 3: 交叉引用完整性 ───
echo -n "🔗 交叉引用完整性 ... "
if python3 scripts/ci-check-cross-refs.py > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    python3 scripts/ci-check-cross-refs.py 2>&1 | tail -10
    FAILED=1
fi

# ─── Gate 4: 所有 YAML 合法 ───
echo -n "📄 YAML 语法 ... "
YAML_ERRORS=0
for yaml_file in $(find packs -name "*.yaml" -type f); do
    if ! python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
        echo "坏 YAML: $yaml_file"
        YAML_ERRORS=$((YAML_ERRORS+1))
    fi
done
if [ "$YAML_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    FAILED=1
fi

echo ""
if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✅ 全部门禁通过，可以推送 🚀${NC}"
else
    echo -e "${RED}❌ 有门禁未通过，推送被拦截 🔒${NC}"
    echo "   先修复后再推送"
    exit 1
fi
