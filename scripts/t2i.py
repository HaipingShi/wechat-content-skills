#!/usr/bin/env python3
"""文生图工具（Gemini）

使用 Gemini 图像生成 API，根据文章内容或指定文本生成图片。
API Key 通过环境变量 GEMINI_API_KEY 传入（在 claudian 中配置）。

用法:
    # 使用文章内容生成信息图
    python3 t2i.py --input article.md --style infographic

    # 直接输入文本
    python3 t2i.py --content "决策树：RAG vs 人类读者" --style infographic

    # 生成公众号封面
    python3 t2i.py --input article.md --style cover

    # 列出可用风格
    python3 t2i.py --list-styles

    # 使用 Pro 模型（质量更高，速度较慢）
    python3 t2i.py --input article.md --style infographic --model pro
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

import requests

# ── 路径 ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
BUILTIN_PROMPTS_DIR = SKILL_DIR / "prompts"

# 模型配置
MODELS = {
    "flash": "gemini-3.1-flash-image-preview",   # 速度优先（默认）
    "pro":   "gemini-3-pro-image-preview",        # 质量优先，支持 Thinking
}
DEFAULT_MODEL = "flash"

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


# ── Prompt 管理 ──────────────────────────────────────────────────────────

def get_prompts_dirs() -> list[Path]:
    """返回 prompt 查找目录列表（vault 覆盖 > 内置）"""
    dirs = []
    # 1. vault 自定义（用户可在 Obsidian 里编辑）
    vault_prompts = Path.cwd() / "t2i-prompts"
    if vault_prompts.exists():
        dirs.append(vault_prompts)
    # 2. 内置
    if BUILTIN_PROMPTS_DIR.exists():
        dirs.append(BUILTIN_PROMPTS_DIR)
    return dirs


def list_styles() -> list[dict]:
    """列出所有可用风格（vault 覆盖内置同名风格）"""
    seen = set()
    styles = []
    for d in get_prompts_dirs():
        for f in sorted(d.glob("*.json")):
            if f.stem not in seen:
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    styles.append({
                        "id": f.stem,
                        "name": data.get("name", f.stem),
                        "description": data.get("description", ""),
                        "tags": data.get("tags", []),
                        "source": "vault" if d == Path.cwd() / "t2i-prompts" else "builtin",
                    })
                    seen.add(f.stem)
                except (json.JSONDecodeError, OSError):
                    pass
    return styles


def load_style(style_id: str) -> dict:
    """加载指定风格的 prompt，vault 覆盖内置"""
    for d in get_prompts_dirs():
        path = d / f"{style_id}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                print(f"错误：读取 prompt 文件失败 {path}: {e}", file=sys.stderr)
                sys.exit(1)
    available = [s["id"] for s in list_styles()]
    print(f"错误：找不到风格 '{style_id}'", file=sys.stderr)
    print(f"可用风格：{', '.join(available) or '（无）'}", file=sys.stderr)
    sys.exit(1)


# ── 内容提取 ─────────────────────────────────────────────────────────────

def extract_content(args) -> str:
    """从文件或命令行参数提取要可视化的内容"""
    if args.content:
        return args.content.strip()

    if args.input:
        path = Path(args.input)
        if not path.exists():
            # 尝试相对于 vault root 解析
            path = Path.cwd() / args.input
        if not path.exists():
            print(f"错误：找不到文件 {args.input}", file=sys.stderr)
            sys.exit(1)
        text = path.read_text(encoding="utf-8")
        # 去掉 YAML frontmatter
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                text = text[end + 3:].strip()
        # 截断到合理长度（prompt 不宜过长）
        if len(text) > 3000:
            text = text[:3000] + "\n\n[内容已截断]"
        return text.strip()

    print("错误：请通过 --input 或 --content 提供内容", file=sys.stderr)
    sys.exit(1)


# ── Gemini API ───────────────────────────────────────────────────────────

def generate_image(prompt: str, model_key: str, api_key: str) -> bytes:
    """调用 Gemini 图像生成 API，返回 PNG 字节"""
    model = MODELS[model_key]
    url = f"{API_BASE}/{model}:generateContent"

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
    }

    print(f"  模型: {model}", file=sys.stderr)
    print(f"  Prompt 长度: {len(prompt)} 字符", file=sys.stderr)

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
    except requests.Timeout:
        print("错误：API 请求超时（120s）", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"错误：请求失败 {e}", file=sys.stderr)
        sys.exit(1)

    if not resp.ok:
        try:
            err = resp.json()
            msg = err.get("error", {}).get("message", resp.text)
        except Exception:
            msg = resp.text
        print(f"错误：API 返回 {resp.status_code}: {msg}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        print("错误：API 返回空结果", file=sys.stderr)
        sys.exit(1)

    parts = candidates[0].get("content", {}).get("parts", [])
    for part in parts:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
        if "inline_data" in part:
            return base64.b64decode(part["inline_data"]["data"])

    # 如果只返回了文本（通常是 safety block 或说明）
    text_parts = [p.get("text", "") for p in parts if "text" in p]
    if text_parts:
        print(f"API 返回文本而非图片：\n{chr(10).join(text_parts)}", file=sys.stderr)
    else:
        print("错误：响应中没有图片数据", file=sys.stderr)
    sys.exit(1)


# ── 输出路径 ─────────────────────────────────────────────────────────────

def resolve_output(args, style_id: str) -> Path:
    """确定输出文件路径"""
    if args.output:
        p = Path(args.output)
        if p.is_dir():
            # 自动生成自然语言文件名
            from datetime import datetime
            # 从内容中提取关键词生成描述性文件名
            content_preview = ""
            if args.prompt:
                content_preview = args.prompt[:50].strip()
            elif args.content:
                content_preview = args.content[:50].strip()
            elif args.input:
                # 从文件名提取关键词
                input_name = Path(args.input).stem
                content_preview = input_name.replace('_', ' ').replace('-', ' ')

            # 生成自然语言文件名
            if content_preview:
                # 清理文件名：移除特殊字符，限制长度
                safe_name = "".join(c for c in content_preview if c.isalnum() or c in " _-").strip()
                safe_name = safe_name.replace(" ", "_").replace("-", "_")[:30].rstrip("_")
                if safe_name:
                    filename = f"{style_id}_{safe_name}.png"
                else:
                    # fallback 到时间戳
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{style_id}_{ts}.png"
            else:
                # fallback 到时间戳
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{style_id}_{ts}.png"

            return p / filename
        # 确保父目录存在
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # 默认：vault attachments 目录或 /tmp
    candidates = [
        Path.cwd() / "attachments",
        Path.cwd() / "assets",
        Path("/tmp"),
    ]
    for d in candidates:
        if d.exists():
            # 生成自然语言文件名
            content_preview = ""
            if args.prompt:
                content_preview = args.prompt[:50].strip()
            elif args.content:
                content_preview = args.content[:50].strip()
            elif args.input:
                # 从文件名提取关键词
                input_name = Path(args.input).stem
                content_preview = input_name.replace('_', ' ').replace('-', ' ')

            # 生成自然语言文件名
            if content_preview:
                # 清理文件名：移除特殊字符，限制长度
                safe_name = "".join(c for c in content_preview if c.isalnum() or c in " _-").strip()
                safe_name = safe_name.replace(" ", "_").replace("-", "_")[:30].rstrip("_")
                if safe_name:
                    filename = f"{style_id}_{safe_name}.png"
                else:
                    # fallback 到时间戳
                    from datetime import datetime
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{style_id}_{ts}.png"
            else:
                # fallback 到时间戳
                from datetime import datetime
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{style_id}_{ts}.png"

            return d / filename

    # fallback
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(f"/tmp/t2i-{style_id}-{ts}.png")


# ── 主流程 ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="文生图工具（Gemini）")
    parser.add_argument("--input", "-i", help="Markdown 文件路径")
    parser.add_argument("--content", "-c", help="直接输入要可视化的文本（原文截段）")
    parser.add_argument("--prompt", "-p", help="Claude 生成的创意指令（优先级最高，覆盖 --content/--input）")
    parser.add_argument("--style", "-s", default="infographic",
                        help="风格 ID（默认: infographic）")
    parser.add_argument("--output", "-o", help="输出路径或目录")
    parser.add_argument("--model", "-m", choices=list(MODELS.keys()),
                        default=DEFAULT_MODEL,
                        help=f"模型（默认: {DEFAULT_MODEL}）: "
                             + " | ".join(f"{k}={v}" for k, v in MODELS.items()))
    parser.add_argument("--list-styles", action="store_true",
                        help="列出所有可用风格")
    args = parser.parse_args()

    # 列出风格
    if args.list_styles:
        styles = list_styles()
        if not styles:
            print("（暂无可用风格）")
            return
        print(f"{'ID':<20} {'名称':<12} {'来源':<8} 描述")
        print("-" * 80)
        for s in styles:
            print(f"{s['id']:<20} {s['name']:<12} {s['source']:<8} {s['description']}")
        return

    # 检查 API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("错误：未找到 GEMINI_API_KEY 环境变量", file=sys.stderr)
        print("请在 claudian 设置中配置 GEMINI_API_KEY", file=sys.stderr)
        sys.exit(1)

    # 加载风格
    style = load_style(args.style)
    system_prompt = style.get("system", "")
    style_name = style.get("name", args.style)

    # 提取内容
    # --prompt 优先：Claude 生成的创意指令直接作为内容部分，跳过原文提取
    if args.prompt:
        content = args.prompt.strip()
    else:
        content = extract_content(args)

    # 组合完整 prompt：视觉语法（style.system）+ 内容指令
    full_prompt = f"{system_prompt}\n\n{'─' * 40}\nVisual direction:\n{'─' * 40}\n\n{content}"

    # 生成
    print(f"生成中... 风格: {style_name}", file=sys.stderr)
    image_bytes = generate_image(full_prompt, args.model, api_key)

    # 保存
    out_path = resolve_output(args, args.style)
    out_path.write_bytes(image_bytes)

    # 输出路径到 stdout（供 skill 读取）
    print(str(out_path))
    print(f"已保存: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
