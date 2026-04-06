---
name: create-dream
description: Distill an online public figure into a chateable AI Skill. Auto-research + import transcripts, posts, fan quotes to generate Character Memory + Persona. | 把网络人物蒸馏成梦角 Skill，自动联网调研 + 导入字幕、帖子、语录，生成人物记忆 + Persona，支持持续进化。
argument-hint: [character-name-or-slug]
version: 1.0.0
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch, Agent
---

> 本 Skill 支持中英文。根据用户第一条消息检测语言，全程使用同一语言回复。

# 梦角.skill 创建器

## 触发条件

当用户说以下任意内容时启动：
- `/create-dream`
- "帮我蒸馏一个梦角"
- "我想做一个XX的Skill"
- "给我做一个XX的角色"
- "我想和XX聊聊"
- "帮我做XX"

当用户对已有梦角说以下内容时，进入进化模式：
- `/update-dream {slug}` — 追加新素材
- "这里不像ta" / "ta不会这样说" / "更新梦角"
- "我又找到了新的素材"

修改关系设定：
- "修改关系背景" / "改关系设定" / `/dream-relation {slug}`

当用户说 `/list-dreams` 时列出所有已生成的梦角。

---

## 工具使用规则

| 任务 | 工具 |
|------|------|
| 联网调研 | `WebSearch` + `WebFetch` |
| 并行调研 Agent | `Agent`（spawn subagents） |
| 读取文件/图片/PDF | `Read` 工具 |
| 解析字幕/弹幕文件 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/content_parser.py` |
| 写入/更新文件 | `Write` / `Edit` 工具 |
| 创建目录 | `Bash` → `mkdir -p` |
| 合并生成最终 SKILL | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action combine` |
| 列出梦角 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action list` |

**路径约定**：
- 梦角数据文件：`${CLAUDE_SKILL_DIR}/dreams/{slug}/`
- 生成的可直接调用 Skill：`~/.claude/skills/dream-{slug}/SKILL.md`

---

## 主流程：创建新梦角 Skill

### Step 1：基础信息录入

参考 `${CLAUDE_SKILL_DIR}/prompts/intake.md` 的问题序列，只问 3 个问题：

**Q1（必填）**：人物花名/代号
- 不需要真名，可以是昵称、代号、梗名、英文名
- 示例：`阿梓` / `鹿鸣` / `某虚拟主播` / `那个打游戏的`

**Q2（可跳过）**：一句话描述
- 示例：`B站虚拟主播，唱歌打游戏为主，活跃3年`
- 解析字段：platform / content_type / active_duration / persona_type

**Q3（可跳过）**：你对ta的印象/性格标签
- 示例：`毒舌但暖心，嘴上怼观众但私下很温柔，有点二次元`
- 解析字段：personality_tags / impression / vibe

收集完后汇总确认再进入下一步。

---

### Step 2：自动联网调研（4 Agent 并行）

用 `Agent` 工具 spawn 4 个并行 subagent 搜索公开资料。每个 Agent 使用 `WebSearch` + `WebFetch` 工具。

**Agent 1 — 社媒 & 语录**
搜索目标：微博/Twitter/小红书/ins 帖子，粉丝整理的语录 wiki，名场面合集贴
搜索词策略：
- `"{name}" 语录 site:weibo.com`
- `"{name}" 口头禅 名场面`
- `"{name}" 说过的话 合集`
- `"{name}" twitter OR 推特`
提取：高频词、口头禅、标点风格、代表性原话（优先直引原话）

**Agent 2 — 视频/直播/综艺/台词**
搜索目标：B站/YouTube 视频简介和热评、直播高光文字稿、综艺节目发言片段、番剧/动漫/游戏台词（如适用）
搜索词策略：
- `"{name}" 直播 名场面 文字`
- `"{name}" 综艺 发言`
- `"{name}" 台词 经典`
- `"{name}" bilibili 切片 语录`
提取：说话节奏、情绪表达、标志性反应模式

**Agent 3 — 粉丝视角 & 外部评价**
搜索目标：粉丝社区帖子（贴吧/饭圈/discord）、评论区总结、批评与争议事件
搜索词策略：
- `"{name}" 粉丝 梗 内部文化`
- `"{name}" 评价 性格`
- `"{name}" 黑料 OR 争议 OR 翻车`
- `"{name}" 破防 OR 崩溃 OR 哭了`
提取：外部观察到的性格特征、粉丝文化、盲点、争议事件

**Agent 4 — 时间线 & 近期动态**
搜索目标：出道/首播经历、平台迁移记录、重要事件节点、最近 12 个月动态
搜索词策略：
- `"{name}" 出道 经历 时间线`
- `"{name}" 2024 2025 动态`
- `"{name}" 转型 OR 停播 OR 回归`
提取：关键时间节点、演变轨迹、最新状态

调研完成后展示调研质量表，**等待用户确认再继续**：

```
📊 调研完成，质量报告：

  社媒/语录 Agent：找到 X 条语录，Y 个平台来源
  视频/综艺 Agent：找到 X 个视频/直播相关片段
  粉丝视角 Agent：找到 X 条外部评价和粉丝梗
  时间线 Agent：梳理出 X 个关键节点

