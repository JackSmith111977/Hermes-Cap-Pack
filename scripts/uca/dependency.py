"""
DependencyChecker — 能力包依赖检查器

检查安装能力包所需的前置条件是否满足。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .protocol import CapPack


class DependencyError(Exception):
    """依赖检查失败"""
    pass


class DependencyChecker:
    """检查能力包的依赖是否满足"""

    def __init__(self):
        self._packages_cache: Optional[set[str]] = None

    def _get_installed_packages(self) -> set[str]:
        """获取当前环境中已安装的 Python 包名"""
        if self._packages_cache is None:
            try:
                import pkg_resources
                self._packages_cache = {
                    pkg.key.lower()
                    for pkg in pkg_resources.working_set
                }
            except ImportError:
                # fallback: importlib.metadata
                try:
                    from importlib import metadata
                    self._packages_cache = {
                        dist.metadata["Name"].lower()
                        for dist in metadata.distributions()
                        if dist.metadata.get("Name")
                    }
                except Exception:
                    self._packages_cache = set()
        return self._packages_cache

    def check_python_packages(self, requirements: list[str]) -> list[str]:
        """检查 Python 包依赖，返回缺失的包列表"""
        installed = self._get_installed_packages()
        missing = []
        for req in requirements:
            pkg_name = req.split(">=")[0].split("==")[0].split("<")[0].strip().lower()
            if pkg_name and pkg_name not in installed:
                missing.append(req)
        return missing

    def check_skills_exist(self, skill_ids: list[str], skills_dir: Path) -> list[str]:
        """检查前置 skill 是否存在，返回缺失的 skill 列表"""
        missing = []
        for sid in skill_ids:
            skill_path = skills_dir / sid / "SKILL.md"
            if not skill_path.exists():
                missing.append(sid)
        return missing

    def check(self, pack: CapPack, skills_dir: Optional[Path] = None) -> dict:
        """执行所有依赖检查，返回检查报告

        返回值:
        {
            "all_satisfied": bool,
            "missing_packages": [...],
            "missing_skills": [...],
        }
        """
        result = {
            "all_satisfied": True,
            "missing_packages": [],
            "missing_skills": [],
        }

        if pack.dependencies:
            missing_pkgs = self.check_python_packages(pack.dependencies)
            result["missing_packages"] = missing_pkgs
            if missing_pkgs:
                result["all_satisfied"] = False

        return result
