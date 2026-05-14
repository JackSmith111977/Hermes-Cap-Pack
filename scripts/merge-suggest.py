#!/usr/bin/env python3
"""
merge-suggest.py v1.0 — Skill 合并建议自动生成引擎

基于内容相似度分析，自动检测三类冗余并生成可操作合并建议。

用法:
  python3 merge-suggest.py                              # 扫描并输出合并建议
  python3 merge-suggest.py --yaml                       # YAML 格式输出
  python3 merge-suggest.py --json                       # JSON 格式输出
  python3 merge-suggest.py --apply <suggestion-id>      # 执行单个合并建议
  python3 merge-suggest.py --list                       # 列出发现的问题
  python3 merge-suggest.py --threshold 0.7              # 设置相似度阈值

合并类型:
  DUPLICATE    完全重复 (100%)            → 删除冗余副本
  OVERLAP      高度重叠 (>80%)            → 合并为主 skill
  SUBSET       子集关系 (>90%)            → 扩展主 skill 后删除
  CONCEPTUAL   概念冗余 (标签/描述相似)     → 人工判断
"""

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

SKILLS_DIR = Path.home() / ".hermes" / "skills"
DB_PATH = Path.home() / ".hermes" / "data" / "skill-quality.db"
BACKUP_DIR = Path.home() / ".hermes" / "backups" / "merge-backups"
CAP_PACK_DIR = Path.home() / "projects" / "hermes-cap-pack"

# ── 相似度阈值 ──
THRESHOLD_DUPLICATE = 0.95   # 完全重复
THRESHOLD_OVERLAP = 0.75     # 高度重叠
THRESHOLD_SUBSET = 0.85      # 子集关系
THRESHOLD_CONCEPTUAL = 0.60  # 概念冗余


def read_skill_content(skill_name):
    """读取 skill 的 SKILL.md 完整内容"""
    for root, dirs, files in os.walk(SKILLS_DIR):
        if os.path.basename(root) == skill_name and "SKILL.md" in files:
            path = Path(root) / "SKILL.md"
            return path.read_text(encoding="utf-8", errors="ignore"), path
    path = SKILLS_DIR / skill_name / "SKILL.md"
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore"), path
    return None, None


