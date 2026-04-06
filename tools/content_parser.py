#!/usr/bin/env python3
"""公开内容解析器 — dream-skill 专用

支持的输入格式：
- .srt / .vtt   视频字幕文件
- .txt          纯文本（弹幕导出、直播文字稿、粉丝语录）
- .json         结构化数据（各平台 API 导出）
- .xml          B站弹幕导出文件（基础支持）
- 图片/截图     由 Claude Read 工具处理，无需本脚本

Usage:
    python3 content_parser.py --file <path> --target <name> --output <path> [--format auto]
"""

import argparse
import json
import re
import os
import sys
from pathlib import Path
from collections import Counter


# ─────────────────────────────────────────────
# 格式检测
# ─────────────────────────────────────────────

def detect_format(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext in ('.srt', '.vtt'):
        return 'subtitle'
    if ext == '.xml':
        return 'bilibili_danmaku'
    if ext == '.json':
        return 'json'
    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            head = f.read(1000)
        # B站弹幕有时导出为 txt
        if '<d p=' in head:
            return 'bilibili_danmaku'
        return 'plaintext'
    return 'plaintext'


# ─────────────────────────────────────────────
# 字幕解析（.srt / .vtt）
# ─────────────────────────────────────────────

def parse_subtitle(file_path: str, target_name: str) -> dict:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.read()

    # 去除序号、时间码行，只保留文字
    # SRT 时间码: 00:00:01,000 --> 00:00:03,000
    # VTT 时间码: 00:00:01.000 --> 00:00:03.000
    lines = raw.splitlines()
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\d+$', line):
            continue
        if re.match(r'[\d:,\.]+ --> [\d:,\.]+', line):
            continue
        if line.startswith('WEBVTT'):
            continue
        # 去除 HTML 标签（字幕常有 <i> <b> 等）
        line = re.sub(r'<[^>]+>', '', line)
        if line:
            text_lines.append(line)

    full_text = '\n'.join(text_lines)
    return _analyze_text(full_text, target_name, source_type='subtitle')


# ─────────────────────────────────────────────
# B站弹幕解析（.xml）
# ─────────────────────────────────────────────

def parse_bilibili_danmaku(file_path: str, target_name: str) -> dict:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.read()

    # 提取 <d p="...">弹幕内容</d>
    pattern = re.compile(r'<d\s+p="[^"]*">([^<]+)</d>')
    danmaku_list = pattern.findall(raw)

    if not danmaku_list:
        # 尝试纯文本格式的弹幕
        danmaku_list = [line.strip() for line in raw.splitlines() if line.strip()]

    full_text = '\n'.join(danmaku_list)
    result = _analyze_text(full_text, target_name, source_type='bilibili_danmaku')
    result['danmaku_count'] = len(danmaku_list)
    return result


# ─────────────────────────────────────────────
# JSON 解析
# ─────────────────────────────────────────────

def parse_json(file_path: str, target_name: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    texts = []

    def extract_text(obj, depth=0):
        if depth > 5:
            return
        if isinstance(obj, str) and len(obj) > 2:
            texts.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                extract_text(item, depth + 1)
        elif isinstance(obj, dict):
            # 优先提取常见文本字段
            for key in ('content', 'text', 'message', 'body', 'caption',
                        'description', 'comment', 'note', 'post'):
                if key in obj:
                    extract_text(obj[key], depth + 1)
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    extract_text(v, depth + 1)

    extract_text(data)
    full_text = '\n'.join(texts)
    return _analyze_text(full_text, target_name, source_type='json')


# ─────────────────────────────────────────────
# 纯文本解析
# ─────────────────────────────────────────────

def parse_plaintext(file_path: str, target_name: str) -> dict:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        full_text = f.read()
    return _analyze_text(full_text, target_name, source_type='plaintext')


# ─────────────────────────────────────────────
# 核心分析逻辑（所有格式共用）
# ─────────────────────────────────────────────

def _analyze_text(text: str, target_name: str, source_type: str) -> dict:
    # 语气词提取
    particle_pattern = re.compile(r'[哈嗯哦噢嘿唉呜啊呀吧嘛呢吗么诶哇草]{1,4}')
    particles = particle_pattern.findall(text)
    top_particles = Counter(particles).most_common(10)

    # Emoji 提取
    emoji_pattern = re.compile(
        r'[\U0001F600-\U0001F64F'
        r'\U0001F300-\U0001F5FF'
        r'\U0001F680-\U0001F6FF'
        r'\U0001F1E0-\U0001F1FF'
        r'\U00002702-\U000027B0'
        r'\U0001F900-\U0001F9FF'
        r'\U0001FA00-\U0001FA9F]+',
        re.UNICODE
    )
    emojis = emoji_pattern.findall(text)
    top_emojis = Counter(emojis).most_common(10)

    # 标点统计
    punctuation = {
        '句号（。）': text.count('。'),
        '感叹号（！）': text.count('！') + text.count('!'),
        '问号（？）': text.count('？') + text.count('?'),
        '省略号（...）': text.count('...') + text.count('…'),
        '波浪号（～）': text.count('～') + text.count('~'),
        '无标点短句': len(re.findall(r'[^\。！？\.\!\?…]{5,20}\n', text)),
    }

    # 句子长度分布
    sentences = re.split(r'[。！？\n]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 1]
    lengths = [len(s) for s in sentences]
    avg_len = round(sum(lengths) / len(lengths), 1) if lengths else 0

    # 高频词（简单实现：2字以上词频）
    words = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
    # 过滤停用词
    stopwords = {'这个', '那个', '一个', '什么', '怎么', '为什么', '因为', '所以',
                 '但是', '然后', '现在', '已经', '可以', '没有', '这样', '那样',
                 '觉得', '知道', '感觉', '时候', '大家', '自己', '我们', '你们',
                 '他们', '这里', '那里', '真的', '其实', '一直', '一样', '还是'}
    filtered_words = [w for w in words if w not in stopwords]
    top_words = Counter(filtered_words).most_common(20)

    # 提取样本（前 80 个非空行，最能代表说话风格）
    all_lines = [line.strip() for line in text.splitlines() if line.strip()]
    samples = all_lines[:80]

    # 判断说话风格
    if avg_len < 15:
        style = '短句连发型'
    elif avg_len < 40:
        style = '中等长度型'
    else:
        style = '长段落型'

    return {
        'target_name': target_name,
        'source_type': source_type,
        'char_count': len(text),
        'line_count': len(all_lines),
        'analysis': {
            'top_particles': top_particles,
            'top_emojis': top_emojis,
            'punctuation_habits': punctuation,
            'avg_sentence_length': avg_len,
            'speaking_style': style,
            'top_words': top_words,
        },
        'samples': samples,
    }


# ─────────────────────────────────────────────
# 输出格式化
# ─────────────────────────────────────────────

def write_output(result: dict, output_path: str):
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    target = result.get('target_name', '未知')
    src = result.get('source_type', '未知')
    analysis = result.get('analysis', {})

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# 公开内容分析 — {target}\n\n")
        f.write(f"来源类型：{src}\n")
        f.write(f"文本量：{result.get('char_count', 0)} 字 / {result.get('line_count', 0)} 行\n")
        if result.get('danmaku_count'):
            f.write(f"弹幕条数：{result['danmaku_count']} 条\n")
        f.write("\n")

        # 说话风格
        f.write("## 说话风格\n")
        f.write(f"- 平均句子长度：{analysis.get('avg_sentence_length', 'N/A')} 字\n")
        f.write(f"- 风格类型：{analysis.get('speaking_style', 'N/A')}\n\n")

        # 高频语气词
        particles = analysis.get('top_particles', [])
        if particles:
            f.write("## 高频语气词\n")
            for word, count in particles:
                f.write(f"- {word}：{count} 次\n")
            f.write("\n")

        # Emoji
        emojis = analysis.get('top_emojis', [])
        if emojis:
            f.write("## 高频 Emoji\n")
            for emoji, count in emojis:
                f.write(f"- {emoji}：{count} 次\n")
            f.write("\n")

        # 标点习惯
        punct = analysis.get('punctuation_habits', {})
        if punct:
            f.write("## 标点习惯\n")
            for name, count in punct.items():
                f.write(f"- {name}：{count} 次\n")
            f.write("\n")

        # 高频词
        top_words = analysis.get('top_words', [])
        if top_words:
            f.write("## 高频词（前20）\n")
            f.write("、".join([f"{w}({c})" for w, c in top_words[:20]]))
            f.write("\n\n")

        # 样本
        samples = result.get('samples', [])
        if samples:
            f.write("## 内容样本（前80行）\n")
            for i, line in enumerate(samples[:80], 1):
                f.write(f"{i}. {line}\n")

    print(f"分析完成，结果已写入 {output_path}")


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='公开内容解析器 — dream-skill')
    parser.add_argument('--file', required=True, help='输入文件路径')
    parser.add_argument('--target', required=True, help='人物名字/代号')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--format', default='auto',
                        help='格式：auto / subtitle / bilibili_danmaku / json / plaintext')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)

    fmt = args.format
    if fmt == 'auto':
        fmt = detect_format(args.file)
        print(f"自动检测格式：{fmt}")

    parsers = {
        'subtitle': parse_subtitle,
        'bilibili_danmaku': parse_bilibili_danmaku,
        'json': parse_json,
        'plaintext': parse_plaintext,
    }

    parse_fn = parsers.get(fmt, parse_plaintext)
    result = parse_fn(args.file, args.target)
    write_output(result, args.output)


if __name__ == '__main__':
    main()
