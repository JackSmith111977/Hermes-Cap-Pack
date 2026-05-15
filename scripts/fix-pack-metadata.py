#!/usr/bin/env python3
"""
fix-pack-metadata.py — 补齐 16 个能力包的 cap-pack.yaml 元数据字段
确保每个包至少包含 name/version/description/author/triggers。
"""
import os, sys, yaml, re

PACKS_DIR = "/home/ubuntu/projects/hermes-cap-pack/packs"

# 元数据模板 — 每个包的描述和触发词
PACK_META = {
    'agent-orchestration': {
        'description': 'Agent 编排能力包。提供多智能体协调、任务委派和并行执行能力。适用场景：需要多个 AI agent 协同完成复杂任务时加载。',
        'triggers': ['agent 编排', '多智能体', '任务委派', '并行执行', 'delegate_task'],
        'author': 'Emma (小玛)'
    },
    'creative-design': {
        'description': '创意设计能力包。涵盖 SVG 图表、ASCII 艺术、视频制作、表情包等创意内容生成。适用场景：需要生成视觉创意内容或设计素材时加载。',
        'triggers': ['创意设计', 'SVG 图表', 'ASCII 艺术', '视频制作', '设计'],
        'author': 'Emma (小玛)'
    },
    'developer-workflow': {
        'description': '开发者工作流能力包。涵盖 TDD、代码审查、调试、计划编写等标准化开发流程。适用场景：任何开发实施任务，从规划到提交的完整工具链。',
        'triggers': ['开发工作流', 'TDD', '代码审查', '调试', '开发流程'],
        'author': 'Emma (小玛)'
    },
    'devops-monitor': {
        'description': '运维监控能力包。提供 Docker 管理、代理监控、健康检查等基础设施运维能力。适用场景：服务器运维、容器管理、代理节点健康监控。',
        'triggers': ['运维', '监控', 'Docker', '代理', '健康检查'],
        'author': 'Emma (小玛)'
    },
    'doc-engine': {
        'description': '文档引擎能力包。涵盖 PDF、HTML、Markdown、EPUB 等格式的文档生成与排版。适用场景：需要生成专业文档、报告或电子书时加载。',
        'triggers': ['文档引擎', 'PDF 生成', '排版', '报告生成', '文档排版'],
        'author': 'Emma (小玛)'
    },
    'financial-analysis': {
        'description': '金融分析能力包。基于 akshare 获取金融数据，ta 库计算技术指标，matplotlib 可视化分析。适用场景：股票分析、金融数据处理和可视化研报生成。',
        'triggers': ['金融分析', '股票数据', '技术指标', '数据分析', 'akshare'],
        'author': 'Emma (小玛)'
    },
    'github-ecosystem': {
        'description': 'GitHub 生态能力包。提供仓库管理、PR 工作流、代码审查、Issue 管理等完整 GitHub 操作能力。适用场景：Git 仓库运维和 GitHub 协作流程管理。',
        'triggers': ['GitHub', '仓库管理', 'PR 工作流', '代码审查', 'Issue'],
        'author': 'Emma (小玛)'
    },
    'learning-engine': {
        'description': '研究与学习引擎能力包。提供深度调研、论文检索、RSS 订阅、知识库构建等研究能力。适用场景：技术调研、学术研究、知识沉淀和学习新主题。',
        'triggers': ['学习引擎', '调研', '研究', '论文检索', '知识沉淀'],
        'author': 'Emma (小玛)'
    },
    'learning-workflow': {
        'description': '学习工作流能力包。强制状态机驱动的学习流程，防跳过机制确保深度理解。适用场景：从零学习新主题时，按 5 阶段循环迭代推进。',
        'triggers': ['学习工作流', '学习流程', '知识沉淀', '学习状态机', 'learning workflow'],
        'author': 'Emma (小玛)'
    },
    'media-processing': {
        'description': '媒体处理能力包。涵盖音视频处理、GIF 搜索、Spotify 控制等多媒体操作。适用场景：媒体内容消费、音频可视化和音乐创作场景。',
        'triggers': ['媒体处理', '音视频', 'GIF', '音乐', 'Spotify'],
        'author': 'Emma (小玛)'
    },
    'messaging': {
        'description': '消息平台能力包。提供飞书、微信等平台的消息发送、文件传输和卡片交互能力。适用场景：多渠道消息通知和自动化消息推送。',
        'triggers': ['消息平台', '飞书', '微信', '消息发送', '卡片交互'],
        'author': 'Emma (小玛)'
    },
    'metacognition': {
        'description': '元认知能力包。提供自我审查、文档对齐、质量检查等 AI 自省能力。适用场景：质量检查、文档对齐、自我审查和技能评估。',
        'triggers': ['元认知', '自我审查', '文档对齐', '质量检查', 'AI 自省'],
        'author': 'Emma (小玛)'
    },
    'network-proxy': {
        'description': '网络代理能力包。提供代理配置管理、节点发现、流量监控等网络工具。适用场景：代理软件配置、节点健康检查和网络优化。',
        'triggers': ['网络代理', '代理配置', 'Clash', '节点管理', '代理发现'],
        'author': 'Emma (小玛)'
    },
    'quality-assurance': {
        'description': '质量保证能力包。提供 SQS 质量评分、生命周期审计、技能树索引等质量门禁工具。适用场景：技能质量评估和全生命周期管理。',
        'triggers': ['质量保证', 'SQS', '技能评分', '质量门禁', '生命周期审计'],
        'author': 'Emma (小玛)'
    },
    'security-audit': {
        'description': '安全审计能力包。提供 1Password 集成、OSINT 用户名搜索等安全工具。适用场景：密码管理、安全扫描和账户安全性检查。',
        'triggers': ['安全审计', '1Password', 'OSINT', '安全扫描'],
        'author': 'Emma (小玛)'
    },
    'skill-quality': {
        'description': '技能质量门禁能力包。纯外部方案的质量门禁系统，零修改 Hermes 核心代码。适用场景：技能质量检测、创建前检查和删除前影响分析。',
        'triggers': ['技能质量', '质量门禁', '技能检测', '外部门禁', 'skill quality'],
        'author': 'Emma (小玛)'
    },
    'social-gaming': {
        'description': '社交娱乐能力包。提供游戏服务器搭建、自动游戏游玩、Bangumi 追番等娱乐能力。适用场景：搭建游戏服务器或追踪动漫番剧。',
        'triggers': ['社交娱乐', '游戏', 'Minecraft', '追番', 'Bangumi'],
        'author': 'Emma (小玛)'
    },
}