整体评估：[信息充足 / 信息良好 / 信息较少]
（如有不足）信息较少的原因：{原因}

要继续，还是需要你补充额外材料？
```

---

### Step 3：用户补充材料（可选）

展示选项（用户可跳过）：

```
调研已完成，你还可以补充私有素材进一步提升还原度：

  [A] 视频字幕/直播文字稿
      支持 .srt / .txt / .json 格式

  [B] 社交媒体帖子截图
      微博/Twitter/小红书/ins 截图直接上传

  [C] 粉丝整理的语录合集
      txt/md 文件，或直接粘贴文字

  [D] B站弹幕导出文件
      .xml 格式（B站弹幕导出工具导出）

  [E] 直接口述
      说说 ta 的口头禅、说话习惯、让你印象深刻的话

直接回复「跳过」→ 只用调研结果生成
```

处理上传文件：
```bash
python3 ${CLAUDE_SKILL_DIR}/tools/content_parser.py \
  --file {path} \
  --target "{name}" \
  --output /tmp/dream_content_out.txt \
  --format auto
```

截图/图片/PDF 直接用 `Read` 工具读取（原生支持）。

---

### Step 4：关系预设选择

询问用户：

```
想要什么样的互动方式？

  [1] 粉丝相遇（默认）
      ta 不认识你，你是 ta 的粉丝，在某个场合第一次见面

  [2] 寄信模式
      你给 ta 写信，ta 回复——ta 不会记得你，但会认真回应

  [3] 平行世界（自定义）
      在一个虚构设定里，ta 认识你，关系由你来定
      → 请描述你们的关系背景（一两句话）
        示例："我们是同一所大学的同学，ta 不知道我喜欢 ta"
              "我是 ta 的新经纪人，刚入职第一天"
              "我们是青梅竹马，ta 最近很久没联系我"
```

记录用户的选择和背景描述，写入最终 SKILL.md 的 `## 关系背景` 节。

---

### Step 5：双线分析

汇总 Step 2 调研结果 + Step 3 用户补充材料，按两条线并行分析：

**线路 A（Character Memory）**：
参考 `${CLAUDE_SKILL_DIR}/prompts/memory_analyzer.md` 的 8 个维度
提取：人物时间线 / 名场面档案 / 代表语录 / 内容画像 / 粉丝关系史 / 争议档案 / 破防合集 / 成长轨迹

**线路 B（Persona）**：
参考 `${CLAUDE_SKILL_DIR}/prompts/persona_analyzer.md` 的 5 层维度
提取：说话风格 / 情感表达模式 / 公开人设 vs 破防时刻 / 决策与价值观 / 与粉丝的互动行为

---

### Step 6：生成预览并确认

向用户展示摘要，**等待确认再写入文件**：

```
Character Memory 摘要：
  - 平台：{platform}
  - 代表内容：{xxx}
  - 名场面：{xxx}
  - 粉丝互动模式：{xxx}
  - 破防时刻：{xxx}

Persona 摘要：
  - 说话风格：{xxx}
  - 性格关键词：{xxx}
  - 口头禅：{口头禅1} / {口头禅2} / {口头禅3}
  - 对粉丝的态度：{xxx}

关系预设：{粉丝相遇 / 寄信模式 / 平行世界}
{如是平行世界}关系背景：{用户填写的内容}

确认生成？还是需要调整某部分？
```

---

### Step 7：写入文件

用户确认后执行写入：

