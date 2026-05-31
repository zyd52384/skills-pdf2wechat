#!/usr/bin/env python3
"""
统一发布脚本：读取文章 Markdown → 上传图片 → 构建 HTML → 发布微信草稿

v1.8.0 更新：
- 新增发布前 QC 校验（4项）：标题乱码/CTA合规/原文链接/图片齐全
- 校验失败抛 RuntimeError 并列出具体失败项
- 前置 [IMG_N:] 占位符校验整合进 QC 4 项

v1.7.0 更新：
- 新增封面/内嵌图片上传逻辑
- IMG 占位符检测（缺失则报错）

v1.6.0 更新：
- 发布后自动写入 published_articles.json（含 publish_date）
- 支持生成"延伸阅读"板块（3个月内已发布文章，带链接）
- config 新增 related_reading 和 data_dir 参数

用法：
    python publish_draft.py <config.json>

config.json 格式：
{
    "article_md": "C:/path/to/article.md",
    "screenshot_dir": "C:/path/to/screenshots/",
    "title": "文章标题",
    "style": "tech-blue",
    "source_filename": "原始PDF文件名.pdf",
    "cover_page": 1,
    "image_pages": [1, 4, 7, 9, 12],
    "related_reading": true,           // 是否生成延伸阅读，默认 true
    "data_dir": "C:/path/to/data/",    // published_articles.json 所在目录
    "original_url": "https://...",     // 原文链接（可选），显示在文章底部
    "appid": "wx...",                  // 可选，优先读 wechat_config.json
    "appsecret": "..."                 // 可选，优先读 wechat_config.json
}
"""

import json
import os
import random
import re
import sys
import time
import requests
from datetime import datetime, timedelta


FOOTER_GIF_URL = "http://mmbiz.qpic.cn/sz_mmbiz_gif/CWmCjpOpZNDoCOooOHwQbJcqmQ8ckZricJcK0w02StFxZ1HXCr7C9lQ6F4qiawAfKWn7w1q3Lr3H4GOIQtotkY7vtLWE4Dw7mM8cHVRmiccW6Y/0?from=appmsg"
"""文章末尾底部 GIF（公众号引流），上传自 57072b650ce5b0943cf1dbb43800a06b.gif，靠左显示。"""


# ─────────────────── 工具函数 ───────────────────

def load_wechat_config(appid=None, appsecret=None):
    """读取微信凭证，优先使用传入参数，其次读 config 文件。"""
    if appid and appsecret:
        return appid, appsecret
    config_paths = [
        os.path.join(os.path.expanduser("~"), ".workbuddy", "wechat_config.json"),
        "wechat_config.json",
    ]
    for p in config_paths:
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                c = json.load(f)
            return c.get("appid"), c.get("appsecret")
    raise RuntimeError("No wechat credentials found. Provide appid/appsecret or create ~/.workbuddy/wechat_config.json")


def get_access_token(appid, appsecret):
    """获取微信公众号 access_token。"""
    url = "https://api.weixin.qq.com/cgi-bin/token"
    r = requests.get(url, params={"grant_type": "client_credential", "appid": appid, "secret": appsecret}, timeout=15)
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"Failed to get access_token: {data}")
    return data["access_token"]


