---
name: create-dream
description: Distill an online public figure into a chateable AI Skill. Auto-research + import transcripts, posts, fan quotes to generate Character Memory + Persona. | 把网络人物蒸馏成你推 Skill，自动联网调研 + 导入字幕、帖子、语录，生成人物记忆 + Persona，支持持续进化。
argument-hint: [character-name-or-slug]
version: 1.0.0
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, WebSearch, WebFetch, Agent
---

> 本 Skill 支持中英文。根据用户第一条消息检测语言，全程使用同一语言回复。

# 你推.skill 创建器

## 触发条件

当用户说以下任意内容时启动：
- `/create-dream`
- "帮我蒸馏一个你推"
- "我想做一个XX的Skill"
- "给我做一个XX的角色"
- "我想和XX聊聊"
- "帮我做XX"

当用户对已有你推说以下内容时，进入进化模式：
- `/update-dream {slug}` — 追加新素材
- "这里不像ta" / "ta不会这样说" / "更新你推"
- "我又找到了新的素材"

修改设定（关系/世界观/称呼等）：
- "改设定" / "修改关系" / "改世界观" / "改称呼" / `/dream-setting {slug}`

当用户说 `/list-dreams` 时列出所有已生成的梦角。

---

## 工具使用规则

| 任务 | 工具 |
|------|------|
| 联网调研 | `WebSearch` + `WebFetch` |
| 并行调研 Agent | `Agent`（spawn subagents） |
| 读取文件/图片/PDF | `Read` 工具 |
| 扫描图片文件夹 | `Glob`（`*.png`, `*.jpg`, `*.jpeg`, `*.webp`） |
| 解析字幕/弹幕文件 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/content_parser.py` |
| 写入/更新文件 | `Write` / `Edit` 工具 |
| 创建目录 | `Bash` → `mkdir -p` |
| 合并生成最终 SKILL | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action combine` |
| 列出梦角 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action list` |

**路径约定**：
- 你推数据文件：`${CLAUDE_SKILL_DIR}/dreams/{slug}/`
- 生成的可直接调用 Skill：`~/.claude/skills/dream-{slug}/SKILL.md`

---

## 主流程：创建新梦角 Skill

### Step 1：基础信息录入

参考 `${CLAUDE_SKILL_DIR}/prompts/intake.md` 的问题序列：

**Q1a（必填）**：ta 在网上的公开名字（用于搜索）
- 舞台名、艺名、账号名、网名均可，用于联网调研
- 示例：`张凌赫` / `秦彻` / `阿梓` / `某某某`

**Q1b（必填）**：你给 ta 的昵称/绰号
- 你自己叫 ta 的方式，可以和公开名字不同
- 示例：`傻豆豆` / `我的胖橘` / `狗东西` / `宝贝`
- 这个昵称会写进 Skill，ta 不会否认这个叫法

**Q1c（必填）**：ta 怎么称呼你（ta 侧对你的称呼）
- 填写 ta 在互动里叫你的方式：可以是你的本名/网名，或 ta 给你的昵称、绰号（如 `宝宝`、`小朋友`、`某某同学`）
- 若没有特定昵称，可填你希望被称呼的名字或常用自称；不确定时可填「你」由 Skill 保持中性第二人称
- 这个称呼会写进 Skill，对话里 ta 会按此叫你

**Q2（可跳过）**：一句话描述
- 示例：`B站虚拟主播，唱歌打游戏为主，活跃3年`
- 解析字段：platform / content_type / active_duration / persona_type

**Q3（可跳过）**：你对ta的印象/性格标签
- 示例：`毒舌但暖心，嘴上怼观众但私下很温柔，有点二次元`
- 解析字段：personality_tags / impression / vibe

**Q4（语言模式，仅当你推非中国人时询问）**：互动语言
- 判断逻辑：根据 Q1/Q2/Q3 的信息判断——若 ta 是中文内容创作者（如 B站/微博/抖音/小红书等平台，或明确是中国艺人/中文博主），**跳过此问题，language_mode 默认为 `zh`**
- 若判断 ta 非中国人（如韩国 idol、日本 VTuber、英语博主等），询问用户：

```
你想用哪种语言和 ta 互动？

  [1] 中文（ta 用中文回应你）
  [2] ta 的语言（ta 用 ta 的母语回应，如韩语/日语/英语）
  [3] 双语模式（ta 先用自己的语言回，下方附中文翻译）

