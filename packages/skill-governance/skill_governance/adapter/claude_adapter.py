"""Claude Code adapter — STORY-5-3-3.

:class:`ClaudeAdapter` extends :class:`SkillGovernanceAdapter` to provide
governance‑aware adaptation for the **Claude Code** agent environment.

The adapter delegates all operations to the governance engine via
``subprocess`` — suitable for environments where the Python package is
available but direct imports are not desired (e.g. when the adapter runs
in a separate process or context).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from skill_governance.adapter.base import AdapterConfig, SkillGovernanceAdapter


# ─── Subprocess helpers ────────────────────────────────────────────────────────


def _exec_python(code: str, *args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a Python one‑liner in a subprocess.

    Args:
        code:    Python code to execute via ``-c``.
        *args:   Additional arguments passed to the script via ``sys.argv``.
        timeout: Maximum seconds to wait for completion.

    Returns:
        The :class:`subprocess.CompletedProcess` result.
    """
    return subprocess.run(
        [sys.executable, "-c", code, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ─── ClaudeAdapter ─────────────────────────────────────────────────────────────


class ClaudeAdapter(SkillGovernanceAdapter):
    """Governance adapter for the **Claude Code** agent.

    *   **scan**       — delegates to ``skill-governance scan --format json``
                        via subprocess.
    *   **suggest**    — delegates to :class:`CapPackAdapter` via subprocess.
    *   **dry_run**    — delegates to :class:`CapPackAdapter` via subprocess.
    *   **apply**      — delegates to :class:`CapPackAdapter` via subprocess.
    *   **get_agent_info** — reports Claude Code as the target agent.
    """

    def __init__(self, config: AdapterConfig | None = None) -> None:
        """Initialise the Claude adapter.

        Args:
            config: Adapter configuration.  When *None*, a default config with
                    ``agent_type='claude'`` and ``dry_run=True`` is created.
        """
        self._config = config or AdapterConfig(
            agent_type="claude",
            dry_run=True,
        )

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Human-readable adapter identifier."""
        return "claude"

    @property
    def config(self) -> AdapterConfig:
        """Return the adapter configuration."""
        return self._config

    # ── scan ──────────────────────────────────────────────────────────────

    def scan(self, path: str) -> dict[str, Any]:
        """Run L0‑L4 compliance scan via the governance engine CLI.

        Invokes ``python3 -m skill_governance.cli.main scan <path> --format json``
        in a subprocess and parses the JSON output.

        Args:
            path: Path to a cap‑pack directory (containing ``cap-pack.yaml``)
                  or a skill directory.

        Returns:
            Parsed scan report dictionary, or an error dict on failure.
        """
        target = Path(path).resolve()
        if not target.exists():
            return {
                "error": f"Path does not exist: {path}",
                "target_path": str(target),
            }

        cmd = [
            sys.executable,
            "-m",
            "skill_governance.cli.main",
            "scan",
            str(target),
            "--format",
            "json",
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            return {"error": "Governance scan timed out", "target_path": str(target)}

        if result.returncode != 0:
            return {
                "error": f"Governance scan failed: {result.stderr.strip()}",
                "target_path": str(target),
            }

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            return {
                "error": f"Failed to parse scan output: {exc}",
                "target_path": str(target),
                "raw_output": result.stdout,
            }

    # ── suggest ───────────────────────────────────────────────────────────

    def suggest(self, path: str) -> list[dict[str, Any]]:
        """Recommend cap‑pack packages via subprocess CLI call.

        Runs a Python one‑liner that imports :class:`CapPackAdapter` and
        invokes :meth:`CapPackAdapter.suggest`.

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
        target = Path(path).resolve()
        if not target.exists() or not (target / "SKILL.md").exists():
            return []

        python_code = (
            "import json, sys;"
            "from skill_governance.adapter.cap_pack_adapter import CapPackAdapter;"
            "adapter = CapPackAdapter();"
            "result = adapter.suggest(sys.argv[1]);"
            "print(json.dumps(["
            "  {'pack_name': s.pack_name, 'pack_path': s.pack_path, "
            "   'score': s.score, 'reasons': s.reasons}"
            "  for s in result.suggestions"
            "]))"
        )
        try:
            proc = _exec_python(python_code, str(target), timeout=60)
        except subprocess.TimeoutExpired:
            return []

        if proc.returncode != 0:
            return []

        try:
            return json.loads(proc.stdout)
        except (json.JSONDecodeError, TypeError):
            return []

    # ── dry_run ───────────────────────────────────────────────────────────

    def dry_run(self, path: str) -> str:
        """Preview the changes :meth:`apply` would perform via subprocess.

        Runs a Python one‑liner that imports :class:`CapPackAdapter` and
        invokes :meth:`CapPackAdapter.dry_run`.

        Args:
            path: Path to the skill or pack directory.

        Returns:
            A human‑readable string describing the proposed modifications.
        """
        target = Path(path).resolve()
        if not target.exists():
            return f"Error: path does not exist: {path}"

        python_code = (
            "import sys;"
            "from skill_governance.adapter.cap_pack_adapter import CapPackAdapter;"
            "adapter = CapPackAdapter();"
            "result = adapter.dry_run(sys.argv[1]);"
            "print(result.message)"
        )
        try:
            proc = _exec_python(python_code, str(target), timeout=60)
        except subprocess.TimeoutExpired:
            return f"Error: dry_run timed out for {path}"

        if proc.returncode != 0:
            return f"Error: {proc.stderr.strip()}" if proc.stderr else f"dry_run failed for {path}"

        return proc.stdout.strip()

    # ── apply ─────────────────────────────────────────────────────────────

    def apply(self, path: str) -> bool:
        """Execute adaptation via subprocess CLI call.

        Runs a Python one‑liner that imports :class:`CapPackAdapter` and
        invokes :meth:`CapPackAdapter.apply`.  Respects the adapter's
        ``dry_run`` and ``auto_confirm`` config settings.

        Args:
            path: Path to the skill directory.

        Returns:
            ``True`` if changes were applied successfully, ``False`` otherwise.
        """
        target = Path(path).resolve()
        if not target.exists() or not (target / "SKILL.md").exists():
            return False

        if self._config.dry_run:
            print(self.dry_run(path))
            return True

        confirm_flag = "False" if self._config.auto_confirm else "True"
        python_code = (
            "import sys;"
            "from skill_governance.adapter.cap_pack_adapter import CapPackAdapter;"
            "adapter = CapPackAdapter();"
            f"result = adapter.apply(sys.argv[1], confirm={confirm_flag});"
            "print(int(result.applied))"
        )
        try:
            proc = _exec_python(python_code, str(target), timeout=60)
        except subprocess.TimeoutExpired:
            return False

        if proc.returncode != 0:
            return False

        try:
            return bool(int(proc.stdout.strip()))
        except (ValueError, TypeError):
            return False

    # ── get_agent_info ────────────────────────────────────────────────────

    def get_agent_info(self) -> dict[str, Any]:
        """Return metadata about the Claude Code agent environment.

        Returns:
            A dictionary with agent type and version information.
        """
        return {
            "agent_type": "claude",
            "version": "unknown",
        }