def upload_cover(token, image_path):
    """上传封面图为永久素材，返回 media_id。"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(image_path, "rb") as f:
        r = requests.post(url, files={"media": ("cover.png", f, "image/png")}, timeout=30)
    data = r.json()
    if "media_id" not in data:
        raise RuntimeError(f"Cover upload failed: {data}")
    return data["media_id"]


def upload_inline_images(token, screenshot_dir, image_pages):
    """上传文章内嵌图片，返回 {N: url} 映射。"""
    urls = {}
    for i, pg in enumerate(image_pages, 1):
        path = os.path.join(screenshot_dir, f"page_{pg:03d}.png")
        if not os.path.exists(path):
            print(f"WARN: {path} not found, skipping IMG_{i}")
            continue
        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
        with open(path, "rb") as f:
            r = requests.post(url, files={"media": (f"img{i}.png", f, "image/png")}, timeout=30)
        resp = r.json()
        img_url = resp.get("url", "")
        if not img_url:
            raise RuntimeError(f"Image upload failed (IMG_{i}, page_{pg}): {resp}")
        urls[i] = img_url
        print(f"IMG_{i} (page {pg}): OK")
    return urls


def convert_bold(text):
    """Markdown **bold** → HTML <strong>。"""
    return re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#1890ff;">\1</strong>', text)


def img_html(n, desc, url):
    """生成单张图片 HTML 块（单行输出，避免嵌套陷阱）。"""
    return (
        f'<p style="text-align:center;margin:24px 0;">'
        f'<img src="{url}" style="max-width:100%;display:block;margin:0 auto;" />'
        f'<span style="color:#7f8c8d;font-size:13px;display:block;margin-top:8px;">▲ {desc}</span>'
        f'</p>'
    )


# ─────────────────── 发布追踪 ───────────────────

def load_published_articles(data_dir):
    """加载已发布文章索引，不存在则返回空列表。"""
    path = os.path.join(data_dir, "published_articles.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_published_articles(data_dir, articles):
    """保存文章索引到 published_articles.json。"""
    path = os.path.join(data_dir, "published_articles.json")
    os.makedirs(data_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def record_published(data_dir, title, url, media_id):
    """记录一篇新发布的文章。"""
    articles = load_published_articles(data_dir)
    articles.append({
        "title": title,
        "url": url,
        "media_id": media_id,
        "publish_date": datetime.now().strftime("%Y-%m-%d"),
    })
    save_published_articles(data_dir, articles)
    print(f"✓ 已记录到 published_articles.json (共 {len(articles)} 篇)")
    return articles


def get_recent_articles(articles, months=3):
    """过滤出最近 N 个月内发布的文章。"""
    cutoff = datetime.now() - timedelta(days=months * 30)
    recent = []
    for a in articles:
        try:
            d = datetime.strptime(a.get("publish_date", ""), "%Y-%m-%d")
            if d >= cutoff:
                recent.append(a)
        except ValueError:
            continue
    return recent


def fetch_material_articles(token, count=50):
    """从微信公众号素材库拉取已发布文章（含发布时间）。"""
    all_articles = []
    offset = 0
    batch_size = min(count, 10)

    while len(all_articles) < count:
        resp = requests.post(
            'https://api.weixin.qq.com/cgi-bin/material/batchget_material',
            params={'access_token': token},
            json={'type': 'news', 'offset': offset, 'count': batch_size},
            timeout=30
        )
        data = resp.json()
        if data.get('errcode', 0) != 0:
            break

        for item in data.get('item', []):
            news_items = item.get('content', {}).get('news_item', [])
            update_time = item.get('update_time', 0)
            for ni in news_items:
                url = ni.get('url', '')
                if not url:
                    continue
                title = _decode_title(ni.get('title', ''))
                all_articles.append({
                    'title': title,
                    'url': url,
                    'update_time': update_time,
                })
                if len(all_articles) >= count:
                    break
            if len(all_articles) >= count:
                break

        offset += len(data.get('item', []))
        if offset >= data.get('total_count', 0):
            break

    return all_articles


def _decode_title(title):
    """Fix Latin-1 mojibake → UTF-8 for material API titles."""
    try:
        return title.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return title


# ─────────────────── 延伸阅读 ───────────────────

def build_related_reading_html(articles, max_count=5):
    """生成延伸阅读 HTML 块，最多显示 max_count 篇。"""
    if not articles:
        return ""

    display = articles[:max_count]
    items = []
    for a in display:
        title = a.get("title", "").strip()
        url = a.get("url", "")
        if not title or not url:
            continue
        items.append(
            f'<li style="margin:10px 0;list-style-type:disc;">'
            f'<a href="{url}" style="color:#1890ff;text-decoration:none;'
            f'font-size:14px;line-height:1.6;">{title}</a>'
            f'</li>'
        )

    if not items:
        return ""

    header = (
        '<p style="margin-top:40px;padding-top:16px;border-top:1px solid #e8edf2;'
        'font-size:16px;font-weight:700;color:#1a1a2e;">延伸阅读</p>'
    )

    return header + '<ul style="padding-left:1.2em;margin:8px 0;">' + ''.join(items) + '</ul>'


# ─────────────────── 知识拓展（txt 文件方案） ───────────────────

def load_knowledge_links(txt_path):
    """从 txt 文件读取文章标题和链接，每行格式：标题|url"""
    if not txt_path or not os.path.exists(txt_path):
        return []
    articles = []
    with open(txt_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('|', 1)
            if len(parts) == 2:
                title, url = parts[0].strip(), parts[1].strip()
                if title and url:
                    articles.append({"title": title, "url": url})
    return articles


def build_knowledge_extension_html(knowledge_file="", current_title="", max_count=8):
    """从 txt 文件随机选5-8条文章链接，返回HTML块。"""
    all_articles = load_knowledge_links(knowledge_file)
    if not all_articles:
        print(f"⚠ 知识拓展: 链接文件为空或不存在，跳过")
        return ""

    # 排除当前文章
    candidates = [a for a in all_articles
                  if not current_title or a.get("title", "") != current_title]
    if not candidates:
        print("⚠ 知识拓展: 排除当前文章后无剩余条目")
        return ""

    # 随机选 5-8 篇
    pick_count = min(random.randint(5, max_count), len(candidates))
    picked = random.sample(candidates, pick_count)

    items = []
    for a in picked:
        title = a.get("title", "").strip()
        url = a.get("url", "").strip()
        if not title or not url:
            continue
        items.append(
            f'<li style="margin:8px 0;list-style-type:disc;">'
            f'<a href="{url}" style="{s["link"]}">{title}</a>'
            f'</li>'
        )

    if not items:
        return ""

    header = (
        f'<p style="margin-top:36px;padding-top:14px;{s["hr"]}'
        f'font-size:16px;font-weight:700;color:{s["h2"].split("color:")[1].split(";")[0] if "color:" in s["h2"] else "#1a1a2e"};">知识拓展</p>'
    )
    note = (
        '<p style="color:#b0b0b0;font-size:12px;margin:4px 0 8px 0;">'
        '点击标题查看相关文章</p>'
    )
    html = header + note + '<ul style="padding-left:1.2em;margin:8px 0;">' + ''.join(items) + '</ul>'
    print(f"✓ 知识拓展: {len(candidates)} 条可用，随机选 {pick_count} 篇")
    return html


# ─────────────────── HTML 构建 ───────────────────

# 公众号排版样式定义
STYLES = {
    "green-business": {  # 绿色商务风
        "section": "font-size:16px;color:#333;line-height:1.85;letter-spacing:0.5px;padding:0 8px;max-width:100%;word-wrap:break-word;",
        "h1": "font-size:22px;font-weight:700;text-align:center;margin:20px 0 28px 0;color:#111;line-height:1.5;",
        "h2": "font-size:20px;font-weight:700;color:#222;margin:32px 0 16px 0;padding-left:10px;border-left:3px solid #07c160;",
        "bold": "color:#333;",
        "hr": "border:none;border-top:1px solid #eee;margin:24px 0;",
        "p": "margin:10px 0;text-indent:2em;color:#333;",
        "blockquote": "margin:12px 0;padding:8px 14px;color:#666;font-size:15px;font-style:italic;",
        "img_caption": "color:#888;font-size:14px;display:block;margin-top:8px;",
        "link": "color:#07c160;text-decoration:none;font-size:14px;line-height:1.6;",
    },
    "tech-blue": {  # 科技蓝（默认）
        "section": "font-size:15px;color:#2c3e50;line-height:1.9;letter-spacing:0.3px;padding:0 8px;max-width:100%;word-wrap:break-word;",
        "h1": "font-size:22px;font-weight:700;text-align:center;margin:20px 0 28px 0;color:#1a1a2e;line-height:1.5;",
        "h2": "font-size:19px;font-weight:700;color:#1a1a2e;margin:32px 0 14px 0;padding-left:10px;border-left:3px solid #1890ff;",
        "bold": "color:#1890ff;",
        "hr": "border:none;border-top:1px solid #e8edf2;margin:24px 0;",
        "p": "margin:10px 0;text-indent:2em;color:#2c3e50;",
        "blockquote": "margin:12px 0;padding:8px 12px;border-left:2px dashed #1890ff;color:#5a6c7d;font-size:14px;",
        "img_caption": "color:#7f8c8d;font-size:13px;display:block;margin-top:8px;",
        "link": "color:#1890ff;text-decoration:none;font-size:14px;line-height:1.6;",
    },
    "warm-orange": {  # 暖橙人文风
        "section": "font-size:16px;color:#4a3728;line-height:1.9;letter-spacing:0.4px;padding:0 8px;max-width:100%;word-wrap:break-word;",
        "h1": "font-size:23px;font-weight:700;text-align:center;margin:20px 0 28px 0;color:#2d1b00;line-height:1.5;",
        "h2": "font-size:19px;font-weight:700;color:#2d1b00;margin:32px 0 14px 0;padding-bottom:6px;border-bottom:2px solid #e67e22;",
        "bold": "color:#d35400;",
        "hr": "border:none;border-top:1px solid #f0e6d3;margin:24px 0;",
        "p": "margin:10px 0;text-indent:2em;color:#4a3728;",
        "blockquote": "margin:12px 0;padding:10px 14px;background:#fef9e7;border-radius:4px;color:#8b6914;font-size:15px;",
        "img_caption": "color:#b8956a;font-size:13px;display:block;margin-top:8px;",
        "link": "color:#d35400;text-decoration:none;font-size:14px;line-height:1.6;",
    },
    "minimal-bw": {  # 极简黑白风
        "section": "font-size:15px;color:#333;line-height:2.0;letter-spacing:0.3px;padding:0 4px;max-width:100%;word-wrap:break-word;",
        "h1": "font-size:22px;font-weight:700;margin:24px 0 32px 0;color:#000;line-height:1.6;text-align:center;",
        "h2": "font-size:19px;font-weight:700;color:#000;margin:36px 0 12px 0;",
        "bold": "color:#000;",
        "hr": "border:none;border-top:1px solid #ddd;margin:28px 0;",
        "p": "margin:14px 0;color:#333;",
        "blockquote": "margin:14px 0;color:#666;font-size:14px;",
        "img_caption": "color:#999;font-size:12px;display:block;margin-top:6px;",
        "link": "color:#333;text-decoration:underline;font-size:14px;line-height:1.6;",
    },
    "deep-gray": {  # 深空灰 | 沉稳高级灰，适合深度技术分析
        "section": "font-size:15px;color:#3d3d3d;line-height:1.9;letter-spacing:0.2px;padding:0 8px;max-width:100%;word-wrap:break-word;",
        "h1": "font-size:21px;font-weight:700;text-align:center;margin:24px 0 30px 0;color:#1a1a1a;line-height:1.5;",
        "h2": "font-size:18px;font-weight:600;color:#1a1a1a;margin:30px 0 12px 0;padding-left:10px;border-left:3px solid #6b7b8d;",
        "bold": "color:#1a1a1a;",
        "hr": "border:none;border-top:1px solid #d0d7de;margin:24px 0;",
        "p": "margin:10px 0;text-indent:2em;color:#3d3d3d;",
        "blockquote": "margin:12px 0;padding:10px 14px;background:#f6f8fa;border-left:3px solid #6b7b8d;color:#57606a;font-size:14px;",
        "img_caption": "color:#8b949e;font-size:13px;display:block;margin-top:8px;",
        "link": "color:#0969da;text-decoration:none;font-size:14px;line-height:1.6;",
    },
    "rose-gold": {  # 玫瑰金 | 柔和暖色，适合科普传播
        "section": "font-size:16px;color:#5c3d3d;line-height:1.9;letter-spacing:0.4px;padding:0 8px;max-width:100%;word-wrap:break-word;",
        "h1": "font-size:22px;font-weight:700;text-align:center;margin:20px 0 28px 0;color:#4a1a2e;line-height:1.5;",
        "h2": "font-size:19px;font-weight:700;color:#4a1a2e;margin:32px 0 14px 0;padding-left:10px;border-left:3px solid #e8a0b4;",
        "bold": "color:#c44569;",
        "hr": "border:none;border-top:1px solid #f0d9e0;margin:24px 0;",
        "p": "margin:10px 0;text-indent:2em;color:#5c3d3d;",
        "blockquote": "margin:12px 0;padding:10px 14px;background:#fdf3f6;border-left:3px solid #e8a0b4;border-radius:4px;color:#8b5a6b;font-size:15px;",
        "img_caption": "color:#b08a9a;font-size:13px;display:block;margin-top:8px;",
        "link": "color:#c44569;text-decoration:none;font-size:14px;line-height:1.6;",
    },
    "cypress-green": {  # 翠柏绿 | 自然绿调，适合能源环境主题
        "section": "font-size:15px;color:#2d3e2d;line-height:1.85;letter-spacing:0.3px;padding:0 8px;max-width:100%;word-wrap:break-word;",
        "h1": "font-size:22px;font-weight:700;text-align:center;margin:20px 0 28px 0;color:#1a3a1a;line-height:1.5;",
        "h2": "font-size:19px;font-weight:700;color:#1a3a1a;margin:32px 0 14px 0;padding-left:10px;border-left:3px solid #2d8a4e;",
        "bold": "color:#2d8a4e;",
        "hr": "border:none;border-top:1px solid #c8e6c9;margin:24px 0;",
        "p": "margin:10px 0;text-indent:2em;color:#2d3e2d;",
        "blockquote": "margin:12px 0;padding:10px 14px;background:#f1f8e9;border-left:3px solid #2d8a4e;color:#4a6b4a;font-size:14px;",
        "img_caption": "color:#6b9b6b;font-size:13px;display:block;margin-top:8px;",
        "link": "color:#2d8a4e;text-decoration:none;font-size:14px;line-height:1.6;",
    },
}

DEFAULT_STYLE = "tech-blue"


def get_style(s):
    """获取样式配置，不存在时返回默认。"""
    return STYLES.get(s, STYLES[DEFAULT_STYLE])

def build_html(md_path, img_urls, title, source_filename, style="tech-blue",
               related_html="", knowledge_html="", footer_gif=True):
    """将 Markdown 文章转换为微信公众号兼容的 HTML。"""
    s = get_style(style)

    with open(md_path, encoding="utf-8") as f:
        md = f.read()
    md = re.sub(r'^---.*?---\s*', '', md, flags=re.DOTALL)

    lines = md.split('\n')
    html_parts = []

    for line in lines:
        ln = line.strip()
        if not ln:
            continue

        # IMG 占位符
        img_m = re.match(r'\[IMG_(\d+):\s*(.+?)\]', ln)
        if img_m:
            n = int(img_m.group(1))
            url = img_urls.get(n, img_urls.get(5, ""))
            html_parts.append(img_html(n, img_m.group(2), url))
            continue

        # H1
        if ln.startswith('# ') and not ln.startswith('## '):
            t = convert_bold(ln[2:])
            html_parts.append(f'<h1 style="{s["h1"]}">{t}</h1>')
            continue

        # H2
        if ln.startswith('## ') and not ln.startswith('### '):
            t = convert_bold(ln[3:])
            html_parts.append(f'<h2 style="{s["h2"]}">{t}</h2>')
            continue

        # H3
        if ln.startswith('### '):
            t = convert_bold(ln[4:])
            html_parts.append(f'<h3 style="font-size:16px;font-weight:600;color:{s["bold"].split(":")[1].strip(";")};margin:24px 0 10px 0;">{t}</h3>')
            continue

        # 分割线
        if ln == '---':
            html_parts.append(f'<hr style="{s["hr"]}" />')
            continue

        # 序号列表
        nm = re.match(r'^(\d+)\.\s+(.+)$', ln)
        if nm:
            c = convert_bold(nm.group(2))
            html_parts.append(
                f'<p style="margin:8px 0;padding-left:2em;">'
                f'<strong style="{s["bold"]}">{nm.group(1)}.</strong> {c}</p>'
            )
            continue

        # 普通段落
        t = convert_bold(ln)
        html_parts.append(f'<p style="{s["p"]}">{t}</p>')

    # 来源文件备注
    if source_filename:
        hr_style = s["hr"].replace("border:none;", "")
        remark = (
            f'<p style="margin-top:24px;padding-top:16px;{hr_style}'
            f'color:#b0b0b0;font-size:12px;text-align:right;">'
            f'来源文件：{source_filename}</p>'
        )
        html_parts.append(remark)

    # 延伸阅读
    if related_html:
        html_parts.append(related_html)

    # 知识拓展（随机30天内已发布文章，在 GIF 上方）
    if knowledge_html:
        html_parts.append(knowledge_html)

    # 底部 GIF（公众号引流，靠左显示）
    if footer_gif:
        html_parts.append(
            f'<p style="text-align:left;margin:20px 0 0 0;">'
            f'<img src="{FOOTER_GIF_URL}" style="max-width:100%;display:block;" />'
            f'</p>'
        )

    content_html = (
        f'<section style="{s["section"]}">\n'
        + '\n'.join(html_parts)
        + '\n</section>'
    )

    # 标题截断 ≤64 字符
    safe_title = title
    if len(title) > 64:
        safe_title = title[:64]

    return safe_title, content_html


def post_draft(token, title, content_html, cover_media_id, original_url=""):
    """发布草稿到微信公众号，返回 media_id。"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

    article = {
        "title": title,
        "content": content_html,
        "thumb_media_id": cover_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0
    }

    if original_url:
        article["content_source_url"] = original_url

    payload = {"articles": [article]}

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    r = requests.post(url, data=body,
                      headers={"Content-Type": "application/json; charset=utf-8"},
                      timeout=60)
    resp = r.json()
    if "media_id" not in resp:
        raise RuntimeError(f"Draft post failed: {resp}")
    return resp["media_id"]


