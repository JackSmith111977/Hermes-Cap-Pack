"""Tests for HermesAdapter"""

import pytest
import json
import os
import yaml
from pathlib import Path

from scripts.adapters.hermes import HermesAdapter, SnapshotManager
from scripts.uca.protocol import CapPack, CapPackSkill, CapPackMCP


@pytest.fixture
def adapter() -> HermesAdapter:
    return HermesAdapter()


@pytest.fixture
def hermes_home(tmp_path: Path) -> Path:
    """模拟 Hermes 家目录"""
    hh = tmp_path / ".hermes"
    hh.mkdir()
    (hh / "skills").mkdir()
    # 创建基础 config.yaml
    config = {"model": {"default": "test-model"}, "mcp_servers": {}}
    with open(hh / "config.yaml", "w") as f:
        yaml.dump(config, f)
    return hh


@pytest.fixture
def sample_pack(tmp_path: Path) -> tuple[CapPack, Path]:
    """创建测试用的能力包"""
    pack_dir = tmp_path / "test-pack"
    pack_dir.mkdir()

    # Skills — 带 YAML frontmatter（验证门禁需要）
    for sid in ["skill-a", "skill-b"]:
        d = pack_dir / "SKILLS" / sid
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"""---
id: {sid}
name: {sid}
description: Test skill {sid}
---
# {sid}
Description of {sid}
""")

    # cap-pack.yaml
    manifest = {
        "name": "test-pack",
        "version": "1.0.0",
        "type": "capability-pack",
        "skills": [
            {"id": "skill-a", "path": "SKILLS/skill-a/SKILL.md", "description": "Skill A"},
            {"id": "skill-b", "path": "SKILLS/skill-b/SKILL.md", "description": "Skill B"},
        ],
        "mcp_servers": [
            {"id": "test-mcp", "command": "npx", "args": ["test-mcp"], "timeout": 30},
        ],
    }
    with open(pack_dir / "cap-pack.yaml", "w") as f:
        yaml.dump(manifest, f)

    pack = CapPack(
        name="test-pack",
        version="1.0.0",
        pack_dir=pack_dir,
        manifest=manifest,
        skills=[
            CapPackSkill(id="skill-a", path="SKILLS/skill-a/SKILL.md", description="Skill A"),
            CapPackSkill(id="skill-b", path="SKILLS/skill-b/SKILL.md", description="Skill B"),
        ],
        mcp_configs=[
            CapPackMCP(name="test-mcp", config={"command": "npx", "args": ["test-mcp"], "timeout": 30}),
        ],
    )
    return pack, pack_dir


class TestHermesAdapterProperties:
    def test_name(self, adapter: HermesAdapter):
        assert adapter.name == "hermes"

    def test_is_available_false(self, adapter: HermesAdapter, tmp_path: Path):
        """在非 Hermes 环境中不可用"""
        import scripts.adapters.hermes as h
        original_config = h.HERMES_CONFIG
        h.HERMES_CONFIG = tmp_path / "nonexistent" / "config.yaml"
        try:
            assert adapter.is_available is False
        finally:
            h.HERMES_CONFIG = original_config


