#!/usr/bin/env python3
"""
health-dashboard.py v1.0 — Skill 健康趋势仪表盘生成器

从 SQS 数据库读取历史数据，生成 HTML 仪表盘（Chart.js 可视化）。

用法:
  python3 health-dashboard.py                          # 生成仪表盘
  python3 health-dashboard.py --output /path/to.html   # 指定输出路径
  python3 health-dashboard.py --open                   # 生成并打开浏览器
  python3 health-dashboard.py --cron                   # cron 模式（静默生成）

输出: reports/health-dashboard.html（默认）
"""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 路径 ──
CAP_PACK_DIR = Path.home() / "projects" / "hermes-cap-pack"
REPORTS_DIR = CAP_PACK_DIR / "reports"
DB_PATH = Path.home() / ".hermes" / "data" / "skill-quality.db"

# ── 18 模块定义（用 emoji + 名称） ──
MODULES = [
    ("📚", "知识库系统", "knowledge-base"),
    ("🧠", "学习引擎", "learning-engine"),
    ("📄", "文档生成", "doc-engine"),
    ("💻", "开发工作流", "developer-workflow"),
    ("🔒", "安全审计", "security-audit"),
    ("✅", "质量保障", "quality-assurance"),
    ("🔧", "运维监控", "devops-monitor"),
    ("🌐", "网络代理", "network-proxy"),
    ("💬", "消息平台", "messaging"),
    ("🤖", "Agent 协作", "agent-orchestration"),
    ("🔌", "MCP 集成", "mcp-integration"),
    ("📊", "金融分析", "financial-analysis"),
    ("🎨", "创意设计", "creative-design"),
    ("🎵", "音视频媒体", "media-processing"),
    ("🐙", "GitHub 生态", "github-ecosystem"),
    ("📰", "新闻研究", "news-research"),
    ("🪞", "元认知系统", "metacognition"),
    ("🎮", "社交娱乐", "social-gaming"),
]


