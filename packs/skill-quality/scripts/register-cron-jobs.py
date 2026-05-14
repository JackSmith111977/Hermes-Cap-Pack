#!/usr/bin/env python3
"""
register-cron-jobs.py — skill-quality cron 任务自动注册器
根据 cap-pack.yaml 的 monitors + audits 配置，自动注册/更新/卸载 cron 任务
用法:
  python3 register-cron-jobs.py install    # 注册所有 cron
  python3 register-cron-jobs.py uninstall  # 移除所有 cron
  python3 register-cron-jobs.py update     # 更新（重新注册）
  python3 register-cron-jobs.py status     # 查看当前状态
  python3 register-cron-jobs.py save       # 备份当前配置
  python3 register-cron-jobs.py restore    # 从备份恢复
"""

import json, os, sys, subprocess, shutil, tempfile
from pathlib import Path
from datetime import datetime

CAP_PACK_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = CAP_PACK_DIR / "scripts"
STATE_DIR = Path.home() / ".hermes" / "cap-packs" / "skill-quality" / "state"
BACKUP_DIR = STATE_DIR / "cron-backups"


def load_cap_pack_config() -> dict:
    """Load skill-quality cap-pack.yaml and extract monitors + audits."""
    import yaml
    yaml_path = CAP_PACK_DIR / "cap-pack.yaml"
    if not yaml_path.exists():
        print(f"❌ cap-pack.yaml not found at {yaml_path}")
        sys.exit(1)
    with open(yaml_path) as f:
        config = yaml.safe_load(f)
    integration = config.get("integration", {})
    return {
        "monitors": integration.get("monitors", []),
        "audits": integration.get("audits", []),
    }


def get_existing_cron_jobs() -> list:
    """List existing cron jobs via hermes CLI."""
    try:
        result = subprocess.run(
            ["hermes", "cron", "list", "--all"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.split('\n') if line.strip()]
    except Exception:
        pass
    return []


def register_cron_job(name: str, schedule: str, script: str, description: str) -> bool:
    """Register a single cron job via hermes cron create."""
    script_path = SCRIPTS_DIR / script
    if not script_path.exists():
        print(f"  ⚠️  Script not found: {script_path}, skipping")
        return False
    
    # Build the prompt — it runs the script and delivers output
    prompt = (
        f"Run the skill-quality script: python3 {script_path}\n"
        f"Purpose: {description}\n"
        f"If the script produces output, deliver it to the feishu home channel."
    )
    
    try:
        result = subprocess.run(
            ["hermes", "cron", "create", schedule,
             "--name", f"sq-{name}",
             "--prompt", prompt,
             "--deliver", "origin",
             "--no-agent"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            print(f"  ✅ Registered: sq-{name} ({schedule})")
            return True
        else:
            print(f"  ❌ Failed: sq-{name}: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ⏰ Timeout: sq-{name}")
        return False
    except Exception as e:
        print(f"  ❌ Error: sq-{name}: {e}")
        return False


def unregister_cron_job(name: str) -> bool:
    """Remove a cron job."""
    full_name = f"sq-{name}"
    try:
        # List to find the job_id
        result = subprocess.run(
            ["hermes", "cron", "list", "--all"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if full_name in line:
                    # Extract job_id from line format
                    parts = line.split()
                    if parts:
                        job_id = parts[0]  # Usually first column is ID
                        subprocess.run(
                            ["hermes", "cron", "remove", job_id],
                            capture_output=True, timeout=10,
                        )
                        print(f"  ✅ Removed: {full_name}")
                        return True
        print(f"  ⏭️  Not found: {full_name}")
        return False
    except Exception as e:
        print(f"  ❌ Error removing {full_name}: {e}")
        return False


def save_backup() -> str:
    """Backup current cron configuration."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"cron_backup_{timestamp}.json"
    
    try:
        result = subprocess.run(
            ["hermes", "cron", "list", "--all"],
            capture_output=True, text=True, timeout=10,
        )
        backup = {
            "timestamp": timestamp,
            "cron_list_output": result.stdout,
            "cron_list_error": result.stderr,
        }
        backup_file.write_text(json.dumps(backup, indent=2))
        print(f"  💾 Backup saved: {backup_file}")
        return str(backup_file)
    except Exception as e:
        print(f"  ❌ Backup failed: {e}")
        return ""


def cmd_install():
    """Install all monitors and audits as cron jobs."""
    config = load_cap_pack_config()
    monitors = config.get("monitors", [])
    audits = config.get("audits", [])
    
    print(f"\n{'='*50}")
    print(f"  📡 skill-quality: Installing cron jobs")
    print(f"{'='*50}")
    print(f"  Monitors: {len(monitors)}, Audits: {len(audits)}")
    
    success = 0
    total = 0
    
    for monitor in monitors:
        total += 1
        if register_cron_job(
            name=monitor["id"],
            schedule=monitor.get("schedule", "*/30 * * * *"),
            script=monitor["script"],
            description=monitor.get("description", ""),
        ):
            success += 1
    
    for audit in audits:
        total += 1
        if register_cron_job(
            name=audit["id"],
            schedule=audit.get("schedule", "0 6 * * *"),
            script=audit["script"],
            description=audit.get("description", ""),
        ):
            success += 1
    
    print(f"\n  ✅ {success}/{total} jobs registered")
    if success < total:
        print(f"  ⚠️  {total - success} job(s) failed — check errors above")


def cmd_uninstall():
    """Remove all skill-quality cron jobs."""
    config = load_cap_pack_config()
    all_jobs = config.get("monitors", []) + config.get("audits", [])
    
    print(f"\n{'='*50}")
    print(f"  🗑️  skill-quality: Uninstalling cron jobs")
    print(f"{'='*50}")
    
    success = 0
    for job in all_jobs:
        if unregister_cron_job(job["id"]):
            success += 1
    
    print(f"\n  ✅ {success}/{len(all_jobs)} jobs removed")


def cmd_update():
    """Re-register all jobs (save backup first, then reinstall)."""
    save_backup()
    cmd_uninstall()
    cmd_install()


def cmd_status():
    """Show current skill-quality cron job status."""
    config = load_cap_pack_config()
    all_jobs = config.get("monitors", []) + config.get("audits", [])
    existing = get_existing_cron_jobs()
    
    print(f"\n{'='*50}")
    print(f"  📊 skill-quality: Cron Job Status")
    print(f"{'='*50}")
    
    for job in all_jobs:
        full_name = f"sq-{job['id']}"
        found = any(full_name in line for line in existing)
        marker = "✅" if found else "⬜"
        schedule = job.get("schedule", "?")
        script = job.get("script", "?")
        print(f"  {marker} {full_name} ({schedule})")
        print(f"     Script: {script}")
    
    if not all_jobs:
        print("  (no jobs configured in cap-pack.yaml)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="skill-quality cron manager")
    parser.add_argument("action", choices=["install", "uninstall", "update", "status", "save", "restore"])
    args = parser.parse_args()
    
    if args.action == "install":
        cmd_install()
    elif args.action == "uninstall":
        cmd_uninstall()
    elif args.action == "update":
        cmd_update()
    elif args.action == "status":
        cmd_status()
    elif args.action == "save":
        save_backup()
    elif args.action == "restore":
        backups = sorted(BACKUP_DIR.glob("cron_backup_*.json"))
        if not backups:
            print("❌ No backups found")
            return
        latest = backups[-1]
        print(f"📄 Latest backup: {latest.name}")
        print(f"  Contents: {latest.read_text()[:200]}...")


if __name__ == "__main__":
    main()
