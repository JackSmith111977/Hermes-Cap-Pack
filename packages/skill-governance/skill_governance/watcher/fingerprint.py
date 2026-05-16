"""Fingerprint watcher — SHA-256 fingerprint-based change detection for SKILL.md files."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional


class FingerprintWatcher:
    """SHA-256 fingerprint watcher with init/check/auto_scan.

    Monitors SKILL.md files for changes by comparing SHA-256 hashes.
    Supports initialization (generating baseline), checking (diffing against
    baseline), and auto_scan (check + return changed files).
    """

    def __init__(self, state_file: Optional[os.PathLike[str]] = None) -> None:
        self.state_file = Path(state_file) if state_file else Path.cwd() / ".governance-fingerprints.json"
        self._fingerprints: dict[str, str] = {}

    def init(self, skills: list[dict[str, Any]]) -> dict[str, str]:
        """Initialize fingerprints for all skill SKILL.md files.

        Args:
            skills: List of skill dicts with "path" keys.

        Returns:
            Dict mapping file paths to their SHA-256 hashes.
        """
        fingerprints: dict[str, str] = {}
        for sk in skills:
            skill_path = sk.get("path", "")
            if not skill_path:
                continue
            skill_md = Path(skill_path) / "SKILL.md"
            if skill_md.exists():
                fhash = self._hash_file(skill_md)
                fingerprints[str(skill_md)] = fhash

        self._fingerprints = fingerprints
        self._save()
        return fingerprints

    def check(self, skills: list[dict[str, Any]]) -> dict[str, str]:
        """Check current files against stored fingerprints.

        Args:
            skills: List of skill dicts with "path" keys.

        Returns:
            Dict of changed file paths to new hashes.
        """
        self._load()
        changed: dict[str, str] = {}
        for sk in skills:
            skill_path = sk.get("path", "")
            if not skill_path:
                continue
            skill_md = Path(skill_path) / "SKILL.md"
            if not skill_md.exists():
                skey = str(skill_md)
                if skey in self._fingerprints:
                    changed[skey] = ""  # deleted
                continue
            current_hash = self._hash_file(skill_md)
            stored_hash = self._fingerprints.get(str(skill_md))
            if stored_hash is None or current_hash != stored_hash:
                changed[str(skill_md)] = current_hash

        return changed

    def auto_scan(self, skills: list[dict[str, Any]]) -> tuple[bool, dict[str, str]]:
        """Check for changes and update fingerprints.

        Returns:
            Tuple of (has_changes, dict_of_changed_files).
        """
        changed = self.check(skills)
        if changed:
            # Update changed entries
            for fpath, new_hash in changed.items():
                if new_hash:
                    self._fingerprints[fpath] = new_hash
                else:
                    self._fingerprints.pop(fpath, None)
            self._save()
        return (len(changed) > 0, changed)

    def get_status(self) -> dict[str, Any]:
        """Get current fingerprint status."""
        self._load()
        return {
            "state_file": str(self.state_file),
            "fingerprinted_files": len(self._fingerprints),
            "files": dict(self._fingerprints),
        }

    def _hash_file(self, path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
        except OSError:
            return ""
        return hasher.hexdigest()

    def _save(self) -> None:
        """Save fingerprints to state file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "version": "1.0",
                    "fingerprints": self._fingerprints,
                },
                f,
                indent=2,
            )

    def _load(self) -> None:
        """Load fingerprints from state file."""
        if not self.state_file.exists():
            self._fingerprints = {}
            return
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._fingerprints = data.get("fingerprints", {})
        except (json.JSONDecodeError, OSError):
            self._fingerprints = {}