def get_db():
    """获取 SQS 数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_module_for_skill(skill_name):
    """模糊匹配 skill 到模块（基于 skill-tree-index 的分类规则）"""
    rules = [
        (["knowledge", "precipitation", "routing", "llm-wiki", "file-classification"], "knowledge-base"),
        (["learning", "skill-creator", "deep-research", "night-study"], "learning-engine"),
        (["pdf", "pptx", "docx", "html-guide", "markdown", "latex", "epub", "doc-design", "readme-for-ai"], "doc-engine"),
        (["plan", "writing-plans", "sdd", "systematic-debugging", "tdd", "subagent", "spike", "git-advanced", "python-env", "patch-file"], "developer-workflow"),
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
    name_lower = skill_name.lower()
    for keywords, module in rules:
        for kw in keywords:
            if kw.lower() in name_lower:
                return module
    return "unclassified"


def collect_data():
    """从 SQS 数据库收集仪表盘所需数据"""
    conn = get_db()

    # ── 总体健康度 ──
    cur = conn.execute("SELECT AVG(sqs_total) as avg_sqs, COUNT(*) as total FROM scores")
    row = cur.fetchone()
    overall_avg = round(row["avg_sqs"], 1) if row["avg_sqs"] else 0
    total_skills = row["total"]

    # ── 分布 ──
    dist = {}
    for label, lo, hi in [("优秀", 90, 101), ("良好", 70, 90), ("需改进", 50, 70), ("不合格", 0, 50)]:
        cur = conn.execute("SELECT COUNT(*) FROM scores WHERE sqs_total >= ? AND sqs_total < ?", (lo, hi))
        dist[label] = cur.fetchone()[0]

    # ── SQS 历史趋势（按天聚合） ──
    cur = conn.execute("""
        SELECT DATE(scored_at) as day, AVG(sqs_total) as avg_sqs
        FROM score_history
        GROUP BY DATE(scored_at)
        ORDER BY day ASC
    """)
    trend_rows = cur.fetchall()
    trend_labels = [r["day"] for r in trend_rows]
    trend_data = [round(r["avg_sqs"], 1) for r in trend_rows]

    # ── 各模块健康度（当前最新 + 历史） ──
    cur = conn.execute("SELECT skill_name, sqs_total FROM scores")
    all_scores = cur.fetchall()

    module_current = {}  # module_id -> [sqs_scores]
    for r in all_scores:
        mod = get_module_for_skill(r["skill_name"])
        if mod not in module_current:
            module_current[mod] = []
        module_current[mod].append(r["sqs_total"])

    module_avgs = {}
    for mod_id, scores in module_current.items():
        module_avgs[mod_id] = round(sum(scores) / len(scores), 1)

    # 按 18 模块顺序排列
    module_labels = []
    module_radar = []
    for emoji, name, mod_id in MODULES:
        if mod_id in module_avgs:
            module_labels.append(f"{emoji} {name}")
            module_radar.append(module_avgs[mod_id])
        else:
            module_labels.append(f"{emoji} {name}")
            module_radar.append(0)

    # ── 低分 skill 排行榜 ──
    cur = conn.execute("""
        SELECT skill_name, sqs_total, version
        FROM scores
        ORDER BY sqs_total ASC
        LIMIT 15
    """)
    low_scores = [{"name": r["skill_name"], "sqs": r["sqs_total"], "version": r["version"]} for r in cur.fetchall()]

    # ── 高分 skill 排行榜 ──
    cur = conn.execute("""
        SELECT skill_name, sqs_total, version
        FROM scores
        ORDER BY sqs_total DESC
        LIMIT 5
    """)
    high_scores = [{"name": r["skill_name"], "sqs": r["sqs_total"], "version": r["version"]} for r in cur.fetchall()]

    # ── 退化检测：对比最新两次历史记录 ──
    degradation = []
    cur = conn.execute("""
        SELECT skill_name, sqs_total, scored_at
        FROM score_history
        ORDER BY scored_at ASC
    """)
    all_hist = cur.fetchall()
    # 按 skill 分组找到最早和最新的评分
    skill_first = {}
    skill_last = {}
    for r in all_hist:
        skill = r["skill_name"]
        if skill not in skill_first:
            skill_first[skill] = r
        skill_last[skill] = r
    for skill in skill_last:
        if skill in skill_first:
            first_sqs = skill_first[skill]["sqs_total"]
            last_sqs = skill_last[skill]["sqs_total"]
            delta = last_sqs - first_sqs
            skill_first_sqs = first_sqs
            skill_last_sqs = last_sqs
            if delta < -2:
                degradation.append({"name": skill, "delta": round(delta, 1), "from": round(skill_first_sqs, 1), "to": round(skill_last_sqs, 1)})
    degradation.sort(key=lambda x: x["delta"])
    degradation = degradation[:8]

    # ── 每个模块的 skill 计数 ──
    module_counts = {}
    for r in all_scores:
        mod = get_module_for_skill(r["skill_name"])
        module_counts[mod] = module_counts.get(mod, 0) + 1

    conn.close()

    return {
        "overall_avg": overall_avg,
        "total_skills": total_skills,
        "distribution": dist,
        "trend_labels": trend_labels,
        "trend_data": trend_data,
        "module_labels": module_labels,
        "module_radar": module_radar,
        "module_counts": module_counts,
        "low_scores": low_scores,
        "high_scores": high_scores,
        "degradation": degradation,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def health_level(sqs):
    """返回健康度等级标签"""
    if sqs >= 80:
        return "🟢 优秀"
    elif sqs >= 60:
        return "🟡 良好"
    elif sqs >= 40:
        return "🟠 需关注"
    return "🔴 危险"


def generate_html(data):
    """生成 Chart.js 仪表盘 HTML"""
    trend_labels_json = json.dumps(data["trend_labels"], ensure_ascii=False)
    trend_data_json = json.dumps(data["trend_data"])
    module_labels_json = json.dumps(data["module_labels"], ensure_ascii=False)
    module_radar_json = json.dumps(data["module_radar"])
    low_score_rows = "".join(
        f'<tr><td>{s["name"]}</td><td>{s["sqs"]:.1f}</td><td class="{"bad" if s["sqs"]<55 else "warn" if s["sqs"]<65 else "ok"}">{health_level(s["sqs"])}</td></tr>'
        for s in data["low_scores"]
    )
    high_score_rows = "".join(
        f'<tr><td>{s["name"]}</td><td>{s["sqs"]:.1f}</td><td class="ok">{health_level(s["sqs"])}</td></tr>'
        for s in data["high_scores"]
    )
    deg_rows = "".join(
        f'<tr><td>{d["name"]}</td><td class="bad">{d["from"]:.1f} → {d["to"]:.1f}</td><td class="bad">{d["delta"]:+.1f}</td></tr>'
        for d in data["degradation"]
    )

    # 模块分布表
    module_dist_rows = "".join(
        f'<tr><td>{data["module_labels"][i]}</td><td>{data["module_radar"][i]:.1f}</td>'
        f'<td>{data["module_counts"].get(MODULES[i][2], 0)}</td></tr>'
        for i in range(len(MODULES)) if MODULES[i][2] in data["module_counts"]
    )

    overall = data["overall_avg"]
    overall_level = health_level(overall)
    trend_dir = "↗" if len(data["trend_data"]) >= 2 and data["trend_data"][-1] > data["trend_data"][0] else "↘" if len(data["trend_data"]) >= 2 and data["trend_data"][-1] < data["trend_data"][0] else "→"

    dist = data["distribution"]
    dist_bar = (
        f'<div class="dist-bar"><span class="dist-excellent" style="width:{dist["优秀"]/2}%">{dist["优秀"]}</span>'
        f'<span class="dist-good" style="width:{dist["良好"]/2}%">{dist["良好"]}</span>'
        f'<span class="dist-needs" style="width:{dist["需改进"]/2}%">{dist["需改进"]}</span>'
        f'<span class="dist-fail" style="width:{max(1,dist["不合格"]/2)}%">{dist["不合格"]}</span></div>'
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🌳 Hermes Skill 健康仪表盘</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0d1117;
    --card: #161b22;
    --border: #30363d;
    --text: #c9d1d9;
    --text-dim: #8b949e;
    --green: #3fb950;
    --yellow: #d29922;
    --red: #f85149;
    --blue: #58a6ff;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; padding:20px; }}
  .container {{ max-width:1400px; margin:0 auto; }}
  h1 {{ font-size:1.8rem; margin-bottom:5px; }}
  .subtitle {{ color:var(--text-dim); font-size:0.9rem; margin-bottom:20px; }}
  .grid {{ display:grid; gap:16px; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); margin-bottom:20px; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:8px; padding:18px; }}
  .card h2 {{ font-size:1rem; color:var(--text-dim); margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px; }}
  .stat-value {{ font-size:2.5rem; font-weight:700; }}
  .stat-bar {{ margin-top:8px; font-size:0.85rem; color:var(--text-dim); }}
  .full-width {{ grid-column:1 / -1; }}
  .chart-container {{ position:relative; height:320px; }}
  .chart-container.radar {{ height:380px; }}
  .chart-container.trend {{ height:280px; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.85rem; }}
  th, td {{ padding:8px 10px; text-align:left; border-bottom:1px solid var(--border); }}
  th {{ color:var(--text-dim); font-weight:500; }}
  .ok {{ color:var(--green); }}
  .warn {{ color:var(--yellow); }}
  .bad {{ color:var(--red); }}
  .dist-bar {{ display:flex; height:24px; border-radius:12px; overflow:hidden; margin-top:10px; }}
  .dist-bar span {{ display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:600; min-width:24px; }}
  .dist-excellent {{ background:#2ea043; }}
  .dist-good {{ background:#d29922; }}
  .dist-needs {{ background:#f0883e; }}
  .dist-fail {{ background:#da3633; }}
  .footer {{ text-align:center; color:var(--text-dim); font-size:0.8rem; padding:20px; border-top:1px solid var(--border); margin-top:20px; }}
  .degradation-list {{ list-style:none; }}
  .degradation-list li {{ padding:6px 0; border-bottom:1px solid var(--border); }}
  .degradation-list li:last-child {{ border-bottom:none; }}
  .badge {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:0.75rem; font-weight:600; }}
  .badge-green {{ background:rgba(63,185,80,0.15); color:var(--green); }}
  .badge-yellow {{ background:rgba(210,153,34,0.15); color:var(--yellow); }}
  .badge-red {{ background:rgba(248,81,73,0.15); color:var(--red); }}
  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  @media (max-width:768px) {{ .two-col {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<div class="container">

  <h1>🌳 Hermes Skill 健康仪表盘</h1>
  <p class="subtitle">生成于 {data["generated_at"]} · 共 {data["total_skills"]} 个 skill</p>

  <div class="grid">
    <div class="card">
      <h2>📊 总体健康度</h2>
      <div class="stat-value">{overall}<span style="font-size:1.2rem;margin-left:8px;">{trend_dir}</span></div>
      <div class="stat-bar">{overall_level} · 满分 100</div>
      {dist_bar}
    </div>
    <div class="card">
      <h2>📈 分布</h2>
      <div style="margin-top:8px;">
        🟢 优秀: <strong class="ok">{dist["优秀"]}</strong><br>
        🟡 良好: <strong class="warn">{dist["良好"]}</strong><br>
        🟠 需改进: <strong style="color:#f0883e">{dist["需改进"]}</strong><br>
        🔴 不合格: <strong class="bad">{dist["不合格"]}</strong>
      </div>
    </div>
    <div class="card">
      <h2>🏆 Top 5</h2>
      <table>
        {high_score_rows if high_score_rows else '<tr><td colspan="3">暂无数据</td></tr>'}
      </table>
    </div>
  </div>

  <div class="two-col">
    <div class="card">
      <h2>📈 SQS 历史趋势</h2>
      <div class="chart-container trend">
        <canvas id="trendChart"></canvas>
      </div>
    </div>
    <div class="card">
      <h2>🎯 模块雷达图</h2>
      <div class="chart-container radar">
        <canvas id="radarChart"></canvas>
      </div>
    </div>
  </div>

  <div class="two-col">
    <div class="card full-width">
      <h2>📋 模块健康度详情</h2>
      <div style="max-height:400px;overflow-y:auto;">
      <table>
        <tr><th>模块</th><th>SQS 均分</th><th>Skill 数</th></tr>
        {module_dist_rows}
      </table>
      </div>
    </div>
  </div>

  <div class="two-col">
    <div class="card">
      <h2>⚠️ 退化检测 Top 8</h2>
      {f'<table><tr><th>Skill</th><th>变化</th><th>Δ</th></tr>{deg_rows}</table>' if data["degradation"] else '<p style="color:var(--green);">✅ 无显著退化</p>'}
    </div>
    <div class="card">
      <h2>🔻 低分 Skill 排行榜</h2>
      <div style="max-height:400px;overflow-y:auto;">
      <table>
        <tr><th>Skill</th><th>SQS</th><th>等级</th></tr>
        {low_score_rows}
      </table>
      </div>
    </div>
  </div>

  <p class="footer">
    数据源: skill-quality.db · 由 health-dashboard.py 自动生成
  </p>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {{
  // ── 趋势折线图 ──
  const trendCtx = document.getElementById('trendChart').getContext('2d');
  new Chart(trendCtx, {{
    type: 'line',
    data: {{
      labels: {trend_labels_json},
      datasets: [{{
        label: 'SQS 均分',
        data: {trend_data_json},
        borderColor: '#58a6ff',
        backgroundColor: 'rgba(88,166,255,0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#58a6ff',
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        y: {{ min: 50, max: 100, ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }} }},
        x: {{ ticks: {{ color: '#8b949e', maxTicksLimit: 8 }}, grid: {{ display: false }} }}
      }}
    }}
  }});

  // ── 模块雷达图 ──
  const radarCtx = document.getElementById('radarChart').getContext('2d');
  new Chart(radarCtx, {{
    type: 'radar',
    data: {{
      labels: {module_labels_json},
      datasets: [{{
        label: 'SQS 均分',
        data: {module_radar_json},
        borderColor: '#3fb950',
        backgroundColor: 'rgba(63,185,80,0.15)',
        pointBackgroundColor: '#3fb950',
        pointBorderColor: '#3fb950',
        pointRadius: 3,
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        r: {{
          min: 0, max: 100,
          ticks: {{ color: '#8b949e', backdropColor: 'transparent', stepSize: 20 }},
          grid: {{ color: '#21262d' }},
          angleLines: {{ color: '#21262d' }},
          pointLabels: {{ color: '#c9d1d9', font: {{ size: 10 }} }}
        }}
      }}
    }}
  }});
}});
</script>
</body>
</html>"""
    return html


def generate_dashboard(output_path=None, open_browser=False):
    """生成仪表盘 HTML"""
    data = collect_data()
    html = generate_html(data)

    out = Path(output_path) if output_path else REPORTS_DIR / "health-dashboard.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    print(f"✅ 健康仪表盘已生成: {out}")
    print(f"   📊 总体 SQS: {data['overall_avg']} | 趋势数据点: {len(data['trend_labels'])} | 退化项: {len(data['degradation'])}")

    if open_browser:
        subprocess.run(["xdg-open", str(out)] if sys.platform.startswith("linux") else ["open", str(out)])

    return out


def main():
    output_path = None
    open_browser = "--open" in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]

    if "--cron" in sys.argv:
        # cron 模式：静默生成
        generate_dashboard(output_path)
        return

    generate_dashboard(output_path, open_browser)


if __name__ == "__main__":
    main()
