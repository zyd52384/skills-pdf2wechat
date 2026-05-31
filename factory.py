#!/usr/bin/env python3
"""
factory.py - PDF转公众号内容工厂

批量处理 E:\pdftowechat 目录下的 PDF 文件：
1. MD5去重（processed.json）
2. 每天最多5篇限制
3. 失败跳过继续
4. 自动调用 pdf-to-wechat 流程

用法：
    python factory.py [--dry-run] [--limit N]

参数：
    --dry-run     - 只扫描，不执行处理
    --limit N     - 强制限制处理数量（默认5）
    --force       - 忽略5篇限制，全量处理
"""

import os
import json
import hashlib
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta


# ─────────────────── 配置 ───────────────────

CONFIG = {
    "source_dir": "E:\\pdftowechat",       # PDF 源文件目录
    "temp_dir": "C:\\temp\\wechat_article", # 中转 ASCII 路径
    "data_dir": "C:\\Users\\zyd523\\.workbuddy\\data\\pdf_wechat", # 数据存储
    "processed_json": "processed.json",      # MD5去重记录
    "published_json": "published_articles.json", # 已发布文章索引
    "daily_limit": 5,                        # 每日发布限制
    "pdf_file_extensions": [".pdf", ".PDF"],
    "months_filter": 3,                      # 延伸阅读3个月过滤
    "original_url": "https://www.203060.com", # 原文链接（默认203060.com）
}

# ─────────────────── 工具函数 ───────────────────

def load_processed_files():
    """加载已处理文件 MD5 记录。"""
    path = os.path.join(CONFIG["data_dir"], CONFIG["processed_json"])
    if not os.path.exists(path):
        return {}
    
    os.makedirs(CONFIG["data_dir"], exist_ok=True)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_processed_files(processed):
    """保存 MD5 去重记录。"""
    path = os.path.join(CONFIG["data_dir"], CONFIG["processed_json"])
    os.makedirs(CONFIG["data_dir"], exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)


