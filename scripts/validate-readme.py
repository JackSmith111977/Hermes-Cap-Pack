#!/usr/bin/env python3
"""
README 对齐验证器 — 检查 README.md 是否符合 AI 友好模板规范

用法:
    python3 scripts/validate-readme.py              # 验证 README.md
    python3 scripts/validate-readme.py --template   # 同时输出模板符合率
    python3 scripts/validate-readme.py --fix        # 自动修复已知问题
    python3 scripts/validate-readme.py README.md    # 验证指定文件

退出码:
    0 = 通过 (所有检查项通过)
    1 = 警告 (有非阻塞问题)
    2 = 失败 (有阻塞问题)
"""

import re
import sys
from pathlib import Path

# ── 项目根 ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_README = PROJECT_ROOT / "README.md"
TEMPLATE_PATH = PROJECT_ROOT / "docs" / "templates" / "README-template.md"

# ── 检查规则定义 ────────────────────────────────────
# 每条规则: (名称, 类型, 模式/检查函数, 严重度)
# 类型: 'contains' = 内容必须包含, 'regex' = 正则匹配,
#       'count' = 计数检查, 'custom' = 自定义函数
# 严重度: 'blocking' = 必须通过, 'warning' = 建议通过

RULES = [
    # ── P0: 必须包含的区块 ──
    ("一、项目身份", "contains", "# 一、项目身份", "blocking"),
    ("二、快速安装", "contains", "# 二、快速安装", "blocking"),
    ("版本号声明", "regex", r"\*\*版本\*\*.*`[\d\.]+`", "blocking"),
    ("测试数声明", "regex", r"测试.*`\d+", "blocking"),
    ("仓库地址", "regex", r"github\.com/JackSmith111977", "blocking"),
    ("CLI 命令参考", "contains", "完整命令速查", "warning"),
    ("三列 CLI 表格", "regex", r"\|.*命令.*\|.*作用.*\|.*关键参数.*\|", "warning"),
    ("验证命令", "regex", r"```bash\n[\s\S]*?# 预期输出", "warning"),
    ("FAQ / 排错", "contains", "FAQ", "warning"),

    # ── P1: 核心内容完整性 ──
    ("能力包列表", "contains", "能力包列表", "warning"),
    ("安装步骤", "regex", r"(git clone|pip install)", "warning"),
    ("前置条件", "contains", "前置条件", "warning"),
    ("目录结构", "regex", r"```\n.*hermes-cap-pack/", "warning"),

    # ── P2: 格式规范 ──
    ("编号章节", "regex", r"# [一二三四五六七八九十]、", "warning"),
    ("项目身份表格", "regex", r"\|\s*\*\*目的\*\*\s*\|", "warning"),
    ("命令速查表", "contains", "## 十", "warning"),
    ("版本号一致性", "custom", "check_version_consistency", "blocking"),
    ("超长行", "custom", "check_no_overlong_lines", "warning"),
]


def check_contains(content: str, pattern: str) -> bool:
    return pattern in content


def check_regex(content: str, pattern: str) -> bool:
    return bool(re.search(pattern, content))


def check_version_consistency(content: str, readme_path: Path) -> list[str]:
    """检查 README 中的版本号与 pyproject.toml 一致"""
    issues = []
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return issues

    # 从 pyproject.toml 读取版本
    pyproject_text = pyproject.read_text()
    m = re.search(r'version\s*=\s*"([^"]+)"', pyproject_text)
    if not m:
        return issues
    pyproject_ver = m.group(1)

    # 从 README 读取版本
    readme_ver_match = re.search(r'\*\*版本\*\*.*`([\d\.]+)`', content)
    if readme_ver_match:
        readme_ver = readme_ver_match.group(1)
        if readme_ver != pyproject_ver:
            issues.append(f"版本不一致: README={readme_ver}, pyproject.toml={pyproject_ver}")

    return issues


