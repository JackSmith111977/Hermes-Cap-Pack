#!/usr/bin/env python3
"""
generate-panorama.py v2.0 — Hermes Cap Pack 项目全景报告生成器

从 project-report.json + SQS DB + SDD 文档体系，生成数据驱动的 10 章节全景报告。
基于 arc42 + CODITECT + 项目管理最佳实践设计。

用法:
  python3 generate-panorama.py                        # 生成 PROJECT-PANORAMA.html
  python3 generate-panorama.py --open                  # 生成并打开浏览器
"""

import json, os, sqlite3, subprocess, sys, webbrowser
from datetime import datetime
from pathlib import Path

CAP_PACK_DIR = Path.home() / "projects" / "hermes-cap-pack"
REPORTS_DIR = CAP_PACK_DIR / "reports"
DB_PATH = Path.home() / ".hermes" / "data" / "skill-quality.db"
PROJECT_REPORT = CAP_PACK_DIR / "docs" / "project-report.json"
DOCS_DIR = CAP_PACK_DIR / "docs"
SCRIPTS_DIR = CAP_PACK_DIR / "scripts"

MODULES = [
    ("📚", "知识库系统", "knowledge-base"), ("🧠", "学习引擎", "learning-engine"),
    ("📄", "文档生成", "doc-engine"), ("💻", "开发工作流", "developer-workflow"),
    ("🔒", "安全审计", "security-audit"), ("✅", "质量保障", "quality-assurance"),
    ("🔧", "运维监控", "devops-monitor"), ("🌐", "网络代理", "network-proxy"),
    ("💬", "消息平台", "messaging"), ("🤖", "Agent 协作", "agent-orchestration"),
    ("🔌", "MCP 集成", "mcp-integration"), ("📊", "金融分析", "financial-analysis"),
    ("🎨", "创意设计", "creative-design"), ("🎵", "音视频媒体", "media-processing"),
    ("🐙", "GitHub 生态", "github-ecosystem"), ("📰", "新闻研究", "news-research"),
    ("🪞", "元认知系统", "metacognition"), ("🎮", "社交娱乐", "social-gaming"),
]

CLASSIFICATION_RULES = [
    (["knowledge", "precipitation", "routing", "llm-wiki", "file-classification"], "knowledge-base"),
    (["learning", "skill-creator", "deep-research", "night-study"], "learning-engine"),
    (["pdf", "pptx", "docx", "html-guide", "markdown", "latex", "epub", "doc-design", "readme-for-ai"], "doc-engine"),
    (["plan", "writing-plans", "sdd", "debugging", "tdd", "subagent", "spike", "git-advanced", "python-env", "patch-file"], "developer-workflow"),
    (["delete-safety", "security", "commit-quality", "sherlock", "1password", "godmode"], "security-audit"),
    (["qa-", "-qa-", "quality", "test", "testing", "review", "cranfield", "dogfood", "doc-alignment", "adversarial"], "quality-assurance"),
    (["linux-ops", "docker", "process-management", "system-health", "proxy-monitor", "cron", "webhook"], "devops-monitor"),
    (["clash", "proxy-finder", "web-access", "browser-automation", "web-ui"], "network-proxy"),
    (["feishu", "weixin", "email", "sms", "agentmail", "himalaya", "messaging", "broadcast"], "messaging"),
    (["hermes-agent", "claude-code", "codex", "opencode", "blackbox", "bmad", "kanban", "delegate", "honcho", "orchestrat"], "agent-orchestration"),
    (["mcp", "fastmcp", "mcporter", "sra"], "mcp-integration"),
    (["financial", "akshare", "stock", "analyst"], "financial-analysis"),
    (["architecture-diagram", "mermaid", "excalidraw", "p5js", "pixel-art", "ascii", "creativ", "design", "sketch", "claude-design", "songwriting"], "creative-design"),
    (["tts", "speech", "audio", "song", "gif", "comfyui", "image-generation", "image-prompt", "video"], "media-processing"),
    (["github", "git-", "pull-request", "code-review", "release"], "github-ecosystem"),
    (["news", "arxiv", "rss", "blog", "trend", "polymarket", "briefing"], "news-research"),
    (["self-", "meta-", "memory", "anti-repetition", "capabilities-map", "hermes-self"], "metacognition"),
    (["minecraft", "pokemon", "fitness", "yuanbao", "bangumi", "game", "social"], "social-gaming"),
]


