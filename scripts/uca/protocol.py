"""
AgentAdapter Protocol — 统一适配器接口定义

所有 Agent 适配器必须实现此 Protocol。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Optional


# ── 数据类 ─────────────────────────────────────────────


@dataclass
class CapPackSkill:
    """能力包中的单个技能"""
    id: str
    path: str               # 相对于 pack 的路径
    category: str = ""
    description: str = ""
    source: str = ""         # 来源 skill 名（提取时记录）


@dataclass
class CapPackExperience:
    """能力包中的经验文档"""
    id: str
    path: str
    description: str = ""


@dataclass
class CapPackMCP:
    """能力包中的 MCP 配置"""
    name: str
    config: dict


@dataclass
class CapPack:
    """解析后的能力包，包含所有组件"""
    name: str
    version: str
    pack_dir: Path
    manifest: dict

    skills: list[CapPackSkill] = field(default_factory=list)
    experiences: list[CapPackExperience] = field(default_factory=list)
    mcp_configs: list[CapPackMCP] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    hooks: list[dict] = field(default_factory=list)
    compatibility: dict = field(default_factory=dict)


@dataclass
class AdapterResult:
    """适配器操作的结果"""
    success: bool
    pack_name: str = ""
    action: str = ""          # install / uninstall / update / verify
    details: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    backup_path: str = ""


# ── Protocol ────────────────────────────────────────────


class AgentAdapter(Protocol):
    """Agent 适配器必须实现的方法

    所有方法接收 CapPack 对象进行操作，返回 AdapterResult。
    """

    @property
    def name(self) -> str:
        """适配器名称，如 'hermes', 'claude-code'"""
        ...

    @property
    def is_available(self) -> bool:
        """当前环境是否支持此适配器"""
        ...

    def install(self, pack: CapPack) -> AdapterResult:
        """安装能力包到当前 Agent 环境"""
        ...

    def uninstall(self, pack_name: str) -> AdapterResult:
        """卸载已安装的能力包"""
        ...

    def update(self, pack: CapPack, old_version: str) -> AdapterResult:
        """更新已安装的能力包到新版本"""
        ...

    def list_installed(self) -> list[dict]:
        """列出所有已安装的能力包及其状态"""
        ...

    def verify(self, pack_name: str) -> AdapterResult:
        """验证已安装的能力包是否完整可用"""
        ...
