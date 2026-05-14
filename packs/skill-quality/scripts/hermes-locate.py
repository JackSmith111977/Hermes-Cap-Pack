#!/usr/bin/env python3
"""
hermes-locate.py — Hermes 安装环境自动检测引擎 (v2.0)
skill-quality cap-pack 核心基础设施

用法:
  python3 hermes-locate.py                        # JSON 输出
  python3 hermes-locate.py --format human         # 可读格式
  python3 hermes-locate.py --format feishu        # 飞书卡片格式
  python3 hermes-locate.py --check-only           # 可用性检查 (exit 0/1)
  python3 hermes-locate.py --watch                # 持续监控模式
  python3 hermes-locate.py --save-state           # 保存状态快照
  python3 hermes-locate.py --diff                 # 与上次状态对比
"""

import json, os, sys, re, subprocess, time, hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

STATE_DIR = Path.home() / ".hermes" / "cap-packs" / "skill-quality" / "state"
STATE_FILE = STATE_DIR / "last_locate_state.json"
HISTORY_FILE = STATE_DIR / "locate_history.jsonl"


def detect_hermes_home() -> Path:
    """Detect Hermes home directory (respects HERMES_HOME env var)."""
    env_val = os.environ.get("HERMES_HOME", "").strip()
    if env_val:
        return Path(env_val)
    return Path.home() / ".hermes"


def detect_hermes_source(hermes_home: Path) -> Dict[str, Any]:
    """Detect Hermes source location using multiple strategies."""
    result = {"location": "unknown", "path": None,
              "tools_path": None, "hermes_cli_path": None, "agent_path": None}

    # Strategy 1: Git clone
    git_path = hermes_home / "hermes-agent"
    if git_path.exists() and (git_path / "tools").exists():
        result["location"] = "git_clone"
        result["path"] = str(git_path.resolve())
        result["tools_path"] = str((git_path / "tools").resolve())
        result["hermes_cli_path"] = str((git_path / "hermes_cli").resolve())
        result["agent_path"] = str((git_path / "agent").resolve())
        return result

    # Strategy 2: pip package
    try:
        import hermes_cli as hc
        pkg_path = Path(hc.__file__).parent.parent
        if (pkg_path / "tools").exists():
            result["location"] = "pip_package"
            result["path"] = str(pkg_path.resolve())
            result["tools_path"] = str((pkg_path / "tools").resolve())
            result["hermes_cli_path"] = str((pkg_path / "hermes_cli").resolve())
            result["agent_path"] = str((pkg_path / "agent").resolve())
            return result
    except (ImportError, AttributeError):
        pass

    # Strategy 3: which hermes -> trace to package
    try:
        which = subprocess.run(["which", "hermes"], capture_output=True, text=True, timeout=5)
        if which.returncode == 0:
            bin_path = Path(which.stdout.strip()).resolve()
            result["binary_path"] = str(bin_path)
            # Check common site-packages locations relative to bin
            for candidate in [bin_path.parent.parent / "lib" / "python*" / "site-packages",
                              Path("/usr/lib/python3*/dist-packages")]:
                import glob
                matches = glob.glob(str(candidate))
                for mp in matches:
                    pp = Path(mp) / "hermes_agent" / "tools"
                    if pp.exists():
                        result["location"] = "system"
                        result["path"] = str(pp.parent.parent)
                        result["tools_path"] = str(pp)
                        return result
    except Exception:
        pass

    return result