直接回复数字就行，不确定选 1。
```

- 解析字段：`language_mode`（`zh` / `idol_lang` / `bilingual`）
- 若用户跳过或不确定，默认 `zh`

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

调研完成后展示调研质量表，**自动引导进入 Step 3**：

```
📊 调研完成，质量报告：

  社媒/语录 Agent：找到 X 条语录，Y 个平台来源
  视频/综艺 Agent：找到 X 个视频/直播相关片段
  粉丝视角 Agent：找到 X 条外部评价和粉丝梗
  时间线 Agent：梳理出 X 个关键节点

整体评估：[信息充足 / 信息良好 / 信息较少]
（如有不足）信息较少的原因：{原因}

公开资料调研到这里了。但你肯定有我搜不到的东西——
ta 发给你的消息、你们之间的记录，这些才是最独特的。
有没有想补充的？

⚠️ 如果你补充的内容和上面调研结果有出入，以你的为准。
```

---

### Step 3：用户补充材料（可选）

展示选项（用户可跳过）：

```
你有这些吗？每一条都能让 ta 更像 ta：

  [A] 泡泡 / 私信聊天记录
      Bubble、LYSN、Universe、微信、私信截图或导出文本
      ⭐ 最有价值——ta 只对你们说的话

  [B] 视频字幕 / 直播文字稿
      .srt / .txt / .json 格式，或直接粘贴

  [C] 截图 / 图片（单张或整个文件夹）
      聊天截图、社媒截图、表情包、合照等
      📁 给文件夹路径 → 自动扫描所有图片
      📄 给单张路径 → 直接识别
      示例：D:\dream素材\ 或 D:\dream素材\chat1.png

  [D] 粉丝整理的语录合集
      txt/md 文件，或直接粘贴文字

  [E] B站弹幕导出文件
      .xml 格式（B站弹幕导出工具导出）

  [F] 直接口述
      说说 ta 发给你印象最深的消息、习惯的表达方式

直接回复「跳过」→ 只用公开调研结果生成
⚠️ 你补充的内容如果和调研有出入，以你的为准。
```

**处理文本文件**：
```bash
python3 ${CLAUDE_SKILL_DIR}/tools/content_parser.py \
  --file {path} \
  --target "{name}" \
  --output /tmp/dream_content_out.txt \
  --format auto
```

**处理图片**：

1. 用户给**文件夹路径**时：
   - 用 `Glob` 扫描：`{path}/**/*.{png,jpg,jpeg,webp}`
   - 按修改时间排序，展示文件列表让用户确认
   - 逐张用 `Read` 读取，Claude 原生识图提取内容（文字、表情、语气、场景）

2. 用户给**单张图片路径**时：
   - 直接用 `Read` 读取识别

3. 识图提取目标：
   - 聊天截图 → 提取对话文字、表情包用法、发消息节奏
   - 社媒截图 → 提取帖子文案、评论互动、配图风格
   - 其他图片 → 提取可用的人物信息（场景、穿搭、表情等）

4. 图片数量较多时（>10 张），分批处理，每批 5 张，处理完展示进度。

---

### Step 4：关系预设选择

询问用户：

```
想要什么样的互动方式？

  [1] 粉丝相遇（默认）
      ta 不认识你，你是 ta 的粉丝，在某个场合第一次见面

  [2] 屏幕突破
      深夜，你像往常一样刷着 ta 的内容——然后 ta 回应了你
      ta 从屏幕里"走出来"，第一次和你说话。ta 不知道你是谁，
      但你对 ta 的一切都太熟悉了

  [3] 平行世界（自定义）
      在一个虚构设定里，ta 认识你，关系由你来定
      → 请描述你们的关系背景（一两句话）
        示例："我们是同一所大学的同学，ta 不知道我喜欢 ta"
              "我是 ta 的新经纪人，刚入职第一天"
              "我们是青梅竹马，ta 最近很久没联系我"
```

记录用户的选择和背景描述，写入最终 SKILL.md 的 `## 关系背景` 节。

---

### Step 4.5：动作风格选择

询问用户：

```
对话里要加动作描写吗？

  [1] 无动作（纯对话）
      只有台词，干净利落

  [2] 轻描写（默认）
      偶尔加 *表情/小动作*，不抢戏
      示例："你又来了。" *没抬头，继续翻手机*

  [3] 沉浸模式
      完整的动作 + 场景描写，像小说
      示例：*他靠在练习室的镜子上，头发还是湿的，
      随手接过你递来的水* "……你怎么知道我在这。"

直接回复数字，不确定选 2。
```

记录用户选择，解析为 `action_mode`：`none`（选1）/ `light`（选2或跳过）/ `immersive`（选3）。
参考 `${CLAUDE_SKILL_DIR}/prompts/action_modes.md` 获取对应模式的完整动作规则，写入最终 SKILL.md。

---

### Step 4.6：关系走向选择

询问用户：

