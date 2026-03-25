# wechat-content-skills

专为 **Obsidian + [claudian](https://github.com/YishenTu/claudian)** 工作流设计的微信公众号内容创作技能套件——从写作到发布，全程在 Obsidian 内完成。

**[English README](README.md)**

> **Fork 自 [xiaohuailabs/xiaohu-wechat-format](https://github.com/xiaohuailabs/xiaohu-wechat-format)**
> 在原版基础上增加了 polish（去AI味）技能、Gemini 文生图、暗色深度报告主题，以及专为 claudian 设计的 per-vault 配置架构。

---

## 为什么选择 Obsidian + claudian

[claudian](https://github.com/YishenTu/claudian) 是一个 Obsidian 插件，能在 vault 内直接运行 Claude Code，并将 **vault 根目录设为工作目录**。这带来了一个天然的多账号管理模型：每个 vault 有自己的 `wechat-config.json`，多个公众号互不干扰，无需手动指定路径。

在 Obsidian 里写作 → 通过 claudian 调用技能 → 发布到公众号，一条完整的流水线，不需要切换任何工具。

---

## 三个技能

### `/format` — 微信排版

将 Markdown 转换为微信公众号兼容的内联样式 HTML。

- 31 套主题，可视化画廊预览（用真实文章预览每套主题效果）
- AI 内容增强：自动识别对话体、callout 提示框、连续图片序列
- 处理微信限制：只用内联样式、外链自动转脚注、Obsidian `![[image]]` 格式自动解析
- 一键发布到草稿箱（自动上传图片到微信 CDN）

**触发方式**：说 `排版这篇文章`、`/format`、或 `微信排版`

### `/polish` — 去AI味

分析并改写文章，消除"AI腔"——可预测的句型、连接词堆砌、机械三段式结构。

基于两个问题的决策树：
- **读者**：AI/RAG 系统，还是真实人类？
- **内容类型**：理性向（知识、教程）还是情感向（叙事、随笔）？

不同路径对应不同策略：为 RAG 强化结构，为理性内容去模板化，为情感内容打破可预测节奏。

**触发方式**：说 `去AI味`、`/polish`、或 `润色这篇文章`

### `/t2i` — 文生图（Gemini）

根据文章的情绪基调和叙事节奏生成配图——不是通用素材图。

生成前，Claude 先做**视觉选角分析**：
1. 判断文章的情绪弧线和内容密度
2. 找自然插图位置（概念转折点、情绪高峰——不是机械地每节一图）
3. 为每张图写创意指令：具体的视觉隐喻、构图说明、情绪注脚

使用 Gemini 图像生成 API。风格 prompt 以 JSON 文件存储在 `prompts/` 目录——内置风格随技能发布，自定义风格放在 `{vault}/t2i-prompts/`，可直接在 Obsidian 里编辑。

**触发方式**：说 `生成配图`、`/t2i`、或 `把这个可视化`

**需要**：在 claudian 的环境变量中配置 `GEMINI_API_KEY`

---

## 完整流程

```
在 Obsidian 里写作
      ↓
/polish          ← 去AI味（可选）
      ↓
/t2i             ← 视觉选角 + 生成配图
      ↓
/format          ← 微信排版 + 主题选择
      ↓
发布到草稿箱
```

---

## 安装

### 配合 claudian（推荐）

安装到 Claude Code 的 skills 目录：

```bash
cd ~/.claude/skills/
git clone https://github.com/HaipingShi/wechat-content-skills.git
pip3 install markdown requests
```

在每个 vault 根目录放一个 `wechat-config.json`（见配置章节），claudian 会自动识别。

### 独立使用（不依赖 claudian）

格式化和发布脚本可独立运行：

```bash
# 带画廊预览排版
python3 scripts/format.py --input article.md --gallery

# 指定主题排版
python3 scripts/format.py --input article.md --theme newspaper

# 发布到公众号草稿箱
python3 scripts/publish.py --dir /tmp/wechat-format/article/ --cover cover.jpg

# 生成图片
python3 scripts/t2i.py --prompt "你的创意指令" --style cover
```

---

## 配置

配置文件放在 **vault 根目录**，命名为 `wechat-config.json`——一个 vault 一个文件，对应一个公众号账号。复制示例配置：

```bash
cp ~/.claude/skills/wechat-content-skills/config.example.json /path/to/your/vault/wechat-config.json
```

```json
{
  "output_dir": "/tmp/wechat-format",
  "settings": {
    "default_theme": "newspaper",
    "auto_open_browser": true
  },
  "wechat": {
    "app_id": "你的AppID",
    "app_secret": "你的AppSecret"
  }
}
```

`vault_root` 不需要填写——claudian 会自动将工作目录设为 vault 根目录。

**微信 API**：AppID 和 AppSecret 在公众号后台 → 设置与开发 → 基本配置 获取。需要将服务器 IP 加入 IP 白名单（报 40164 说明 IP 未加白）。

**Gemini API**：在 claudian 的环境变量设置中添加 `GEMINI_API_KEY`（per-vault）。

---

## 主题（31 套）

### 独立风格（9 个）

| 主题 | ID | 风格 |
|------|----|------|
| 赤陶 | `terracotta` | 暖橙色，圆角标题 |
| 字节蓝 | `bytedance` | 蓝青渐变，科技现代 |
| 中国风 | `chinese` | 朱砂红，古典雅致 |
| 报纸 | `newspaper` | 纽约时报风，严肃深度 |
| GitHub | `github` | 开发者风，浅色代码块 |
| 少数派 | `sspai` | 中文科技媒体红 |
| 包豪斯 | `bauhaus` | 三原色，几何先锋 |
| 墨韵 | `ink` | 纯黑极简，大量留白 |
| 暗夜 | `midnight` | 深色底，霓虹色点缀 |

### 精选风格（8 个）

| 主题 | ID | 风格 |
|------|----|------|
| 运动 | `sports` | 渐变色带，活力动感 |
| 薄荷 | `mint-fresh` | 薄荷绿，清爽 |
| 日落 | `sunset-amber` | 琥珀暖调 |
| 薰衣草 | `lavender-dream` | 紫色梦幻 |
| 咖啡馆 | `coffee-house` | 棕色暖调 |
| 微信原生 | `wechat-native` | 微信绿 |
| 杂志 | `magazine` | 超大留白，编辑感 |
| 深度报告 | `dark-report` | 深暖碳灰底，琥珀金点缀——适合分析和策略类文章 |

### 模板系列（14 个）

4 种布局（简约 / 聚焦 / 精致 / 醒目）× 配色变体（金 / 蓝 / 红 / 绿 / 藏青 / 灰）

---

## 图片生成风格

内置两种风格：

| 风格 | ID | 适用场景 |
|------|----|----------|
| 技术信息图 | `infographic` | 架构图、决策树、系统图——高对比度黑白 |
| 公众号题图 | `cover` | 文章头图——16:9 横版，编辑风格 |

在 `{vault}/t2i-prompts/` 目录放 JSON 文件可添加自定义风格。同名文件优先级高于内置，可直接在 Obsidian 里迭代调整 prompt。

---

## 微信兼容性处理

微信编辑器会过滤掉 `<style>` 标签和 CSS class。格式化脚本的处理策略：

- 所有样式写为内联 `style="..."` 属性
- `<ul>/<ol>` 转换为 `<section>` + flex 布局（微信会破坏原生列表）
- 外链 `[文字](url)` → 行内脚注引用 + 文末脚注列表
- Obsidian `![[image.jpg]]` 格式在 vault 内全局搜索并解析
- Callout 块（`[!tip]`、`[!important]`、`[!warning]`、`[!callout]`）带独立颜色样式
- 对话块（`:::dialogue`）→ 气泡聊天布局
- 图片画廊（`:::gallery`）→ 横向滚动容器

---

## 依赖

- Python 3
- `pip3 install markdown requests`
- claudian（Obsidian 集成）— [github.com/YishenTu/claudian](https://github.com/YishenTu/claudian)
- Gemini API Key（仅 `/t2i` 需要）

---

## License

MIT

---

*基于 [xiaohuailabs/xiaohu-wechat-format](https://github.com/xiaohuailabs/xiaohu-wechat-format)。在原版基础上增加了 polish 技能、Gemini 文生图、deep-report 主题，以及 claudian-native 的 per-vault 配置架构。*
