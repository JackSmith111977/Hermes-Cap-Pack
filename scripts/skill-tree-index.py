#!/usr/bin/env python3
"""
skill-tree-index.py v1.1 — Hermes Skill 分层树状索引生成器 + CHI 健康仪表盘

基于 18 能力包模块 + skill 元数据扫描，生成三层树状索引：
  Layer 1: Capability Pack (领域层, 18 个)
  Layer 2: Skill Cluster    (功能层, ~60 个)
  Layer 3: Atomic Skill     (实现层, ~200 个)
    └── references/scripts/experiences (叶子节点)

同时检测:
  - 重复 skill（名称/内容相似）
  - 微小 skill（应降级为经验）
  - 路由型 skill（应被包索引吸收）
  - 未分类 skill

用法:
  python3 skill-tree-index.py                      # 生成全量树状索引
  python3 skill-tree-index.py --pack doc-engine     # 只看某个包
  python3 skill-tree-index.py --consolidate         # 显示合并建议
  python3 skill-tree-index.py --json               # JSON 输出
  python3 skill-tree-index.py --health             # 系统健康度速览
  python3 skill-tree-index.py --sra                # SRA 兼容格式
  python3 skill-tree-index.py --dashboard          # CHI 健康仪表盘 (HTML)
    --input <chi-by-pack.json>                     #  聚合数据输入
    --output <chi-dashboard.html>                  #  HTML 输出
"""

import os, sys, json, re, yaml
from pathlib import Path
from collections import defaultdict

SKILLS_DIR = Path.home() / ".hermes" / "skills"
CAP_PACK_DIR = Path.home() / "projects" / "hermes-cap-pack"


# ===== 18 模块定义（从 README 提取） =====

MODULES = {
    "knowledge-base":       {"name": "知识库系统",     "emoji": "📚"},
    "learning-engine":      {"name": "学习引擎",       "emoji": "🧠"},
    "doc-engine":           {"name": "文档生成",       "emoji": "📄"},
    "developer-workflow":   {"name": "开发工作流",     "emoji": "💻"},
    "security-audit":       {"name": "安全审计",       "emoji": "🔒"},
    "quality-assurance":    {"name": "质量保障",       "emoji": "✅"},
    "devops-monitor":       {"name": "运维监控",       "emoji": "🔧"},
    "network-proxy":        {"name": "网络代理",       "emoji": "🌐"},
    "messaging":            {"name": "消息平台",       "emoji": "💬"},
    "agent-orchestration":  {"name": "Agent 协作",    "emoji": "🤖"},
    "mcp-integration":      {"name": "MCP 集成",      "emoji": "🔌"},
    "financial-analysis":   {"name": "金融分析",       "emoji": "📊"},
    "creative-design":      {"name": "创意设计",       "emoji": "🎨"},
    "media-processing":     {"name": "音视频媒体",     "emoji": "🎵"},
    "github-ecosystem":     {"name": "GitHub 生态",   "emoji": "🐙"},
    "news-research":        {"name": "新闻研究",       "emoji": "📰"},
    "metacognition":        {"name": "元认知系统",     "emoji": "🪞"},
    "social-gaming":        {"name": "社交娱乐",       "emoji": "🎮"},
}

EXTENSION_SLOTS = {
    "hermes-new-features": "Hermes 框架新功能",
    "custom-plugin":       "第三方 Plugin",
    "future-domain":       "未来新领域",
}


# ===== Skill 分类映射规则 =====

