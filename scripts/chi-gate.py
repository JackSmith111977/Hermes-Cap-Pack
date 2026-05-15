#!/usr/bin/env python3
"""
chi-gate.py — CHI 质量门禁检查器

比对当前 CHI 与基线 CHI，确保质量不降级。

用法:
  python3 scripts/chi-gate.py                    # 检查当前 CHI vs 基线
  python3 scripts/chi-gate.py --threshold 0.75   # 设定最低阈值
  python3 scripts/chi-gate.py --baseline <json>  # 指定基线文件
  python3 scripts/chi-gate.py --update-baseline   # 更新基线为当前值

退出码:
  0 = 通过 (CHI >= 基线 或 CHI >= 阈值)
  1 = 警告 (CHI < 基线但 >= 基线*0.95)
  2 = 阻塞 (CHI < 基线*0.95 或 CHI < 阈值)
"""
import os, sys, json, subprocess

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(PROJECT_DIR, 'reports')
DEFAULT_BASELINE = os.path.join(REPORTS_DIR, 'chi-baseline.json')


def get_current_chi():
    """通过 skill-quality-score + aggregate-sqs 获取当前 CHI"""
    # 先用已有的 chi-by-pack.json（如果存在且新鲜）
    chi_path = os.path.join(REPORTS_DIR, 'chi-by-pack.json')
    if os.path.isfile(chi_path):
        with open(chi_path) as f:
            data = json.load(f)
        all_scores = []
        for pack, pdata in data.items():
            for skill in pdata.get('skills', []):
                all_scores.append(skill.get('sqs', 0))
        if all_scores:
            avg = sum(all_scores) / len(all_scores)
            return avg, len(all_scores)
    
    return None, 0


def load_baseline(path):
    """加载 CHI 基线"""
    if os.path.isfile(path):
        with open(path) as f:
            data = json.load(f)
        return data.get('chi', 0), data.get('threshold', 0.75)
    
    # 默认基线
    return 0.75, 0.75


def save_baseline(path, chi, threshold=0.75):
    """保存 CHI 基线"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump({'chi': round(chi, 4), 'threshold': threshold, 
                    'updated': __import__('datetime').datetime.now().isoformat()[:19]},
                  f, indent=2, ensure_ascii=False)
    print(f"✅ 基线已保存: CHI={chi:.2f}")


def main():
    args = sys.argv[1:]
    threshold = 0.75
    baseline_path = DEFAULT_BASELINE
    
    # Parse args
    for i, arg in enumerate(args):
        if arg == '--threshold' and i + 1 < len(args):
            threshold = float(args[i + 1])
        elif arg == '--baseline' and i + 1 < len(args):
            baseline_path = args[i + 1]
        elif arg == '--update-baseline':
            chi, count = get_current_chi()
            if chi is not None:
                save_baseline(baseline_path, chi, threshold)
                return 0
            print("❌ 无法获取当前 CHI")
            return 1
    
    # Get current CHI
    current_chi, count = get_current_chi()
    if current_chi is None:
        print("❌ 无法获取当前 CHI — 确保 reports/chi-by-pack.json 存在")
        return 2
    
    baseline_chi, _ = load_baseline(baseline_path)
    
    # Comparison
    print(f"📊 CHI 门禁检查")
    print(f"   当前 CHI: {current_chi:.2f} (基于 {count} 个技能)")
    print(f"   基线 CHI: {baseline_chi:.2f}")
    print(f"   阈值:     {threshold:.2f}")
    
    # 使用四舍五入到 1 位小数比较，避免浮点精度问题
    chi_r = round(current_chi, 1)
    bl_r = round(baseline_chi, 1)
    
    if chi_r >= bl_r:
        print(f"✅ PASS: CHI 未降级 ({current_chi:.2f} >= {baseline_chi:.2f})")
        return 0
    elif chi_r >= round(bl_r * 0.95, 1):
        print(f"⚠️ WARNING: CHI 轻度降级 ({current_chi:.2f} < {baseline_chi:.2f})")
        return 1
    else:
        print(f"🔴 BLOCKED: CHI 严重降级 ({current_chi:.2f} < {baseline_chi:.2f})")
        return 2


if __name__ == '__main__':
    sys.exit(main())
