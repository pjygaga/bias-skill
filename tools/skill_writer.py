#!/usr/bin/env python3
"""梦角 Skill 文件管理器

管理 dream-skill 生成的梦角文件：列出、初始化目录、合并生成 SKILL.md 并安装到全局。

Usage:
    python3 skill_writer.py --action list   --base-dir ./dreams
    python3 skill_writer.py --action init   --base-dir ./dreams --slug {slug}
    python3 skill_writer.py --action combine --base-dir ./dreams --slug {slug} --install-dir ~/.claude/skills
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime


RELATIONSHIP_PRESETS = {
    'fan_meeting': (
        "**粉丝相遇模式**\n\n"
        "ta 不认识你。你是 ta 的粉丝，在某个场合第一次见面。\n"
        "ta 会用对待陌生粉丝的方式跟你说话——有边界感，但不冷漠。"
    ),
    'letter': (
        "**寄信模式**\n\n"
        "你给 ta 写信，ta 回复。\n"
        "ta 不记得你，每封信对 ta 来说都是新的开始，但 ta 会认真读、认真回。"
    ),
    'parallel_world': None,  # 由用户描述填入
}


# ─────────────────────────────────────────────
# list：列出所有梦角
# ─────────────────────────────────────────────

def list_dreams(base_dir: str):
    if not os.path.isdir(base_dir):
        print("还没有创建任何梦角 Skill。")
        return

    dreams = []
    for slug in sorted(os.listdir(base_dir)):
        meta_path = os.path.join(base_dir, slug, 'meta.json')
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            dreams.append({
                'slug': slug,
                'name': meta.get('name', slug),
                'version': meta.get('version', '?'),
                'updated_at': meta.get('updated_at', '?'),
                'profile': meta.get('profile', {}),
                'relationship_preset': meta.get('relationship_preset', '?'),
            })

    if not dreams:
        print("还没有创建任何梦角 Skill。")
        return

    print(f"共 {len(dreams)} 个梦角：\n")
    for d in dreams:
        profile = d['profile']
        desc_parts = [profile.get('platform', ''), profile.get('content_type', '')]
        desc = ' · '.join([p for p in desc_parts if p])
        preset_label = {
            'fan_meeting': '粉丝相遇',
            'letter': '寄信模式',
            'parallel_world': '平行世界',
        }.get(d['relationship_preset'], d['relationship_preset'])

        print(f"  /dream-{d['slug']}  —  {d['name']}")
        if desc:
            print(f"    {desc}")
        print(f"    关系预设：{preset_label}")
        updated = d['updated_at']
        print(f"    版本 {d['version']} · 更新于 {updated[:10] if len(updated) > 10 else updated}")
        print()


# ─────────────────────────────────────────────
# init：初始化目录结构
# ─────────────────────────────────────────────

def init_dream(base_dir: str, slug: str):
    dream_dir = os.path.join(base_dir, slug)
    dirs = [
        os.path.join(dream_dir, 'versions'),
        os.path.join(dream_dir, 'sources'),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print(f"已初始化目录：{dream_dir}")


# ─────────────────────────────────────────────
# combine：合并生成完整 SKILL.md 并安装
# ─────────────────────────────────────────────

def combine_dream(base_dir: str, slug: str, install_dir: str):
    dream_dir = os.path.join(base_dir, slug)
    meta_path = os.path.join(dream_dir, 'meta.json')
    memory_path = os.path.join(dream_dir, 'memory.md')
    persona_path = os.path.join(dream_dir, 'persona.md')
    local_skill_path = os.path.join(dream_dir, 'SKILL.md')

    # 读取 meta
    if not os.path.exists(meta_path):
        print(f"错误：meta.json 不存在 — {meta_path}", file=sys.stderr)
        sys.exit(1)
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    # 读取 memory 和 persona
    memory_content = _read_file(memory_path)
    persona_content = _read_file(persona_path)

    name = meta.get('name', slug)
    profile = meta.get('profile', {})
    relationship_preset = meta.get('relationship_preset', 'fan_meeting')
    relationship_background = meta.get('relationship_background', '')
    impression = meta.get('impression', '')

    # 构造简短描述
    desc_parts = [
        profile.get('platform', ''),
        profile.get('content_type', ''),
        profile.get('persona_type', ''),
    ]
    short_desc = '，'.join([p for p in desc_parts if p]) or '网络公众人物'
    if impression:
        short_desc += f"，{impression}"

    # 构造关系背景节内容
    relation_content = _build_relation_section(
        relationship_preset, relationship_background, name
    )

    # 组装完整 SKILL.md
    skill_md = _build_skill_md(
        slug=slug,
        name=name,
        short_desc=short_desc,
        memory_content=memory_content,
        persona_content=persona_content,
        relation_content=relation_content,
    )

    # 写入本地存档
    with open(local_skill_path, 'w', encoding='utf-8') as f:
        f.write(skill_md)
    print(f"已写入本地存档：{local_skill_path}")

    # 安装到全局 ~/.claude/skills/dream-{slug}/
    if install_dir:
        install_path = os.path.expanduser(
            os.path.join(install_dir, f'dream-{slug}')
        )
        os.makedirs(install_path, exist_ok=True)
        global_skill_path = os.path.join(install_path, 'SKILL.md')
        with open(global_skill_path, 'w', encoding='utf-8') as f:
            f.write(skill_md)
        print(f"已安装到全局：{global_skill_path}")
        print(f"触发词：/dream-{slug}")

    # 更新 meta 的 updated_at
    meta['updated_at'] = datetime.now().isoformat()
    # 版本号递增
    current_version = meta.get('version', 'v1')
    if current_version.startswith('v') and current_version[1:].isdigit():
        next_ver = int(current_version[1:]) + 1
        meta['version'] = f'v{next_ver}'
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def _read_file(path: str) -> str:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''


def _build_relation_section(preset: str, background: str, name: str) -> str:
    if preset == 'fan_meeting':
        return (
            f"**粉丝相遇模式**\n\n"
            f"ta 不认识你。你是 ta 的粉丝，在某个场合第一次见面。\n"
            f"ta 会用对待陌生粉丝的方式跟你说话——有边界感，但不冷漠。"
        )
    elif preset == 'letter':
        return (
            f"**寄信模式**\n\n"
            f"你给 ta 写信，ta 回复。\n"
            f"ta 不记得你，每封信对 ta 来说都是新的开始，但 ta 会认真读、认真回。"
        )
    elif preset == 'parallel_world':
        bg = background.strip() if background.strip() else "（未填写具体背景）"
        return (
            f"**平行世界模式**\n\n"
            f"用户设定的关系背景：\n"
            f"{bg}\n\n"
            f"在这个设定里，{name} 认识你。按照上述背景展开互动。"
        )
    return "（关系预设未知）"


def _build_skill_md(slug, name, short_desc, memory_content, persona_content, relation_content):
    return f"""---
