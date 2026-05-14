#!/usr/bin/env python3
"""
bump-version.py — Cap Pack 版本号自动管理 + 全文档版本对齐（SDD 语义版）

版本映射规则:
  patch  ← Story / Debug 更新（迭代完成一个小故事或修复）
  minor  ← Spec 更新（完成一个完整规范）
  major  ← Epic 完成（整条 Epic 线交付，可能含多个 Spec）

用法:
  python3 scripts/bump-version.py patch   # 0.3.0 → 0.3.1  (story/debug)
  python3 scripts/bump-version.py minor   # 0.3.0 → 0.4.0  (spec)
  python3 scripts/bump-version.py major   # 0.3.0 → 1.0.0  (epic)
  python3 scripts/bump-version.py show    # 显示当前版本
  python3 scripts/bump-version.py sync    # 仅同步所有文档版本（不 bump）

工作流程:
  1. 更新 pyproject.toml 中的 version 字段
  2. 更新 CHANGELOG.md 的 [Unreleased] 头部
  3. 同步所有文档中的版本号（README.md, project-state.yaml 等）
  4. 创建 git tag
"""

import re, sys, os
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"

# ── 需要同步版本号的文档列表 ──
VERSION_SYNC_TARGETS = [
    {
        "path": "README.md",
        "patterns": [
            (r'(\*\*版本\*\*：)`[\d\.]+`', r'\g<1>`{version}`'),
            (r'(v)[\d\.]+', r'\g<1>{version}'),  # 目录树中的 v0.x.x
        ],
    },
    {
        "path": "docs/project-state.yaml",
        "patterns": [
            (r'^(  version: )[\d\.]+', r'\g<1>{version}'),
        ],
    },
]


def get_current_version() -> str:
    """从 pyproject.toml 读取当前版本"""
    text = PYPROJECT.read_text()
    m = re.search(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', text, re.MULTILINE)
    if not m:
        print("❌ 无法从 pyproject.toml 读取版本号")
        sys.exit(1)
    return m.group(1)


def bump_version(current: str, part: str) -> str:
    """版本号递增"""
    major, minor, patch = map(int, current.split("."))
    if part == "major":
        return f"{major+1}.0.0"
    elif part == "minor":
        return f"{major}.{minor+1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch+1}"
    else:
        print(f"❌ 未知的 bump 类型: {part}（可选: major, minor, patch）")
        sys.exit(1)


def update_pyproject(new_version):
    """更新 pyproject.toml 中的版本号"""
    text = PYPROJECT.read_text()
    text = re.sub(
        r'^version\s*=\s*"\d+\.\d+\.\d+"',
        f'version = "{new_version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^(# Current: )\d+\.\d+\.\d+',
        f'\\g<1>{new_version}',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^(last_bump = )"\d{4}-\d{2}-\d{2}"',
        f'\\g<1>"{date.today().isoformat()}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    PYPROJECT.write_text(text)
    print(f"✅ pyproject.toml: version → {new_version}")


def update_changelog(current, new_version):
    """CHANGELOG：将 Unreleased 替换为版本号"""
    text = CHANGELOG.read_text()
    
    # 检查是否有 [Unreleased] 标题
    unreleased_pattern = r'## \[Unreleased\]'
    if re.search(unreleased_pattern, text):
        text = re.sub(
            unreleased_pattern,
            f'## [{new_version}] — {date.today().isoformat()}',
            text,
            count=1,
        )
        CHANGELOG.write_text(text)
        print(f"✅ CHANGELOG.md: [Unreleased] → [{new_version}]")
    else:
        print(f"ℹ️  CHANGELOG.md: 没有 [Unreleased] 段，跳过更新")


def git_tag(new_version):
    """创建 git tag"""
    import subprocess
    tag = f"v{new_version}"
    result = subprocess.run(
        ["git", "tag", "-a", tag, "-m", f"Release {tag}"],
        capture_output=True, text=True, cwd=ROOT,
    )
    if result.returncode == 0:
        print(f"✅ git tag: {tag} 已创建")
        print(f"   推送: git push origin {tag}")
    else:
        print(f"⚠️  git tag 创建失败: {result.stderr.strip()}")


def sync_all_versions(version: str | None = None, show_sync: bool = True) -> int:
    """同步所有文档中的版本号

    扫描 VERSION_SYNC_TARGETS 中定义的文档和模式，
    将版本号统一替换为指定版本（或 pyproject.toml 中的版本）。

    Returns:
        更新的文件数
    """
    if version is None:
        version = get_current_version()

    updated_count = 0

    for target in VERSION_SYNC_TARGETS:
        target_path = ROOT / target["path"]
        if not target_path.exists():
            if show_sync:
                print(f"  ⚠️  文件不存在，跳过: {target['path']}")
            continue

        text = target_path.read_text()
        original = text
        for pattern, replacement in target["patterns"]:
            formatted = replacement.replace("{version}", version)
            text = re.sub(pattern, formatted, text)

        if text != original:
            target_path.write_text(text)
            updated_count += 1
            if show_sync:
                print(f"  ✅ {target['path']}: 版本同步到 {version}")
        elif show_sync:
            print(f"  ℹ️  {target['path']}: 版本已是最新")

    if show_sync:
        print(f"\n  📊 共同步 {updated_count} 个文件")
    return updated_count


def show_current():
    """显示当前版本信息"""
    ver = get_current_version()
    print(f"当前版本: {ver}")
    print(f"项目: hermes-cap-pack")
    print(f"路径: {PYPROJECT}")
    print(f"")
    print(f"版本映射规则（SDD 语义版）:")
    print(f"  python3 scripts/bump-version.py patch  ← Story / Debug")
    print(f"  python3 scripts/bump-version.py minor  ← Spec")
    print(f"  python3 scripts/bump-version.py major  ← Epic")
    print(f"  python3 scripts/bump-version.py sync   ← 仅对齐文档版本")
    print(f"")
    
    # 同步状态
    print(f"版本一致性检查:")
    sync_all_versions(show_sync=False)  # 静默同步检查
    
    # 检查 git tag
    import subprocess
    result = subprocess.run(
        ["git", "tag", "-l", f"v{ver}"],
        capture_output=True, text=True, cwd=ROOT,
    )
    if result.stdout.strip():
        print(f"git tag: ✅ v{ver} 已存在")
    else:
        print(f"git tag: ❌ 尚未创建")
    
    # 检查 CHANGELOG
    text = CHANGELOG.read_text()
    if f"[{ver}]" in text:
        print(f"CHANGELOG: ✅ [{ver}] 已记录")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "show":
        show_current()
        return

    if cmd == "sync":
        print(f"📋 同步所有文档版本...")
        count = sync_all_versions()
        print(f"\n🎉 版本同步完成，{count} 个文件已更新")
        return

    # Bump mode
    current = get_current_version()
    new_version = bump_version(current, cmd)
    print(f"📦 {current} → {new_version} ({cmd})")
    
    update_pyproject(new_version)
    update_changelog(current, new_version)
    sync_all_versions(new_version, show_sync=True)
    git_tag(new_version)
    
    print(f"\n🎉 版本已从 {current} 升级到 {new_version}")


if __name__ == "__main__":
    main()
