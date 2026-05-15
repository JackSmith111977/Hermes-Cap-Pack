#!/usr/bin/env python3
"""
fix-low-score-skills.py — v3 安全批量修复低分 skill frontmatter
直接在 --- 关闭标记前插入 depends_on/see_also。
"""
import os, sys, re, yaml

PACKS_DIR = "/home/ubuntu/projects/hermes-cap-pack/packs"

LOW_SKILLS = {
    'epub-guide':       {'depends_on': ['markdown-guide','html-guide'], 'see_also': ['pdf-layout','docx-guide']},
    'latex-guide':      {'depends_on': ['pdf-layout-weasyprint'], 'see_also': ['markdown-guide','docx-guide']},
    'markdown-guide':   {'depends_on': ['html-guide','pdf-layout-weasyprint'], 'see_also': ['epub-guide','latex-guide']},
    'docx-guide':       {'depends_on': ['markdown-guide'], 'see_also': ['pdf-layout-weasyprint','epub-guide','latex-guide']},
    'html-guide':       {'depends_on': ['markdown-guide'], 'see_also': ['epub-guide','pdf-layout-weasyprint']},
    'plan':             {'depends_on': ['writing-plans','spike'], 'see_also': ['test-driven-development','subagent-driven-development']},
    'one-three-one-rule': {'depends_on': ['writing-plans'], 'see_also': ['information-decomposition','anti-repetition-loop']},
    'test-driven-development': {'depends_on': ['python-testing','systematic-debugging'], 'see_also': ['subagent-driven-development','generic-dev-workflow']},
    'humanizer':        {'depends_on': ['writing-styles-guide'], 'see_also': ['sketch','ascii-art']},
    'manim-video':      {'depends_on': ['ascii-video'], 'see_also': ['p5js','sketch']},
    'p5js':             {'depends_on': ['sketch'], 'see_also': ['manim-video','claude-design']},
    'ascii-video':      {'depends_on': ['ascii-art'], 'see_also': ['manim-video','sketch','p5js']},
    'songwriting-and-ai-music': {'depends_on': ['songsee'], 'see_also': ['spotify','humanizer']},
    'ascii-art':        {'depends_on': ['sketch'], 'see_also': ['ascii-video','concept-diagrams']},
    'sketch':           {'depends_on': ['claude-design'], 'see_also': ['p5js','ascii-art','architecture-diagram']},
    'youtube-content':  {'depends_on': ['spotify'], 'see_also': ['songsee','gif-search']},
    'gif-search':       {'depends_on': ['youtube-content'], 'see_also': ['spotify','songsee']},
    'spotify':          {'depends_on': ['youtube-content'], 'see_also': ['gif-search','songwriting-and-ai-music']},
    'songsee':          {'depends_on': ['youtube-content','spotify'], 'see_also': ['gif-search','songwriting-and-ai-music']},
    'arxiv':            {'depends_on': ['llm-wiki','deep-research'], 'see_also': ['blogwatcher','ai-trends']},
    'blogwatcher':      {'depends_on': ['llm-wiki'], 'see_also': ['arxiv','ai-trends']},
    'llm-wiki':         {'depends_on': ['deep-research','blogwatcher'], 'see_also': ['arxiv','hermes-knowledge-base']},
    'pokemon-player':   {'depends_on': ['minecraft-modpack-server'], 'see_also': []},
    'minecraft-modpack-server': {'depends_on': ['pokemon-player'], 'see_also': []},
    'feishu-card-merge-streaming': {'depends_on': ['feishu','feishu-send-file'], 'see_also': ['feishu-batch-send']},
    'proxy-finder':     {'depends_on': ['clash-config','proxy-monitor'], 'see_also': ['docker-management']},
}


def inject_frontmatter_blocks(content, info):
    """注入 depends_on / see_also 块到 frontmatter 末尾"""
    # Find the closing --- of frontmatter
    m = re.match(r'^(---\n)(.*?)(\n---\n)(.*)', content, re.DOTALL)
    if not m:
        return content, False
    
    yaml_content = m.group(2)
    
    # Check if already has these fields
    if 'depends_on:' in yaml_content and 'see_also:' in yaml_content:
        return content, False
    
    lines = yaml_content.split('\n')
    deps = info.get('depends_on', [])
    refs = info.get('see_also', [])
    
    # Build new lines
    new_lines = []
    dep_done = 'depends_on:' in yaml_content
    see_done = 'see_also:' in yaml_content
    
    for line in lines:
        new_lines.append(line)
    
    # Insert before closing ---
    if not dep_done and deps:
        new_lines.append('depends_on:')
        for d in deps:
            new_lines.append(f'  - {d}')
    
    if not see_done and refs:
        new_lines.append('see_also:')
        for r in refs:
            new_lines.append(f'  - {r}')
    
    result = '---\n' + '\n'.join(new_lines) + '\n---\n' + m.group(4)
    
    if result == content:
        return content, False
    return result, True


def main():
    fixed = 0
    errors = []
    skipped = 0
    
    for skill_name, info in LOW_SKILLS.items():
        # Find the skill file
        for pack in os.listdir(PACKS_DIR):
            sk_path = os.path.join(PACKS_DIR, pack, 'SKILLS', skill_name, 'SKILL.md')
            if os.path.isfile(sk_path):
                break
        else:
            errors.append(f"{skill_name}: 未找到")
            continue
        
        with open(sk_path) as f:
            original = f.read()
        
        modified, changed = inject_frontmatter_blocks(original, info)
        if not changed:
            skipped += 1
            print(f"⏭️  {skill_name:35s} | 已有字段")
            continue
        
        # Validate YAML
        fm = re.match(r'^---\n(.*?)\n---\n', modified, re.DOTALL)
        try:
            yaml.safe_load(fm.group(1))
        except Exception as e:
            # Try to see what went wrong
            print(f"  YAML 错误: {e}")
            errors.append(f"{skill_name}: YAML 无效")
            continue
        
        with open(sk_path, 'w') as f:
            f.write(modified)
        fixed += 1
        pack_name = os.path.basename(os.path.dirname(os.path.dirname(sk_path)))
        print(f"✅ {skill_name:35s} | 包={pack_name:20s} | +depends_on/see_also")
    
    print(f"\n---\n✅ 修复: {fixed}, ⏭️ 已有: {skipped}, ❌ 错误: {len(errors)}")
    for e in errors:
        print(f"  ❌ {e}")
    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(main())
