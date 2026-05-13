#!/usr/bin/env python3
"""
ci-check-cross-refs.py — 跨包引用完整性检查（CI 使用）
验证所有 cap-pack.yaml 之间的 depends_on、experience skill_refs、
cluster skill 引用都指向存在的目标
"""

import yaml, sys, os
from pathlib import Path

packs_dir = Path('packs')
if not packs_dir.exists():
    packs_dir = Path(os.environ.get('GITHUB_WORKSPACE', '.')) / 'packs'

all_skills = {}
pack_names = set()

for pack_dir in sorted(packs_dir.iterdir()):
    manifest_file = pack_dir / 'cap-pack.yaml'
    if not manifest_file.exists():
        continue
    with open(manifest_file) as f:
        manifest = yaml.safe_load(f)
    pack_name = manifest.get('name', pack_dir.name)
    pack_names.add(pack_name)
    for skill in manifest.get('skills', []):
        skill_id = skill.get('id')
        if skill_id:
            all_skills[skill_id] = pack_name

errors = []
for pack_dir in sorted(packs_dir.iterdir()):
    manifest_file = pack_dir / 'cap-pack.yaml'
    if not manifest_file.exists():
        continue
    with open(manifest_file) as f:
        manifest = yaml.safe_load(f)
    pack_name = manifest.get('name', pack_dir.name)

    for dep_name in (manifest.get('depends_on') or {}):
        if dep_name not in pack_names:
            errors.append('{}: depends_on "{}" — pack not found'.format(pack_name, dep_name))

    for exp in manifest.get('experiences', []):
        for s_ref in exp.get('skill_refs', []):
            if s_ref not in all_skills:
                errors.append('{}/experiences/{}: skill_ref "{}" not found in any pack'.format(
                    pack_name, exp.get('id'), s_ref))

    pack_skills = {s.get('id') for s in manifest.get('skills', [])}
    for cluster in manifest.get('clusters', []):
        for s_ref in cluster.get('skills', []):
            if s_ref not in pack_skills:
                errors.append('{}/clusters/{}: skill "{}" not found in this pack'.format(
                    pack_name, cluster.get('id'), s_ref))

if errors:
    for err in errors:
        print('❌ ' + err)
    sys.exit(1)

print('✅ All cross-pack references are valid')
