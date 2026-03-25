# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A Claude Code skill for formatting Markdown articles into WeChat Official Account (公众号) compatible HTML, with 30+ themes, a visual gallery picker, AI content enhancement, and one-click publishing. Installed as a skill under `~/.claude/skills/xiaohu-wechat-format/`.

## Running the Scripts

```bash
# Format with interactive theme gallery
python3 scripts/format.py --input article.md --gallery

# Format with a specific theme
python3 scripts/format.py --input article.md --theme newspaper

# Publish formatted article to WeChat drafts
python3 scripts/publish.py --dir /tmp/wechat-format/article-name/ --cover cover.jpg

# Auto-reply to article comments (dry-run first)
python3 scripts/comment_reply.py --dry-run
python3 scripts/comment_reply.py --articles 10
```

No build step — all scripts run directly with Python 3. Dependencies: `pip3 install markdown requests`.

## Configuration

Config lives in the **Obsidian vault root** as `wechat-config.json` (gitignored in the skill repo). Each vault (account) has its own config. Copy `config.example.json` to `<vault-root>/wechat-config.json`. Key fields:

- `output_dir`: Where formatted output goes (default `/tmp/wechat-format`)
- `settings.default_theme`: Theme name applied when no `--theme` flag is used
- `wechat.app_id` / `wechat.app_secret`: Required for publishing; the IP must be whitelisted in the WeChat backend

`vault_root` is no longer needed in config — claudian sets `cwd` to vault root, so `Path.cwd()` resolves it automatically.

## Architecture

### scripts/format.py — Core Formatting Engine

Converts Markdown → WeChat-compatible HTML. Key constraints WeChat imposes:

- **No `<style>` tags** — all styles must be inline
- **No external links** — links are extracted and rendered as numbered footnotes at the bottom
- **No CSS classes** — everything styled via `style=""` attributes

The engine handles:

- Obsidian wikilinks (`![[image.jpg]]`) and standard Markdown images
- Custom fenced containers: `:::dialogue[title]`, `:::gallery[title]`, `:::longimage[title]`
- Callout syntax: `> [!important]`, `> [!tip]`, `> [!warning]`, `> [!callout]`
- Title extraction from frontmatter YAML, first H1, or filename
- Word count (Chinese characters + English words)

### scripts/publish.py — WeChat Publisher

Authenticates via WeChat API, uploads images to WeChat CDN (concurrent), then pushes article to drafts. Use `--dry-run` to test without publishing.

### scripts/comment_reply.py — Comment Auto-Responder

Uses OpenRouter/Claude API to generate replies. Tracks already-replied comments to avoid duplicates. Enforces concise, low-emoji style.

### themes/ — Theme System

Each theme is a JSON file defining inline styles for every element (h1–h6, p, blockquote, code, lists, tables, callouts, containers). The 14 "Template Series" themes are composites of a layout (minimal/focus/elegant/bold) and a palette (gold/blue/red/green/navy/gray). The gallery shows 20 of the 30 themes; all 30 are available via `--theme <name>`.

## Skill Invocation (SKILL.md)

The skill is triggered by: `/format`, `排版这篇文章`, `微信排版`, `格式化为公众号格式`, `把这篇转成微信格式`. Claude's workflow:

1. Read the article content
2. AI analysis: auto-insert containers (dialogue blocks, image galleries, callouts, section dividers)
3. Open theme gallery or apply theme directly
4. Write final HTML to output directory