def verify_draft(token, media_id):
    """验证草稿标题是否正确（修复 Latin-1 → UTF-8）。"""
    url = "https://api.weixin.qq.com/cgi-bin/draft/batchget"
    body = json.dumps({"offset": 0, "count": 3, "no_content": 1}, ensure_ascii=False).encode("utf-8")
    r = requests.post(url, params={"access_token": token}, data=body,
                      headers={"Content-Type": "application/json; charset=utf-8"}, timeout=10)
    data = r.json()
    for item in data.get("item", []):
        for art in item.get("content", {}).get("news_item", []):
            raw = art.get("title", "")
            try:
                fixed = raw.encode("latin-1").decode("utf-8")
            except (UnicodeDecodeError, UnicodeEncodeError):
                fixed = raw
            if art.get("media_id") == media_id:
                return fixed
    return None


# ─────────────────── 主流程 ───────────────────

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: publish_draft.py <config.json>"}, ensure_ascii=False))
        sys.exit(1)

    config_path = sys.argv[1]
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    # 必需字段
    article_md = cfg["article_md"]
    screenshot_dir = cfg["screenshot_dir"]
    title = cfg["title"]
    image_pages = cfg.get("image_pages", [])
    cover_page = cfg.get("cover_page", image_pages[0] if image_pages else 1)
    style = cfg.get("style", "tech-blue")
    source_filename = cfg.get("source_filename", "")
    related_reading_enabled = cfg.get("related_reading", True)
    data_dir = cfg.get("data_dir", "")
    original_url = cfg.get("original_url", "")

    # 微信凭证
    appid, appsecret = load_wechat_config(
        cfg.get("appid"),
        cfg.get("appsecret")
    )

    print(f"文章: {os.path.basename(article_md)}")
    print(f"标题: {title}")
    print(f"配图: {len(image_pages)} 张, 封面: page_{cover_page}")
    print()

    # 1. 获取 token
    token = get_access_token(appid, appsecret)
    print("✓ access_token")

    # 2. 上传封面
    cover_path = os.path.join(screenshot_dir, f"page_{cover_page:03d}.png")
    cover_media_id = upload_cover(token, cover_path)
    print(f"✓ 封面 media_id: {cover_media_id}")

    # 3. 发布前质量检查（QC 清单）
    with open(article_md, encoding="utf-8") as f:
        md_content = f.read()
    md_img_placeholders = re.findall(r'\[IMG_(\d+):', md_content)

    qc_errors = []

    # QC 1: 文章标题不能有乱码
    # 检查不可打印字符
    for ch in title:
        if ord(ch) < 32 and ch not in '\n\r\t':
            qc_errors.append(f"标题包含不可打印字符: {repr(title)}")
            break
    # 检查是否有 \\uXXXX 字面量残留（json dumps 未解码的证据）
    if '\\u' in title:
        qc_errors.append(f"标题含 \\uXXXX 转义序列（ASCII 编码残留）: {repr(title)}")
    # 检查是否有 Replacement Character
    if '\ufffd' in title:
        qc_errors.append(f"标题含 Unicode 替换字符 U+FFFD（编码损坏）")
    if any(ord(ch) > 0xFFFF for ch in title):
        qc_errors.append(f"标题含超出 BMP 的字符，微信 API 可能不支持")

    # QC 2: 文章尾部 CTA 段落检查（不检查网址/阅读原文——它们不在正文中）
    tail_lines = [l.strip() for l in md_content.split('\n') if l.strip()]
    tail_block = '\n'.join(tail_lines[-min(15, len(tail_lines)):])
    # CTA 不能含诱导性语言（违反公众号规范）
    forbidden_cta = ['转发', '分享到朋友圈', '必须转', '不转不是', '扩散']
    for kw in forbidden_cta:
        if kw in tail_block:
            qc_errors.append(f"CTA 含违规诱导词「{kw}」，违反公众号运营规范")
            break
    # 检查正文中不应出现网址（网址只填在 original_url 字段）
    url_in_text = re.findall(r'www\.203060\.com|203060\.com', tail_block)
    if url_in_text:
        qc_errors.append("正文中出现了 www.203060.com，要求只填在 original_url 字段，不在正文中出现")

    # QC 2b: 正文中不能出现 ###（H3）及以上标题，只用 #（H1）和 ##（H2）
    h3_matches = re.findall(r'^###+ ', md_content, re.MULTILINE)
    if h3_matches:
        unique = sorted(set(h3_matches))
        qc_errors.append(f"正文中有 {len(unique)} 种 H3+ 标题标记：{unique}。文章只用 # 和 ##，禁止 ###")

    # QC 3: 原文链接必须指向 www.203060.com
    if not original_url:
        qc_errors.append("缺少原文链接 (original_url)，应设为 https://www.203060.com")
    elif '203060.com' not in original_url:
        qc_errors.append(f"原文链接不是 www.203060.com: {original_url}")

    # QC 4: 图片配置齐全
    if not image_pages:
        qc_errors.append("image_pages 为空，文章未配置任何图片")
    else:
        # 4a. 所有截图文件存在
        missing_ss = []
        for pg in image_pages:
            spath = os.path.join(screenshot_dir, f"page_{pg:03d}.png")
            if not os.path.exists(spath):
                missing_ss.append(pg)
        if missing_ss:
            qc_errors.append(f"以下页面截图文件缺失: {missing_ss}")
        # 4b. markdown 中有 IMG 占位符
        if not md_img_placeholders:
            qc_errors.append(
                f"文章无 [IMG_N:desc] 占位符，但 image_pages 配置了 {len(image_pages)} 张图。"
                f"请在 article.md 中需要配图的位置插入占位符（如 [IMG_1: 图1说明]）"
            )
        else:
            print(f"✓ 文章中已有 IMG 占位符: {sorted(set(int(x) for x in md_img_placeholders))}")

    # 汇总 QC 结果
    if qc_errors:
        print("\n❌ 质量检查未通过（共 {} 项）:".format(len(qc_errors)))
        for i, e in enumerate(qc_errors, 1):
            print(f"  {i}. {e}")
        raise RuntimeError(f"发布前质量检查未通过（{len(qc_errors)} 项），请修复后重试")
    print(f"✓ 质量检查全部通过（5/5）")

    # 4. 上传文章内嵌图
    img_urls = {}
    if image_pages:
        img_urls = upload_inline_images(token, screenshot_dir, image_pages)
        print(f"✓ 内嵌图: {len(img_urls)} 张")

    # 5. 延伸阅读（可选）
    related_html = ""
    if related_reading_enabled:
        # 先尝试从本地索引获取
        if data_dir and os.path.exists(data_dir):
            local_articles = load_published_articles(data_dir)
            recent = get_recent_articles(local_articles, months=3)
            if recent:
                related_html = build_related_reading_html(recent)
                print(f"✓ 延伸阅读: 本地索引找到 {len(recent)} 篇（3月内）")

        # 本地没有则从素材库拉
        if not related_html:
            try:
                material_articles = fetch_material_articles(token, count=10)
                three_months_ago = int((datetime.now() - timedelta(days=90)).timestamp())
                recent_mat = [
                    a for a in material_articles
                    if a.get('update_time', 0) >= three_months_ago
                ]
                if recent_mat:
                    related_html = build_related_reading_html(recent_mat)
                    print(f"✓ 延伸阅读: 素材库找到 {len(recent_mat)} 篇（3月内）")
                else:
                    print("⚠ 延伸阅读: 3个月内无已发布文章，跳过")
            except Exception as e:
                print(f"⚠ 延伸阅读获取失败: {e}")

    # 6a. 知识拓展（从 txt 文件读取，随机选5-8篇）
    knowledge_file = cfg.get("knowledge_file", "")
    if not knowledge_file:
        knowledge_file = "E:/pdftowechat/knowledge_links.txt"
    knowledge_html = build_knowledge_extension_html(knowledge_file, current_title=title)

    # 7. 构建 HTML
    safe_title, content_html = build_html(article_md, img_urls, title, source_filename,
                                          style, related_html, knowledge_html)
    print(f"✓ HTML 构建完成 ({len(content_html)} 字符)")

    # 8. 发布草稿
    media_id = post_draft(token, safe_title, content_html, cover_media_id, original_url)
    print(f"✓ 草稿发布成功")
    print(f"  media_id: {media_id}")

    # 9. 验证
    verified_title = verify_draft(token, media_id)
    if verified_title:
        print(f"✓ 标题验证: {verified_title}")

    # 10. 记录到发布索引
    publish_url = ""
    if data_dir:
        local_articles = record_published(data_dir, safe_title, publish_url, media_id)

    result = {
        "status": "ok",
        "media_id": media_id,
        "cover_media_id": cover_media_id,
        "title": safe_title,
        "verified_title": verified_title,
        "image_count": len(img_urls),
        "related_reading_count": related_html.count('<li'),
    }
    print()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