REQUIRED_FIELDS = ['name', 'version', 'description', 'author', 'triggers']


def ensure_fields(yaml_path, meta):
    """Ensure all required fields exist in the YAML file"""
    with open(yaml_path) as f:
        content = f.read()
    
    try:
        data = yaml.safe_load(content)
    except Exception as e:
        print(f"  ❌ YAML 解析失败: {e}")
        return False
    
    if not isinstance(data, dict):
        print(f"  ❌ 不是字典格式")
        return False
    
    changes = []
    for field in REQUIRED_FIELDS:
        if field not in data or not data[field]:
            if field == 'author':
                data[field] = meta.get('author', 'Emma (小玛)')
            elif field == 'description':
                data[field] = meta.get('description', '')
            elif field == 'triggers':
                data[field] = meta.get('triggers', [])
            elif field == 'version':
                data[field] = '1.0.0'
            elif field == 'name':
                continue
            changes.append(field)
    
    if not changes:
        return False  # No changes needed
    
    # Write back preserving comments
    new_yaml = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    # Preserve comment lines from original
    lines = content.split('\n')
    comment_lines = [l for l in lines if l.strip().startswith('#')]
    if comment_lines:
        new_yaml = '\n'.join(comment_lines) + '\n\n' + new_yaml
    
    with open(yaml_path, 'w') as f:
        f.write(new_yaml)
    
    print(f"  ➕ 补充字段: {', '.join(changes)}")
    return True


def main():
    fixed = 0
    total = 0
    errors = []
    
    for pack_name in sorted(PACK_META.keys()):
        yaml_path = os.path.join(PACKS_DIR, pack_name, 'cap-pack.yaml')
        if not os.path.isfile(yaml_path):
            errors.append(f"{pack_name}: cap-pack.yaml 未找到")
            continue
        
        meta = PACK_META[pack_name]
        total += 1
        print(f"📦 {pack_name:25s}", end=' ')
        
        changed = ensure_fields(yaml_path, meta)
        if changed:
            fixed += 1
        else:
            print(f" ✅ 已完整")
    
    print(f"\n---\n📦 总计: {total}, ✏️ 修复: {fixed}")
    for e in errors:
        print(f"  ❌ {e}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
