"""Adapter abstraction layer — STORY-5-3-1.

Defines the :class:`SkillGovernanceAdapter` abstract base class and
:class:`AdapterConfig` dataclass for all skill governance adapters.

Every concrete adapter (Hermes, OpenCode, Claude Code, etc.) inherits
from ``SkillGovernanceAdapter`` and implements the five abstract methods.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ─── Configuration ────────────────────────────────────────────────────────────


@dataclass
class AdapterConfig:
    """Configuration for a skill governance adapter.

    Attributes:
        agent_type:    Target agent identifier (e.g. ``"hermes"``,
                       ``"opencode"``, ``"claude-code"``).
        working_dir:   Working directory the adapter should operate in.
        dry_run:       When *True*, no actual filesystem changes are
                       performed — only preview / dry-run behaviour.
        auto_confirm:  When *True*, user confirmation prompts are skipped.
    """

    agent_type: str
    working_dir: str = ""
    dry_run: bool = True
    auto_confirm: bool = False


# ─── Abstract Base Class ──────────────────────────────────────────────────────


class SkillGovernanceAdapter(ABC):
    """Abstract base class for all skill governance adapters.

    Defines the contract every adapter must fulfil:

    * :meth:`scan`        — L0‑L4 compliance inspection
    * :meth:`suggest`     — pack recommendation for a skill
    * :meth:`dry_run`     — preview of pending changes
    * :meth:`apply`       — execution of the adaptation
    * :meth:`get_agent_info` — agent-environment metadata

    Subclasses also provide a *name* property (e.g. ``"hermes"``).
    """

    # ── Subclass contract ─────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable adapter identifier (e.g. ``'hermes'``)."""
        ...

    @abstractmethod
    def scan(self, path: str) -> dict[str, Any]:
        """Run a four‑layer (L0‑L4) compliance scan on *path*.

        Args:
            path: Filesystem path to a skill directory **or** a cap‑pack
                  directory (containing ``cap-pack.yaml``).

        Returns:
            A dictionary with per‑layer results, overall compliance verdict,
            and any blocking failures detected.
        """
        ...

    @abstractmethod
    def suggest(self, path: str) -> list[dict[str, Any]]:
        """Recommend target cap‑pack packages for the skill at *path*.

        Uses tag matching, description similarity, and classification to
        rank suitable packages.

        Args:
            path: Path to the skill directory (must contain ``SKILL.md``).

        Returns:
            A list of suggestion dicts sorted by score descending.
            Each dict contains:
                - ``pack_name`` (str)
                - ``pack_path`` (str)
                - ``score`` (float, 0.0‑1.0)
                - ``reasons`` (list[str])
        """
        ...

    @abstractmethod
    def dry_run(self, path: str) -> str:
        """Preview the changes :meth:`apply` would perform.

        No files are modified during this call.

        Args:
            path: Path to the skill or pack directory.

        Returns:
            A human‑readable string describing the proposed modifications.
        """
        ...

    @abstractmethod
    def apply(self, path: str) -> bool:
        """Execute the adaptation or modification.

        Applies the changes determined by :meth:`scan` / :meth:`suggest`.
        May interact with the user unless ``auto_confirm`` is set in the
        adapter's config.

        Args:
            path: Path to the skill or pack directory.

        Returns:
            ``True`` if changes were applied successfully, ``False`` otherwise.
        """
        ...

    @abstractmethod
    def get_agent_info(self) -> dict[str, Any]:
        """Return metadata about the target agent environment.

        Returns:
            A dictionary with at least:
                - ``name`` (str):          Agent name.
                - ``available`` (bool):    Whether the agent is detected.
                - ``version`` (str):       Agent version, if detectable.
                - ``config_path`` (str):   Location of the agent's config.
        """
        ...
