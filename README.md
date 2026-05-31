# pdf-to-wechat — PDF 转微信公众号草稿自动化工具

将各类 PDF 文件（行业报告、研究论文、政策文件）自动转化为排版精美的微信公众号科普文章，并一键发布到公众号草稿箱。AI 驱动，全流程自动化。

---

## 功能特性

- **PDF 智能提取** — 自动提取 PDF 文本内容，纯图片 PDF 自动截图配图
- **AI 撰写文章** — 3000-5000 字专业解读，去除 AI 味，标题直接使用 PDF 文件名
- **7 种排版样式** — 绿色商务 / 科技蓝 / 暖橙人文 / 极简黑白 / 深空灰 / 玫瑰金 / 翠柏绿
- **自动配图** — 关键页面截图自动嵌入正文，微信永久素材上传
- **5 项质量门禁** — 标题乱码 / H3标题 / CTA合规 / 原文链接 / 图片齐全
- **知识拓展** — 文末随机推荐历史文章（从 `knowledge_links.txt` 读取）
- **底部 GIF 引流** — 自动添加公众号引流 GIF
- **串行处理** — 批量 PDF 逐一处理，互不干扰
- **发布追踪** — 已处理记录自动保存，避免重复

---

## 快速开始

### 环境要求

- Python 3.10+
- 微信公众号已获得接口权限（AppID + AppSecret）

### 安装

```bash
# 克隆仓库
git clone https://github.com/zyd52384/skills-pdf2wechat.git
cd skills-pdf2wechat

# 安装依赖
pip install -r requirements.txt
```

### 配置

创建 `~/.workbuddy/wechat_config.json`：

```json
{
  "appid": "your_appid",
  "appsecret": "your_appsecret"
}
```

### 基本用法

处理单篇 PDF：

```bash
python scripts/publish_draft.py path/to/config.json
```

批量处理（配合 `factory.py`）：

```bash
python factory.py
```

---

## 目录结构

```
skills-pdf2wechat/
├── SKILL.md                          # WorkBuddy Skill 定义（AI agent 执行指南）
├── FACTORY_GUIDE.md                  # 工厂模式使用说明
├── factory.py                        # 批处理辅助脚本（MD5 去重 / 限流）
├── requirements.txt                  # Python 依赖
├── references/
│   ├── styles.md                     # 7 种排版样式定义
│   └── writing-guide.md              # 写作规范（去 AI 味规则）
└── scripts/
    ├── publish_draft.py              # 核心发布脚本
    ├── capture_pages.py              # PDF 截图工具
    ├── extract_pdf.py                # PDF 文本提取
    └── fetch_related_articles.py     # 关联文章获取
```

---

## 配置文件说明

`publish_draft.py` 接收一个 JSON 配置文件的路径：

```json
{
  "article_md": "/path/to/article.md",
  "screenshot_dir": "/path/to/screenshots/",
  "title": "文章标题（默认使用 PDF 文件名）",
  "style": "tech-blue",
  "source_filename": "原始 PDF 文件名",
  "cover_page": 1,
  "image_pages": [1, 3, 5, 7, 10],
  "related_reading": true,
  "data_dir": "/path/to/data",
  "original_url": "https://www.203060.com"
}
```

### 可选样式

| style_id | 风格 | 适用场景 |
|----------|------|---------|
| `green-business` | 绿色商务 | 政策解读、行业报告 |
| `tech-blue` | 科技蓝 | 技术白皮书、数据分析 |
| `warm-orange` | 暖橙人文 | 观点评论、行业洞察 |
| `minimal-bw` | 极简黑白 | 纯文字深度内容 |
| `deep-gray` | 深空灰 | 技术分析、学术期刊 |
| `rose-gold` | 玫瑰金 | 科普传播、行业故事 |
| `cypress-green` | 翠柏绿 | 双碳、能源环境主题 |

---

## 知识拓展

在 PDF 源目录（`E:\pdftowechat\`）下创建 `knowledge_links.txt`，每行一条：

```
文章标题|https://mp.weixin.qq.com/s/xxxxx
```

`publish_draft.py` 每次发布时自动读取并随机选 5-8 条插入文末。

---

## 版本历史

### v2.2.0 (2026-05-30)
- 7 种排版样式（新增深空灰/玫瑰金/翠柏绿）
- CTA 规则调整：正文不出现网址，按知识点延伸
- 标题直接用 PDF 文件名
- QC 新增 H3 标题检查
- 底部 GIF 引流自动追加
- 知识拓展模块（txt 文件方案）
- 公众号排版样式系统化重构

### v2.1.0
- QC Checklist 自动化校验
- 串行处理规则
- 发布前 AI 自检 + 脚本校验双保险

### v1.0.0
- 基础 PDF 转公众号功能
- 截图自动配图
- 科技蓝单一样式
## 希望跟更好从事虚拟资料项目的同学建立链接
### baomafenxiang520  欢迎交流学习
