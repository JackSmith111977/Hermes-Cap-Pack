"""Adapter package — cap-pack auto-adaptation engine & governance adapters."""

from skill_governance.adapter.base import AdapterConfig, SkillGovernanceAdapter
from skill_governance.adapter.cap_pack_adapter import (
    AdaptationResult,
    CapPackAdapter,
    PackSuggestion,
)
from skill_governance.adapter.opencode_adapter import OpenCodeAdapter
from skill_governance.adapter.openclaw_adapter import OpenClawAdapter
from skill_governance.adapter.claude_adapter import ClaudeAdapter

__all__ = [
    # Base
    "AdapterConfig",
    "SkillGovernanceAdapter",
    # Cap-pack adapter
    "CapPackAdapter",
    "AdaptationResult",
    "PackSuggestion",
    # Agent-specific adapters
    "OpenCodeAdapter",
    "OpenClawAdapter",
    "ClaudeAdapter",
]