def check_no_overlong_lines(content: str, readme_path: Path) -> list[str]:
    """检查超长行（>120 字符的非代码行）"""
    issues = []
    in_code_block = False
    for i, line in enumerate(content.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if len(line) > 120:
            issues.append(f"第 {i} 行: {len(line)} 字符 (最大 120)")
    return issues[:5]  # 最多报 5 个


# ── 主验证逻辑 ────────────────────────────────────


def validate_readme(readme_path: Path, check_template_ratio: bool = False) -> int:
    """验证 README，返回退出码"""
    if not readme_path.exists():
        print(f"❌ 文件不存在: {readme_path}", file=sys.stderr)
        return 2

    content = readme_path.read_text()
    total_checks = 0
    passed = 0
    failed_blocking = 0
    failed_warning = 0
    issues_detail = []

    # 自定义检查函数映射
    CUSTOM_FN_MAP = {
        "check_version_consistency": check_version_consistency,
        "check_no_overlong_lines": check_no_overlong_lines,
    }

    print(f"\n{'='*60}")
    print(f"  📋 README 对齐检查: {readme_path.name}")
    print(f"{'='*60}\n")

    for name, check_type, pattern_or_fn, severity in RULES:
        total_checks += 1

        if check_type == "contains":
            ok = check_contains(content, pattern_or_fn)
        elif check_type == "regex":
            ok = check_regex(content, pattern_or_fn)
        elif check_type == "custom":
            fn = CUSTOM_FN_MAP.get(pattern_or_fn)
            if fn:
                issues = fn(content, readme_path)
                ok = len(issues) == 0
                if not ok:
                    issues_detail.extend(issues)
            else:
                ok = True
        else:
            ok = True

        if ok:
            passed += 1
        else:
            if severity == "blocking":
                failed_blocking += 1
                print(f"  🔴 [{severity}] {name}")
            else:
                failed_warning += 1
                print(f"  🟡 [{severity}] {name}")

    # 打印自定义检查的详细信息
    for detail in issues_detail:
        print(f"  📝   {detail}")

    # 统计
    print(f"\n{'='*60}")
    print(f"  结果: {passed}/{total_checks} 通过")
    print(f"  🔴 阻塞: {failed_blocking}  |  🟡 警告: {failed_warning}")
    print(f"{'='*60}\n")

    # 模板符合率
    if check_template_ratio:
        ratio = passed / total_checks * 100 if total_checks > 0 else 0
        print(f"  📊 模板符合率: {ratio:.1f}%")
        if ratio >= 90:
            print(f"  🟢 优秀")
        elif ratio >= 70:
            print(f"  🟡 良好")
        else:
            print(f"  🟠 需改进")
        print()

    if failed_blocking > 0:
        return 2
    elif failed_warning > 0:
        return 1
    return 0


def auto_fix(readme_path: Path) -> int:
    """尝试自动修复已知问题"""
    content = readme_path.read_text()
    fixes = 0

    # 修复 1: 更新版本号
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if pyproject.exists():
        pyproject_text = pyproject.read_text()
        m = re.search(r'version\s*=\s*"([^"]+)"', pyproject_text)
        if m:
            correct_ver = m.group(1)
            # 更新 README 中的版本号
            content, count = re.subn(
                r'(\*\*版本\*\*.*`)[\d\.]+(`)',
                rf'\g<1>{correct_ver}\g<2>',
                content
            )
            if count > 0:
                fixes += 1
                print(f"  ✅ 更新版本号: {correct_ver}")

    if fixes > 0:
        readme_path.write_text(content)
        print(f"  ✅ 已应用 {fixes} 个自动修复")
    else:
        print("  ℹ️  无需自动修复")

    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="README 对齐验证器")
    parser.add_argument("readme", nargs="?", default=str(DEFAULT_README),
                        help="README 文件路径 (默认: README.md)")
    parser.add_argument("--template", action="store_true",
                        help="输出模板符合率")
    parser.add_argument("--fix", action="store_true",
                        help="自动修复已知问题")
    args = parser.parse_args()

    readme_path = Path(args.readme).resolve()

    if args.fix:
        return auto_fix(readme_path)

    rc = validate_readme(readme_path, check_template_ratio=args.template)
    return rc


if __name__ == "__main__":
    sys.exit(main())
