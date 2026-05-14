#!/usr/bin/env python3
"""
aggregate-sqs.py — 按能力包分组聚合 SQS 评分数据

用法:
  # 生成全量 SQS 扫描
  python3 scripts/skill-quality-score.py --audit --json > reports/chi-baseline.json
  
  # 按 pack 聚合
  python3 scripts/aggregate-sqs.py \\
    --input reports/chi-baseline.json \\
    --output reports/chi-by-pack.json
  
  # 优先级排序（标注健康状态）
  python3 scripts/aggregate-sqs.py --prioritize \\
    --input reports/chi-by-pack.json \\
    --output reports/chi-priority-list.md
  
  # 管道模式（一步到位）
  python3 scripts/skill-quality-score.py --audit --json \\
    | python3 scripts/aggregate-sqs.py --output reports/chi-by-pack.json
"""

import json, sys, re, os
from collections import defaultdict

PACK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "packs")


def extract_json(text):
    """从混合输出中提取 JSON 数组（在最后面）"""
    # 尝试从末尾找 JSON 数组
    lines = text.strip().split('\n')
    # 从后往前找，找到以 [ 开头的行
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith('['):
            json_text = '\n'.join(lines[i:])
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                continue
    # 如果末尾找不到，尝试解析整个文本
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    return None


def get_pack_for_skill(skill_name):
    """从 skill 名称推测所属能力包"""
    # 读取 packs/*/SKILLS/ 目录结构
    if not os.path.isdir(PACK_DIR):
        return "uncategorized"
    for pack in sorted(os.listdir(PACK_DIR)):
        pack_skills = os.path.join(PACK_DIR, pack, "SKILLS")
        if os.path.isdir(pack_skills):
            for skill_dir in os.listdir(pack_skills):
                if skill_dir == skill_name:
                    return pack
    return "uncategorized"


def aggregate(skills):
    """按 pack 分组聚合 SQS 评分"""
    packs = defaultdict(list)
    pack_names = {}
    
    for s in skills:
        name = s.get("skill", s.get("name", "unknown"))
        pack = s.get("pack", s.get("module", get_pack_for_skill(name)))
        packs[pack].append(s)
        
        # Try to read pack name from cap-pack.yaml
        if pack not in pack_names:
            yaml_path = os.path.join(PACK_DIR, pack, "cap-pack.yaml")
            if os.path.isfile(yaml_path):
                with open(yaml_path) as f:
                    for line in f:
                        if line.startswith("name:"):
                            pack_names[pack] = line.split(":", 1)[1].strip()
                            break
        
    result = {}
    for pack, skills_list in sorted(packs.items()):
        scores = [s.get("sqs_total", s.get("score", 0)) for s in skills_list]
        avg_sqs = round(sum(scores) / len(scores), 2) if scores else 0
        
        # 评分分布
        dist = {"🟢 excellent": 0, "🟡 good": 0, "🟠 needs_work": 0, "🔴 poor": 0}
        for sc in scores:
            if sc >= 80: dist["🟢 excellent"] += 1
            elif sc >= 60: dist["🟡 good"] += 1
            elif sc >= 40: dist["🟠 needs_work"] += 1
            else: dist["🔴 poor"] += 1
        
        result[pack] = {
            "pack_name": pack_names.get(pack, pack),
            "skill_count": len(skills_list),
            "avg_sqs": avg_sqs,
            "min_sqs": min(scores) if scores else 0,
            "max_sqs": max(scores) if scores else 0,
            "distribution": dist,
            "skills": [{
                "name": s.get("skill", s.get("name", "?")),
                "sqs": s.get("sqs_total", s.get("score", 0)),
                "level": s.get("level", ""),
                "dimensions": s.get("dimensions", {})
            } for s in sorted(skills_list, key=lambda x: x.get("sqs_total", x.get("score", 0)), reverse=True)]
        }
    
    return result


