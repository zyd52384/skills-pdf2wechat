"""
fetch_related_articles.py v1.1.0
拉取公众号素材库中已发布的图文消息，返回标题、URL 和发布时间。
支持按时间范围过滤（默认 3 个月）。

用法：
    python fetch_related_articles.py <appid> <appsecret> [count] [months]

参数：
    count  - 拉取数量，默认 10
    months - 时间过滤（月），默认 3，0 表示不过滤

输出 JSON：
    {
        "articles": [
            {"title": "...", "url": "...", "update_time": 1716508800},
            ...
        ],
        "total": 28
    }
"""
import requests
import json
import sys
import time
from datetime import datetime, timedelta


def decode_title(title):
    """Fix Latin-1 mojibake → UTF-8 for material API titles."""
    try:
        return title.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return title


def get_access_token(appid, appsecret):
    resp = requests.get('https://api.weixin.qq.com/cgi-bin/token', params={
        'grant_type': 'client_credential',
        'appid': appid,
        'secret': appsecret
    })
    data = resp.json()
    if 'access_token' not in data:
        raise RuntimeError(f"Failed to get token: {data}")
    return data['access_token']


def fetch_articles(token, count=10, months=3):
    """Fetch published articles from material library, optionally filtered by time."""
    all_articles = []
    offset = 0
    batch_size = min(count, 10)

    # 时间过滤阈值
    cutoff_timestamp = 0
    if months > 0:
        cutoff_timestamp = int((datetime.now() - timedelta(days=months * 30)).timestamp())

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
            update_time = item.get('update_time', 0)

            # 时间过滤
            if cutoff_timestamp and update_time < cutoff_timestamp:
                continue

            news_items = item.get('content', {}).get('news_item', [])
            for ni in news_items:
                url = ni.get('url', '')
                if not url:
                    continue
                title = decode_title(ni.get('title', ''))
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


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            'error': 'Usage: fetch_related_articles.py <appid> <appsecret> [count] [months]'
        }, ensure_ascii=False))
        sys.exit(1)

    appid = sys.argv[1]
    appsecret = sys.argv[2]
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    months = int(sys.argv[4]) if len(sys.argv) > 4 else 3

    try:
        token = get_access_token(appid, appsecret)
        articles = fetch_articles(token, count, months)
        result = {
            'articles': articles,
            'total': len(articles),
            'filter_months': months,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