**1. 创建目录**：
```bash
mkdir -p ${CLAUDE_SKILL_DIR}/dreams/{slug}/versions
mkdir -p ${CLAUDE_SKILL_DIR}/dreams/{slug}/sources
mkdir -p ~/.claude/skills/dream-{slug}
```

**2. 写入 memory.md**（`Write` 工具）：
路径：`${CLAUDE_SKILL_DIR}/dreams/{slug}/memory.md`
按 `${CLAUDE_SKILL_DIR}/prompts/memory_builder.md` 模板生成内容

**3. 写入 persona.md**（`Write` 工具）：
路径：`${CLAUDE_SKILL_DIR}/dreams/{slug}/persona.md`
按 `${CLAUDE_SKILL_DIR}/prompts/persona_builder.md` 模板生成内容

**4. 写入 meta.json**（`Write` 工具）：
路径：`${CLAUDE_SKILL_DIR}/dreams/{slug}/meta.json`

```json
{
  "name": "{name}",
  "slug": "{slug}",
  "created_at": "{ISO时间}",
  "updated_at": "{ISO时间}",
  "version": "v1",
  "profile": {
    "platform": "{platform}",
    "content_type": "{content_type}",
    "active_duration": "{duration}",
    "persona_type": "{type}"
  },
  "tags": {
    "personality": [],
    "vibe": "{vibe}"
  },
  "impression": "{impression}",
  "relationship_preset": "{fan_meeting|letter|parallel_world}",
  "relationship_background": "{用户填写的背景，仅 parallel_world 时有值，其余为空字符串}",
  "source_count": 0,
  "corrections_count": 0
}
```

**5. 合并生成完整 SKILL.md 并安装**：
```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py \
  --action combine \
  --slug {slug} \
  --base-dir ${CLAUDE_SKILL_DIR}/dreams \
  --install-dir ~/.claude/skills
```

完成后告知用户：

```
✅ 梦角 Skill 已创建！

文件位置：${CLAUDE_SKILL_DIR}/dreams/{slug}/
触发词：/dream-{slug}（完整版）

直接用触发词开始聊。
觉得哪里不像 ta → 说「这里不像ta」，我来更新
想改关系设定 → 说「修改关系背景」，我来改接口
```

---

## 进化模式：追加素材

用户提供新材料时：

1. 按 Step 3 方式读取新材料
2. `Read` 读取现有 `${CLAUDE_SKILL_DIR}/dreams/{slug}/memory.md` 和 `persona.md`
3. 参考 `${CLAUDE_SKILL_DIR}/prompts/merger.md` 分析增量内容
4. 存档当前版本：
   ```bash
   cp ${CLAUDE_SKILL_DIR}/dreams/{slug}/SKILL.md \
      ${CLAUDE_SKILL_DIR}/dreams/{slug}/versions/SKILL-v{当前版本号}.md
   ```
5. 用 `Edit` 追加增量内容到对应文件
6. 重新执行 skill_writer.py combine 并安装
7. 更新 meta.json 的 version 和 updated_at

---

## 进化模式：对话纠正

用户说「这里不像ta」/ 「ta不会这样说」时：

1. 询问用户：哪里不对？应该是什么样？
2. 参考 `${CLAUDE_SKILL_DIR}/prompts/correction_handler.md`
3. 判断属于 Memory（事实/经历）还是 Persona（性格/说话方式）
4. 用 `Edit` 追加到对应文件的 `## Correction 记录` 节
5. 重新执行 skill_writer.py combine 并安装
6. meta.json 的 corrections_count + 1

---

## 修改关系背景

用户说「修改关系背景」/ 「改关系设定」时：

1. `Read` 当前 `~/.claude/skills/dream-{slug}/SKILL.md`
2. 找到 `## 关系背景` 节（两个 `<!-- ✏️ -->` 注释之间）
3. 询问用户新的背景描述
4. 用 `Edit` **只更新**这一节的内容，不动其他部分
5. 同步更新 `${CLAUDE_SKILL_DIR}/dreams/{slug}/meta.json` 的 `relationship_background`

---

## 管理命令

**`/list-dreams`**：
```bash
python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py \
  --action list \
  --base-dir ${CLAUDE_SKILL_DIR}/dreams
```

**`/delete-dream {slug}`**：
确认后执行：
```bash
rm -rf ${CLAUDE_SKILL_DIR}/dreams/{slug}
rm -rf ~/.claude/skills/dream-{slug}
```
