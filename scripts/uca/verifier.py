"""
PackVerifier — 能力包安装后验证器

验证已安装的能力包是否完整可用。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .protocol import CapPack, AdapterResult


class VerificationResult:
    """验证结果"""
    def __init__(self):
        self.all_passed: bool = True
        self.file_checks: list[dict] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []


class PackVerifier:
    """验证能力包安装完整性"""

    def __init__(self, skills_base: Optional[Path] = None):
        self.skills_base = skills_base

    def verify_skill_files(self, skills: list, installed_dir: Path) -> list[dict]:
        """检查 skill 文件是否存在于 installed_dir"""
        results = []
        for skill in skills:
            sid = skill.id if hasattr(skill, 'id') else (skill.get('id', '?') if isinstance(skill, dict) else '?')
            skill_dir = installed_dir / sid
            skill_file = skill_dir / "SKILL.md"

            check = {
                "id": sid,
                "exists": skill_file.exists(),
                "path": str(skill_file),
            }
            if not skill_file.exists():
                check["error"] = f"SKILL.md not found at {skill_file}"
            results.append(check)
        return results

    def verify(self, pack: CapPack, installed_dir: Path) -> AdapterResult:
        """验证能力包安装完整性"""
        result = AdapterResult(
            success=True,
            pack_name=pack.name,
            action="verify",
        )

        # 检查 skill 文件
        file_checks = self.verify_skill_files(pack.skills, installed_dir)
        result.details["file_checks"] = file_checks

        for check in file_checks:
            if not check.get("exists"):
                result.success = False
                result.errors.append(f"缺少 skill 文件: {check['id']}")

        if result.success:
            result.details["skills_found"] = len(pack.skills)

        return result