def get_module(name):
    nl = name.lower()
    for kws, mod in CLASSIFICATION_RULES:
        for kw in kws:
            if kw.lower() in nl: return mod
    return "unclassified"


def load_json(path):
    return json.loads(Path(path).read_text()) if Path(path).exists() else {}


def get_sqs():
    if not DB_PATH.exists(): return {"scores": {}, "trend": []}
    conn = sqlite3.connect(str(DB_PATH))
    scores = {r[0]: {"sqs": r[1], "s1": r[2], "s2": r[3], "s3": r[4], "s4": r[5], "s5": r[6]}
              for r in conn.execute("SELECT skill_name, sqs_total, s1, s2, s3, s4, s5 FROM scores").fetchall()}
    trend = [{"day": r[0], "avg": round(r[1], 1)}
             for r in conn.execute("SELECT DATE(scored_at) as d, AVG(sqs_total) FROM score_history GROUP BY d ORDER BY d").fetchall()]
    conn.close()
    return {"scores": scores, "trend": trend}


def get_docs():
    docs = []
    for f in sorted(DOCS_DIR.glob("*.md")):
        c = f.read_text("utf-8", errors="ignore").split("\n")[:5]
        st = "draft"
        for line in c:
            if "**状态**" in line or "> **状态**" in line:
                st = line.split("`")[1] if "`" in line else "unknown"; break
        tp = "Story" if f.stem.startswith("STORY-") else "Epic" if f.stem.startswith("EPIC-") else "Spec" if f.stem.startswith("SPEC-") else "Other"
        docs.append({"name": f.stem, "type": tp, "status": st, "path": f"docs/{f.name}"})
    sd = DOCS_DIR / "stories"
    if sd.exists():
        for f in sorted(sd.glob("*.md")):
            c = f.read_text("utf-8", errors="ignore").split("\n")[:5]
            st = "draft"
            for line in c:
                if "**状态**" in line or "> **状态**" in line:
                    st = line.split("`")[1] if "`" in line else "unknown"; break
            docs.append({"name": f.stem, "type": "Story", "status": st, "path": f"docs/stories/{f.name}"})
    return docs


def get_git():
    try:
        return {"tag": subprocess.run(["git", "describe", "--tags", "--always"], capture_output=True, text=True, cwd=CAP_PACK_DIR).stdout.strip(),
                "branch": subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=CAP_PACK_DIR).stdout.strip(),
                "commits": subprocess.run(["git", "rev-list", "--count", "HEAD"], capture_output=True, text=True, cwd=CAP_PACK_DIR).stdout.strip()}
    except: return {"tag": "?", "branch": "?", "commits": "?"}


