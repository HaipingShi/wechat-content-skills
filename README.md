# wechat-content-skills

Claude Code skills for end-to-end WeChat Official Account (公众号) content creation — optimized for the **Obsidian + [claudian](https://github.com/YishenTu/claudian)** workflow.

**[中文说明](README_CN.md)**

> **Fork of [xiaohuailabs/xiaohu-wechat-format](https://github.com/xiaohuailabs/xiaohu-wechat-format)**
> Extended with a polish skill, text-to-image generation, a dark editorial theme, and per-vault configuration designed for claudian.

---

## Why Obsidian + claudian

[claudian](https://github.com/YishenTu/claudian) is an Obsidian plugin that runs Claude Code directly inside your vault. It sets the **vault root as the working directory**, which unlocks a natural per-account configuration model: each vault has its own `wechat-config.json`, so you can manage multiple WeChat accounts without any path juggling.

Writing in Obsidian → running these skills via claudian → publishing to WeChat is a single continuous flow, with no context switching.

---

## Three Skills

### `/format` — WeChat Formatter

Converts Markdown to WeChat-compatible inline-styled HTML.

- 31 themes with a visual gallery picker (previews your actual article)
- AI content enhancement: auto-detects dialogue, callouts, image sequences
- Handles WeChat's restrictions: inline styles only, external links → footnotes, Obsidian `![[image]]` wikilinks
- One-click publish to WeChat drafts (uploads images to WeChat CDN)

**Trigger**: say `排版这篇文章`, `/format`, or `微信排版`

### `/polish` — AI Flavor Removal

Analyzes and rewrites articles to remove the "written by AI" feel — predictable sentence patterns, filler connectives, mechanical three-part structure.

Follows a decision tree based on two questions:
- **Audience**: AI/RAG system, or human readers?
- **Content type**: rational (knowledge, tutorials) or emotional (narrative, reflection)?

Each path applies a different strategy: hardening structure for RAG, stripping template language for rational content, or breaking predictable rhythm for emotional pieces.

**Trigger**: say `去AI味`, `/polish`, or `润色这篇文章`

### `/t2i` — Text to Image (Gemini)

Generates illustrations that match the article's emotional tone and rhythm — not generic stock images.

Before generating, Claude does a **visual art direction pass**:
1. Maps the article's emotional arc and content density
2. Identifies natural insertion points (concept transitions, emotional peaks — not mechanical "one image per section")
3. Writes a creative brief for each image: a specific visual metaphor, composition notes, mood descriptor

Uses Gemini's image generation API. Style prompts are stored as JSON files in `prompts/` — built-in styles ship with the skill, custom styles go in `{vault}/t2i-prompts/` where you can edit them in Obsidian.

**Trigger**: say `生成配图`, `/t2i`, or `把这个可视化`

**Requires**: `GEMINI_API_KEY` set in claudian's environment variables

---

## Full Pipeline

```
Write in Obsidian
      ↓
/polish          ← remove AI flavor (optional)
      ↓
/t2i             ← generate illustrations
      ↓
/format          ← WeChat-compatible HTML + theme gallery
      ↓
Publish to drafts
```

---

## Installation

### With claudian (recommended)

Install to Claude Code's skills directory:

```bash
cd ~/.claude/skills/
git clone https://github.com/HaipingShi/wechat-content-skills.git
pip3 install markdown requests
```

Place `wechat-config.json` in each vault root (see Configuration below). claudian will pick it up automatically.

### Standalone (without claudian)

The format and publish scripts run independently of any AI framework:

```bash
# Format with gallery
python3 scripts/format.py --input article.md --gallery

# Format with specific theme
python3 scripts/format.py --input article.md --theme newspaper

# Publish to WeChat drafts
python3 scripts/publish.py --dir /tmp/wechat-format/article/ --cover cover.jpg

# Generate image
python3 scripts/t2i.py --prompt "your creative brief" --style cover
```

---

## Configuration

Config lives in the **vault root** as `wechat-config.json` — one file per vault, per WeChat account. Copy the example:

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
    "app_id": "YOUR_APP_ID",
    "app_secret": "YOUR_APP_SECRET"
  }
}
```

`vault_root` is not needed — claudian sets the working directory to the vault root automatically.

**WeChat API**: Get AppID/AppSecret from WeChat Official Account Admin → Settings → Basic Configuration. Add your public IP to the IP whitelist (error 40164 means the IP is missing).

**Gemini API**: Set `GEMINI_API_KEY` in claudian's Environment Variables settings (per-vault).

---

## Themes (31)

### Standalone Styles (9)

| Theme | ID | Style |
|-------|----|-------|
| Terracotta | `terracotta` | Warm orange, rounded headers |
| ByteDance | `bytedance` | Blue-teal gradient, modern tech |
| Chinese | `chinese` | Vermillion red, classical |
| Newspaper | `newspaper` | NYT-style serif, serious depth |
| GitHub | `github` | Developer-friendly, light code blocks |
| SSPAI | `sspai` | Chinese tech media red |
| Bauhaus | `bauhaus` | Primary colors, geometric |
| Ink | `ink` | Pure black, minimal whitespace |
| Midnight | `midnight` | Dark background, neon accents |

### Curated Styles (8)

| Theme | ID | Style |
|-------|----|-------|
| Sports | `sports` | Gradient stripes, energetic |
| Mint | `mint-fresh` | Mint green, fresh |
| Sunset | `sunset-amber` | Warm amber tones |
| Lavender | `lavender-dream` | Purple, dreamy |
| Coffee | `coffee-house` | Brown, warm |
| WeChat Native | `wechat-native` | WeChat green |
| Magazine | `magazine` | Extra whitespace, editorial |
| Dark Report | `dark-report` | Dark warm charcoal, amber accents — for analysis and strategy pieces |

### Template Series (14)

4 layouts (Minimal / Focus / Elegant / Bold) × color variants (Gold / Blue / Red / Green / Navy / Gray)

---

## Image Generation Styles

Two built-in styles ship with the skill:

| Style | ID | Use case |
|-------|----|----------|
| Technical Infographic | `infographic` | Architecture diagrams, decision trees, system maps — high-contrast monochrome |
| Article Cover | `cover` | WeChat header images — 16:9, editorial quality |

Add custom styles by placing JSON files in `{vault}/t2i-prompts/`. Vault styles override built-in styles with the same name, so you can iterate on prompts directly in Obsidian.

---

## WeChat Compatibility

WeChat's editor strips `<style>` tags and CSS classes. The format script handles:

- All styles written as inline `style="..."` attributes
- `<ul>/<ol>` converted to `<section>` + flexbox (WeChat mangles native lists)
- External links `[text](url)` → inline footnote references + footnote list at bottom
- Obsidian `![[image.jpg]]` wikilinks searched across the vault and resolved
- Callout blocks (`[!tip]`, `[!important]`, `[!warning]`, `[!callout]`) with distinct colors
- Dialogue blocks (`:::dialogue`) → chat bubble layout
- Image galleries (`:::gallery`) → horizontal scroll container

---

## Requirements

- Python 3
- `pip3 install markdown requests`
- claudian (for Obsidian integration) — [github.com/YishenTu/claudian](https://github.com/YishenTu/claudian)
- Gemini API key (for `/t2i` only)

---

## License

MIT

---

*Based on [xiaohuailabs/xiaohu-wechat-format](https://github.com/xiaohuailabs/xiaohu-wechat-format). Extended with polish skill, Gemini image generation, dark-report theme, and claudian-native per-vault configuration.*
