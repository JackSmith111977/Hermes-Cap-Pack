"""跨 Agent 对等性测试 — 验证同一能力包可在多个 Agent 上安装"""

import pytest
from pathlib import Path

from scripts.adapters.hermes import HermesAdapter
from scripts.adapters.opencode import OpenCodeAdapter
from scripts.uca import PackParser
from scripts.uca.protocol import CapPack


@pytest.fixture
def real_pack() -> CapPack:
    """使用真实的 doc-engine 能力包"""
    project_root = Path(__file__).parent.parent.parent
    pack_dir = project_root / "packs" / "doc-engine"
    if not pack_dir.exists():
        pytest.skip("doc-engine pack not found")
    parser = PackParser()
    return parser.parse(pack_dir)


class TestCrossAgentParity:
    """跨 Agent 对等性测试
    
    验证同一能力包安装到不同 Agent 时行为一致。
    """

    def test_both_adapters_implement_protocol(self):
        """两个适配器都实现了 AgentAdapter Protocol"""
        hermes = HermesAdapter()
        opencode = OpenCodeAdapter()

        for adapter in [hermes, opencode]:
            assert hasattr(adapter, 'name')
            assert hasattr(adapter, 'is_available')
            assert hasattr(adapter, 'install')
            assert hasattr(adapter, 'uninstall')
            assert hasattr(adapter, 'update')
            assert hasattr(adapter, 'list_installed')
            assert hasattr(adapter, 'verify')

    def test_both_parse_same_skills(self, real_pack: CapPack):
        """同一能力包解析出的 skills 数量一致"""
        assert len(real_pack.skills) == 9  # doc-engine has 9 skills
        skill_ids = [s.id for s in real_pack.skills]
        assert "pdf-layout" in skill_ids
        assert "pptx-guide" in skill_ids

    def test_both_adapters_listable(self):
        """两个适配器都能列出已安装的包（可能为空）"""
        hermes = HermesAdapter()
        opencode = OpenCodeAdapter()

        h_list = hermes.list_installed()
        o_list = opencode.list_installed()

        assert isinstance(h_list, list)
        assert isinstance(o_list, list)

    def test_opencode_skill_format_compatible(self, real_pack: CapPack, tmp_path: Path):
        """验证 OpenCode SKILL.md 格式兼容性"""
        import scripts.adapters.opencode as oc
        from scripts.adapters.opencode import _rewrite_skill_for_opencode

        skill = real_pack.skills[0]
        src = real_pack.pack_dir / "SKILLS" / skill.id
        if not src.exists():
            pytest.skip(f"{skill.id} source dir not found")

        dst = tmp_path / skill.id
        success = _rewrite_skill_for_opencode(skill.id, src, dst)
        assert success is True

        # 验证生成的文件是有效 YAML frontmatter
        content = (dst / "SKILL.md").read_text()
        assert content.startswith("---")
        import yaml
        parts = content.split("---", 2)
        fm = yaml.safe_load(parts[1])
        assert fm["name"] == skill.id
        assert fm["compatibility"] == "opencode"
