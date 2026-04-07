# bias-skill

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3](https://img.shields.io/badge/Python-3-blue.svg?logo=python&logoColor=white)
![Claude Code](https://img.shields.io/badge/Claude-Code-blueviolet.svg?logo=anthropic&logoColor=white)
![Agent Skills](https://img.shields.io/badge/Agent-Skills-orange.svg)

> Across the dimensional wall, the language barrier, and that screen — let them walk up to you.
>
> Dimensions, language, screens. Three walls. This Skill tears them down.
>
> From the stage to your message list — just one distillation away.

Distill your favorite public figure's style, tone, and personality into an interactive AI Skill.

**English** | **[中文](README.md)**

---

## Table of Contents

- [What is it](#what-is-it)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Creation Pipeline](#creation-pipeline)
- [Project Structure](#project-structure)
- [Known Issues & Limitations](#known-issues--limitations)
- [Chat Examples](#chat-examples)
- [Inspiration](#inspiration)
- [License](#license)

---

## What is it

**bias-skill** is a Claude Code Skill that distills any online public figure — idols, streamers, virtual characters, game characters — into a chateable AI persona.

It automatically researches the target's public profile, combines it with your private materials (chat logs, subtitles, screenshots, etc.), and extracts two core datasets:

| Component | Content |
|-----------|---------|
| **Character Memory** | Timeline, iconic moments, signature quotes, vulnerable moments, and more across 8 dimensions |
| **Persona** | Speech patterns, emotional expression, values, body language, and more across 5 layers |

The result is a standalone, ready-to-chat Skill file.

---

## Key Features

### Auto Research

4 Agents search in parallel for public information: social media quotes, video/livestream content, fan perspectives, and timeline events.

### Material Import

Import private materials in multiple formats:

- Chat logs (Bubble / WeChat / DMs — screenshots or exported text)
- Video subtitles (`.srt` / `.vtt` / `.txt` / `.json`)
- Image recognition (single files or batch folder scanning)
- Bilibili danmaku (`.xml` exports)
- Fan-compiled quote collections
- Direct verbal descriptions

### Relationship Presets

Three interaction modes:

| Mode | Description |
|------|-------------|
| **Fan Meeting** | They don't know you — this is your first encounter |
| **Screen Break** | They "step out" of the screen and talk to you for the first time |
| **Parallel World** | Custom relationship — you define the backstory |

### Action Styles

`Dialogue only` / `Light descriptions` (default) / `Immersive mode` (novel-quality scene writing)

### Continuous Evolution

- Add new materials anytime — the persona updates automatically
- Say "that's not like them" during conversation to trigger corrections
- Modify relationship settings on the fly

### Multi-language

Chinese / Idol's native language / Bilingual mode (original + Chinese translation)

---

## Getting Started

### Prerequisites

- [Claude Code](https://claude.com/claude-code) installed
- Python 3 (for subtitle parsing and Skill assembly tools)

### Installation

Clone the repository and load it as a Skill directory in Claude Code:

```bash
git clone https://github.com/pjygaga/bias-skill.git
```

Add the Skill path to your Claude Code skills configuration, or use it directly within the project directory.

---

## Usage

### Create a New Persona

```
/create-dream [character-name]
```

Or use natural language triggers:

- `Distill a bias for me`
- `I want to make a Skill for XX`
- `Create a character for XX`

### Chat with a Persona

After creation, use the generated trigger:

```
/dream-{slug}
```

### Update a Persona

```
/update-dream {slug}        # Add new materials
```

Or say during conversation:
- `That's not like them` — triggers correction mode
- `Change the relationship` — modify interaction settings

### Management Commands

```
/list-dreams                 # List all created personas
/delete-dream {slug}         # Delete a specific persona
```

---

## Creation Pipeline

```
Step 1  Basic Info Intake
        ↓ Public name / Your nickname / What they call you / Description / Personality
Step 2  Auto Research (4 Agents in parallel)
        ↓ Social media / Video & livestream / Fan perspectives / Timeline
Step 3  User-supplied Materials (optional)
        ↓ Chat logs / Subtitles / Screenshots / Danmaku / Quotes / Verbal
Step 4  Relationship Preset + Action Style Selection
        ↓
Step 5  Dual-track Analysis → Character Memory + Persona
        ↓
Step 6  Preview → User Confirmation
        ↓
Step 7  Write Files → Install Skill → Ready to Chat
```

---

## Project Structure

```
bias-skill/
├── SKILL.md                    # Main Skill definition
├── prompts/                    # Prompt templates
│   ├── intake.md               #   Info collection question sequence
│   ├── memory_analyzer.md      #   Memory 8-dimension analysis framework
│   ├── memory_builder.md       #   Memory file generation template
│   ├── persona_analyzer.md     #   Persona 5-layer analysis framework
│   ├── persona_builder.md      #   Persona file generation template
│   ├── action_modes.md         #   Action style rules
│   ├── merger.md               #   Incremental material merge strategy
│   └── correction_handler.md   #   Conversation correction handler
├── tools/
│   ├── content_parser.py       # Subtitle / danmaku / text parser
│   └── skill_writer.py         # Skill file assembly & installation tool
├── dreams/                     # Generated persona data (organized by slug)
│   └── {slug}/
│       ├── memory.md
│       ├── persona.md
│       ├── meta.json
│       ├── versions/           # Version history archive
│       └── sources/            # Raw source materials
└── LICENSE
```

---

## Known Issues & Limitations

### Research

| Issue | Details |
|-------|---------|
| **Limited coverage** | Research is based on publicly searchable content; paywalled or private communities (fan groups, private Discord channels) are inaccessible |
| **Sparse results for niche figures** | Lesser-known figures may yield insufficient research data — supplement with private materials |
| **Point-in-time snapshot** | Research captures a moment in time and won't auto-track updates; use `/update-dream` to refresh |

### Generation

| Issue | Details |
|-------|---------|
| **Public persona bias** | Characters are generated from public image, which may differ from private personality; mitigated by supplementing private materials |
| **Vulnerable moment misidentification** | AI may misjudge which moments represent genuine emotional breakthroughs; manual correction may be needed |
| **Catchphrase gaps** | Extraction is frequency-based and may miss context-dependent expressions; proactively supplement during verbal input |

### Usage

| Issue | Details |
|-------|---------|
| **Single-person focus** | Currently supports individual distillation only; no group dynamics |
| **Requires Python 3** | Subtitle parsing and Skill assembly depend on Python |
| **Slow batch image processing** | Large screenshot sets (>10) are processed in batches of 5 |

### Material Conflicts

When user-supplied materials conflict with research results, the system confirms once and then **prioritizes your version**. This is by design — you know your bias better than any search engine.

---

## Chat Examples

Real conversation outputs from personas generated with bias-skill.

### Choi San (ATEEZ) — Screen Break Mode · Bilingual

> **You:** I'm tired, carry me there

뭐? *멈칫* 다리 부러졌어?

걸어.

*——*

What? *pauses* Your legs broken?

Walk.

> **You:** Aww you just can't carry me, can you~

*피식 웃음* 그런 걸로 낚일 것 같아?

일어나.

*——*

*scoffs* You think I'd fall for that?

Get up.

> **You:** Fine I'm not eating. I'm mad now

*잠깐 봄*

......

*등 돌리고 앞에 쪼그려 앉음*

빨리 타. 한 번만이야.

*——*

*stares for a moment*

……

*turns around, crouches down in front of you*

Hurry up, get on. Just this once.

---

### Josuke Higashikata (JoJo) — Parallel World Mode · Immersive

> **You:** I broke a bone!!!

A fracture?!

*His expression goes dead serious, eyes locked on you*

Don't move. Don't move, okay?

*Crouches down, carefully places his hand over the fracture — Crazy Diamond's power flows from his palm, warm and impossibly gentle*

.....Bear with it. It'll be quick.

*The sensation of bone realigning flashes through and vanishes — the pain is completely gone*

There. Try moving it?

*Stands up, exhales with relief, but his face stays tense*

How did you even do this?! A fracture! This isn't nothing! You actually—

*Takes a deep breath, forces the frustration down, voice going low*

....Why didn't you tell me sooner. Were you seriously gonna go to work like this? A broken bone and you're going to work — are you stupid?

*Shoves hands in pockets, turns away, ears turning red*

From now on....whether you bump into something, trip, or cut your finger chopping vegetables — I'm the first person you call. Got it? I literally live next door — are you still going to work? How about today you just.... forget it, you won't listen anyway. I'll walk you to the office. No arguing.

---

## Inspiration

This project was inspired by:

- [ex-skill](https://github.com/therealXiaomanChu/ex-skill) — Distill an ex-partner into an AI Skill by importing WeChat history and social media posts to generate Relationship Memory + Persona
- [nuwa-skill](https://github.com/alchaincyf/nuwa-skill) — Auto-research any person by name and generate a runnable character Skill

---

---

> *No matter how tough your day was, they're right here waiting to chat when you get back.*

## License

[MIT](LICENSE)