def compute_file_md5(filepath):
    """计算文件的 MD5 值。"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_today_count():
    """获取今日已处理文件数量。"""
    if not os.path.exists(CONFIG["data_dir"]):
        return 0
    
    today = datetime.now().strftime("%Y-%m-%d")
    count_file = os.path.join(CONFIG["data_dir"], f"processed_{today}.json")
    
    if not os.path.exists(count_file):
        return 0
    
    try:
        with open(count_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return len(data.get("processed", []))
    except:
        return 0


def should_process_file(filepath, processed, daily_count, force_limit=False):
    """判断是否应该处理该文件。"""
    if force_limit:
        return True
    
    # MD5 去重
    file_md5 = compute_file_md5(filepath)
    if file_md5 in processed:
        print(f"⚠️ 跳过重复文件: {os.path.basename(filepath)}")
        return False
    
    # 日限流
    if daily_count >= CONFIG["daily_limit"]:
        print(f"⚠️ 今日已处理 {daily_count} 篇，达到限制（{CONFIG['daily_limit']}）")
        print("✅ 今日任务已完成，明日继续")
        return False
    
    return True


def copy_to_ascii_path(filepath):
    """复制文件到 ASCII 路径（Windows 中文路径兼容）。"""
    os.makedirs(CONFIG["temp_dir"], exist_ok=True)
    
    # 生成临时文件名
    timestamp = int(datetime.now().timestamp())
    temp_filename = f"temp_{timestamp}_{os.path.basename(filepath)}"
    temp_path = os.path.join(CONFIG["temp_dir"], temp_filename)
    
    try:
        shutil.copy2(filepath, temp_path)
        print(f"✓ 已复制到 ASCII 路径: {temp_path}")
        return temp_path
    except Exception as e:
        raise RuntimeError(f"复制失败: {e}")


def scan_pdf_files():
    """扫描源目录获取所有 PDF 文件。"""
    if not os.path.exists(CONFIG["source_dir"]):
        print(f"❌ 源目录不存在: {CONFIG['source_dir']}")
        return []
    
    pdf_files = []
    for root, dirs, files in os.walk(CONFIG["source_dir"]):
        for file in files:
            if any(file.lower().endswith(ext) for ext in CONFIG["pdf_file_extensions"]):
                full_path = os.path.join(root, file)
                pdf_files.append(full_path)
    
    pdf_files.sort()  # 按路径排序
    return pdf_files


# ─────────────────── 核心处理流程 ───────────────────

def process_single_pdf(filepath, processed, published_articles):
    """处理单个 PDF 文件。"""
    print(f"\n🔄 开始处理: {os.path.basename(filepath)}")
    
    try:
        # 1. 检查是否为纯图片 PDF（需要 OCR）
        is_image_pdf = check_is_image_pdf(filepath)
        print(f"📄 PDF 类型: {'纯图片 (需OCR)' if is_image_pdf else '文本PDF'}")
        
        # 2. 复制到 ASCII 路径
        ascii_path = copy_to_ascii_path(filepath)
        
        # 3. 调用 pdf-to-wechat 处理流程
        result = call_pdf_wechat_skill(ascii_path, is_image_pdf, published_articles)
        
        # 4. 记录处理结果
        md5 = compute_file_md5(filepath)
        processed[md5] = {
            "filename": os.path.basename(filepath),
            "original_path": filepath,
            "temp_path": ascii_path,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": result,
            "is_image_pdf": is_image_pdf
        }
        
        print(f"✅ 处理完成: {result.get('title', '未知标题')}")
        return result
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return {"status": "failed", "error": str(e)}


def check_is_image_pdf(filepath):
    """快速判断是否为纯图片 PDF。"""
    try:
        import fitz  # pymupdf
        
        doc = fitz.open(filepath)
        total_text_length = 0
        
        for page in doc:
            text = page.get_text()
            total_text_length += len(text.strip())
        
        doc.close()
        
        if total_text_length < 100:  # 基本没有文字
            return True
        return False
        
    except Exception as e:
        print(f"❌ PDF 类型检测失败: {e}")
        return False  # 假设文本PDF


def call_pdf_wechat_skill(pdf_path, is_image_pdf, published_articles):
    """调用 pdf-to-wechat 的处理流程。
    注意：本 skill 的核心流程由 AI agent 按 SKILL.md 执行。
    factory.py 是批处理辅助脚本，不替代 AI 的写作和发布决策。
    当前函数返回素材准备状态，实际写作由 AI 完成。
    """
    pdf_basename = os.path.basename(pdf_path)
    print("  📋 准备素材...")
    # 模拟生成配置文件信息
    config_data = {
        "article_md": "article.md",
        "screenshot_dir": "screenshots/",
        "title": f"生成文章标题 - {pdf_basename}",
        "style": "tech-blue",
        "source_filename": pdf_basename,
        "cover_page": 1,
        "image_pages": [1, 3, 5],
        "related_reading": True,
        "data_dir": CONFIG["data_dir"],
        "original_url": CONFIG["original_url"],
    }
    return {
        "status": "ok",
        "title": config_data["title"],
        "media_id": f"mock_{int(time.time())}",
        "image_count": 3,
        "related_reading_count": 2,
        "is_image_pdf": is_image_pdf
    }


def main():
    import argparse


    parser = argparse.ArgumentParser(description="PDF转公众号内容工厂")
    parser.add_argument("--dry-run", action="store_true", help="仅扫描，不执行处理")
    parser.add_argument("--limit", type=int, help="强制处理数量限制")
    parser.add_argument("--force", action="store_true", help="忽略5篇限制，全量处理")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 PDF转公众号内容工厂")
    print("=" * 60)
    
    # 创建数据目录
    os.makedirs(CONFIG["data_dir"], exist_ok=True)
    
    # 加载状态
    processed = load_processed_files()
    published_articles = []
    
    # 扫描源文件
    pdf_files = scan_pdf_files()
    if not pdf_files:
        print(f"❌ 在 {CONFIG['source_dir']} 中未找到 PDF 文件")
        return
    
    print(f"📁 扫描到 {len(pdf_files)} 个 PDF 文件")
    print(f"📝 已处理文件数: {len(processed)}")
    
    # 计算今日已处理数量
    daily_count = get_today_count()
    print(f"📅 今日已处理: {daily_count} 篇")
    
    # 有效限制
    effective_limit = args.limit if args.limit else CONFIG["daily_limit"]
    if args.force:
        effective_limit = float('inf')
    
    available_quota = max(0, effective_limit - daily_count)
    print(f"🎯 今日可用额度: {available_quota} 篇")
    
    # 扫描模式
    if args.dry_run:
        print("\n🔍 扫描模式 - 发现可处理文件:")
        processed_count = 0
        for filepath in pdf_files:
            md5 = compute_file_md5(filepath)
            if md5 not in processed:
                processed_count += 1
                print(f"  📄 {os.path.basename(filepath)} ({os.path.dirname(filepath)})")
        
        print(f"\n💡 可处理文件: {processed_count} 个")
        print(f"✅ 今日处理量建议: {min(available_quota, processed_count)}")
        return
    
    # 处理模式
    print(f"\n🚀 开始处理模式 (限额: {effective_limit})")
    
    success_count = 0
    failed_count = 0
    
    for filepath in pdf_files:
        if daily_count >= effective_limit and not args.force:
            break
        
        # 检查是否应该处理
        if not should_process_file(filepath, processed, daily_count, args.force):
            continue
        
        # 处理文件
        result = process_single_pdf(filepath, processed, published_articles)
        
        if result.get("status") == "ok":
            success_count += 1
            daily_count += 1
        else:
            failed_count += 1
        
        # 短暂休止
        time.sleep(2)
    
    # 保存状态
    save_processed_files(processed)
    
    # 保存今日处理记录
    today = datetime.now().strftime("%Y-%m-%d")
    today_file = os.path.join(CONFIG["data_dir"], f"processed_{today}.json")
    
    today_data = {
        "date": today,
        "total_limit": effective_limit,
        "processed": success_count,
        "failed": failed_count,
        "processed_files": [
            info for md5, info in processed.items()
            if info.get("processed_at", "").startswith(today)
        ]
    }
    
    with open(today_file, "w", encoding="utf-8") as f:
        json.dump(today_data, f, ensure_ascii=False, indent=2)
    
    # 报告
    print("\n" + "=" * 60)
    print("📊 处理报告")
    print("=" * 60)
    print(f"📈 成功: {success_count} 篇")
    print(f"❌ 失败: {failed_count} 篇")
    print(f"📅 今日总数: {daily_count} 篇")
    print(f"📁 总去重数: {len(processed)}")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not args.force and daily_count >= CONFIG["daily_limit"]:
        print("\n💡 已达到每日限制，明天继续!")


if __name__ == "__main__":
    main()