def detect_version(hermes_home: Path, source: Dict[str, Any]) -> str:
    """Detect Hermes version from multiple sources."""
    # CLI version
    try:
        r = subprocess.run(["hermes", "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            m = re.search(r'(\d+\.\d+\.\d+)', r.stdout.strip())
            if m:
                return m.group(1)
    except Exception:
        pass
    # Source __init__.py
    if source.get("hermes_cli_path"):
        init_f = Path(source["hermes_cli_path"]) / "__init__.py"
        if init_f.exists():
            m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_f.read_text())
            if m:
                return m.group(1)
    return "unknown"


def detect_skills_dirs(hermes_home: Path) -> Dict[str, Any]:
    """Detect all skills directories including profile-specific ones."""
    primary = hermes_home / "skills"
    external, profile_skills_dirs = [], []
    available_profiles = []

    # External dirs from config
    config_path = hermes_home / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            cfg = yaml.safe_load(config_path.read_text()) or {}
            for d in (cfg.get("skills", {}).get("external_dirs", []) or []):
                p = Path(d)
                if p.exists():
                    external.append(str(p.resolve()))
        except Exception:
            pass

    # Profiles
    profiles_dir = hermes_home / "profiles"
    if profiles_dir.exists():
        available_profiles = sorted(
            d.name for d in profiles_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )
        for p in available_profiles:
            ps = profiles_dir / p / "skills"
            if ps.exists():
                profile_skills_dirs.append(str(ps.resolve()))

    active = "default"
    af = hermes_home / "active_profile"
    if af.exists():
        active = af.read_text().strip() or "default"

    return {
        "primary": str(primary.resolve()) if primary.exists() else str(primary),
        "external": external,
        "profile_specific": profile_skills_dirs,
        "profiles": {"active": active, "available": available_profiles},
        "total_dirs": 1 + len(external) + len(profile_skills_dirs),
    }


def detect_tool_targets(source: Dict[str, Any]) -> Dict[str, Any]:
    """Scan Hermes source for patch-able code points."""
    result = {}
    tp = Path(source["tools_path"]) if source.get("tools_path") else None
    ap = Path(source["agent_path"]) if source.get("agent_path") else None
    cp = Path(source["hermes_cli_path"]) if source.get("hermes_cli_path") else None

    if tp:
        ft = tp / "file_tools.py"
        if ft.exists():
            c = ft.read_text()
            wf = re.search(r'def write_file_tool\(', c)
            sc = re.search(r'_check_sensitive_path\(', c)
            pt = re.search(r'def patch_tool\(', c)
            result["file_tools"] = {
                "file": str(ft), "write_file_line": c[:wf.start()].count('\n') + 1 if wf else None,
                "has_sensitive_check": sc is not None, "has_skill_check": '_check_skill_path' in c}

        dt = tp / "delegate_tool.py"
        if dt.exists():
            c = dt.read_text()
            bm = re.search(r'DELEGATE_BLOCKED_TOOLS\s*=\s*frozenset\(', c)
            if bm:
                items = re.findall(r'"(.+?)"', c[bm.end():bm.end() + 500])
                result["delegate_blocked_tools"] = {
                    "file": str(dt), "current": items, "has_skill_manage": "skill_manage" in items}

    if ap:
        cp_file = ap / "curator.py"
        if cp_file.exists():
            c = cp_file.read_text()
            pm = re.search(r'CURATOR_REVIEW_PROMPT\s*=\s*\(', c)
            if pm:
                result["curator"] = {"file": str(cp_file),
                    "has_quality_gate": 'quality' in c[pm.start():pm.start() + 8000].lower()}

    if cp:
        sh = cp / "skills_hub.py"
        if sh.exists():
            c = sh.read_text()
            result["skills_hub_cli"] = {"file": str(sh),
                "has_do_install": bool(re.search(r'def do_install\(', c)),
                "has_post_quality": 'quality-score' in c or 'skill-quality' in c}
    return result


def detect_patch_status(targets: Dict[str, Any]) -> Dict[str, bool]:
    return {
        "file_tools_guard":  {"applied": targets.get("file_tools", {}).get("has_skill_check", False)},
        "delegate_block":    {"applied": targets.get("delegate_blocked_tools", {}).get("has_skill_manage", False)},
        "curator_quality":   {"applied": targets.get("curator", {}).get("has_quality_gate", False)},
        "cli_quality":       {"applied": targets.get("skills_hub_cli", {}).get("has_post_quality", False)},
    }


def count_skills(hermes_home: Path, skills_dirs: Dict[str, Any]) -> Dict[str, Any]:
    """Count skills across all directories."""
    dirs = [skills_dirs["primary"]] + skills_dirs.get("external", []) + skills_dirs.get("profile_specific", [])
    total, agent_created = 0, 0
    for d in dirs:
        dp = Path(d)
        if not dp.exists():
            continue
        for root, dirs2, files in os.walk(dp):
            if "SKILL.md" in files and ".archive" not in root:
                total += 1
                # Check usage.json for agent-created
                sk_name = os.path.basename(root)
                try:
                    usage_path = hermes_home / "skills" / ".usage.json"
                    if usage_path.exists():
                        usage = json.loads(usage_path.read_text())
                        if usage.get(sk_name, {}).get("source") == "agent":
                            agent_created += 1
                except Exception:
                    pass
    return {"total": total, "agent_created": agent_created}


def check_system_info() -> Dict[str, str]:
    info = {"platform": sys.platform, "python": sys.executable}
    try:
        w = subprocess.run(["which", "hermes"], capture_output=True, text=True, timeout=5)
        if w.returncode == 0:
            info["hermes_cli_binary"] = w.stdout.strip()
    except Exception:
        pass
    try:
        import pwd
        info["user"] = pwd.getpwuid(os.getuid()).pw_name
    except Exception:
        info["user"] = os.environ.get("USER", "?")
    return info


def locate_all(hermes_home_override: Optional[Path] = None) -> Dict[str, Any]:
    """Main entry point: detect everything."""
    hermes_home = hermes_home_override or detect_hermes_home()
    source = detect_hermes_source(hermes_home)
    version = detect_version(hermes_home, source)
    skills_dirs = detect_skills_dirs(hermes_home)
    targets = detect_tool_targets(source)
    patch_status = detect_patch_status(targets)
    skill_count = count_skills(hermes_home, skills_dirs)
    system_info = check_system_info()
    return {
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "hermes_home": str(hermes_home.resolve()),
        "hermes_version": version,
        "hermes_source": source,
        "skills_dirs": skills_dirs,
        "skills": skill_count,
        "tools": targets,
        "patch_status": patch_status,
        "system": system_info,
    }


def verify_can_patch(loc: Dict[str, Any]) -> List[str]:
    issues = []
    src = loc.get("hermes_source", {})
    if src.get("location") == "unknown":
        issues.append("Cannot determine Hermes source location")
    if not src.get("tools_path"):
        issues.append("Cannot find tools directory")
    return issues


def compute_fingerprint(loc: Dict[str, Any]) -> str:
    """Unique fingerprint of the detected environment."""
    raw = f"{loc['hermes_home']}|{loc['hermes_version']}|{loc['hermes_source'].get('location','?')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def format_human(loc: Dict[str, Any]) -> str:
    lines = ["=" * 55, f"  🔍 Hermes Environment — {loc.get('hermes_version', '?')}", "=" * 55]
    lines.append(f"  Home:    {loc.get('hermes_home', '?')}")
    lines.append(f"  Source:  {loc.get('hermes_source', {}).get('location', '?')}")
    lines.append(f"  Skills:  {loc.get('skills', {}).get('total', 0)} total, "
                 f"{loc.get('skills', {}).get('agent_created', 0)} agent-created")
    lines.append(f"  Dirs:    {loc.get('skills_dirs', {}).get('total_dirs', 0)} skill directories")
    lines.append("")
    lines.append("  📋 Patch Status:")
    for n, s in loc.get("patch_status", {}).items():
        lines.append(f"    {'✅' if s.get('applied') else '⬜'} {n}")
    issues = verify_can_patch(loc)
    if issues:
        lines.append(f"\n  ⚠️  Issues:")
        for i in issues:
            lines.append(f"    • {i}")
    fp = compute_fingerprint(loc)
    lines.append(f"\n  Fingerprint: {fp}")
    return "\n".join(lines)


def format_feishu(loc: Dict[str, Any]) -> str:
    """Format as a Feishu interactive card JSON."""
    ps = loc.get("patch_status", {})
    sk = loc.get("skills", {})
    fp = compute_fingerprint(loc)
    cards = []
    for name, st in ps.items():
        label = {"file_tools_guard": "文件工具防护", "delegate_block": "子代理阻断",
                 "curator_quality": "策展人质量", "cli_quality": "CLI 质量"}.get(name, name)
        cards.append(f"**{label}**: {'✅ 已应用' if st.get('applied') else '⬜ 未应用'}")
    return json.dumps({
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": f"🛡️ Hermes 环境检测报告 v{loc['hermes_version']}"},
                   "template": "green" if not verify_can_patch(loc) else "yellow"},
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content":
                f"**检测时间**: {loc['detected_at'][:19]}\n"
                f"**安装路径**: `{loc['hermes_home']}`\n"
                f"**安装类型**: `{loc['hermes_source'].get('location', '?')}`\n"
                f"**Skill 总数**: {sk.get('total', '?')}（agent创建: {sk.get('agent_created', '?')}）"
            }},
            {"tag": "hr"},
            {"tag": "div", "text": {"tag": "lark_md", "content": "**🔧 质量门禁状态**\n" + "\n".join(cards)}},
            {"tag": "hr"},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"指纹: `{fp}`"}},
        ]
    }, ensure_ascii=False)