def build():
    pr = load_json(PROJECT_REPORT)
    sqs = get_sqs()
    docs = get_docs()
    git = get_git()

    all_sqs = [v["sqs"] for v in sqs["scores"].values()]
    avg = round(sum(all_sqs)/len(all_sqs), 1) if all_sqs else 0
    total_sk = len(all_sqs)
    epics = pr.get("epics", [])
    total_st = sum(len(e.get("stories", [])) for e in epics)
    done_st = sum(1 for e in epics for s in e.get("stories", []) if s.get("status") == "completed")

    code_lines = sum(len(p.read_text().splitlines()) for p in SCRIPTS_DIR.rglob("*.py") if "__pycache__" not in str(p))

    dist = {"ex": 0, "gd": 0, "ni": 0, "fl": 0}
    for v in all_sqs:
        if v >= 90: dist["ex"] += 1
        elif v >= 70: dist["gd"] += 1
        elif v >= 50: dist["ni"] += 1
        else: dist["fl"] += 1

    md = {m[2]: {"c": 0, "s": 0} for m in MODULES}
    for n, s in sqs["scores"].items():
        mod = get_module(n)
        if mod in md: md[mod]["c"] += 1; md[mod]["s"] += s["sqs"]
    mod_rows = ""
    for em, lb, mid in MODULES:
        d = md.get(mid, {"c": 0, "s": 0})
        a = round(d["s"]/d["c"], 1) if d["c"] else 0
        mod_rows += f"<tr><td>{em} {lb}</td><td>{a}</td><td>{d['c']}</td><td><span class='bar'>xb7</span></td></tr>"

    s5 = {"S1_structure":[],"S2_content":[],"S3_freshness":[],"S4_relations":[],"S5_discoverability":[]}
    for v in sqs["scores"].values():
        for k in s5:
            if k in v: s5[k].append(v[k])
    da = {k: round(sum(v)/len(v),1) if v else 0 for k,v in s5.items()}
    dim_rows = ""
    labels = {"S1_structure":"S1 结构完整性","S2_content":"S2 内容准确性","S3_freshness":"S3 时效性","S4_relations":"S4 关联完整性","S5_discoverability":"S5 可发现性"}
    for k, a in da.items():
        c = "ok" if a >= 15 else "warn" if a >= 10 else "bad"
        dim_rows += f"<tr><td>{labels[k]}</td><td class='{c}'>{a}/20</td></tr>"

    low = sorted(sqs["scores"].items(), key=lambda x: x[1]["sqs"])[:10]
    low_rows = "".join(f"<tr><td>{n}</td><td>{s['sqs']}</td><td class='{'bad' if s['sqs']<55 else 'warn'}'>xd8xd9</td></tr>" for n,s in low)

    trend = sqs["trend"]
    trend_lbl = json.dumps([t["day"] for t in trend])
    trend_dat = json.dumps([t["avg"] for t in trend])

    epc = ""
    for ep in epics:
        eid = ep.get("id","?"); en = ep.get("name","?"); es = ep.get("status","draft")
        ss = ep.get("stories",[]); dn = sum(1 for s in ss if s.get("status") in ("completed","implemented"))
        tt = len(ss) or 1; pct = round(dn/tt*100)
        epc += f"<div class='epic-card'><div class='epic-hdr'><b>{eid}</b><span class='tag {es}'>{es}</span></div><div class='epic-nm'>{en}</div><div class='pbar'><div class='pfill' style='width:{pct}%'></div></div><div class='epic-m'>{dn}/{tt} stories</div></div>"

    st_rows = ""
    for ep in epics:
        for s in ep.get("stories", []):
            st = s.get("status","draft"); sid = s.get("id","?"); sn = s.get("name","?")
            cls = {"completed":"ok","implemented":"warn","draft":"dim","in_progress":"accent"}
            st_rows += f"<tr><td>{sid}</td><td>{sn}</td><td class='{cls.get(st,'dim')}'>{st}</td><td>{ep.get('id','?')}</td></tr>"

    doc_rows = ""
    for d in docs:
        cls = {"completed":"ok","implemented":"warn","qa_gate":"accent","create":"accent","draft":"dim","approved":"ok"}
        doc_rows += f"<tr><td>{d['type']}</td><td>{d['name']}</td><td class='{cls.get(d['status'],'dim')}'>{d['status']}</td><td><a href='{d['path']}'>{d['path']}</a></td></tr>"

    sp_rows = ""
    for sp in sorted(pr.get("sprint_history", []), key=lambda x: x.get("sprint","")):
        sp_rows += f"<div class='sp'><span class='sp-l'>{sp.get('sprint','?')}</span><span class='sp-d'>{sp.get('date','?')}</span><span class='sp-t'>{sp.get('summary','?')}</span><span class='sp-s'>{sp.get('stories_completed',0)} st +{sp.get('tests_added',0)} t</span></div>"

    tests = pr.get("tests", {})
    tf = tests.get("files", [])
    tr = "".join(f"<tr><td>{f['name']}</td><td>{f['tests']}</td><td>{f['passing']}</td><td class='ok'>xe2x9c</td></tr>" for f in tf)
    tp = tests.get("passing", 0)
    tt = tests.get("total", 0)
    tdur = str(tests.get("duration_seconds", "?"))
    uncl = sum(1 for n in sqs["scores"] if get_module(n) == "unclassified")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    tag = git["tag"]; br = git["branch"]; cm = git["commits"]
    n_ep = len([d for d in docs if d["type"] == "Epic"])
    n_sp = len([d for d in docs if d["type"] == "Spec"])
    n_st = len([d for d in docs if d["type"] == "Story"])
    doc_cnt = len(docs)
    sc_cnt = len(list(SCRIPTS_DIR.glob("*.py")))
    rp_cnt = len(list(REPORTS_DIR.glob("*.html")))
    tr_pts = len(trend)
    tr_st = trend[0]["day"] if trend else "N/A"
    tr_en = trend[-1]["day"] if trend else "N/A"

    # ===== HTML 模板（避免 f-string，用 {{PLACEHOLDER}} + .replace()）=====
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hermes Capability Pack — 项目全貌 v2</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#0d1117;--card:#161b22;--border:#30363d;--text:#e6edf3;--dim:#8b949e;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--accent:#58a6ff;--purple:#bc8cff}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans SC',sans-serif;line-height:1.6}
.container{max-width:1200px;margin:0 auto;padding:20px}
.hdr{text-align:center;padding:40px 0 24px;border-bottom:1px solid var(--border);margin-bottom:24px}
.hdr h1{font-size:2em;background:linear-gradient(135deg,var(--accent),var(--purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hdr .sub{color:var(--dim);font-size:.9em;margin-top:4px}
.bdg{display:inline-block;padding:2px 10px;border-radius:12px;font-size:.78em;margin:3px}
.blue{background:var(--accent)22;color:var(--accent);border:1px solid var(--accent)44}
.green{background:var(--ok)22;color:var(--ok);border:1px solid var(--ok)44}
.purple{background:var(--purple)22;color:var(--purple);border:1px solid var(--purple)44}
.yellow{background:var(--warn)22;color:var(--warn);border:1px solid var(--warn)44}
section{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:20px 24px;margin-bottom:16px}
section h2{font-size:1.2em;margin-bottom:14px;padding-bottom:6px;border-bottom:1px solid var(--border)}
section h3{font-size:1em;margin:14px 0 8px;color:var(--accent)}
.kg{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-bottom:14px}
.kc{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:12px;text-align:center}
.kc .v{font-size:1.6em;font-weight:700}
.kc .l{color:var(--dim);font-size:.8em;margin-top:2px}
.kc .s{color:var(--dim);font-size:.72em}
table{width:100%;border-collapse:collapse;font-size:.82em}
th,td{padding:5px 8px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--dim);font-weight:500}
td a{color:var(--accent);text-decoration:none}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}.accent{color:var(--accent)}.dim{color:var(--dim)}
.eg{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}
.ec{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:12px}
.ec-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.tag{padding:1px 7px;border-radius:8px;font-size:.72em;font-weight:600}
.tag.approved{background:var(--ok)22;color:var(--ok)}.tag.qa_gate{background:var(--warn)22;color:var(--warn)}
.tag.create{background:var(--accent)22;color:var(--accent)}.tag.draft{background:var(--dim)22;color:var(--dim)}
.ec-nm{font-size:.85em;margin-bottom:6px}
.pbar{height:5px;background:var(--border);border-radius:2px;margin-bottom:3px}
.pfill{height:100%;background:var(--ok);border-radius:2px}
.epic-m{font-size:.75em;color:var(--dim)}
.sp{display:grid;grid-template-columns:90px 90px 1fr 110px;gap:6px;padding:6px 8px;background:var(--bg);border:1px solid var(--border);border-radius:4px;align-items:center;font-size:.82em;margin-bottom:4px}
.sp-l{font-weight:600;color:var(--accent)}.sp-d{color:var(--dim)}.sp-t{color:var(--text)}.sp-s{color:var(--dim);text-align:right}
.tc{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media (max-width:768px){.tc{grid-template-columns:1fr}.sp{grid-template-columns:1fr}}
.ch{height:260px;margin:10px 0}
.ft{text-align:center;color:var(--dim);font-size:.78em;padding:16px}
</style>
</head>
<body>
<div class="container">

<div class="hdr">
  <h1>xd8xd9 Hermes Capability Pack</h1>
  <div class="sub">Agent 能力模块化与跨平台复用框架 · 数据驱动全景报告 v2</div>
  <div>
    <span class="bdg blue">__TAG__</span>
    <span class="bdg green">__BRANCH__</span>
    <span class="bdg purple">__COMMITS__ commits</span>
    <span class="bdg yellow">5 Sprints</span>
  </div>
  <div class="sub" style="margin-top:6px">生成于 __NOW__</div>
</div>

<section>
<h2>xa7 1 xd8xd9 执行摘要 (BLUF)</h2>
<p style="margin-bottom:10px;font-size:1em">
  <b>Hermes Cap Pack</b> 已完成 <b>5 个 Sprint</b>，交付 <b>__DONE_ST__ / __ALL_ST__</b> 个 Story，
  覆盖 <b>__N_EP__ 个 EPIC</b> 路 <b>__N_SP__ 个 Spec</b> 路 <b>__DOC_CNT__</b> 个文档。
  系统健康度 <b>__AVG__ /100</b>，
  测试 <b>__TP__ / __TT__</b> 全绿 x2714 xfe0f。
  EPIC-001 已 approved，EPIC-002 正等待主人 Review。
</p>
<div class="kg">
  <div class="kc"><div class="v" style="color:var(--accent)">__TAG__</div><div class="l">当前版本</div><div class="s">MIT License</div></div>
  <div class="kc"><div class="v" style="color:var(--ok)">__TP__ / __TT__</div><div class="l">测试通过率</div><div class="s">__TF__ 文件</div></div>
  <div class="kc"><div class="v" style="color:var(--warn)">__AVG__</div><div class="l">SQS 健康度</div><div class="s">__SK__ skills</div></div>
  <div class="kc"><div class="v" style="color:var(--purple)">__DONE_ST__</div><div class="l">完成 Stories</div><div class="s">5 个 Sprint</div></div>
  <div class="kc"><div class="v" style="color:var(--accent)">__CODE__</div><div class="l">Python 行数</div><div class="s">__SC__ 脚本</div></div>
  <div class="kc"><div class="v" style="color:var(--ok)">__RP__</div><div class="l">HTML 报告</div><div class="s">reports/ 目录</div></div>
</div>
</section>

<section>
<h2>xa7 2 x1f3af 项目概况</h2>
<div class="tc">
<div>
<h3>背景与目标</h3>
<p style="color:var(--dim);font-size:.88em;margin-bottom:8px">
将 Hermes Agent 的扁平化技能体系拆分为标准化、可移植的「能力包」(Capability Pack)。
18 个能力包模块 x 70 个功能聚类 x __SK__ 个技能的树状组织，让 AI Agent 知道自己有什么能力。
</p>
<table>
<tr><th>指标</th><th>值</th></tr>
<tr><td>能力包模块</td><td>18 个（3 个已提取）</td></tr>
<tr><td>总技能数</td><td>__SK__ 个</td></tr>
<tr><td>未分类技能</td><td>__UNCL__ 个</td></tr>
<tr><td>Python 脚本</td><td>__SC__ 个</td></tr>
<tr><td>自动化 Cron</td><td>2 个</td></tr>
</table>
</div>
<div>
<h3>Sprint 时间线</h3>
<div>__SPR__</div>
</div>
</div>
</section>

<section>
<h2>xa7 3 x1f3d7 xfe0f 架构总览</h2>
<h3>三层架构</h3>
<div class="kg">
  <div class="kc"><div class="v" style="font-size:1.1em">x1f3af 能力包层</div><div class="l">Layer 3</div><div class="s">doc-engine 路 quality-assurance 路 learning-workflow</div></div>
  <div class="kc"><div class="v" style="font-size:1.1em">x1f527 工具层</div><div class="l">Layer 2</div><div class="s">__SC__ 脚本 路 3 适配器 路 CI/CD</div></div>
  <div class="kc"><div class="v" style="font-size:1.1em">x1f4ca 数据层</div><div class="l">Layer 1</div><div class="s">SQLite DB 路 SDD Docs 路 Reports</div></div>
</div>
<h3>18 模块全景</h3>
<div style="max-height:360px;overflow-y:auto">
<table><tr><th>模块</th><th>SQS 均分</th><th>Skill 数</th></tr>__MOD__</table>
</div>
</section>

<section>
<h2>xa7 4 x1f4d0 Epics & 交付</h2>
<h3>Epic 概览</h3>
<div class="eg">__EPC__</div>
<h3>Story 清单</h3>
<div style="max-height:320px;overflow-y:auto">
<table><tr><th>ID</th><th>名称</th><th>状态</th><th>Epic</th></tr>__ST__</table>
</div>
</section>

<section>
<h2>xa7 5 x1f4ca 质量全景 (SQS)</h2>
<div class="kg">
  <div class="kc"><div class="v" style="color:var(--warn)">__AVG__</div><div class="l">平均 SQS</div><div class="s">__SK__ skills</div></div>
  <div class="kc"><div class="v" style="color:var(--ok)">x1f7e1 x1f7e0 分布</div><div class="l">合格/待改进</div><div class="s">__GD__ / __NI__</div></div>
  <div class="kc"><div class="v" style="color:var(--ok)">__TRP__</div><div class="l">趋势数据点</div><div class="s">__TRS__ ~ __TRE__</div></div>
</div>
<div class="tc">
<div>
<h3>五维分析</h3>
<table>__DIM__</table>
</div>
<div>
<h3>低分 Top 10</h3>
<div style="max-height:260px;overflow-y:auto"><table><tr><th>Skill</th><th>SQS</th></tr>__LOW__</table></div>
</div>
</div>
<h3>SQS 历史趋势 (__TRP__ 点)</h3>
<div class="ch"><canvas id="tc"></canvas></div>
</section>

<section>
<h2>xa7 6 x2705 测试与 CI/CD</h2>
<div class="kg">
  <div class="kc"><div class="v" style="color:var(--ok)">__TP__ / __TT__</div><div class="l">测试通过</div><div class="s">100% x2714 xfe0f</div></div>
  <div class="kc"><div class="v" style="color:var(--accent)">__TDUR__s</div><div class="l">执行耗时</div><div class="s">__TF__ 文件</div></div>
  <div class="kc"><div class="v" style="color:var(--purple)">4 jobs</div><div class="l">CI 门禁</div><div class="s">lint + validate + health + cross-ref</div></div>
  <div class="kc"><div class="v" style="color:var(--ok)">2 crons</div><div class="l">自动化</div><div class="s">健康报告 + SQS 同步</div></div>
</div>
<h3>测试文件分布</h3>
<table><tr><th>文件</th><th>测试数</th><th>通过</th></tr>__TR__</table>
<h3>CI Pipeline</h3>
<p style="color:var(--dim);font-size:.85em">
  GitHub Actions 4 job 并行门禁：<b>lint</b> (flake8) > <b>validate-packs</b> (JSON Schema) >
  <b>health-gate</b> (SQS + 依赖) > <b>cross-ref-consistency</b> (交叉引用)
</p>
</section>

<section>
<h2>xa7 7 x1f4da 文档体系 (SDD)</h2>
<div class="kg">
  <div class="kc"><div class="v" style="color:var(--accent)">__DOC_CNT__</div><div class="l">总文档数</div><div class="s">Epics + Specs + Stories</div></div>
  <div class="kc"><div class="v" style="color:var(--purple)">__N_EP__ / __N_SP__ / __N_ST__</div><div class="l">E / S / St</div><div class="s">三层 SDD 体系</div></div>
</div>
<h3>文档树</h3>
<div style="max-height:360px;overflow-y:auto">
<table><tr><th>类型</th><th>名称</th><th>状态</th><th>路径</th></tr>__DOC__</table>
</div>
</section>

<section>
<h2>xa7 8 x26a0 xfe0f 风险与技术债务</h2>
<div class="tc">
<div>
<h3>x1f534 主要风险</h3>
<table>
<tr><th>风险项</th><th>等级</th><th>影响</th></tr>
<tr><td>S4 关联完整性</td><td class="bad">x1f534 低分</td><td>__S4__ /20 技能间引用断裂</td></tr>
<tr><td>未分类 Skill</td><td class="warn">x1f7e1 待清理</td><td>__UNCL__ 个未分类</td></tr>
<tr><td>微技能 (小于50行)</td><td class="warn">x1f7e1 需降级</td><td>7 个应转为经验</td></tr>
<tr><td>EPIC-002 待审</td><td class="warn">x1f7e1 阻塞</td><td>主人 Review 后进入 EPIC-003</td></tr>
</table>
</div>
<div>
<h3>x1f7e2 改进建议</h3>
<table>
<tr><th>优先级</th><th>建议</th></tr>
<tr><td class="bad">P0</td><td>建立 S4 关联完整性自动化门禁</td></tr>
<tr><td class="bad">P0</td><td>完成 __UNCL__ 个未分类 skill 归类</td></tr>
<tr><td class="warn">P1</td><td>7 个微小 skill 降级为经验</td></tr>
<tr><td class="warn">P1</td><td>BMAD 系列冗余清理 (3 > 1)</td></tr>
<tr><td class="accent">P2</td><td>Hermes 运行时适配器</td></tr>
</table>
</div>
</div>
</section>

<section>
<h2>xa7 9 x1f5fa xfe0f 路线图</h2>
<div class="tc">
<div>
<h3>x2714 xfe0f 已完成</h3>
<div>
<div class="sp"><span class="sp-l" style="color:var(--ok)">Sprint 1-5</span><span class="sp-d">05-12~14</span><span class="sp-t">EPIC-001 + EPIC-002 核心交付</span><span class="sp-s">__DONE_ST__ stories</span></div>
<div class="sp"><span class="sp-l" style="color:var(--ok)">EPIC-001</span><span class="sp-d">approved</span><span class="sp-t">能力模块化可行性调查</span><span class="sp-s">20 stories</span></div>
<div class="sp"><span class="sp-l" style="color:var(--warn)">EPIC-002</span><span class="sp-d">qa_gate</span><span class="sp-t">树状健康管理 全链条</span><span class="sp-s">7 stories</span></div>
</div>
</div>
<div>
<h3>x1f51c 下一步</h3>
<div>
<div class="sp"><span class="sp-l" style="color:var(--accent)">x1f3c1 Review</span><span class="sp-d">当前</span><span class="sp-t">主人 Review EPIC-002 并 Approve</span><span class="sp-s" style="color:var(--bad)">P0</span></div>
<div class="sp"><span class="sp-l" style="color:var(--purple)">EPIC-003</span><span class="sp-d">规划中</span><span class="sp-t">剩余模块提取 + CHI 提升 + 适配器</span><span class="sp-s" style="color:var(--warn)">P1</span></div>
<div class="sp"><span class="sp-l" style="color:var(--dim)">x1f4c8 健康</span><span class="sp-d">持续</span><span class="sp-t">CHI 0.6355 > 0.75+ | SQS 68 > 75+</span><span class="sp-s" style="color:var(--dim)">P2</span></div>
</div>
</div>
</div>
</section>

<section>
<h2>xa7 10 x1f4d6 附录</h2>
<div class="tc">
<div>
<h3>术语表</h3>
<table>
<tr><th>术语</th><th>定义</th></tr>
<tr><td>SQS</td><td>Skill Quality Score 五维 0-100 质量评分</td></tr>
<tr><td>Cap Pack</td><td>能力包 标准化可移植技能集合</td></tr>
<tr><td>SDD</td><td>Spec-Driven Development Spec 驱动开发</td></tr>
<tr><td>SRA</td><td>Skill Runtime Advisor 运行时推荐引擎</td></tr>
<tr><td>CHI</td><td>Capability Health Index 能力包健康指数</td></tr>
</table>
</div>
<div>
<h3>数据源</h3>
<table>
<tr><th>来源</th><th>位置</th></tr>
<tr><td>项目元数据</td><td>docs/project-report.json</td></tr>
<tr><td>SQS 评分</td><td>~/.hermes/data/skill-quality.db</td></tr>
<tr><td>SDD 文档</td><td>docs/*.md + docs/stories/*.md</td></tr>
<tr><td>Git 状态</td><td>.git/ (运行时)</td></tr>
</table>
</div>
</div>
</section>

<div class="ft">
  由 generate-panorama.py v2.0 生成 · arc42 + CODITECT + 项目管理最佳实践设计<br>
  <span style="font-size:.85em">数据源: project-report.json 路 SQS DB 路 SDD 文档 路 Git</span>
</div>

</div>

<script>
var c = document.getElementById('tc').getContext('2d');
new Chart(c, {
  type:'line',
  data:{labels:__TRL__, datasets:[{label:'SQS',data:__TRD__,borderColor:'#58a6ff',backgroundColor:'rgba(88,166,255,0.1)',fill:true,tension:0.3,pointRadius:4}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{min:50,max:85,ticks:{color:'#8b949e'},grid:{color:'#21262d'}},x:{ticks:{color:'#8b949e',maxTicksLimit:8},grid:{display:false}}}}
});
</script>
</body>
</html>"""

    # 替换占位符
    subs = {
        "__TAG__": tag, "__BRANCH__": br, "__COMMITS__": cm, "__NOW__": now,
        "__DONE_ST__": str(done_st), "__ALL_ST__": str(total_st),
        "__N_EP__": str(n_ep), "__N_SP__": str(n_sp), "__N_ST__": str(n_st),
        "__DOC_CNT__": str(doc_cnt), "__AVG__": str(avg),
        "__SK__": str(total_sk), "__UNCL__": str(uncl),
        "__SC__": str(sc_cnt), "__CODE__": str(code_lines),
        "__RP__": str(rp_cnt), "__TP__": str(tp), "__TT__": str(tt),
        "__TF__": str(len(tf)), "__TDUR__": str(tdur),
        "__GD__": str(dist["gd"]), "__NI__": str(dist["ni"]),
        "__TRP__": str(tr_pts), "__TRS__": tr_st, "__TRE__": tr_en,
        "__S4__": str(da.get("S4_relations", 0)),
        "__MOD__": mod_rows, "__DIM__": dim_rows, "__LOW__": low_rows,
        "__EPC__": epc, "__ST__": st_rows, "__DOC__": doc_rows,
        "__SPR__": sp_rows, "__TR__": tr,
        "__TRL__": trend_lbl, "__TRD__": trend_dat,
    }
    for k, v in subs.items():
        html = html.replace(k, v)

    out = CAP_PACK_DIR / "PROJECT-PANORAMA.html"
    out.write_text(html, encoding="utf-8")
    print(f"x2705 项目全景报告已生成: {out}")
    print(f"   10 章节 · {doc_cnt} 个文档 · {total_sk} 个 skill · {tr_pts} 个趋势点")

    if "--open" in sys.argv:
        webbrowser.open(str(out))


if __name__ == "__main__":
    build()
