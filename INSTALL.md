# 详细安装说明

## Claude Code 安装

> **重要**：Claude Code 从 **git 仓库根目录** 的 `.claude/skills/` 查找 skill。请在正确的位置执行。

### 项目级安装（推荐）

在你的 git 仓库根目录执行：

```bash
mkdir -p .claude/skills
git clone https://github.com/pjygaga/bias-skill .claude/skills/create-dream
```

### 全局安装

```bash
git clone https://github.com/pjygaga/bias-skill ~/.claude/skills/create-dream
```

安装完成后，在 Claude Code 中输入 `/create-dream [角色名]` 即可开始使用。

---

## 依赖安装（可选）

```bash
cd .claude/skills/create-dream  # 或你的安装路径
pip3 install -r requirements.txt
```

目前依赖项：
- `chardet` — 字幕/文本文件编码检测
- `Pillow` — 图片 EXIF 信息读取（照片素材分析）

如果你不需要字幕解析或照片分析功能，可以跳过。

---

## 常见问题

### Q: 数据会上传到云端吗？
A: 不会。所有数据都存储在你的本地文件系统中，不会上传到任何服务器。

### Q: 可以同时创建多个角色吗？
A: 可以。每个角色会生成独立的 `dreams/{slug}/` 目录。

### Q: 创建后还能修改吗？
A: 可以。在对话中说"这里不像 ta"触发纠正，或用 `/update-dream {slug}` 追加新素材。每次修改都有版本存档。

### Q: 我想删除怎么办？
A: 使用 `/delete-dream {slug}` 命令。
