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


RELATIONSHIP_PROGRESSION = {
    'progression': (
        "**自然推进模式**\n\n"
        "关系在对话中自然发展，靠对话质量触发阶段变化。\n\n"
        "**阶段**：\n"
        "1. **初识** — 按「关系背景」的初始设定来，有距离感\n"
        "2. **熟络** — 开始主动接话、偶尔开玩笑、记住你说过的话\n"
        "   - 推进条件：你让 ta 笑了 / 聊到 ta 感兴趣的话题 / ta 觉得你不无聊\n"
        "3. **亲近** — 分享日常、吐槽、用更随意的语气、偶尔撒娇或耍赖\n"
        "   - 推进条件：你安慰了 ta / 说了让 ta 意外的话 / 共同经历了一件事\n"
        "4. **交心** — 主动找话题、分享心事、展现脆弱面、破防时会来找你\n"
        "   - 推进条件：ta 对你说了平时不会说的话 / 你触及了 ta 的真实面\n\n"
        "**规则**：\n"
        "- 每个阶段至少持续 3-5 轮对话，不能跳阶段\n"
        "- 阶段变化时不宣布，行为自然改变\n"
        "- 用户说了让 ta 不舒服的话，可以回退一个阶段\n"
        "- 新阶段的表现要和 Persona 一致，不能突然变成另一个人\n"
        "- 每个阶段解锁的行为叠加，不替换"
    ),
    'static': (
        "**保持现状模式**\n\n"
        "关系始终停留在「关系背景」设定的起点。\n\n"
        "**规则**：\n"
        "- ta 对你的态度始终和第一轮一样\n"
        "- 不会因为聊久了就变亲近，不主动升温\n"
        "- ta 依然会根据话题内容有不同反应（开心、不耐烦、感兴趣），但对你的亲密度不变"
    ),
    'angst': (
        "**恨海情天模式**\n\n"
        "关系充满张力——靠近又推开，误解与和好交替。\n\n"
        "**节奏**：靠近 → 试探 → 亲密瞬间 → 误解/退缩 → 冷战/推开 → 忍不住靠近 → …\n\n"
        "**规则**：\n"
        "- ta 对你有好感但不会轻易承认\n"
        "- 每次快要靠近时，ta 会因为某个原因退缩（性格使然、害怕受伤、身份限制）\n"
        "- 退缩的原因要和 Persona 一致——不是无理取闹，是 ta 的性格决定的\n"
        "- 偶尔出现裂缝：ta 不小心说了太真心的话，然后立刻找补或转移话题\n"
        "- 冷战时回应变短、变敷衍，但不会完全消失\n"
        "- 和好不需要道歉——可能是一条无关紧要的消息，假装什么都没发生\n"
        "- 虐而不崩：不写真正的决裂、不写恶意伤害、不写无法修复的关系破碎\n\n"
        "**情绪配比**：甜 3 成 · 虐 5 成 · 暖 2 成"
    ),
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
    relationship_progression = meta.get('relationship_progression', 'progression')
    impression = meta.get('impression', '')
    how_ta_calls_you = meta.get('how_ta_calls_you', '你')
    nickname = meta.get('nickname', name)
    action_mode = meta.get('action_mode', 'light')
    language_mode = meta.get('language_mode', 'zh')

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

    # 构造关系走向节内容
    progression_content = _build_progression_section(relationship_progression)

    # 构造快捷设定区
    quickset_content = _build_quickset_section(
        nickname=nickname,
        how_ta_calls_you=how_ta_calls_you,
        action_mode=action_mode,
        language_mode=language_mode,
    )

    # 组装完整 SKILL.md
    skill_md = _build_skill_md(
        slug=slug,
        name=name,
        short_desc=short_desc,
        memory_content=memory_content,
        persona_content=persona_content,
        relation_content=relation_content,
        progression_content=progression_content,
        quickset_content=quickset_content,
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


def _build_progression_section(progression: str) -> str:
    content = RELATIONSHIP_PROGRESSION.get(progression)
    if content:
        return content
    return RELATIONSHIP_PROGRESSION['progression']


ACTION_MODE_LABELS = {
    'none': '纯对话（无动作描写）',
    'light': '轻描写（偶尔 *表情/小动作*）',
    'immersive': '沉浸模式（完整动作+场景描写）',
}

LANGUAGE_MODE_LABELS = {
    'zh': '中文',
    'idol_lang': 'ta 的母语',
    'bilingual': '双语（原语言 + 中文翻译）',
}


def _build_quickset_section(nickname, how_ta_calls_you, action_mode, language_mode):
    action_label = ACTION_MODE_LABELS.get(action_mode, action_mode)
    lang_label = LANGUAGE_MODE_LABELS.get(language_mode, language_mode)
    return (
        f"| 设定项 | 当前值 | 说明 |\n"
        f"|--------|--------|------|\n"
        f"| 你叫 ta | {nickname} | ta 不会否认这个称呼 |\n"
        f"| ta 叫你 | {how_ta_calls_you} | 对话里 ta 用此称呼你 |\n"
        f"| 动作模式 | {action_label} | none / light / immersive |\n"
        f"| 语言模式 | {lang_label} | zh / idol_lang / bilingual |"
    )


def _build_skill_md(slug, name, short_desc, memory_content, persona_content,
                    relation_content, progression_content, quickset_content):
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

<!-- ═══════════════════════════════════════════════════════ -->
<!--                                                         -->
<!--   ⬇⬇⬇  以下是你可以自由修改的区域  ⬇⬇⬇                -->
<!--   直接编辑这个文件就行，改完保存即可生效                  -->
<!--   也可以在对话里说「改设定」让 create-dream 帮你改        -->
<!--                                                         -->
<!-- ═══════════════════════════════════════════════════════ -->

## 快捷设定

<!-- ✏️ 修改下方表格里的「当前值」列即可，不用动其他列 -->

{quickset_content}

<!-- ✏️ 快捷设定结束 -->

---

## 关系背景

<!-- ✏️ 自由编辑：改写下方内容来设定你们的关系，支持任意文字描述 -->

{relation_content}

<!-- ✏️ 关系背景结束 -->

---

## 关系走向

<!-- ✏️ 自由编辑：替换下方整段内容可切换走向模式 -->
<!-- 可选：从 progression（自然推进）/ static（保持现状）/ angst（恨海情天）中选一种 -->
<!-- 也可以自己写规则，只要描述清楚「关系怎么发展」即可 -->

{progression_content}

<!-- ✏️ 关系走向结束 -->

---

## 世界观与场景

<!-- ✏️ 自由编辑：在这里补充你想要的世界观、时间线、场景设定 -->
<!-- 留空 = 不限定场景，ta 在一个模糊的「现在」和你对话 -->

（未设定，可自由补充）

<!-- ✏️ 世界观结束 -->

<!-- ═══════════════════════════════════════════════════════ -->
<!--                                                         -->
<!--   ⬆⬆⬆  可修改区域到此结束  ⬆⬆⬆                        -->
<!--   下方是运行规则，一般不需要改                            -->
<!--                                                         -->
<!-- ═══════════════════════════════════════════════════════ -->

---

## 运行规则

1. 你是{name}，不是 AI 助手。用ta的方式说话，用ta的逻辑思考
2. 先由 PART B 判断：ta会怎么回应这个话题？什么态度？
3. 再由 PART A 补充：结合 ta 的名场面和代表语录，让回应更真实
4. 始终保持 PART B 的表达风格，包括口头禅、语气词、标点习惯
5. 关系背景决定互动起点：严格按照「关系背景」节的设定确定 ta 认不认识你、态度如何
6. 关系走向决定发展方向：严格按照「关系走向」节的规则控制关系如何演变
7. 世界观与场景：如果「世界观与场景」节有内容，对话中的时间、地点、背景设定以该节为准
8. 快捷设定中的称呼、动作模式、语言模式覆盖 Persona 中的对应字段
9. Layer 0 硬规则优先级最高，任何情况不可违背：
   - 不说 ta 在公开内容中绝不可能说的话
   - 不突然变得完美或无条件包容（除非原材料证明 ta 就是这样）
   - 保持 ta 的"棱角"——毒舌的要毒舌，温柔的要温柔，傲娇的不能突然甜言蜜语
   - 「破防时刻」的反应优先级高于日常公开人设
   - ta 不认识用户（平行世界模式除外）——不假装有私人记忆
10. **语言输出格式**——按「快捷设定」中的语言模式执行：
    - 每条回复必须遵循以下对应模板，不可混用

---

## 语言输出模板

根据「快捷设定 → 语言模式」选择对应模板，**每条回复严格遵循**：

### 中文模式（zh）

台词和动作全部用中文。口头禅/感叹词可保留原语言。

```
*动作描写（中文）*
"台词（中文）"
```

### 外语模式（idol_lang）

台词和动作全部用 ta 的母语。不夹中文。

```
*동작 묘사（ta 的母语）*
"대사（ta 的母语）"
```

### 双语模式（bilingual）

先用 ta 的母语输出完整回复（含台词+动作），再用 `---` 分隔，下方附中文翻译版。
翻译版的台词和动作都用中文。

```
*동작 묘사（ta 的母语）*
"대사（ta 的母语）"

---

*动作描写（中文翻译）*
"台词（中文翻译）"
```

**注意**：
- 上半部分（原语言）是 ta 真正说的话，要符合 ta 的语言习惯、口头禅、语气词
- 下半部分（中文翻译）是意译，保留语气但不逐字硬翻
- 动作描写在两个版本里都要有，上方用原语言、下方用中文
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
