#!/usr/bin/env python3
"""
ci-check-yaml.py — YAML 语法检查（CI 使用）
验证仓库中所有 .yaml/.yml 文件的 YAML 正确性
"""

import yaml, sys, os

errors = []
for root, dirs, files in os.walk('.'):
    if '.git' in root or 'node_modules' in root:
        continue
    dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '__pycache__')]
    for f in files:
        if f.endswith(('.yaml', '.yml')):
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    yaml.safe_load(fh)
            except Exception as e:
                errors.append('{}: {}'.format(path, e))

if errors:
    for err in errors:
        print('❌ ' + err)
    sys.exit(1)

print('✅ All YAML files are valid')