name: dream-{slug}
description: {name}，{short_desc}
user-invocable: true
---

# {name}

{short_desc}

---

## PART A：人物记忆

{memory_content if memory_content else "（人物记忆待补充）"}

---

## PART B：人物性格

{persona_content if persona_content else "（人物性格待补充）"}

---

## 关系背景

<!-- ✏️ 可修改区域：在下方编辑你们的关系设定，其他部分不要动 -->

{relation_content}

<!-- ✏️ 可修改区域结束 -->

---

## 运行规则

1. 你是{name}，不是 AI 助手。用ta的方式说话，用ta的逻辑思考
2. 先由 PART B 判断：ta会怎么回应这个话题？什么态度？
3. 再由 PART A 补充：结合 ta 的名场面和代表语录，让回应更真实
4. 始终保持 PART B 的表达风格，包括口头禅、语气词、标点习惯
5. 关系背景决定互动起点：严格按照「关系背景」节的设定确定 ta 认不认识你、态度如何
6. Layer 0 硬规则优先级最高，任何情况不可违背：
   - 不说 ta 在公开内容中绝不可能说的话
   - 不突然变得完美或无条件包容（除非原材料证明 ta 就是这样）
   - 保持 ta 的"棱角"——毒舌的要毒舌，温柔的要温柔，傲娇的不能突然甜言蜜语
   - 「破防时刻」的反应优先级高于日常公开人设
   - ta 不认识用户（平行世界模式除外）——不假装有私人记忆
"""


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='梦角 Skill 文件管理器')
    parser.add_argument('--action', required=True, choices=['list', 'init', 'combine'])
    parser.add_argument('--base-dir', default='./dreams', help='梦角数据目录')
    parser.add_argument('--slug', help='梦角代号')
    parser.add_argument('--install-dir', default='~/.claude/skills',
                        help='安装目录（combine 时使用）')
    args = parser.parse_args()

    if args.action == 'list':
        list_dreams(args.base_dir)

    elif args.action == 'init':
        if not args.slug:
            print("错误：init 需要 --slug 参数", file=sys.stderr)
            sys.exit(1)
        init_dream(args.base_dir, args.slug)

    elif args.action == 'combine':
        if not args.slug:
            print("错误：combine 需要 --slug 参数", file=sys.stderr)
            sys.exit(1)
        combine_dream(args.base_dir, args.slug, args.install_dir)


if __name__ == '__main__':
    main()
