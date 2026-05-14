"""
PackParser — 能力包 YAML 解析器

解析 cap-pack.yaml 并返回 CapPack 对象。
支持可选 JSON Schema 验证。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import yaml

from .protocol import CapPack, CapPackSkill, CapPackExperience, CapPackMCP


class PackParseError(Exception):
    """解析 cap-pack.yaml 时出错"""
    pass


class PackParser:
    """cap-pack.yaml 解析器"""

    def __init__(self, schema_path: Optional[Path] = None):
        self.schema_path = schema_path

    def _validate_schema(self, data: dict, manifest_path: Path) -> list[str]:
        """如果提供了 schema，执行 JSON Schema 验证，返回警告列表"""
        warnings = []
        if not self.schema_path or not self.schema_path.exists():
            return warnings

        try:
            import jsonschema
            with open(self.schema_path) as f:
                schema = json.load(f)
            jsonschema.validate(data, schema)
        except ImportError:
            warnings.append("jsonschema 未安装，跳过 schema 验证")
        except jsonschema.ValidationError as e:
            warnings.append(f"Schema 验证警告: {e.message}")
        except Exception as e:
            warnings.append(f"Schema 验证异常: {e}")
        return warnings

    def _parse_skills(self, data: dict, pack_dir: Path) -> list[CapPackSkill]:
        """解析 skills 列表"""
        skills = []
        for s in data.get("skills", []):
            sid = s.get("id", "?")
            skills.append(CapPackSkill(
                id=sid,
                path=s.get("path", f"SKILLS/{sid}/SKILL.md"),
                category=s.get("category", s.get("cluster", "")),
                description=s.get("description", ""),
                source=s.get("source", ""),
            ))
        return skills

    def _parse_experiences(self, data: dict) -> list[CapPackExperience]:
        """解析 experiences 列表"""
        experiences = []
        for e in data.get("experiences", []):
            eid = e.get("id", "?")
            experiences.append(CapPackExperience(
                id=eid,
                path=e.get("path", f"EXPERIENCES/{eid}.md"),
                description=e.get("description", e.get("title", "")),
            ))
        return experiences

    def _parse_mcp(self, data: dict) -> list[CapPackMCP]:
        """解析 MCP 配置"""
        mcp_list = []
        for m in data.get("mcp_servers", []):
            mcp_list.append(CapPackMCP(
                name=m.get("id", "?"),
                config={k: v for k, v in m.items() if k != "id"},
            ))
        return mcp_list

    def _parse_dependencies(self, data: dict) -> list[str]:
        """解析 Python 包依赖"""
        deps = data.get("dependencies", {})
        if isinstance(deps, dict):
            return deps.get("python_packages", [])
        return []

    def _parse_hooks(self, data: dict) -> list[dict]:
        """解析 hooks"""
        hooks_data = data.get("hooks", {})
        if isinstance(hooks_data, dict):
            return hooks_data.get("on_activate", [])
        return []

    def _parse_depends_on(self, data: dict) -> dict:
        """解析 depends_on（包级依赖）"""
        deps = data.get("depends_on", {})
        if isinstance(deps, dict):
            return deps
        return {}

    def parse(self, pack_dir: Path) -> CapPack:
        """解析 pack_dir 下的 cap-pack.yaml，返回 CapPack 对象

        Args:
            pack_dir: 能力包目录（必须包含 cap-pack.yaml）

        Returns:
            CapPack 对象

        Raises:
            PackParseError: 解析失败时
        """
        manifest_path = pack_dir / "cap-pack.yaml"

        if not manifest_path.exists():
            # 尝试 cap-pack.yml
            alt_path = pack_dir / "cap-pack.yml"
            if alt_path.exists():
                manifest_path = alt_path
            else:
                raise PackParseError(
                    f"找不到能力包清单文件: {manifest_path}\n"
                    f"  请确认目录 '{pack_dir}' 下存在 cap-pack.yaml 或 cap-pack.yml"
                )

        # 读取 YAML
        try:
            with open(manifest_path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PackParseError(
                f"YAML 格式错误 ({manifest_path}):\n  {e}"
            )

        if not isinstance(data, dict):
            raise PackParseError(
                f"cap-pack.yaml 内容必须是对象 (dict)，当前类型: {type(data).__name__}"
            )

        # 基本信息
        name = data.get("name") or pack_dir.name
        version = str(data.get("version", "1.0.0"))

        # Schema 验证（非阻塞，收集警告）
        schema_warnings = self._validate_schema(data, manifest_path)

        # 解析各组件
        skills = self._parse_skills(data, pack_dir)
        experiences = self._parse_experiences(data)
        mcp_configs = self._parse_mcp(data)
        dependencies = self._parse_dependencies(data)
        hooks = self._parse_hooks(data)
        depends_on = self._parse_depends_on(data)
        compatibility = data.get("compatibility", {})

        # 如果没有 skills，警告
        warnings = list(schema_warnings)
        if not skills:
            warnings.append(f"能力包 '{name}' 没有定义任何 skill")

        # 构造 CapPack
        pack = CapPack(
            name=name,
            version=version,
            pack_dir=pack_dir.resolve(),
            manifest=data,
            skills=skills,
            experiences=experiences,
            mcp_configs=mcp_configs,
            dependencies=dependencies,
            depends_on=depends_on,
            hooks=hooks,
            compatibility=compatibility,
        )

        return pack