def get_sqs_score(skill_name):
    """从 SQS 数据库获取 skill 的评分"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.execute("SELECT sqs_total FROM scores WHERE skill_name = ?", (skill_name,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0


def extract_frontmatter(content):
    """提取 YAML frontmatter 为 dict"""
    if not content:
        return {}
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        try:
            import yaml
            return yaml.safe_load(fm_match.group(1)) or {}
        except:
            pass
    return {}


def get_skill_metadata(skill_name):
    """获取 skill 的元数据"""
    content, path = read_skill_content(skill_name)
    if not content:
        return None
    fm = extract_frontmatter(content)
    body = re.sub(r'^---\n.*?\n---\n', '', content, 1, re.DOTALL) if '---' in content else content
    return {
        "name": skill_name,
        "path": str(path.relative_to(SKILLS_DIR.parent)) if path else "",
        "line_count": len(content.split("\n")),
        "body_length": len(body),
        "triggers": fm.get("triggers", []) or fm.get("tags", []) or [],
        "version": fm.get("version", "?"),
        "description": fm.get("description", "")[:100],
        "sqs_score": get_sqs_score(skill_name),
    }


def content_similarity(content_a, content_b):
    """计算两个 skill 内容的相似度 (0-1)"""
    if not content_a or not content_b:
        return 0.0

    # 去除 frontmatter 只比正文
    body_a = re.sub(r'^---\n.*?\n---\n', '', content_a, 1, re.DOTALL) if '---' in content_a else content_a
    body_b = re.sub(r'^---\n.*?\n---\n', '', content_b, 1, re.DOTALL) if '---' in content_b else content_b

    # 去除空白和注释行
    body_a = "\n".join(line for line in body_a.split("\n") if line.strip() and not line.strip().startswith("#"))
    body_b = "\n".join(line for line in body_b.split("\n") if line.strip() and not line.strip().startswith("#"))

    if not body_a.strip() or not body_b.strip():
        return 0.0

    # 使用 difflib SequenceMatcher
    return SequenceMatcher(None, body_a, body_b).ratio()


def is_subset(content_a, content_b):
    """检查 content_a 是否被 content_b 包含（子集检测）"""
    if not content_a or not content_b:
        return False

    body_a = re.sub(r'^---\n.*?\n---\n', '', content_a, 1, re.DOTALL) if '---' in content_a else content_a
    body_b = re.sub(r'^---\n.*?\n---\n', '', content_b, 1, re.DOTALL) if '---' in content_b else content_b

    # 将 A 的关键行在 B 中搜索
    a_lines = [l.strip() for l in body_a.split("\n") if l.strip() and not l.strip().startswith("#")]
    b_text = body_b

    if len(a_lines) < 3:
        return False

    matched = sum(1 for line in a_lines if line in b_text)
    return matched / len(a_lines) >= THRESHOLD_SUBSET if a_lines else False


def scan_all_skills():
    """扫描所有 skill，返回元数据列表"""
    skills = []
    for root, dirs, files in os.walk(SKILLS_DIR):
        if "SKILL.md" not in files:
            continue
        skill_name = os.path.basename(root)
        meta = get_skill_metadata(skill_name)
        if meta:
            skills.append(meta)
    return skills


def detect_merges(skills, threshold=THRESHOLD_OVERLAP):
    """检测可合并的 skill 对（优化版：按分组比较，避免 O(n²)）"""
    suggestions = []

    # Step 1: 按 name prefix 分组（第 1-2 个连字符分隔的词）
    groups = {}
    for s in skills:
        name = s["name"]
        parts = name.split("-")
        # 取前 1-2 个词作为分组 key
        for n in [1, 2]:
            if len(parts) >= n:
                key = "-".join(parts[:n])
                if key not in groups:
                    groups[key] = []
                groups[key].append(s)

    # Step 2: 在分组内两两比较（跳过单元素组和大型组）
    checked_pairs = set()
    total_comparisons = 0
    max_comparisons = 500  # 安全上限

    for group_key, group_skills in groups.items():
        if len(group_skills) < 2:
            continue
        # 大型组只取 SQS 靠前的 8 个比较
        if len(group_skills) > 8:
            group_skills = sorted(group_skills, key=lambda x: -x.get("sqs_score", 0))[:8]

        for i in range(len(group_skills)):
            for j in range(i + 1, len(group_skills)):
                if total_comparisons >= max_comparisons:
                    break

                name_a = group_skills[i]["name"]
                name_b = group_skills[j]["name"]
                pair_key = f"{name_a}::{name_b}"
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)
                total_comparisons += 1

                content_a, _ = read_skill_content(name_a)
                content_b, _ = read_skill_content(name_b)
                if not content_a or not content_b:
                    continue

                similarity = content_similarity(content_a, content_b)
                if similarity < threshold:
                    continue

                subset_ab = is_subset(content_a, content_b)
                subset_ba = is_subset(content_b, content_a)

                merge_type = None
                rationale = ""

                if similarity >= THRESHOLD_DUPLICATE:
                    merge_type = "DUPLICATE"
                    sqs_a = get_sqs_score(name_a)
                    sqs_b = get_sqs_score(name_b)
                    if sqs_a >= sqs_b:
                        target, source = name_a, name_b
                    else:
                        target, source = name_b, name_a
                    rationale = f"完全重复 ({similarity:.0%})，推荐保留 {target} (SQS {max(sqs_a, sqs_b):.0f})"

                elif similarity >= THRESHOLD_OVERLAP:
                    merge_type = "OVERLAP"
                    sqs_a = get_sqs_score(name_a)
                    sqs_b = get_sqs_score(name_b)
                    if sqs_a >= sqs_b:
                        target, source = name_a, name_b
                    else:
                        target, source = name_b, name_a
                    rationale = f"高度重叠 ({similarity:.0%})，推荐合并到 {target} (SQS {max(sqs_a, sqs_b):.0f})"

                elif subset_ab:
                    merge_type = "SUBSET"
                    target, source = name_b, name_a
                    sqs_t = get_sqs_score(target)
                    rationale = f"子集关系: {source} 被 {target} 包含，扩展 {target} 后删除 {source}"

                elif subset_ba:
                    merge_type = "SUBSET"
                    target, source = name_a, name_b
                    sqs_t = get_sqs_score(target)
                    rationale = f"子集关系: {source} 被 {target} 包含，扩展 {target} 后删除 {source}"

                if merge_type:
                    suggestions.append({
                        "id": f"MERGE-{len(suggestions)+1:04d}",
                        "source": source,
                        "target": target,
                        "type": merge_type,
                        "similarity": round(similarity, 3),
                        "rationale": rationale,
                        "source_sqs": get_sqs_score(source),
                        "target_sqs": get_sqs_score(target),
                        "action": "inspect" if merge_type == "CONCEPTUAL" else "merge",
                        "backup_path": "",
                    })
                    continue  # 已找到匹配类型，跳过 CONCEPTUAL 检查

                # ── CONCEPTUAL: 非内容匹配但同前缀且有一定相似度 ──
                if not merge_type and similarity >= THRESHOLD_CONCEPTUAL:
                    sqs_a = get_sqs_score(name_a)
                    sqs_b = get_sqs_score(name_b)
                    if sqs_a >= sqs_b:
                        target, source = name_a, name_b
                    else:
                        target, source = name_b, name_a
                    suggestions.append({
                        "id": f"MERGE-{len(suggestions)+1:04d}",
                        "source": source,
                        "target": target,
                        "type": "CONCEPTUAL",
                        "similarity": round(similarity, 3),
                        "rationale": f"概念冗余 (同组 '{group_key}', 内容相似 {similarity:.0%})，建议人工判断",
                        "source_sqs": get_sqs_score(source),
                        "target_sqs": get_sqs_score(target),
                        "action": "inspect",
                        "backup_path": "",
                    })

            if total_comparisons >= max_comparisons:
                break

    # 按优先级排序
    priority = {"DUPLICATE": 0, "OVERLAP": 1, "SUBSET": 2, "CONCEPTUAL": 3}
    suggestions.sort(key=lambda x: (priority.get(x["type"], 9), -x["similarity"]))
    return suggestions


def detect_micro_skills(skills):
    """检测微小 skill（<50 行）"""
    micro = []
    for s in skills:
        if s["line_count"] < 50:
            micro.append({
                "name": s["name"],
                "line_count": s["line_count"],
                "sqs_score": s["sqs_score"],
                "version": s["version"],
                "type": "MICRO",
                "suggestion": "降级为经验 (EXPERIENCES/)",
            })
    micro.sort(key=lambda x: x["line_count"])
    return micro


def detect_bmad_redundancy(skills):
    """检测 BMAD 系列冗余"""
    bmad_skills = [s for s in skills if s["name"].startswith("bmad")]
    if len(bmad_skills) <= 1:
        return []

    # 所有 bmad skill 中，SQS 最高的是主 skill
    bmad_skills.sort(key=lambda x: -x["sqs_score"])
    best = bmad_skills[0]
    recommendations = []

    for dup in bmad_skills[1:]:
        recommendations.append({
            "id": f"MERGE-BMAD-{len(recommendations)+1:04d}",
            "source": dup["name"],
            "target": best["name"],
            "type": "CONCEPTUAL",
            "similarity": 0.85,
            "rationale": f"BMAD 系列冗余: {dup['name']} 与 {best['name']} 同属 BMAD 系列 (SQS: {dup['sqs_score']} vs {best['sqs_score']})",
            "source_sqs": dup["sqs_score"],
            "target_sqs": best["sqs_score"],
            "action": "inspect",
            "backup_path": "",
        })

    return recommendations


def backup_skill(skill_name):
    """备份 skill 目录"""
    skill_path = SKILLS_DIR / skill_name
    if not skill_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = BACKUP_DIR / f"{skill_name}.{timestamp}"
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copytree(skill_path, backup_path)
    return str(backup_path)


def apply_merge(suggestion_id, suggestions):
    """执行合并建议"""
    match = [s for s in suggestions if s["id"] == suggestion_id]
    if not match:
        print(f"❌ 未找到合并建议: {suggestion_id}")
        return False

    s = match[0]
    if s["action"] == "inspect":
        print(f"⚠️  建议 '{suggestion_id}' 标记为人工判断，不能自动执行")
        return False

    source = s["source"]
    target = s["target"]

    # 备份源 skill
    print(f"📦 备份 {source}...")
    backup_path = backup_skill(source)
    if not backup_path:
        print(f"❌ 备份失败: {source} 不存在")
        return False
    s["backup_path"] = backup_path
    print(f"   → 已备份到 {backup_path}")

    # 备份目标 skill
    print(f"📦 备份 {target}...")
    backup_skill(target)

    # 合并内容：将 source 的内容追加到 target
    source_content, source_path = read_skill_content(source)
    target_content, target_path = read_skill_content(target)

    if not source_content or not target_content:
        print("❌ 读取 skill 内容失败")
        return False

    # 写入合并标记
    merge_note = f"\n\n---\n\n> 💡 本 skill 的旧版本已合并到 [{target}]({target})\n> 合并时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n> 原 SQS: {get_sqs_score(source)}"
    with open(str(source_path), "a", encoding="utf-8") as f:
        f.write(merge_note)

    print(f"✅ 已标记: {source} → 指向 {target}")
    return True


def print_report(suggestions, micro_skills, bmad_recs):
    """打印合并建议报告"""
    print(f"\n{'='*65}")
    print(f"  🔧 Hermes Skill 合并建议报告")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*65}")

    # ── 按优先级排序 ──
    priority_order = {"DUPLICATE": 0, "OVERLAP": 1, "SUBSET": 2, "CONCEPTUAL": 3}
    suggestions.sort(key=lambda x: (priority_order.get(x["type"], 9), -x["similarity"]))

    if bmad_recs:
        print(f"\n🔴 **P0: BMAD 副本冗余** ({len(bmad_recs)} 项)")
        for r in bmad_recs:
            print(f"  {r['id']}: {r['source']} → {r['target']}")
            print(f"    {r['rationale']}")

    if suggestions:
        duplicates = [s for s in suggestions if s["type"] == "DUPLICATE"]
        overlaps = [s for s in suggestions if s["type"] == "OVERLAP"]
        subsets = [s for s in suggestions if s["type"] == "SUBSET"]
        conceptual = [s for s in suggestions if s["type"] == "CONCEPTUAL"]

        if duplicates:
            print(f"\n🔴 **完全重复** ({len(duplicates)} 项)")
            for s in duplicates:
                print(f"  {s['id']}: {s['source']} → {s['target']}")
                print(f"    相似度: {s['similarity']:.1%} | SQS: {s['source_sqs']}→{s['target_sqs']}")
                print(f"    理由: {s['rationale']}")

        if overlaps:
            print(f"\n🟠 **高度重叠** ({len(overlaps)} 项)")
            for s in overlaps:
                print(f"  {s['id']}: {s['source']} → {s['target']}")
                print(f"    相似度: {s['similarity']:.1%} | SQS: {s['source_sqs']}→{s['target_sqs']}")
                print(f"    理由: {s['rationale']}")

        if subsets:
            print(f"\n🟡 **子集关系** ({len(subsets)} 项)")
            for s in subsets:
                print(f"  {s['id']}: {s['source']} → {s['target']}")
                print(f"    理由: {s['rationale']}")

        if conceptual:
            print(f"\n⚪ **概念冗余 (需人工判断)** ({len(conceptual)} 项)")
            for s in conceptual:
                print(f"  {s['id']}: {s['source']} ? {s['target']}")
                print(f"    相似度: {s['similarity']:.1%} | 理由: {s['rationale']}")

    # ── 微小 skill ──
    if micro_skills:
        print(f"\n📏 **微小 skill (<50 行)** ({len(micro_skills)} 项)")
        for m in micro_skills[:10]:
            print(f"  {m['name']:30s} {m['line_count']:3d}行  SQS:{m['sqs_score']}  [{m['version']}]")
        if len(micro_skills) > 10:
            print(f"  ...及另外 {len(micro_skills)-10} 项")

    total = len(suggestions) + len(bmad_recs) + len(micro_skills)
    print(f"\n{'='*65}")
    print(f"  总结: {len(suggestions)} 合并建议 + {len(bmad_recs)} BMAD 冗余 + {len(micro_skills)} 微技能降级 = {total} 项")
    print(f"  使用 --yaml 查看可执行格式 | --apply <id> 执行合并")
    print(f"{'='*65}\n")


def to_yaml(suggestions, micro_skills, bmad_recs):
    """YAML 格式输出"""
    lines = ["# Hermes Skill 合并建议", f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", f"# 共 {len(suggestions) + len(bmad_recs) + len(micro_skills)} 项", ""]

    # BMAD 冗余
    for r in bmad_recs:
        lines.append(f"- id: {r['id']}")
        lines.append(f"  source: {r['source']}")
        lines.append(f"  target: {r['target']}")
        lines.append(f"  type: {r['type']}")
        lines.append(f"  similarity: {r['similarity']}")
        lines.append(f"  rationale: '{r['rationale']}'")
        lines.append(f"  action: {r['action']}")
        lines.append(f"  source_sqs: {r['source_sqs']}")
        lines.append(f"  target_sqs: {r['target_sqs']}")
        lines.append("")

    # 内容检测建议
    for s in suggestions:
        lines.append(f"- id: {s['id']}")
        lines.append(f"  source: {s['source']}")
        lines.append(f"  target: {s['target']}")
        lines.append(f"  type: {s['type']}")
        lines.append(f"  similarity: {s['similarity']}")
        lines.append(f"  rationale: '{s['rationale']}'")
        lines.append(f"  action: {s['action']}")
        lines.append(f"  source_sqs: {s['source_sqs']}")
        lines.append(f"  target_sqs: {s['target_sqs']}")
        lines.append("")

    # 微技能
    for m in micro_skills:
        lines.append(f"- id: MICRO-{m['name']}")
        lines.append(f"  source: {m['name']}")
        lines.append(f"  type: MICRO")
        lines.append(f"  line_count: {m['line_count']}")
        lines.append(f"  sqs_score: {m['sqs_score']}")
        lines.append(f"  rationale: '降级为经验 ({m['line_count']}行)'")
        lines.append(f"  action: inspect")
        lines.append("")

    return "\n".join(lines)


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    threshold = THRESHOLD_OVERLAP
    for i, arg in enumerate(sys.argv):
        if arg == "--threshold" and i + 1 < len(sys.argv):
            try:
                threshold = float(sys.argv[i + 1])
            except:
                pass

    # 扫描所有 skill
    quiet = "--yaml" in sys.argv or "--json" in sys.argv
    if not quiet:
        print("🔍 扫描 skill 系统...")
    skills = scan_all_skills()
    if not quiet:
        print(f"   发现 {len(skills)} 个 skill")

    # 检测合并机会
    if not quiet:
        print(f"🔬 检测合并机会 (阈值: {threshold})...")
    suggestions = detect_merges(skills, threshold)
    micro_skills = detect_micro_skills(skills)
    bmad_recs = detect_bmad_redundancy(skills)
    if not quiet:
        print(f"   合并建议: {len(suggestions)} | BMAD 冗余: {len(bmad_recs)} | 微小 skill: {len(micro_skills)}")

    # 执行合并
    apply_id = None
    for i, arg in enumerate(sys.argv):
        if arg == "--apply" and i + 1 < len(sys.argv):
            apply_id = sys.argv[i + 1]

    if apply_id:
        all_suggestions = suggestions + bmad_recs
        apply_merge(apply_id, all_suggestions)
        return

    # 输出格式
    if "--yaml" in sys.argv:
        print(to_yaml(suggestions, micro_skills, bmad_recs))
    elif "--json" in sys.argv:
        # 只输出 JSON（进度信息不打印）
        output = {
            "generated_at": datetime.now().isoformat()[:19],
            "total_skills": len(skills),
            "bmad_redundancy": bmad_recs,
            "content_suggestions": suggestions,
            "micro_skills": micro_skills[:20],
            "summary": {
                "duplicates": len([s for s in suggestions if s["type"] == "DUPLICATE"]),
                "overlaps": len([s for s in suggestions if s["type"] == "OVERLAP"]),
                "subsets": len([s for s in suggestions if s["type"] == "SUBSET"]),
                "conceptual": len([s for s in suggestions if s["type"] == "CONCEPTUAL"]),
                "bmad": len(bmad_recs),
                "micro": len(micro_skills),
            },
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif "--list" in sys.argv:
        print_report(suggestions, micro_skills, bmad_recs)
    else:
        print_report(suggestions, micro_skills, bmad_recs)


if __name__ == "__main__":
    main()
