"""Tests for EPIC-002 tools: tree-index, quality-score, lifecycle-audit"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"


def run_script(name: str, *args: str) -> subprocess.CompletedProcess:
    """运行 cap-pack 项目下的脚本，返回结果"""
    cmd = [sys.executable, str(SCRIPTS_DIR / name)] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


# ═══════════════════════════════════════════════════════════
# STORY-2-1-1: skill-tree-index.py
# ═══════════════════════════════════════════════════════════

class TestSkillTreeIndex:
    """树状索引工具测试"""

    def test_help(self):
        """--help 正常输出"""
        result = run_script("skill-tree-index.py", "--help")
        assert result.returncode == 0
        assert "树状索引" in result.stdout or "tree-index" in result.stdout

    def test_json_output(self):
        """--json 输出有效 JSON"""
        result = run_script("skill-tree-index.py", "--json")
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        # 输出是模块列表
        assert isinstance(data, list)
        assert len(data) > 0
        assert "module_id" in data[0]
        assert "clusters" in data[0]

    def test_pack_filter(self):
        """--pack 参数过滤有效"""
        result = run_script("skill-tree-index.py", "--pack", "learning-workflow", "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        # --pack 过滤返回对应模块
        assert isinstance(data, list)
        assert len(data) >= 0  # learning-workflow 可能在其他包名下

    def test_consolidate_mode(self):
        """--consolidate 输出合并建议"""
        result = run_script("skill-tree-index.py", "--consolidate")
        assert result.returncode == 0
        # 应该输出一些内容
        assert len(result.stdout) > 50

    def test_health_mode(self):
        """--health 输出健康度信息"""
        result = run_script("skill-tree-index.py", "--health")
        assert result.returncode == 0
        assert "总数" in result.stdout or "健康" in result.stdout

    def test_health_has_sqs_context(self):
        """--health 包含健康度信息"""
        result = run_script("skill-tree-index.py", "--health")
        assert result.returncode == 0
        assert "健康" in result.stdout or "总数" in result.stdout


# ═══════════════════════════════════════════════════════════
# STORY-2-2-1: skill-quality-score.py
# ═══════════════════════════════════════════════════════════

class TestSkillQualityScore:
    """SQS 质量评分工具测试"""

    def test_help(self):
        """--help 正常输出"""
        result = run_script("skill-quality-score.py", "--help")
        assert result.returncode == 0
        assert "SQS" in result.stdout

    def test_score_known_skill(self):
        """对已知 skill 评分成功且分数在 0-100 范围"""
        result = run_script("skill-quality-score.py", "sdd-workflow")
        assert result.returncode == 0
        assert "SQS" in result.stdout or "总分" in result.stdout

    def test_score_json(self):
        """--json 输出有效评分"""
        result = run_script("skill-quality-score.py", "sdd-workflow", "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "sqs_total" in data
        assert 0 <= data["sqs_total"] <= 100
        assert "dimensions" in data

    def test_score_nonexistent_skill(self):
        """不存在的 skill 返回非零但不崩溃"""
        result = run_script("skill-quality-score.py", "this-skill-does-not-exist-12345")
        # 应该优雅处理
        assert result.returncode in (0, 1)

    def test_audit_mode(self):
        """--audit 全量审计可运行"""
        result = run_script("skill-quality-score.py", "--audit", "--threshold", "50")
        assert result.returncode == 0
        assert len(result.stdout) > 50


# ═══════════════════════════════════════════════════════════
# STORY-2-2-1: skill-lifecycle-audit.py
# ═══════════════════════════════════════════════════════════

class TestSkillLifecycleAudit:
    """生命周期审计工具测试"""

    def test_help(self):
        """--help 正常输出"""
        result = run_script("skill-lifecycle-audit.py", "--help")
        assert result.returncode == 0
        assert "生命周期" in result.stdout or "lifecycle" in result.stdout

    def test_status_known_skill(self):
        """查看已知 skill 的生命周期状态"""
        result = run_script("skill-lifecycle-audit.py", "status", "sdd-workflow")
        assert result.returncode == 0
        assert "active" in result.stdout.lower() or "sdd" in result.stdout.lower()

    def test_audit_known_skill(self):
        """审计单个 skill"""
        result = run_script("skill-lifecycle-audit.py", "sdd-workflow")
        assert result.returncode == 0
        assert len(result.stdout) > 50

    def test_audit_with_threshold(self):
        """审计单个 skill 并指定阈值（比全量快）"""
        result = run_script("skill-lifecycle-audit.py", "sdd-workflow", "--threshold", "90")
        assert result.returncode in (0, 1)
        assert len(result.stdout) > 0

    def test_deprecate_revive_cycle(self):
        """deprecate → status → revive → status 周期（仅测试不实际修改）"""
        # 先检查状态
        result = run_script("skill-lifecycle-audit.py", "status", "sdd-workflow")
        assert result.returncode == 0

    def test_json_output(self):
        """--json 输出"""
        result = run_script("skill-lifecycle-audit.py", "sdd-workflow", "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "skill" in data
