#!/usr/bin/env python3
"""
doc-engine 健康检查与量化测试脚本 v1.0
========================================
测量 6 个 KPI + 综合健康指数 (CHI)
可重复执行，用于 before/after 对比

用法:
  python3 health-check.py              # 全量检查
  python3 health-check.py --json       # JSON 输出（便于机器解析）
  python3 health-check.py --gate       # 门禁模式（exit 0/1）
"""

import json, sys, os, subprocess, math
from pathlib import Path

CAP_PACK = Path.home() / "projects" / "hermes-cap-pack"
SQS_SCRIPT = CAP_PACK / "scripts" / "skill-quality-score.py"
TREE_SCRIPT = CAP_PACK / "scripts" / "skill-tree-index.py"

# doc-engine 技能列表（Before 状态）
BEFORE_SKILLS = [
    "pdf-layout", "pdf-layout-reportlab", "pdf-layout-weasyprint",
    "pdf-pro-design", "pdf-render-comparison",
    "doc-design", "docx-guide", "html-guide", "html-presentation",
    "pptx-guide", "latex-guide", "markdown-guide", "epub-guide",
    "xlsx-guide", "readme-for-ai", "vision-qc-patterns", "nano-pdf"
]

def run_sqs(skill):
    """返回单个技能的 SQS 评分数据"""
    r = subprocess.run(
        ["python3", str(SQS_SCRIPT), skill, "--json"],
        capture_output=True, text=True, timeout=15, cwd=CAP_PACK
    )
    if r.returncode == 0 and r.stdout.strip():
        return json.loads(r.stdout)
    return None

def get_sqs_stats():
    """获取所有 doc-engine 技能的 SQS 数据"""
    scores = []
    versions = []
    s4_scores = []
    
    for skill in BEFORE_SKILLS:
        d = run_sqs(skill)
        if d:
            scores.append(d["sqs_total"])
            s4_scores.append(d["dimensions"]["S4_relations"])
            ver = d.get("version", "?")
            versions.append(ver if ver and ver != "?" else None)
    
    return scores, versions, s4_scores

def calc_chi(avg_sqs, low_rate, ver_rate, avg_s4, cluster_std, total):
    """综合健康指数计算"""
    chi = (
        (avg_sqs / 100) * 0.30 +
        (1 - low_rate) * 0.20 +
        (ver_rate) * 0.15 +
        (avg_s4 / 20) * 0.15 +
        max(0, 1 - cluster_std / 5) * 0.10 +
        max(0, 1 - abs(total - 10) / 20) * 0.10
    )
    return round(chi, 4)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="doc-engine 健康检查")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--gate", action="store_true", help="门禁模式 (exit 0/1)")
    args = parser.parse_args()
    
    print("🔬 doc-engine 健康检查")
    print("=" * 55)
    
    # 获取 SQS 数据
    scores, versions, s4_scores = get_sqs_stats()
    
    if not scores:
        print("❌ 无法获取 SQS 数据")
        sys.exit(1)
    
    # KPI-1: 平均 SQS
    avg_sqs = sum(scores) / len(scores)
    print(f"\n📊 KPI-1 平均 SQS:         {avg_sqs:.1f}/100  "
          f"{'🟢' if avg_sqs >= 75 else '🟡' if avg_sqs >= 60 else '🔴'}")
    
    # KPI-2: 低分率
    low_count = sum(1 for s in scores if s < 60)
    low_rate = low_count / len(scores)
    print(f"📊 KPI-2 低分率:           {low_count}/{len(scores)} ({low_rate*100:.0f}%)  "
          f"{'🟢' if low_count == 0 else '🟡' if low_rate < 0.2 else '🔴'}")
    
    # KPI-3: 版本完整率
    ver_count = sum(1 for v in versions if v is not None)
    ver_rate = ver_count / len(versions)
    print(f"📊 KPI-3 版本完整率:        {ver_count}/{len(versions)} ({ver_rate*100:.0f}%)  "
          f"{'🟢' if ver_rate == 1.0 else '🟡' if ver_rate >= 0.8 else '🔴'}")
    
    # KPI-4: 关联完整率
    avg_s4 = sum(s4_scores) / len(s4_scores)
    print(f"📊 KPI-4 关联完整率(S4):   {avg_s4:.1f}/20  "
          f"{'🟢' if avg_s4 >= 10 else '🟡' if avg_s4 >= 7 else '🔴'}")
    
    # KPI-5: 簇内聚度
    # 从树索引获取
    r = subprocess.run(
        ["python3", str(TREE_SCRIPT), "--pack", "doc-engine", "--json"],
        capture_output=True, text=True, timeout=30, cwd=CAP_PACK
    )
    if r.returncode == 0 and r.stdout.strip():
        tree_list = json.loads(r.stdout)
        # tree_list is a list of modules, find doc-engine
        doc_engine = {}
        for mod in tree_list:
            if mod.get("module_id") == "doc-engine":
                doc_engine = mod
                break
        clusters = doc_engine.get("clusters", [])
        cluster_sizes = [c.get("count", len(c.get("skills", []))) for c in clusters]
        cluster_count = len(cluster_sizes)
        cluster_std = statistics.stdev(cluster_sizes) if len(cluster_sizes) > 1 else 0
    else:
        cluster_count = 0
        cluster_std = 0
    
    print(f"📊 KPI-5 簇数:             {cluster_count} 簇 (标准差 {cluster_std:.1f})  "
          f"{'🟢' if cluster_std < 2 else '🟡' if cluster_std < 3 else '🔴'}")
    
    # KPI-6: 技能总数
    total = len(scores)
    print(f"📊 KPI-6 技能总数:         {total}  "
          f"{'🟢' if total <= 12 else '🟡' if total <= 15 else '🔴'}")
    
    # 综合健康指数
    chi = calc_chi(avg_sqs, low_rate, ver_rate, avg_s4, cluster_std, total)
    print(f"\n{'=' * 55}")
    
    chi_level = "🟢 优秀" if chi >= 0.85 else "🟡 良好" if chi >= 0.70 else "🟠 需改进" if chi >= 0.55 else "🔴 不合格"
    print(f"🏥 综合健康指数 (CHI):     {chi:.4f}  — {chi_level}")
    
    print(f"\n{'=' * 55}")
    print(f"目标: CHI ≥ 0.75  | 平均SQS ≥ 70 | 低分=0 | 版本完整=100%")
    
    if args.json:
        print(json.dumps({
            "kpi1_avg_sqs": round(avg_sqs, 1),
            "kpi2_low_rate": round(low_rate, 3),
            "kpi2_low_count": low_count,
            "kpi3_version_rate": round(ver_rate, 3),
            "kpi3_version_count": ver_count,
            "kpi4_avg_s4": round(avg_s4, 1),
            "kpi5_clusters": cluster_count,
            "kpi5_cluster_std": round(cluster_std, 1),
            "kpi6_total_skills": total,
            "chi": chi,
            "chi_level": chi_level.strip()
        }, ensure_ascii=False, indent=2))
    
    if args.gate:
        passes = (
            avg_sqs >= 70 and
            low_count == 0 and
            ver_rate >= 0.8 and
            chi >= 0.70
        )
        sys.exit(0 if passes else 1)

if __name__ == "__main__":
    import statistics
    main()
