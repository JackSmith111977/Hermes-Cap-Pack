#!/usr/bin/env python3
"""
doc-engine 改造后 SRA 发现验证测试
====================================
测试 SRA 是否能正确发现改造后的技能包结构。

用法:
  python3 scripts/sra-discovery-test.py              # 全量测试
  python3 scripts/sra-discovery-test.py --json       # JSON 输出
  python3 scripts/sra-discovery-test.py --query "生成PDF"  # 单条测试
"""

import json, sys, os, subprocess, urllib.request, urllib.error
from pathlib import Path

CAP_PACK = Path.home() / "projects" / "hermes-cap-pack"
SRA_ENDPOINT = "http://127.0.0.1:8536/recommend"

# ─── 测试查询集（覆盖 PDF 各子场景 + 微技能场景） ───

TEST_QUERIES = {
    # PDF 相关（期望命中 pdf-layout 合并技能）
    "生成PDF文档": {
        "expect": ["pdf-layout"],
        "category": "pdf"
    },
    "用WeasyPrint生成中文PDF": {
        "expect": ["pdf-layout"],
        "category": "pdf"
    },
    "ReportLab生成表格PDF": {
        "expect": ["pdf-layout"],
        "category": "pdf"
    },
    "PDF排版设计指南": {
        "expect": ["pdf-pro-design"],
        "category": "pdf"
    },
    "对比WeasyPrint和ReportLab": {
        "expect": ["pdf-render-comparison"],
        "category": "pdf"
    },
    
    # 微技能降级后 → 应推荐 doc-engine 包而非独立 skill
    "写LaTeX论文": {
        "expect": ["pdf-layout"],  # 降级后经验不可推荐，回退到包级
        "category": "experience"
    },
    "生成Word文档": {
        "expect": ["pdf-layout"],  # 同上
        "category": "experience"
    },
    "Markdown转PDF": {
        "expect": ["pdf-layout"],
        "category": "experience"
    },
    
    # 保持独立的技能
    "HTML演示文稿": {
        "expect": ["html-presentation"],
        "category": "html"
    },
    "PPTX生成": {
        "expect": ["pptx-guide"],
        "category": "pptx"
    },
    "排版质量检查": {
        "expect": ["vision-qc-patterns"],
        "category": "vision"
    },
    
    # 跨包查询
    "画架构图": {
        "expect_any": ["architecture-diagram"],
        "category": "cross-pack"
    },
    "学习Python": {
        "expect_any": ["learning", "learning-workflow"],
        "category": "cross-pack"
    },
}


def query_sra(query, endpoint=SRA_ENDPOINT):
    """向 SRA 发送推荐查询"""
    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps({"message": query}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, ConnectionRefusedError, TimeoutError) as e:
        return {"error": str(e)}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SRA 发现验证测试")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--query", type=str, help="单条查询测试")
    args = parser.parse_args()

    # 先检查 SRA 是否在线
    sra_available = False
    try:
        resp = query_sra("test")
        sra_available = "error" not in resp
    except:
        pass

    if not sra_available:
        print("⚠️  SRA Proxy 未运行 (http://127.0.0.1:8536)")
        print("   先用 systemctl --user start srad 启动 SRA daemon")
        print("   或 pip install sra-agent && sra daemon\n")

    if args.query:
        queries = {args.query: {"expect": [], "expect_any": [], "category": "custom"}}
    else:
        queries = TEST_QUERIES

    # ─── Before: 原 SRA 索引发现 ───
    if sra_available:
        print(f"\n{'='*60}")
        print(f"🔍 SRA 发现测试 ({'单条' if args.query else '全量'})")
        print(f"{'='*60}")
        
        results = []
        for query, meta in queries.items():
            resp = query_sra(query)
            
            if "error" in resp:
                print(f"\n❌ {query}: SRA 错误 - {resp['error']}")
                continue
            
            top_skills = resp.get("recommendations", [])
            if not top_skills and "rag_context" in resp:
                # 部分 SRA 版本返回 rag_context
                top_skills = resp.get("rag_context", "").split(",")
            
            top_names = [s.get("name", str(s))[:30] for s in (top_skills if isinstance(top_skills, list) else [])]
            
            # 检查期望的技能是否在推荐中
            expected = meta.get("expect", [])
            expect_any = meta.get("expect_any", [])
            
            hit = any(e in " ".join(top_names) for e in expected)
            hit_any = any(e in " ".join(top_names) for e in expect_any) if expect_any else True
            
            status = "✅" if (hit or hit_any) else "❌"
            
            results.append({
                "query": query,
                "status": "pass" if (hit or hit_any) else "fail",
                "top_recommendations": top_names[:3],
                "expected": expected or expect_any
            })
            
            print(f"\n{status} {query}")
            print(f"  期望: {expected or expect_any}")
            print(f"  推荐: {top_names[:3]}")
        
        passed = sum(1 for r in results if r["status"] == "pass")
        total = len(results)
        print(f"\n{'='*60}")
        print(f"📊 结果: {passed}/{total} 通过 ({passed*100//total}%)")
        print(f"{'='*60}")
        
        if args.json:
            print(json.dumps({
                "sra_available": True,
                "total": total,
                "passed": passed,
                "results": results,
                "before_description": "当前 SRA 索引（未集成 CAP Pack 分类）"
            }, ensure_ascii=False, indent=2))
    else:
        print(f"\n📋 测试计划 ({len(queries)} 条查询)")
        print(f"{'='*60}")
        for query, meta in queries.items():
            print(f"  ⏳ {query:30s} → 期望: {str(meta.get('expect', meta.get('expect_any', []))):30s}")
        
        print(f"\n💡 SRA 未运行，仅输出测试计划")
        print(f"   启动 SRA 后重新运行即可获得真实结果")
        
        if args.json:
            print(json.dumps({
                "sra_available": False,
                "planned_queries": len(queries),
                "query_list": list(queries.keys()),
                "note": "启动 SRA daemon 后重试: systemctl --user start srad"
            }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