def generate_priority_list(aggregated):
    """生成按优先级排序的 Markdown 报告"""
    # 计算全局 CHI
    all_scores = []
    for pack, data in aggregated.items():
        for skill in data["skills"]:
            all_scores.append(skill["sqs"])
    chi = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
    
    # 按平均分排序
    sorted_packs = sorted(aggregated.items(), key=lambda x: x[1]["avg_sqs"])
    
    lines = []
    lines.append("# 🏥 能力包健康度优先级排序\n")
    lines.append(f"> **生成**: 2026-05-14 · **全局 CHI**: **{chi}**\n")
    lines.append("---\n")
    lines.append("## 按 SQS 均分升序（最低分包优先）\n")
    lines.append("| 排名 | 能力包 | Skills | SQS 均分 | 最低分 | 最高分 | 健康状态 |")
    lines.append("|:----:|:-------|:------:|:--------:|:------:|:------:|:---------|")
    
    for rank, (pack, data) in enumerate(sorted_packs, 1):
        avg = data["avg_sqs"]
        if avg >= 80: status = "🟢"
        elif avg >= 60: status = "🟡"
        elif avg >= 40: status = "🟠"
        else: status = "🔴"
        
        marker = " ⬅️ **优先处理**" if rank <= 3 else ""
        lines.append(f"| {rank} | {pack} | {data['skill_count']} | {avg} | {data['min_sqs']} | {data['max_sqs']} | {status}{marker} |")
    
    lines.append("")
    lines.append("## 评分分布\n")
    lines.append("| 能力包 | 🟢 ≥80 | 🟡 60-79 | 🟠 40-59 | 🔴 <40 |")
    lines.append("|:-------|:-----:|:--------:|:--------:|:------:|")
    
    for pack, data in sorted_packs:
        d = data["distribution"]
        lines.append(f"| {pack} | {d['🟢 excellent']} | {d['🟡 good']} | {d['🟠 needs_work']} | {d['🔴 poor']} |")
    
    lines.append("")
    lines.append("---")
    lines.append(f"**前 3 最低分包**: {', '.join(sorted_packs[i][0] for i in range(min(3, len(sorted_packs))))}")
    lines.append(f"**目标 Phase 1 优先处理**: {sorted_packs[0][0] if sorted_packs else 'N/A'}")
    
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    
    # Parse args
    input_file = None
    output_file = None
    prioritize = False
    
    for i, arg in enumerate(args):
        if arg == "--input" and i + 1 < len(args):
            input_file = args[i + 1]
        elif arg == "--output" and i + 1 < len(args):
            output_file = args[i + 1]
        elif arg == "--prioritize":
            prioritize = True
        elif arg == "--help":
            print(__doc__)
            return
    
    # Read input
    if input_file:
        with open(input_file) as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    
    # Parse JSON
    if text.strip().startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = extract_json(text)
    else:
        data = extract_json(text)
    
    if data is None:
        print("❌ 无法解析 JSON 输入", file=sys.stderr)
        sys.exit(1)
    
    # Detect format: list of skills, or dict of packs (pre-aggregated)
    if isinstance(data, dict) and all(isinstance(v, dict) and "avg_sqs" in v for v in data.values()):
        # Already aggregated
        aggregated = data
        print(f"📦 已聚合数据，共 {len(aggregated)} 个能力包", file=sys.stderr)
    else:
        skills = data if isinstance(data, list) else data.get("skills", data.get("results", []))
        if not skills:
            print(f"❌ 输入数据中没有 skill 列表 (data type: {type(data).__name__})", file=sys.stderr)
            sys.exit(1)
        print(f"📊 扫描到 {len(skills)} 个 skill", file=sys.stderr)
        aggregated = aggregate(skills)
        print(f"📦 归类到 {len(aggregated)} 个能力包", file=sys.stderr)
    
    if prioritize:
        output = generate_priority_list(aggregated)
    else:
        output = json.dumps(aggregated, ensure_ascii=False, indent=2)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"✅ 已写入 {output_file}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