# 基于 tags + 目录路径 + 名称的自动分类
CLASSIFICATION_RULES = [
    # 知识库
    (["knowledge", "precipitation", "routing", "llm-wiki", "file-classification"], "knowledge-base"),
    # 学习
    (["learning", "skill-creator", "deep-research", "night-study"], "learning-engine"),
    # 文档
    (["pdf", "pptx", "docx", "html-guide", "markdown", "latex", "epub", "doc-design", "readme-for-ai"], "doc-engine"),
    # 开发
    (["plan", "writing-plans", "sdd", "systematic-debugging", "tdd", "subagent", "spike", "git-advanced", "python-env", "patch-file"], "developer-workflow"),
    # 安全
    (["delete-safety", "security", "commit-quality", "sherlock", "1password", "godmode", "secret"], "security-audit"),
    # 质量
    (["qa-", "-qa-", "quality", "test", "testing", "review", "cranfield", "dogfood", "doc-alignment", "adversarial"], "quality-assurance"),
    # 运维
    (["linux-ops", "docker", "process-management", "system-health", "proxy-monitor", "cron", "webhook"], "devops-monitor"),
    # 网络
    (["clash", "proxy-finder", "web-access", "browser-automation", "web-ui"], "network-proxy"),
    # 消息
    (["feishu", "weixin", "email", "sms", "agentmail", "himalaya", "messaging", "broadcast"], "messaging"),
    # Agent 协作
    (["hermes-agent", "claude-code", "codex", "opencode", "blackbox", "bmad", "kanban", "delegate", "honcho", "deployment", "orchestrat"], "agent-orchestration"),
    # MCP
    (["mcp", "fastmcp", "mcporter", "sra"], "mcp-integration"),
    # 金融
    (["financial", "akshare", "stock", "analyst"], "financial-analysis"),
    # 创意
    (["architecture-diagram", "mermaid", "excalidraw", "p5js", "pixel-art", "ascii", "creativ", "design", "sketch", "claude-design", "songwriting"], "creative-design"),
    # 媒体
    (["tts", "speech", "audio", "song", "gif", "comfyui", "image-generation", "image-prompt", "video", "media"], "media-processing"),
    # GitHub
    (["github", "git-", "pull-request", "code-review", "release"], "github-ecosystem"),
    # 新闻
    (["news", "arxiv", "rss", "blog", "trend", "polymarket", "briefing"], "news-research"),
    # 元认知
    (["self-", "meta-", "memory", "anti-repetition", "capabilities-map", "hermes-self"], "metacognition"),
    # 社交
    (["minecraft", "pokemon", "fitness", "yuanbao", "bangumi", "game", "social"], "social-gaming"),
]


def classify_skill(skill_name, skill_tags, skill_path):
    """将 skill 归类到一个能力包模块"""
    search_text = f"{skill_name} {' '.join(skill_tags)} {skill_path}".lower()

    for keywords, module in CLASSIFICATION_RULES:
        for kw in keywords:
            if kw.lower() in search_text:
                return module

    # 默认：未分类
    return None