class TestHermesAdapterInstall:
    def test_install_skills(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        """安装 skill 文件"""
        pack, _ = sample_pack
        # 修改路径指向模拟环境
        import scripts.adapters.hermes as h
        original_skills = h.HERMES_SKILLS
        h.HERMES_SKILLS = hermes_home / "skills"

        try:
            result = adapter.install(pack)
            assert result.success is True
            assert len(result.details["installed_skills"]) == 2
            assert (hermes_home / "skills" / "skill-a" / "SKILL.md").exists()
            assert (hermes_home / "skills" / "skill-b" / "SKILL.md").exists()
        finally:
            h.HERMES_SKILLS = original_skills

    def test_install_dry_run(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        """dry-run 不实际安装"""
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        original_skills = h.HERMES_SKILLS
        h.HERMES_SKILLS = hermes_home / "skills"

        try:
            result = adapter.install(pack, dry_run=True)
            assert result.success is True
            assert not (hermes_home / "skills" / "skill-a").exists()
        finally:
            h.HERMES_SKILLS = original_skills

    def test_install_tracking(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        """安装后记录跟踪信息"""
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"
        original_track = h.TRACK_FILE
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        try:
            result = adapter.install(pack)
            assert result.success is True

            tracked = json.loads((hermes_home / "installed_packs.json").read_text())
            assert "test-pack" in tracked
            assert tracked["test-pack"]["version"] == "1.0.0"
            assert tracked["test-pack"]["skill_count"] == 2
        finally:
            h.TRACK_FILE = original_track


class TestHermesAdapterUninstall:
    def test_uninstall_nonexistent(self, adapter: HermesAdapter):
        result = adapter.uninstall("nonexistent-pack")
        assert result.success is False
        assert "未安装" in result.errors[0]

    def test_uninstall_success(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        """卸载已安装的包"""
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        # 先安装
        adapter.install(pack)

        # 再卸载
        result = adapter.uninstall("test-pack")
        assert result.success is True
        assert result.details["removed"] == 2

        # 确认跟踪已清除
        tracked = json.loads((hermes_home / "installed_packs.json").read_text())
        assert "test-pack" not in tracked


class TestHermesAdapterVerify:
    def test_verify_nonexistent(self, adapter: HermesAdapter):
        result = adapter.verify("nonexistent")
        assert result.success is False

    def test_verify_success(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        adapter.install(pack)
        result = adapter.verify("test-pack")
        assert result.success is True
        assert result.details["valid_skills"] == 2

    def test_verify_missing_skill(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        adapter.install(pack)
        # 删除一个 skill 文件
        import shutil
        shutil.rmtree(hermes_home / "skills" / "skill-a")

        result = adapter.verify("test-pack")
        assert result.success is False
        assert len(result.details["missing_skills"]) == 1


class TestHermesAdapterList:
    def test_list_empty(self, adapter: HermesAdapter, tmp_path: Path):
        import scripts.adapters.hermes as h
        h.TRACK_FILE = tmp_path / "empty_track.json"
        h.TRACK_FILE.write_text("{}")

        packs = adapter.list_installed()
        assert packs == []

    def test_list_with_packs(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        adapter.install(pack)
        packs = adapter.list_installed()
        assert len(packs) == 1
        assert packs[0]["name"] == "test-pack"


class TestSnapshotManager:
    def test_create_snapshot(self, hermes_home: Path):
        """创建快照"""
        import scripts.adapters.hermes as h
        h.SNAPSHOT_DIR = hermes_home / ".uca-snapshots"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        # 先创建一些被跟踪的状态
        tracked = {"test-pack": {"version": "1.0.0", "skills": ["skill-a"]}}
        h.TRACK_FILE.write_text(json.dumps(tracked))

        snapshot_id = SnapshotManager.create("test-pack")
        assert snapshot_id is not None
        assert (hermes_home / ".uca-snapshots" / snapshot_id).exists()

    def test_restore_snapshot(self, hermes_home: Path):
        """从快照恢复"""
        import scripts.adapters.hermes as h
        h.SNAPSHOT_DIR = hermes_home / ".uca-snapshots"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        tracked = {"test-pack": {"version": "1.0.0", "skills": ["skill-a"]}}
        h.TRACK_FILE.write_text(json.dumps(tracked))

        snapshot_id = SnapshotManager.create("test-pack")

        # 修改 tracked
        h.TRACK_FILE.write_text("{}")

        # 恢复
        ops = SnapshotManager.restore(snapshot_id)
        assert len(ops) > 0
        restored = json.loads(h.TRACK_FILE.read_text())
        assert "test-pack" in restored


# ── STORY-1-5-2: 依赖检查 + 验证门禁 ──────────────────────


class TestDependencyCheck:
    """_check_dependencies() 测试"""

    def test_no_deps(self, adapter: HermesAdapter, sample_pack: tuple):
        pack, _ = sample_pack
        missing = adapter._check_dependencies(pack)
        assert missing == []

    def test_missing_dep(self, adapter: HermesAdapter, tmp_path: Path):
        """依赖包未安装时返回缺失列表"""
        pack = CapPack(
            name="test-pack",
            version="1.0.0",
            pack_dir=tmp_path / "test-pack",
            manifest={},
            depends_on={"required-pack": {"version": ">=1.0.0", "reason": "核心库"}},
        )
        missing = adapter._check_dependencies(pack)
        assert missing == ["required-pack (核心库)"]

    def test_skip_deps(self, adapter: HermesAdapter, tmp_path: Path):
        """--skip-deps 跳过检查"""
        pack = CapPack(
            name="test-pack",
            version="1.0.0",
            pack_dir=tmp_path / "test-pack",
            manifest={},
            depends_on={"required-pack": {}},
        )
        missing = adapter._check_dependencies(pack, skip_deps=True)
        assert missing == []

    def test_met_dep(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        """依赖包已安装时返回空"""
        pack_a, _ = sample_pack
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        # 先安装一个包
        adapter.install(pack_a)

        # 创建依赖它的第二个包
        pack_b = CapPack(
            name="pack-b",
            version="1.0.0",
            pack_dir=pack_a.pack_dir.parent / "pack-b",
            manifest={},
            depends_on={"test-pack": {"version": ">=1.0.0", "reason": "基础"}},
        )
        missing = adapter._check_dependencies(pack_b)
        assert missing == []


class TestVerificationGate:
    """_verify_installation() 测试"""

    def test_verify_pass(self, adapter: HermesAdapter, sample_pack: tuple):
        pack, _ = sample_pack
        result = adapter._verify_installation(pack)
        assert result["passed"] is True
        assert len(result["failures"]) == 0

    def test_verify_no_frontmatter(self, adapter: HermesAdapter, tmp_path: Path):
        """SKILL.md 缺少 frontmatter → 验证失败"""
        pack_dir = tmp_path / "bad-pack"
        pack_dir.mkdir()
        d = pack_dir / "SKILLS" / "skill-x"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("# No frontmatter")

        pack = CapPack(
            name="bad-pack",
            version="1.0.0",
            pack_dir=pack_dir,
            manifest={},
            skills=[CapPackSkill(id="skill-x", path="SKILLS/skill-x/SKILL.md")],
        )
        result = adapter._verify_installation(pack)
        assert result["passed"] is False
        assert any("缺少 YAML frontmatter" in f for f in result["failures"])

    def test_verify_script_not_executable(self, adapter: HermesAdapter, tmp_path: Path):
        """脚本文件无执行权限 → 验证失败"""
        pack_dir = tmp_path / "script-pack"
        pack_dir.mkdir()
        d = pack_dir / "SKILLS" / "skill-s"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("---\nid: skill-s\nname: skill-s\ndescription: Test\n---\n# skill-s")

        # 创建测试脚本（无执行权限）并放到目标位置
        scripts_dir = pack_dir / "scripts"
        scripts_dir.mkdir()
        script_file = scripts_dir / "test-script.py"
        script_file.write_text("#!/usr/bin/env python3\nprint('hello')")
        script_file.chmod(0o644)

        # 目标文件也创建（模拟安装完成），但无执行权限
        target_path = tmp_path / "test-script.py"
        target_path.write_text("#!/usr/bin/env python3\nprint('hello')")
        target_path.chmod(0o644)

        manifest = {
            "install": {
                "scripts": [
                    {"source": "scripts/test-script.py", "target": str(target_path)},
                ]
            }
        }

        pack = CapPack(
            name="script-pack",
            version="1.0.0",
            pack_dir=pack_dir,
            manifest=manifest,
            skills=[CapPackSkill(id="skill-s", path="SKILLS/skill-s/SKILL.md")],
        )
        result = adapter._verify_installation(pack)
        assert result["passed"] is False
        assert any("缺少可执行权限" in f for f in result["failures"])

    def test_verify_with_install_flow(self, adapter: HermesAdapter, hermes_home: Path, tmp_path: Path):
        """验证门禁在 install 流程中失败 → 自动回滚"""
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        # 创建无 frontmatter 的包
        pack_dir = tmp_path / "bad-flow-pack"
        pack_dir.mkdir()
        d = pack_dir / "SKILLS" / "bad-skill"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("# No frontmatter here")

        manifest = {
            "name": "bad-flow-pack",
            "skills": [{"id": "bad-skill", "path": "SKILLS/bad-skill/SKILL.md", "description": "Bad"}],
        }

        pack = CapPack(
            name="bad-flow-pack",
            version="1.0.0",
            pack_dir=pack_dir,
            manifest=manifest,
            skills=[CapPackSkill(id="bad-skill", path="SKILLS/bad-skill/SKILL.md")],
        )

        result = adapter.install(pack)
        assert result.success is False
        assert any("验证门禁未通过" in w for w in result.warnings)
        assert any("验证失败" in e for e in result.errors)
        # 确认回滚了（没有留下 tracking）
        import scripts.adapters.hermes as h_mod
        tracked = h_mod._load_tracked()
        assert "bad-flow-pack" not in tracked


# ── STORY-1-5-3: 端到端集成测试 ──────────────────────


class TestEndToEndInstall:
    """能力包端到端安装→验证→卸载集成测试"""

    def _create_lw_pack(self, tmp_path: Path, name: str = "learning-workflow") -> CapPack:
        """创建模拟 learning-workflow 的完整能力包"""
        pack_dir = tmp_path / name
        pack_dir.mkdir()

        # Skill 目录
        skill_dir = pack_dir / "SKILLS" / name
        skill_dir.mkdir(parents=True)

        # 带 YAML frontmatter 的 SKILL.md
        (skill_dir / "SKILL.md").write_text(f"""---
id: {name}
name: {name}
description: E2E test pack for {name}
version: 1.0.0
triggers:
  - test
  - e2e
---
# {name}
E2E test description
""")

        # 脚本目录
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()

        # 创建可执行脚本
        for script_name in ["learning-state.py", "reflection-gate.py", "skill_finder.py"]:
            sp = scripts_dir / script_name
            sp.write_text("#!/usr/bin/env python3\n\"\"\"Test script\"\"\"\nimport sys\nprint(f'{script_name} OK')\nsys.exit(0)\n")
            sp.chmod(0o755)

        # references 目录
        ref_dir = skill_dir / "references"
        ref_dir.mkdir()
        (ref_dir / "cycle-troubleshooting.md").write_text("# Cycle Troubleshooting\nGuide for debugging learning loops.")

        # cap-pack.yaml
        manifest = {
            "name": name,
            "version": "1.0.0",
            "type": "capability-pack",
            "skills": [
                {"id": name, "path": f"SKILLS/{name}/SKILL.md", "description": f"E2E test {name}"},
            ],
            "install": {
                "scripts": [
                    {"source": f"SKILLS/{name}/scripts/learning-state.py", "target": f"~/.hermes/skills/{name}/scripts/learning-state.py"},
                    {"source": f"SKILLS/{name}/scripts/reflection-gate.py", "target": f"~/.hermes/skills/{name}/scripts/reflection-gate.py"},
                    {"source": f"SKILLS/{name}/scripts/skill_finder.py", "target": f"~/.hermes/skills/{name}/scripts/skill_finder.py"},
                ],
                "references": [
                    {"source": f"SKILLS/{name}/references", "target": f"~/.hermes/skills/{name}/references/"},
                ],
                "post_install": [
                    f"chmod +x ~/.hermes/skills/{name}/scripts/*.py 2>/dev/null || true",
                ],
            },
            "depends_on": {
                "quality-assurance": {"version": ">=1.0.0", "reason": "质量门禁"},
            },
        }

        with open(pack_dir / "cap-pack.yaml", "w") as f:
            yaml.dump(manifest, f)

        pack = CapPack(
            name=name,
            version="1.0.0",
            pack_dir=pack_dir,
            manifest=manifest,
            depends_on=manifest.get("depends_on", {}),
            skills=[CapPackSkill(id=name, path=f"SKILLS/{name}/SKILL.md", description=f"E2E test {name}")],
        )
        return pack

    # AC-3.1: 安装成功
    def test_install_skill_and_scripts(self, adapter: HermesAdapter, hermes_home: Path, tmp_path: Path):
        """端到端：安装 skill + 脚本 + 引用"""
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        pack = self._create_lw_pack(tmp_path)
        result = adapter.install(pack)
        assert result.success is True, f"安装失败: {result.errors}"

        # 验证 skill 文件存在
        skill_md = hermes_home / "skills" / "learning-workflow" / "SKILL.md"
        assert skill_md.exists(), "SKILL.md 不存在"
        assert skill_md.read_text().startswith("---"), "SKILL.md 缺少 frontmatter"

        # 验证脚本文件存在
        for script in ["learning-state.py", "reflection-gate.py", "skill_finder.py"]:
            sp = hermes_home / "skills" / "learning-workflow" / "scripts" / script
            assert sp.exists(), f"脚本 {script} 不存在"
            assert os.access(str(sp), os.X_OK), f"脚本 {script} 不可执行"

        # 验证引用文件存在
        ref = hermes_home / "skills" / "learning-workflow" / "references" / "cycle-troubleshooting.md"
        assert ref.exists(), "引用文件不存在"

        # 验证跟踪记录
        tracked = json.loads(h.TRACK_FILE.read_text())
        assert "learning-workflow" in tracked
        assert tracked["learning-workflow"]["skill_count"] == 1
        assert tracked["learning-workflow"]["script_count"] == 3

    # AC-3.2: skill_view 可加载（模拟验证）
    def test_verify_after_install(self, adapter: HermesAdapter, hermes_home: Path, tmp_path: Path):
        """端到端：安装后 verify 通过"""
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        pack = self._create_lw_pack(tmp_path)
        adapter.install(pack)

        result = adapter.verify("learning-workflow")
        assert result.success is True
        assert result.details["valid_skills"] == 1
        assert result.details["script_count"] == 3
        assert len(result.details["bad_scripts"]) == 0

    # AC-3.4: 卸载 + 状态恢复
    def test_uninstall_restores_state(self, adapter: HermesAdapter, hermes_home: Path, tmp_path: Path):
        """端到端：卸载后恢复到安装前状态"""
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        pack = self._create_lw_pack(tmp_path)
        adapter.install(pack)

        # 卸载
        uninstall_result = adapter.uninstall("learning-workflow")
        assert uninstall_result.success is True
        assert uninstall_result.details["removed"] == 1

        # 确认跟踪已清除
        assert "learning-workflow" not in json.loads(h.TRACK_FILE.read_text())

    # AC-3.5: 缺失依赖时安装仍成功（非阻塞）
    def test_install_with_missing_deps(self, adapter: HermesAdapter, hermes_home: Path, tmp_path: Path):
        """端到端：尽管依赖缺失，安装仍成功（非阻塞警告）"""
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        pack = self._create_lw_pack(tmp_path)
        result = adapter.install(pack)
        assert result.success is True, f"安装被依赖缺失阻塞: {result.errors}"
        # 应有缺失依赖警告
        assert any("缺失依赖" in w for w in result.warnings), "应警告缺失依赖但未警告"


# ── STORY-1-5-4: 多 Agent 安装与自动检测 ────────────────


class TestMultiAgentInstall:
    """--target hermes/opencode/auto 多 Agent 测试"""

    def test_hermes_target(self, adapter: HermesAdapter, hermes_home: Path, tmp_path: Path):
        """--target hermes 安装成功"""
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        pack = TestEndToEndInstall()._create_lw_pack(tmp_path, name="multi-hermes-test")
        result = adapter.install(pack)
        assert result.success is True
        assert (hermes_home / "skills" / "multi-hermes-test" / "SKILL.md").exists()

    def test_opencode_format_conversion(self, adapter: HermesAdapter, tmp_path: Path):
        """OpenCode 安装时格式转换正确"""
        from scripts.adapters.opencode import OpenCodeAdapter
        oc_adapter = OpenCodeAdapter()

        # 创建测试 pack
        pack_dir = tmp_path / "oc-pack"
        pack_dir.mkdir()
        skill_dir = pack_dir / "SKILLS" / "oc-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("""---
id: oc-skill
name: OC Skill
description: OpenCode format test
version: 1.0.0
---
# OC Skill
Content body
""")

        manifest = {
            "name": "oc-pack",
            "skills": [{"id": "oc-skill", "path": "SKILLS/oc-skill/SKILL.md", "description": "OC test"}],
        }

        pack = CapPack(
            name="oc-pack", version="1.0.0", pack_dir=pack_dir,
            manifest=manifest,
            skills=[CapPackSkill(id="oc-skill", path="SKILLS/oc-skill/SKILL.md")],
        )

        # dry_run 模式下检查
        result = oc_adapter.install(pack, dry_run=True)
        assert result.success is True
        assert "oc-skill" in result.details.get("installed_skills", [])

    def test_opencode_uninstall(self, tmp_path: Path):
        """OpenCode 卸载功能"""
        from scripts.adapters.opencode import OpenCodeAdapter, TRACK_FILE
        oc_adapter = OpenCodeAdapter()

        # 写一个假的 tracking 记录
        fake_track = {"oc-pack": {"version": "1.0.0", "skills": ["oc-skill"]}}
        TRACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        import json
        TRACK_FILE.write_text(json.dumps(fake_track))

        result = oc_adapter.uninstall("oc-pack")
        # 可能没有真的文件可删（不存在的 pack 目录），但不应该崩溃
        assert result.success is True or "未安装" in str(result.errors)

    def test_cli_auto_detection(self):
        """install-pack.py --target auto 检测可用 Agent"""
        import importlib.util
        import sys
        spec = importlib.util.spec_from_file_location(
            "install_pack",
            "/home/ubuntu/projects/hermes-cap-pack/scripts/install-pack.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        available = mod.detect_available()
        # 在测试环境中至少 hermes 应该可用（有 ~/.hermes/）
        assert isinstance(available, list)


class TestEnhancedUninstall:
    """STORY-1-5-5: 卸载增强与快照回滚测试"""

    def test_uninstall_removes_tracking(self, adapter: HermesAdapter, hermes_home: Path, tmp_path: Path):
        """卸载后 tracking 完全清除"""
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        pack = TestEndToEndInstall()._create_lw_pack(tmp_path, name="remove-test")
        adapter.install(pack)
        assert "remove-test" in json.loads(h.TRACK_FILE.read_text())

        result = adapter.uninstall("remove-test")
        assert result.success is True
        assert "remove-test" not in json.loads(h.TRACK_FILE.read_text())

    def test_uninstall_restores_backup(self, adapter: HermesAdapter, hermes_home: Path, tmp_path: Path):
        """卸载时如果存在 .bak 备份，恢复备份"""
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        # 安装一个包
        pack = TestEndToEndInstall()._create_lw_pack(tmp_path, name="bak-test")
        adapter.install(pack)

        # 手动创建一个备份（模拟更新流产生的备份）
        bak_dir = hermes_home / "skills" / "bak-test.bak"
        bak_dir.mkdir(parents=True)
        (bak_dir / "SKILL.md").write_text("---\nid: bak-test\n---\n# Backup version")

        # 再安装一个新版本（会备份旧版本）
        tmp_path2 = tmp_path / "bak-test-new"
        tmp_path2.mkdir()
        new_pack = TestEndToEndInstall()._create_lw_pack(tmp_path2, name="bak-test")
        adapter.install(new_pack)

        # 卸载
        result = adapter.uninstall("bak-test")
        assert result.success is True
        assert "bak-test" not in json.loads(h.TRACK_FILE.read_text())

    def test_install_failure_rollback(self, adapter: HermesAdapter, hermes_home: Path, tmp_path: Path):
        """安装失败（验证门禁）→ 自动回滚，环境恢复原状"""
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        # 先安装一个正常的包
        good_pack = TestEndToEndInstall()._create_lw_pack(tmp_path, name="survivor")
        adapter.install(good_pack)
        assert "survivor" in json.loads(h.TRACK_FILE.read_text())

        # 尝试安装一个坏包（无 frontmatter）→ 应回滚
        bad_dir = tmp_path / "bad-pack-2"
        bad_dir.mkdir()
        bd = bad_dir / "SKILLS" / "bad-skill"
        bd.mkdir(parents=True)
        (bd / "SKILL.md").write_text("# No frontmatter")
        bad_manifest = {
            "name": "bad-pack-2",
            "skills": [{"id": "bad-skill", "path": "SKILLS/bad-skill/SKILL.md", "description": "Bad"}],
        }
        bad_pack = CapPack(
            name="bad-pack-2", version="1.0.0", pack_dir=bad_dir,
            manifest=bad_manifest,
            skills=[CapPackSkill(id="bad-skill", path="SKILLS/bad-skill/SKILL.md")],
        )
        result = adapter.install(bad_pack)
        assert result.success is False
        # 之前的 survivor 包不受影响
        tracked = json.loads(h.TRACK_FILE.read_text())
        assert "survivor" in tracked
        assert "bad-pack-2" not in tracked

    def test_uninstall_nonexistent(self, adapter: HermesAdapter):
        """卸载不存在的包返回错误"""
        result = adapter.uninstall("does-not-exist-12345")
        assert result.success is False
        assert any("未安装" in e for e in result.errors)
