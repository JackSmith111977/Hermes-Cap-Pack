#!/usr/bin/env python3
"""
skill-tree-index.py v1.0 — Hermes Skill 分层树状索引生成器

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
    elif '--health' in sys.argv:
        print_health_summary(all_skills, module_skills, unclassified, name_groups)
    elif '--consolidate' in sys.argv:
        print_tree(tree, pack_filter)
        print("\n" + "─" * 65)
        print_consolidation_report(tree)
    else:
        print_tree(tree, pack_filter)


if __name__ == "__main__":
    main()