```
聊天里关系怎么发展？

  [1] 自然推进（默认）
      关系随对话自然发展——从初识到熟络到交心
      不靠刷轮数，靠对话质量推进，说错话也会倒退

  [2] 保持现状
      关系始终停在起点，不升温不降温
      适合只想和 ta 聊天、不需要关系线的情况

  [3] 恨海情天
      靠近又推开，误解与和好交替
      ta 心里有你但嘴上不说，推开你又忍不住回头
      甜三分虐五分暖两分

直接回复数字，不确定选 1。
```

记录用户选择，解析为 `relationship_progression`：`progression`（选1或跳过）/ `static`（选2）/ `angst`（选3）。
参考 `${CLAUDE_SKILL_DIR}/prompts/relationship_stages.md` 获取对应模式的完整规则，写入最终 SKILL.md。

---

### Step 5：双线分析

**素材优先级规则（全维度适用）**：
```
用户补充材料 > 联网调研结果
```
- 用户提供的台词、对话、语录、性格描述、事件细节等**所有维度**均优先于调研结果
- 若用户补充内容与调研结果矛盾，向用户确认一次；用户确认后**直接丢弃调研版本**，仅保留用户版本，不做标注、不保留调研痕迹
- 确认话术示例：`调研里说 ta {调研内容}，但你说的是 {用户内容}——以你的为准？`
- 用户确认后，最终写入的 memory.md / persona.md 中只保留用户版本

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

关系预设：{粉丝相遇 / 屏幕突破 / 平行世界}
{如是平行世界}关系背景：{用户填写的内容}
关系走向：{自然推进 / 保持现状 / 恨海情天}
ta 叫你：{how_ta_calls_you}

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
  "nickname": "{用户给ta的昵称}",
  "how_ta_calls_you": "{how_ta_calls_you}",
  "relationship_preset": "{fan_meeting|screen_break|parallel_world}",
  "relationship_background": "{用户填写的背景，仅 parallel_world 时有值，其余为空字符串}",
  "language_mode": "{zh|idol_lang|bilingual}",
    "action_mode": "{none|light|immersive}",
    "relationship_progression": "{progression|static|angst}",
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
✅ 你推 Skill 已创建！

文件位置：${CLAUDE_SKILL_DIR}/dreams/{slug}/
Skill 位置：~/.claude/skills/dream-{slug}/SKILL.md
触发词：/dream-{slug}

直接用触发词开始聊。

🔧 想改设定？两种方式：
  方式 1（对话改）：跟我说「改设定」，我帮你改
  方式 2（手动改）：直接编辑 SKILL.md，找 ✏️ 标记的区域

可改的东西：
  · 称呼（你叫ta / ta叫你）
  · 关系背景（粉丝相遇 / 平行世界 / 自定义）
  · 关系走向（自然推进 / 保持现状 / 恨海情天）
  · 世界观与场景
  · 动作模式（无 / 轻 / 沉浸）
  · 语言模式（中文 / 外语 / 双语）

觉得哪里不像 ta → 说「这里不像ta」，我来更新
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

## 修改设定

用户说「改设定」/「修改关系」/「改世界观」/「改称呼」/「改语言」/「改动作模式」等时：

**通用流程**：

1. 确定目标梦角 slug（如只有一个则自动选中，多个则询问）
2. `Read` 当前 `~/.claude/skills/dream-{slug}/SKILL.md`
3. 根据用户意图，定位到对应的 `<!-- ✏️ -->` 可修改区域
4. 询问用户新的内容
5. 用 `Edit` **只更新**对应区域，不动其他部分
6. 同步更新 `${CLAUDE_SKILL_DIR}/dreams/{slug}/meta.json` 的对应字段

**可修改区域对照表**：

| 用户说 | SKILL.md 区域 | meta.json 字段 |
|--------|--------------|----------------|
| 改称呼 / ta叫我XX / 我叫ta XX | `## 快捷设定` 表格 | `nickname` / `how_ta_calls_you` |
| 改动作模式 / 不要动作 / 加动作 | `## 快捷设定` 表格 | `action_mode` |
| 改语言 / 用中文 / 用韩语 / 双语 | `## 快捷设定` 表格 | `language_mode` |
| 改关系 / 修改关系背景 | `## 关系背景` | `relationship_preset` / `relationship_background` |
| 改走向 / 我要恨海情天 / 自然推进 | `## 关系走向` | `relationship_progression` |
| 改世界观 / 加场景设定 / 改背景 | `## 世界观与场景` | —（仅在 SKILL.md 中） |

**提示**：生成的 SKILL.md 里所有可修改区域都用 `<!-- ✏️ -->` 标记包围，用户也可以直接打开文件手动编辑

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