def save_state(loc: Dict[str, Any]) -> None:
    """Save current state for diff/comparison."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(loc, indent=2, ensure_ascii=False))
    # Append to history
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps({"timestamp": loc["detected_at"],
                            "version": loc["hermes_version"],
                            "fingerprint": compute_fingerprint(loc),
                            "skills_total": loc.get("skills", {}).get("total"),
                            "source_type": loc["hermes_source"].get("location")}) + "\n")


def diff_state(loc: Dict[str, Any]) -> List[str]:
    """Compare with last saved state."""
    if not STATE_FILE.exists():
        return ["No previous state to compare against"]
    try:
        old = json.loads(STATE_FILE.read_text())
    except Exception:
        return ["Previous state corrupted"]
    changes = []
    if old.get("hermes_version") != loc["hermes_version"]:
        changes.append(f"版本: {old.get('hermes_version')} → {loc['hermes_version']}")
    if old.get("hermes_source", {}).get("location") != loc["hermes_source"].get("location"):
        changes.append(f"安装类型: {old.get('hermes_source', {}).get('location')} → {loc['hermes_source'].get('location')}")
    old_ps = old.get("patch_status", {})
    new_ps = loc.get("patch_status", {})
    for k in old_ps:
        oa = old_ps[k].get("applied", False)
        na = new_ps.get(k, {}).get("applied", False)
        if oa != na:
            changes.append(f"补丁 {k}: {'已应用' if oa else '未应用'} → {'已应用' if na else '未应用'}")
    old_sk = old.get("skills", {}).get("total", 0)
    new_sk = loc.get("skills", {}).get("total", 0)
    if old_sk != new_sk:
        changes.append(f"Skill 数量: {old_sk} → {new_sk}")
    return changes if changes else ["✅ 无变化"]


def watch_loop(interval: int = 300) -> None:
    """Continuous monitoring mode."""
    first = True
    while True:
        loc = locate_all()
        if first:
            save_state(loc)
            print(format_human(loc))
            print(f"\n🔁 Watching every {interval}s (Ctrl+C to stop)...")
            first = False
        else:
            changes = diff_state(loc)
            if any("无变化" not in c for c in changes):
                print(f"\n[{datetime.now().isoformat()[:19]}] 🔔 环境变更检测!")
                for c in changes:
                    print(f"  {c}")
                save_state(loc)
            else:
                print(f"[{datetime.now().isoformat()[:19]}] ✅ 无变化", end="\r")
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 Watch stopped.")
            break


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hermes Environment Detection Engine")
    parser.add_argument("--format", choices=["json", "human", "feishu"], default="json")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring")
    parser.add_argument("--watch-interval", type=int, default=300, help="Poll interval in seconds")
    parser.add_argument("--save-state", action="store_true", help="Save state snapshot")
    parser.add_argument("--diff", action="store_true", help="Compare with last state")
    args = parser.parse_args()

    if args.watch:
        watch_loop(args.watch_interval)
        return

    loc = locate_all()

    if args.save_state:
        save_state(loc)
        print(f"💾 State saved to {STATE_FILE}")

    if args.diff:
        changes = diff_state(loc)
        for c in changes:
            print(c)
        return

    if args.check_only:
        issues = verify_can_patch(loc)
        if issues:
            print(f"❌ {len(issues)} issue(s):")
            for i in issues:
                print(f"   • {i}")
            sys.exit(1)
        print("✅ Ready")
        sys.exit(0)

    if args.format == "human":
        print(format_human(loc))
    elif args.format == "feishu":
        print(format_feishu(loc))
    else:
        print(json.dumps(loc, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