def read_skill_metadata(skill_path):
    """读取单个 SKILL.md 的元数据"""
    sk_path = Path(skill_path) / "SKILL.md"
    if not sk_path.exists():
        return None

    content = sk_path.read_text(encoding='utf-8', errors='ignore')
    lines = content.split('\n')
    line_count = len(lines)

    # 解析 frontmatter
    fm = {}
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        try:
            fm = yaml.safe_load(fm_match.group(1)) or {}
        except:
            pass

    name = fm.get('name', sk_path.parent.name)
    tags = fm.get('tags', []) or fm.get('triggers', []) or []
    version = fm.get('version', '?')
    design_pattern = fm.get('design_pattern', fm.get('metadata', {}).get('hermes', {}).get('design_pattern', ''))
    description = fm.get('description', '')[:100]

    # 统计子目录
    skill_dir = sk_path.parent
    subdirs = [d.name for d in skill_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    has_refs = 'references' in subdirs
    has_scripts = 'scripts' in subdirs
    has_templates = 'templates' in subdirs

    return {
        "name": name,
        "path": str(sk_path.relative_to(SKILLS_DIR.parent)),
        "line_count": line_count,
        "version": version,
        "tags": tags[:8],
        "design_pattern": design_pattern,
        "description": description,
        "subdirs": subdirs,
        "has_refs": has_refs,
        "has_scripts": has_scripts,
        "has_templates": has_templates,
    }


def scan_all_skills():
    """扫描所有 skill，归类到模块"""
    module_skills = defaultdict(list)
    unclassified = []
    all_skills = {}

    # HMAD 特有：检测名称相似度分组
    name_groups = defaultdict(list)

    for root, dirs, files in os.walk(SKILLS_DIR):
        if "SKILL.md" not in files:
            continue

        skill_path = Path(root)
        meta = read_skill_metadata(skill_path)
        if not meta:
            continue

        skill_name = meta["name"]
        all_skills[skill_name] = meta

        # 归类
        module = classify_skill(skill_name, meta["tags"], str(skill_path))
        if module:
            module_skills[module].append(meta)
        else:
            unclassified.append(meta)

        # 名称相似度分组（取前两个连字符分隔的词）
        base_parts = skill_name.split('-')[:2]
        if len(base_parts) >= 2:
            base = '-'.join(base_parts)
            name_groups[base].append(skill_name)

    return all_skills, module_skills, unclassified, name_groups


def build_tree(module_skills, unclassified):
    """构建三层树状结构"""
    tree = []

    for module_id in MODULES:
        info = MODULES[module_id]
        skills = module_skills.get(module_id, [])

        if not skills:
            continue

        # 技能聚类（第二层）
        clusters = cluster_skills(skills)

        node = {
            "module_id": module_id,
            "name": f"{info['emoji']} {info['name']}",
            "total_skills": len(skills),
            "clusters": clusters,
            "needs_attention": len([s for s in skills if s["line_count"] < 50]),
        }
        tree.append(node)

    # 未分类
    if unclassified:
        tree.append({
            "module_id": "unclassified",
            "name": "❓ 未分类",
            "total_skills": len(unclassified),
            "clusters": [{
                "cluster_name": "未分类技能",
                "count": len(unclassified),
                "skills": unclassified,
            }],
            "needs_attention": len(unclassified),
        })

    return tree


def cluster_skills(skills):
    """将 skills 聚类为功能组（第二层）"""
    # 按前两个词分组
    groups = defaultdict(list)
    for s in skills:
        name = s["name"]
        parts = name.split('-')
        if len(parts) >= 2:
            cluster_key = parts[0]
            # 特殊处理：pdf 相关的都放一起
            if parts[0] in ("pdf", "pdf-layout", "pdf-pro", "pdf-render"):
                cluster_key = "pdf"
            groups[cluster_key].append(s)
        else:
            groups["其他"].append(s)

    clusters = []
    for cluster_name, cluster_skills in sorted(groups.items()):
        clusters.append({
            "cluster_name": cluster_name,
            "count": len(cluster_skills),
            "skills": sorted(cluster_skills, key=lambda x: x["name"]),
            "consolidation": analyze_cluster_consolidation(cluster_name, cluster_skills),
        })

    return clusters


def analyze_cluster_consolidation(cluster_name, skills):
    """分析一个技能聚类中的合并潜力"""
    issues = []

    if len(skills) <= 1:
        return {"issues": [], "merge_potential": "none"}

    # 检查名称相似度
    names = [s["name"] for s in skills]
    base_names = set(n.split('-')[0] for n in names)

    if len(names) >= 3:
        issues.append(f"{len(names)} 个名称以 '{cluster_name}' 开头的 skill，可能可合并")

    # 检查微小 skill
    tiny = [s for s in skills if s["line_count"] < 50]
    if tiny:
        issues.append(f"{len(tiny)} 个微小 skill (<50行) 应降级为经验: {', '.join(s['name'] for s in tiny)}")

    # 检查路由型 skill
    routers = [s for s in skills if "index" in s.get("design_pattern", "").lower() or "router" in s.get("design_pattern", "")]
    if routers:
        issues.append(f"{len(routers)} 个路由型 skill ({', '.join(s['name'] for s in routers)}) — 应被包索引吸收")

    # BMAD 重复检测
    bmad_skills = [s for s in skills if "bmad" in s["name"]]
    if len(bmad_skills) > 10:
        issues.append(f"BMAD 系列 {len(bmad_skills)} 个 skill — 存在三副本冗余，建议清理")

    merge_potential = "high" if len(issues) >= 2 else "medium" if issues else "low"

    return {"issues": issues, "merge_potential": merge_potential}


def print_tree(tree, pack_filter=None):
    """打印树状索引"""
    if pack_filter:
        tree = [n for n in tree if n["module_id"] == pack_filter]

    if not tree:
        print(f"\n📭 (无匹配的能力包)")
        return

    grand_total = sum(n["total_skills"] for n in tree)
    print(f"\n{'='*65}")
    print(f"  🌳 Hermes Skill 分层树状索引")
    print(f"  共 {grand_total} 个 skill | {len(tree)} 个能力包")
    print(f"{'='*65}")

    for pack in tree:
        print(f"\n  {pack['name']} ({pack['total_skills']} skills)")
        if pack.get("needs_attention", 0) > 0:
            print(f"    ⚠️  {pack['needs_attention']} 个需关注")

        for cluster in pack["clusters"]:
            cons = cluster.get("consolidation", {})
            flag = ""
            if cons.get("merge_potential") == "high":
                flag = " 🔴"
            elif cons.get("merge_potential") == "medium":
                flag = " 🟡"

            print(f"    ├─ {cluster['cluster_name']}/ ({cluster['count']} skills){flag}")

            # 只打印前 5 个 skill，其余用 +N 表示
            for skill in cluster["skills"][:5]:
                flags = ""
                if skill["line_count"] < 50:
                    flags += " [微小]"
                if skill["has_refs"]:
                    flags += " 📎"
                if skill.get("design_pattern") in ("index", "router"):
                    flags += " [路由]"
                print(f"    │  ├─ {skill['name']:30s} {skill['version']:8s}{flags}")

            if len(cluster["skills"]) > 5:
                print(f"    │  └─ ...及另外 {len(cluster['skills'])-5} 个")

            # 合并建议
            if cons.get("issues"):
                for issue in cons["issues"][:2]:
                    print(f"    │    💡 {issue}")

    print(f"\n{'='*65}")
    print(f"  💡 查看合并建议: skill-tree-index.py --consolidate")
    print(f"{'='*65}")


def print_consolidation_report(tree):
    """打印合并建议报告"""
    print(f"\n{'='*65}")
    print(f"  🔧 Skill 合并潜力分析")
    print(f"{'='*65}")

    # 收集所有合并建议
    all_issues = []
    for pack in tree:
        for cluster in pack["clusters"]:
            cons = cluster.get("consolidation", {})
            if cons.get("issues"):
                all_issues.append({
                    "pack": pack["name"],
                    "cluster": cluster["cluster_name"],
                    "count": cluster["count"],
                    "issues": cons["issues"],
                    "potential": cons["merge_potential"],
                })

    high = [i for i in all_issues if i["potential"] == "high"]
    medium = [i for i in all_issues if i["potential"] == "medium"]

    print(f"\n🔴 高合并潜力: {len(high)} 组")
    for item in high:
        print(f"\n  {item['pack']} → {item['cluster']}/ ({item['count']} skills)")
        for issue in item["issues"]:
            print(f"    • {issue}")

    print(f"\n🟡 中合并潜力: {len(medium)} 组")
    for item in medium:
        print(f"\n  {item['pack']} → {item['cluster']}/ ({item['count']} skills)")
        for issue in item["issues"]:
            print(f"    • {issue}")

    if not all_issues:
        print("\n✅ 未发现明显合并机会")

    print(f"\n{'='*65}")
    total_skills = sum(n["total_skills"] for n in tree)
    total_clusters = sum(len(n["clusters"]) for n in tree)
    print(f"  总结: {total_skills} skill 分布在 {total_clusters} 个功能聚类中")
    print(f"  预估合并后可精简至 {int(total_skills * 0.75)}-{int(total_skills * 0.85)} 个 core skill")
    print(f"{'='*65}")


def print_health_summary(all_skills, module_skills, unclassified, name_groups):
    """打印系统健康度速览"""
    total = len(all_skills)

    # 规模分布
    tiny = [s for s in all_skills.values() if s["line_count"] < 50]
    small = [s for s in all_skills.values() if 50 <= s["line_count"] < 100]
    medium = [s for s in all_skills.values() if 100 <= s["line_count"] < 300]
    large = [s for s in all_skills.values() if 300 <= s["line_count"] < 500]
    huge = [s for s in all_skills.values() if s["line_count"] >= 500]

    # 模块分布
    module_dist = {mid: len(module_skills.get(mid, [])) for mid in MODULES}
    sorted_modules = sorted(module_dist.items(), key=lambda x: -x[1])

    print(f"\n{'='*65}")
    print(f"  🏥 Skill 系统健康度速览")
    print(f"{'='*65}")
    print(f"\n  总数: {total} SKILL.md")
    print(f"  未分类: {len(unclassified)}")
    print(f"  名称相似组: {len(name_groups)} 组")
    print(f"\n  规模分布:")
    print(f"    🔴 微小 (<50行):    {len(tiny)} (应降级)")
    print(f"    🟡 小型 (50-100):   {len(small)} (部分可合并)")
    print(f"    🟢 中等 (100-300):  {len(medium)} (健康)")
    print(f"    🟢 大型 (300-500):  {len(large)} (健康)")
    print(f"    🟡 超大型 (>500行):  {len(huge)} (可能需拆分)")

    print(f"\n  模块分布 Top 5:")
    for mid, count in sorted_modules[:5]:
        emoji = MODULES.get(mid, {}).get("emoji", "📦")
        pct = count / total * 100 if total > 0 else 0
        bar = "█" * int(pct / 4) + "░" * (25 - int(pct / 4))
        print(f"    {emoji} {mid:25s} {count:3d} ({pct:4.1f}%) {bar}")

    # 最小和最大的模块
    non_zero = [(mid, c) for mid, c in sorted_modules if c > 0]
    if non_zero:
        print(f"\n   最大: {non_zero[0][0]} ({non_zero[0][1]} skills)")
        print(f"   最小: {non_zero[-1][0]} ({non_zero[-1][1]} skills)")

    print(f"\n  效率指标:")
    bmad_count = sum(1 for s in all_skills.values() if "bmad" in s["name"])
    print(f"    BMAD 系列: {bmad_count} (估计 {bmad_count // 3} 冗余)")
    print(f"    路由型: {sum(1 for s in all_skills.values() if s.get('design_pattern') in ('index', 'router'))}")
    print(f"    有 references: {sum(1 for s in all_skills.values() if s['has_refs'])}")
    print(f"    有 scripts: {sum(1 for s in all_skills.values() if s['has_scripts'])}")

    estimated_core = total - len(tiny) - (bmad_count // 3)
    print(f"\n  📊 预估精简后 core skills: ~{estimated_core} (当前 {total})")
    print(f"      精简率: {(1 - estimated_core/total)*100:.0f}%")

    if unclassified:
        print(f"\n  ⚠️  未分类 skill ({len(unclassified)} 个):")
        for s in unclassified[:5]:
            print(f"     ❓ {s['name']} — {s['description'][:50]}")
        if len(unclassified) > 5:
            print(f"     ...及另外 {len(unclassified)-5} 个")

    print(f"\n{'='*65}")


def build_sra_output(tree, all_skills):
    """生成 SRA 兼容的技能索引格式"""
    sra_index = {"version": "1.0", "skills": [], "clusters": []}
    seen_clusters = set()
    
    for module in tree:
        mod_id = module["module_id"]
        mod_name = module["name"]
        for cluster in module.get("clusters", []):
            cluster_key = f"{mod_id}/{cluster['cluster_name']}"
            
            if cluster_key not in seen_clusters:
                seen_clusters.add(cluster_key)
                cluster_skills = []
                for s in cluster.get("skills", []):
                    sqs = all_skills.get(s["name"], {}).get("sqs_score", 50)
                    cluster_skills.append({
                        "name": s["name"],
                        "path": s["path"],
                        "version": s.get("version", "?"),
                        "sqs_score": sqs,
                        "has_refs": s.get("has_refs", False),
                        "has_scripts": s.get("has_scripts", False),
                        "tags": s.get("tags", []),
                        "description": s.get("description", "")
                    })
                
                sra_index["clusters"].append({
                    "cluster": cluster["cluster_name"],
                    "pack": mod_id,
                    "pack_name": mod_name,
                    "skill_count": cluster.get("count", len(cluster_skills)),
                    "skills": [s["name"] for s in cluster_skills],
                    "avg_sqs": round(sum(s["sqs_score"] for s in cluster_skills) / len(cluster_skills), 1) if cluster_skills else 0,
                    "siblings": [s["name"] for s in cluster_skills],
                })
                
                for s in cluster_skills:
                    sra_index["skills"].append({
                        **s,
                        "pack": mod_id,
                        "pack_name": mod_name,
                        "cluster": cluster["cluster_name"],
                    })
    
    return sra_index


def print_dashboard():
    """生成 CHI 健康仪表盘 HTML"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='reports/chi-by-pack.json')
    parser.add_argument('--output', default='reports/chi-dashboard-v2.html')
    
    args, _ = parser.parse_known_args()
    
    with open(args.input) as f:
        packs = json.load(f)
    
    # Calculate global metrics
    all_scores = []
    for pack_name, pack_data in packs.items():
        for skill in pack_data.get("skills", []):
            all_scores.append(skill["sqs"])
    
    chi = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
    total_skills = len(all_scores)
    
    # Sort packs by avg_sqs
    sorted_packs = sorted(packs.items(), key=lambda x: x[1]["avg_sqs"])
    
    # Build HTML
    bars_html = ""
    table_rows_html = ""
    for rank, (pack_name, data) in enumerate(sorted_packs, 1):
        avg = data["avg_sqs"]
        bar_pct = min(avg, 100)
        if avg >= 80: color = "#22c55e"
        elif avg >= 60: color = "#eab308"
        elif avg >= 40: color = "#f97316"
        else: color = "#ef4444"
        
        marker = " 🎯" if rank <= 3 else ""
        bars_html += f"""\
        <div style="margin:12px 0;">
          <div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:4px;">
            <span><strong>{rank}. {pack_name}</strong>{marker} <span style="color:#888;">({data['skill_count']} skills)</span></span>
            <span style="font-weight:bold;color:{color}">{avg}</span>
          </div>
          <div style="background:#eee;border-radius:8px;height:24px;overflow:hidden;">
            <div style="width:{bar_pct}%;background:{color};height:100%;border-radius:8px;transition:width 0.3s;"></div>
          </div>
        </div>"""
        
        dist = data["distribution"]
        table_rows_html += f"""\
        <tr>
          <td style="padding:6px 12px;">{pack_name}</td>
          <td style="padding:6px 12px;text-align:center;">{data['skill_count']}</td>
          <td style="padding:6px 12px;text-align:center;font-weight:bold;color:{color};">{avg}</td>
          <td style="padding:6px 12px;text-align:center;">{dist.get('🟢 excellent', 0)}</td>
          <td style="padding:6px 12px;text-align:center;">{dist.get('🟡 good', 0)}</td>
          <td style="padding:6px 12px;text-align:center;">{dist.get('🟠 needs_work', 0)}</td>
          <td style="padding:6px 12px;text-align:center;">{dist.get('🔴 poor', 0)}</td>
        </tr>"""
    
    # Low-score skills detail
    low_skills = []
    for pack_name, data in sorted_packs:
        for s in data.get("skills", []):
            if s["sqs"] < 60:
                low_skills.append((pack_name, s["name"], s["sqs"]))
    
    low_skills_html = ""
    for pack_name, skill_name, sqs in sorted(low_skills, key=lambda x: x[2]):
        low_skills_html += f"""\
        <tr>
          <td style="padding:4px 12px;">{pack_name}</td>
          <td style="padding:4px 12px;">{skill_name}</td>
          <td style="padding:4px 12px;text-align:center;color:#ef4444;">{sqs}</td>
        </tr>"""
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>CHI 健康仪表盘 v2 — hermes-cap-pack</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f8fafc; color:#1e293b; padding:0; }}
  .header {{ background:linear-gradient(135deg,#1e293b,#334155); color:white; padding:32px 48px; }}
  .header h1 {{ font-size:28px; }}
  .header p {{ color:#94a3b8; margin-top:8px; }}
  .metrics {{ display:flex; gap:24px; padding:24px 48px; background:white; border-bottom:1px solid #e2e8f0; }}
  .metric-card {{ flex:1; padding:20px; border-radius:12px; background:#f8fafc; text-align:center; }}
  .metric-value {{ font-size:36px; font-weight:bold; }}
  .metric-label {{ font-size:14px; color:#64748b; margin-top:4px; }}
  .content {{ display:grid; grid-template-columns:1.2fr 0.8fr; gap:24px; padding:24px 48px; }}
  .card {{ background:white; border-radius:12px; padding:24px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }}
  .card h2 {{ font-size:18px; margin-bottom:16px; }}
  table {{ width:100%; border-collapse:collapse; font-size:14px; }}
  th {{ background:#f1f5f9; padding:8px 12px; text-align:left; font-weight:600; }}
  td {{ border-bottom:1px solid #f1f5f9; }}
  tr:hover td {{ background:#f8fafc; }}
  .footer {{ text-align:center; padding:24px; color:#94a3b8; font-size:13px; }}
  @media (max-width:900px) {{ .content {{ grid-template-columns:1fr; }} .metrics {{ flex-direction:column; }} .header, .metrics, .content {{ padding:16px; }} }}
</style>
</head>
<body>
<div class="header">
  <h1>🏥 CHI 健康仪表盘</h1>
  <p>hermes-cap-pack · 全量 SQS 评分 · 按能力包聚合 · 生成于 2026-05-14</p>
</div>

<div class="metrics">
  <div class="metric-card" style="background:#f0fdf4;">
    <div class="metric-value" style="color:#16a34a;">{chi}</div>
    <div class="metric-label">全局 CHI (均分)</div>
  </div>
  <div class="metric-card" style="background:#fefce8;">
    <div class="metric-value" style="color:#ca8a04;">{total_skills}</div>
    <div class="metric-label">Skill 总数</div>
  </div>
  <div class="metric-card" style="background:#fef2f2;">
    <div class="metric-value" style="color:#dc2626;">{len(sorted_packs)}</div>
    <div class="metric-label">能力包数</div>
  </div>
  <div class="metric-card" style="background:#f0f9ff;">
    <div class="metric-value" style="color:#2563eb;">{len(low_skills)}</div>
    <div class="metric-label">低分 skill (&lt;60)</div>
  </div>
</div>

<div class="content">
  <div class="card">
    <h2>📊 能力包 SQS 均分</h2>
    {bars_html}
  </div>
  <div class="card">
    <h2>📋 评分分布</h2>
    <table>
      <tr><th>能力包</th><th>数</th><th>均分</th><th>🟢</th><th>🟡</th><th>🟠</th><th>🔴</th></tr>
      {table_rows_html}
    </table>
  </div>
  {f'''<div class="card" style="grid-column:1/-1;">
    <h2>⚠️ 低分 skill 详情 (&lt;60)</h2>
    <table>
      <tr><th>能力包</th><th>Skill</th><th>SQS</th></tr>
      {low_skills_html}
    </table>
  </div>''' if low_skills_html else ''}
</div>

<div class="footer">
  <p>hermes-cap-pack · project-state.py &bull; aggregate-sqs.py &bull; skill-tree-index.py --dashboard</p>
</div>
</body>
</html>"""
    
    with open(args.output, 'w') as f:
        f.write(html)
    print(f"✅ 仪表盘已生成: {args.output}", file=sys.stderr)
    print(f"   CHI: {chi} | 能力包: {len(sorted_packs)} | Skill: {total_skills} | 低分: {len(low_skills)}", file=sys.stderr)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    pack_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == '--pack' and i + 1 < len(sys.argv):
            pack_filter = sys.argv[i + 1]

    output_json = '--json' in sys.argv

    print(f"🔍 扫描 skill 系统...", file=sys.stderr)
    all_skills, module_skills, unclassified, name_groups = scan_all_skills()
    tree = build_tree(module_skills, unclassified)

    if output_json:
        print(json.dumps(tree, ensure_ascii=False, indent=2))
    elif '--sra' in sys.argv:
        # SRA 兼容模式：输出簇/包/同类技能信息
        sra_output = build_sra_output(tree, all_skills)
        print(json.dumps(sra_output, ensure_ascii=False, indent=2))
    elif '--health' in sys.argv:
        print_health_summary(all_skills, module_skills, unclassified, name_groups)
    elif '--dashboard' in sys.argv:
        print_dashboard()
    elif '--consolidate' in sys.argv:
        print_tree(tree, pack_filter)
        print("\n" + "─" * 65)
        print_consolidation_report(tree)
    else:
        print_tree(tree, pack_filter)


if __name__ == "__main__":
    main()
