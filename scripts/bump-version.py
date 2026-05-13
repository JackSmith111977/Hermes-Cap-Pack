#!/usr/bin/env python3
"""
bump-version.py — Cap Pack 版本号自动管理

用法:
  python3 scripts/bump-version.py patch   # 0.3.0 → 0.3.1
  python3 scripts/bump-version.py minor   # 0.3.0 → 0.4.0
  python3 scripts/bump-version.py major   # 0.3.0 → 1.0.0
  python3 scripts/bump-version.py show    # 显示当前版本

工作流程:
  1. 更新 pyproject.toml 中的 version 字段
  2. 更新 CHANGELOG.md 的 [Unreleased] 头部
  3. 创建 git tag
"""

import re, sys, os
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"


def get_current_version():
    """从 pyproject.toml 读取当前版本"""
    text = PYPROJECT.read_text()
    m = re.search(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', text, re.MULTILINE)
    if not m:
        print("❌ 无法从 pyproject.toml 读取版本号")
        sys.exit(1)
    return m.group(1)


def bump_version(current, part):
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


def show_current():
    """显示当前版本信息"""
    ver = get_current_version()
    print(f"当前版本: {ver}")
    print(f"项目: hermes-cap-pack")
    print(f"路径: {PYPROJECT}")
    
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

    # Bump mode
    current = get_current_version()
    new_version = bump_version(current, cmd)
    print(f"📦 {current} → {new_version} ({cmd})")
    
    update_pyproject(new_version)
    update_changelog(current, new_version)
    git_tag(new_version)
    
    print(f"\n🎉 版本已从 {current} 升级到 {new_version}")


if __name__ == "__main__":
    main()
