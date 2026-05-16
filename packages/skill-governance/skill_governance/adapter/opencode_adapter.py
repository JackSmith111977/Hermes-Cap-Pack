"""OpenCode adapter — STORY-5-3-1.

:class:`OpenCodeAdapter` extends :class:`SkillGovernanceAdapter` to provide
governance‑aware adaptation for the **OpenCode CLI Agent** environment.

The adapter delegates L0‑L4 compliance scanning to the governance engine CLI
via ``subprocess`` (``skill-governance scan``).  Skill installation writes
OpenCode‑compatible ``SKILL.md`` files into ``~/.config/opencode/skills/``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from skill_governance.adapter.base import AdapterConfig, SkillGovernanceAdapter

# ─── Path constants ───────────────────────────────────────────────────────────

OPENCODE_CONFIG = Path.home() / ".config" / "opencode"
OPENCODE_SKILLS = OPENCODE_CONFIG / "skills"
OPENCODE_CONFIG_FILE = OPENCODE_CONFIG / "opencode.json"

# ─── CLI helpers ──────────────────────────────────────────────────────────────


def _governance_scan_cmd() -> str:
    """Resolve the governance scan CLI invocation."""
    which = shutil.which("skill-governance")
    if which:
        return f"{which} scan"
    return f"{sys.executable} -m skill_governance.cli.main scan"


def _run_governance_scan(pack_path: str) -> dict[str, Any]:
    """Run ``skill-governance scan --format json`` and parse the result.

    Args:
        pack_path: Path to the cap‑pack directory to scan.

    Returns:
        Parsed scan report dictionary, or an error dict on failure.
    """
    cmd = f'{_governance_scan_cmd()} "{pack_path}" --format json'
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return {"error": "Governance scan timed out", "target_path": pack_path}

    if result.returncode != 0:
        return {
            "error": f"Governance scan failed: {result.stderr.strip()}",
            "target_path": pack_path,
        }

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {
            "error": f"Failed to parse scan output: {exc}",
            "target_path": pack_path,
            "raw_output": result.stdout,
        }


# ─── OpenCodeAdapter ──────────────────────────────────────────────────────────


class OpenCodeAdapter(SkillGovernanceAdapter):
    """Governance adapter for the **OpenCode CLI Agent**.

    *   **scan**       — delegates to ``skill-governance scan`` via subprocess.
    *   **suggest**    — lightweight tag‑based pack matching.
    *   **dry_run**    — preview installation steps.
    *   **apply**      — write OpenCode‑compatible ``SKILL.md`` and sub‑resources
                        into ``~/.config/opencode/skills/<skill-id>/``.
    *   **get_agent_info** — reports OpenCode availability and version.
    """

    def __init__(self, config: AdapterConfig | None = None) -> None:
        """Initialise the OpenCode adapter.

        Args:
            config: Adapter configuration.  When *None*, a default config with
                    ``agent_type='opencode'`` and ``dry_run=True`` is created.
        """
        self._config = config or AdapterConfig(
            agent_type="opencode",
            dry_run=True,
        )
        self._packs_root = self._detect_packs_root()

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "opencode"

    @property
    def config(self) -> AdapterConfig:
        return self._config

    # ── scan ──────────────────────────────────────────────────────────────

    def scan(self, path: str) -> dict[str, Any]:
        """Run L0‑L4 compliance scan via the governance engine CLI.

        If *path* points to a skill directory (contains ``SKILL.md``) the
        method attempts to locate the enclosing cap‑pack before scanning.

        Args:
            path: Path to a skill directory or cap‑pack directory.

        Returns:
            Scan report dictionary (see :func:`_run_governance_scan`).
        """
        target = Path(path).resolve()
        if not target.exists():
            return {
                "error": f"Path does not exist: {path}",
                "target_path": str(target),
            }

        # If *path* is a skill, try to discover its parent pack.
        pack_path = str(target)
        if (target / "SKILL.md").exists() and not (target / "cap-pack.yaml").exists():
            # Walk up to find a cap-pack.yaml
            for parent in [target.parent, target.parent.parent]:
                if (parent / "cap-pack.yaml").exists():
                    pack_path = str(parent)
                    break

        return _run_governance_scan(pack_path)

    # ── suggest ───────────────────────────────────────────────────────────

    def suggest(self, path: str) -> list[dict[str, Any]]:
        """Recommend cap‑pack packages for the skill at *path*.

        Performs lightweight tag‑based matching against manifests in the
        ``packs/`` directory.

        Args:
            path: Path to a skill directory containing ``SKILL.md``.

        Returns:
            List of suggestion dicts sorted by score descending.
        """
        target = Path(path).resolve()
        if not target.exists() or not (target / "SKILL.md").exists():
            return []

        skill_tags, skill_desc = _extract_skill_metadata(target)
        if not skill_tags:
            skill_tags = {target.name.lower()}

        packs_dir = self._packs_root
        if not packs_dir.exists():
            return []

        suggestions: list[dict[str, Any]] = []
        for pack_dir in sorted(packs_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            manifest_path = pack_dir / "cap-pack.yaml"
            if not manifest_path.exists():
                continue

            try:
                import yaml

                with open(manifest_path, "r") as fh:
                    manifest = yaml.safe_load(fh)
                if not isinstance(manifest, dict):
                    continue

                pack_tags: set[str] = set()
                for sk in manifest.get("skills", []):
                    for t in sk.get("tags", []):
                        pack_tags.add(str(t).lower())
                for t in manifest.get("triggers", []):
                    pack_tags.add(str(t).lower())
                if manifest.get("domain"):
                    pack_tags.add(str(manifest["domain"]).lower())
                if manifest.get("category"):
                    pack_tags.add(str(manifest["category"]).lower())

                score = _jaccard_similarity(skill_tags, pack_tags)
                if score > 0.0:
                    common = sorted(skill_tags & pack_tags)
                    suggestions.append(
                        {
                            "pack_name": manifest.get("name", pack_dir.name),
                            "pack_path": str(pack_dir.resolve()),
                            "score": round(score, 4),
                            "reasons": [
                                f"Tag overlap: {common[:5]}" if common
                                else "Name-based match"
                            ],
                        }
                    )
            except Exception:
                continue

        suggestions.sort(key=lambda s: s["score"], reverse=True)
        return suggestions

    # ── dry_run ───────────────────────────────────────────────────────────

    def dry_run(self, path: str) -> str:
        """Preview what :meth:`apply` would do without writing any files.

        Args:
            path: Path to the skill directory.

        Returns:
            Human‑readable description of proposed changes.
        """
        target = Path(path).resolve()
        if not target.exists():
            return f"Error: path does not exist: {path}"

        suggestions = self.suggest(path)
        lines = [
            f"[DRY RUN] OpenCode adapter — skill: {target.name}",
            f"  Source path:     {target}",
            f"  Install target:  {OPENCODE_SKILLS / target.name}",
        ]
        if suggestions:
            top = suggestions[0]
            lines.append(f"  Best pack match: {top['pack_name']} (score {top['score']:.2f})")
            for r in top["reasons"]:
                lines.append(f"    - {r}")
        else:
            lines.append("  No matching pack found; skill would still be installed.")

        lines.append("  [no changes written — dry run]")
        return "\n".join(lines)

    # ── apply ─────────────────────────────────────────────────────────────

    def apply(self, path: str) -> bool:
        """Install the skill at *path* into the OpenCode skills directory.

        Rewrites ``SKILL.md`` into an OpenCode‑compatible format and copies
        any sub‑directories (``references/``, ``scripts/``, ``templates/``,
        ``assets/``).

        Args:
            path: Path to the skill directory containing ``SKILL.md``.

        Returns:
            ``True`` on success, ``False`` on failure.
        """
        target = Path(path).resolve()
        if not target.exists() or not (target / "SKILL.md").exists():
            return False

        if self._config.dry_run:
            print(self.dry_run(path))
            return True

        if not self._config.auto_confirm:
            try:
                resp = (
                    input(f"Install skill '{target.name}' to OpenCode? [y/N]: ")
                    .strip()
                    .lower()
                )
                if resp != "y":
                    print("Cancelled.")
                    return False
            except (EOFError, KeyboardInterrupt):
                return False

        skill_id = target.name
        dst = OPENCODE_SKILLS / skill_id

        # Rewrite SKILL.md for OpenCode compatibility
        ok = _rewrite_skill_for_opencode(skill_id, target, dst)
        if not ok:
            return False

        # Copy recognised sub‑directories
        for subdir in ("references", "scripts", "templates", "assets"):
            sub_src = target / subdir
            if sub_src.exists() and sub_src.is_dir():
                sub_dst = dst / subdir
                if sub_dst.exists():
                    shutil.rmtree(sub_dst)
                shutil.copytree(sub_src, sub_dst)

        # Track installation
        if not (_track := _load_tracked()).get(skill_id):
            _track[skill_id] = {
                "skill_id": skill_id,
                "installed_at": __import__("datetime").datetime.now().isoformat()[:19],
                "source_path": str(target),
            }
            _save_tracked(_track)

        return True

    # ── get_agent_info ────────────────────────────────────────────────────

    def get_agent_info(self) -> dict[str, Any]:
        """Return metadata about the OpenCode agent environment.

        Returns:
            Dict with keys: ``name``, ``available``, ``version``,
            ``config_path``, ``skills_path``.
        """
        available = shutil.which("opencode") is not None
        version = ""
        if available:
            try:
                proc = subprocess.run(
                    ["opencode", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                version = (proc.stdout or proc.stderr).strip()
            except Exception:
                pass

        return {
            "name": "opencode",
            "available": available,
            "version": version or "unknown",
            "config_path": str(OPENCODE_CONFIG_FILE),
            "skills_path": str(OPENCODE_SKILLS),
        }

    # ── Internal helpers ──────────────────────────────────────────────────

    @staticmethod
    def _detect_packs_root() -> Path:
        """Auto‑detect the ``packs/`` directory."""
        candidates = [
            Path.cwd() / "packs",
            Path(__file__).resolve().parent.parent.parent.parent.parent / "packs",
            Path.home() / "projects" / "hermes-cap-pack" / "packs",
        ]
        for c in candidates:
            if c.exists():
                return c
        return Path.cwd() / "packs"


# ─── Module‑level helpers ─────────────────────────────────────────────────────


def _extract_skill_metadata(skill_dir: Path) -> tuple[set[str], str]:
    """Extract tags and description from ``SKILL.md`` frontmatter.

    Returns:
        ``(tags_set, description_string)``
    """
    skill_md = skill_dir / "SKILL.md"
    tags: set[str] = set()
    desc = ""
    if skill_md.exists():
        try:
            content = skill_md.read_text(encoding="utf-8")
            if content.startswith("---"):
                import yaml

                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm = yaml.safe_load(parts[1]) or {}
                    raw_tags = fm.get("tags", [])
                    if isinstance(raw_tags, list):
                        tags = set(str(t).lower() for t in raw_tags)
                    desc = fm.get("description", "") or ""
        except Exception:
            pass
    tags.add(skill_dir.name.lower())
    return tags, desc


def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard similarity between two sets of strings.

    Returns a float in ``[0.0, 1.0]``.
    """
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _rewrite_skill_for_opencode(skill_id: str, src_dir: Path, dst_dir: Path) -> bool:
    """Write an OpenCode‑compatible ``SKILL.md`` into *dst_dir*."""
    src_file = src_dir / "SKILL.md"
    if not src_file.exists():
        return False

    content = src_file.read_text(encoding="utf-8")
    frontmatter: dict[str, Any] = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                import yaml

                frontmatter = yaml.safe_load(parts[1]) or {}
            except Exception:
                frontmatter = {}
            body = parts[2].strip() if len(parts) > 2 else ""

    oc_fm: dict[str, Any] = {
        "name": skill_id,
        "description": frontmatter.get("description", f"Skill: {skill_id}"),
    }
    if frontmatter.get("license"):
        oc_fm["license"] = frontmatter["license"]
    oc_fm["compatibility"] = "opencode"
    oc_fm["metadata"] = {
        "source": "hermes-cap-pack",
        "original_name": frontmatter.get("name", skill_id),
    }

    dst_dir.mkdir(parents=True, exist_ok=True)
    import yaml

    new_content = "---\n"
    new_content += yaml.dump(oc_fm, default_flow_style=False, allow_unicode=True)
    new_content += "---\n\n"
    new_content += body
    (dst_dir / "SKILL.md").write_text(new_content)
    return True


def _load_tracked() -> dict:
    """Load tracked installations from ``~/.hermes/installed_opencode_packs.json``."""
    track_file = Path.home() / ".hermes" / "installed_opencode_packs.json"
    if track_file.exists():
        try:
            return json.loads(track_file.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_tracked(data: dict) -> None:
    """Persist tracked installation data."""
    track_file = Path.home() / ".hermes" / "installed_opencode_packs.json"
    track_file.parent.mkdir(parents=True, exist_ok=True)
    track_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
