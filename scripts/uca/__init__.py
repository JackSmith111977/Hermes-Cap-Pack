"""
UCA Core — Unified Capability Adapter Core

为 cap-pack 项目提供统一的适配器基础设施。
所有 Agent 适配器实现此模块中定义的 Protocol。
"""

from .protocol import AgentAdapter, AdapterResult, CapPack, CapPackSkill, CapPackExperience, CapPackMCP
from .parser import PackParser, PackParseError
from .dependency import DependencyChecker, DependencyError
from .verifier import PackVerifier, VerificationResult

__all__ = [
    "AgentAdapter",
    "AdapterResult",
    "CapPack",
    "CapPackSkill",
    "CapPackExperience",
    "CapPackMCP",
    "PackParser",
    "PackParseError",
    "DependencyChecker",
    "DependencyError",
    "PackVerifier",
    "VerificationResult",
]
