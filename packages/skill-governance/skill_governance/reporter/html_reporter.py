"""HTML reporter — dark theme with Chart.js bar charts and L0-L4 progress bars."""

from __future__ import annotations

from typing import Any, Optional

from skill_governance.models.result import ScanReport


class HTMLReporter:
    """Produces a dark-themed HTML report with Chart.js bar charts."""

    CHARTJS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"

    def generate(self, report: ScanReport, output_path: Optional[str] = None) -> str:
        """Generate dark-theme HTML report string and optionally write to file."""
        html = self._build_html(report)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

        return html

    def _build_html(self, report: ScanReport) -> str:
        status = report.overall_status
        status_emoji = {
            "orchestrated": "🔄",
            "excellent": "🏆",
            "healthy": "🟢",
            "needs_improvement": "🟡",
            "compliant": "✅",
            "non_compliant": "❌",
        }.get(status, "❓")

        layers_data = []
        for lid in ["L0", "L1", "L2", "L3", "L4"]:
            lr = report.layers.get(lid)
            if lr:
                layers_data.append(
                    {
                        "id": lid,
                        "name": lr.layer_name,
                        "passed": lr.passed,
                        "score": lr.score,
                        "checks_passed": lr.checks_passed,
                        "checks_total": lr.checks_total,
                        "blocking_failure": lr.blocking_failure,
                        "has_blocking": lr.has_blocking_failures(),
                        "checks": [
                            {
                                "rule_id": c.rule_id,
                                "description": c.description,
                                "severity": c.severity,
                                "passed": c.passed,
                                "score": c.score,
                                "suggestions": c.suggestions,
                            }
                            for c in lr.checks
                        ],
                    }
                )

        checks_json = self._to_json(layers_data)
        summary_json = self._to_json(
            {
                "target_path": report.target_path,
                "timestamp": report.timestamp,
                "overall_status": status,
                "terminated": report.terminated,
            }
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Skill Governance Report — {report.target_path}</title>
<script src="{self.CHARTJS_CDN}"></script>
<style>
  :root {{
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-card: #1c2128;
    --border: #30363d;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --accent-green: #3fb950;
    --accent-red: #f85149;
    --accent-yellow: #d29922;
    --accent-blue: #58a6ff;
    --accent-purple: #bc8cff;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    padding: 24px;
    line-height: 1.6;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{ font-size: 1.75rem; margin-bottom: 8px; }}
  h2 {{ font-size: 1.3rem; margin-bottom: 16px; color: var(--text-primary); }}
  h3 {{ font-size: 1.1rem; margin-bottom: 8px; }}
  .meta {{ color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 24px; }}
  .meta span {{ margin-right: 24px; }}
  .status-badge {{
    display: inline-block; padding: 6px 16px; border-radius: 20px;
    font-weight: 600; font-size: 0.95rem;
  }}
  .status-orchestrated {{ background: #1a3a2a; color: #7ee787; }}
  .status-excellent {{ background: #1a2a3a; color: #79c0ff; }}
  .status-healthy {{ background: #1a3a2a; color: #7ee787; }}
  .status-needs_improvement {{ background: #3a2a1a; color: #e3b341; }}
  .status-compliant {{ background: #1a3a2a; color: #7ee787; }}
  .status-non_compliant {{ background: #3a1a1a; color: #f85149; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .card {{
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px;
    padding: 20px; transition: border-color 0.2s;
  }}
  .card:hover {{ border-color: var(--accent-blue); }}
  .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
  .card-title {{ font-weight: 600; font-size: 1.05rem; }}
  .card-score {{ font-size: 1.5rem; font-weight: 700; }}
  .score-green {{ color: var(--accent-green); }}
  .score-yellow {{ color: var(--accent-yellow); }}
  .score-red {{ color: var(--accent-red); }}
  .progress-bar {{
    width: 100%; height: 8px; background: var(--bg-secondary); border-radius: 4px;
    margin: 8px 0 4px; overflow: hidden;
  }}
  .progress-fill {{
    height: 100%; border-radius: 4px; transition: width 0.5s ease;
  }}
  .progress-green {{ background: var(--accent-green); }}
  .progress-yellow {{ background: var(--accent-yellow); }}
  .progress-red {{ background: var(--accent-red); }}
  .check-count {{ font-size: 0.85rem; color: var(--text-secondary); }}
  .chart-container {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 24px; }}
  .chart-wrapper {{ position: relative; height: 300px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
  th {{ text-align: left; padding: 8px 12px; font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary); border-bottom: 1px solid var(--border); }}
  td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
  .pass {{ color: var(--accent-green); font-weight: 600; }}
  .fail {{ color: var(--accent-red); font-weight: 600; }}
  .severity-blocking {{ color: var(--accent-red); }}
  .severity-warning {{ color: var(--accent-yellow); }}
  .severity-info {{ color: var(--accent-blue); }}
  .suggestions {{ margin-top: 4px; font-size: 0.85rem; color: var(--text-secondary); }}
  .suggestions li {{ margin-left: 16px; }}
  .footer {{ text-align: center; color: var(--text-secondary); font-size: 0.8rem; margin-top: 48px; padding: 16px; border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="container">
  <div style="display:flex;align-items:center;gap:16px;margin-bottom:8px;">
    <h1>{status_emoji} Governance Scan Report</h1>
    <span class="status-badge status-{status}">{status}</span>
  </div>
  <div class="meta">
    <span>📁 {report.target_path}</span>
    <span>🕐 {report.timestamp}</span>
    <span>🔚 {'Terminated early' if not report.terminated else 'Complete scan'}</span>
  </div>

  <h2>L0-L4 Layer Summary</h2>
  <div class="cards">
    {''.join(self._layer_card(ld) for ld in layers_data)}
  </div>

  <div class="chart-container">
    <h3>Layer Scores</h3>
    <div class="chart-wrapper">
      <canvas id="scoreChart"></canvas>
    </div>
  </div>

  {''.join(self._layer_detail(ld) for ld in layers_data)}

  <div class="footer">
    Generated by skill-governance engine &bull; CAP-PACK-STANDARD v1.0
  </div>
</div>

<script>
const layers = {checks_json};
const summary = {summary_json};

// Score chart
const ctx = document.getElementById('scoreChart').getContext('2d');
new Chart(ctx, {{
  type: 'bar',
  data: {{
    labels: layers.map(l => l.id + ': ' + l.name),
    datasets: [{{
      label: 'Score (%)',
      data: layers.map(l => Math.round(l.score)),
      backgroundColor: layers.map(l =>
        l.score >= 80 ? 'rgba(63, 185, 80, 0.7)' :
        l.score >= 50 ? 'rgba(210, 153, 34, 0.7)' :
        'rgba(248, 81, 73, 0.7)'
      ),
      borderColor: layers.map(l =>
        l.score >= 80 ? '#3fb950' :
        l.score >= 50 ? '#d29922' :
        '#f85149'
      ),
      borderWidth: 1,
      borderRadius: 4,
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
    }},
    scales: {{
      y: {{ beginAtZero: true, max: 100, grid: {{ color: '#30363d' }}, ticks: {{ color: '#8b949e' }} }},
      x: {{ grid: {{ display: false }}, ticks: {{ color: '#8b949e' }} }}
    }}
  }}
}});
</script>
</body>
</html>"""

    def _layer_card(self, ld: dict[str, Any]) -> str:
        score = ld["score"]
        score_class = "score-green" if score >= 80 else "score-yellow" if score >= 50 else "score-red"
        prog_class = "progress-green" if score >= 80 else "progress-yellow" if score >= 50 else "progress-red"
        passed_str = "✅ Passed" if ld["passed"] else "❌ Failed"
        if ld["has_blocking"]:
            passed_str += " (blocking)"

        return f"""<div class="card">
    <div class="card-header">
      <span class="card-title">{ld["id"]}: {ld["name"]}</span>
      <span class="card-score {score_class}">{score:.1f}%</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill {prog_class}" style="width:{score:.1f}%"></div>
    </div>
    <div class="check-count">
      {passed_str} &bull; {ld["checks_passed"]}/{ld["checks_total"]} checks
    </div>
  </div>"""

    def _layer_detail(self, ld: dict[str, Any]) -> str:
        if not ld["checks"]:
            return ""
        rows = ""
        for c in ld["checks"]:
            status = "✅ PASS" if c["passed"] else "❌ FAIL"
            status_class = "pass" if c["passed"] else "fail"
            sev_class = f"severity-{c['severity']}"
            suggestions_html = ""
            if c.get("suggestions"):
                items = "".join(f"<li>{s}</li>" for s in c["suggestions"][:3])
                suggestions_html = f'<ul class="suggestions">{items}</ul>'
            rows += f"""<tr>
      <td><span class="{sev_class}">{c["severity"].upper()}</span></td>
      <td><strong>{c["rule_id"]}</strong></td>
      <td>{c["description"]}</td>
      <td><span class="{status_class}">{status}</span></td>
      <td>{c["score"]:.1f}%{suggestions_html}</td>
    </tr>"""

        return f"""<div class="chart-container">
  <h3>{ld["id"]}: {ld["name"]} — Detailed Checks</h3>
  <table>
    <thead>
      <tr><th>Severity</th><th>Rule</th><th>Description</th><th>Status</th><th>Score</th></tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""

    @staticmethod
    def _to_json(obj: Any) -> str:
        import json

        return json.dumps(obj, indent=2, ensure_ascii=False)
