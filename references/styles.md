# 公众号文章排版样式

4 种可选样式（v2.2.0 新增至 7 种），在 Step 3 写作完成后、Step 4 排版前选择。

---

## 样式 1：绿色商务风 `green-business`（默认）

微信原生绿基调，专业克制，适合政策解读、行业报告、企业公告。

| 元素 | 样式 |
|------|------|
| 主色 | `#07c160`（微信绿） |
| H1 标题 | 22px 加粗居中 `#111` |
| H2 小标题 | 20px 加粗 `#222`，左侧 3px `#07c160` 竖条，`padding-left: 10px` |
| 正文 | 16px `#333`，行高 1.85，首行缩进 2em |
| 强调 | `<strong style="color:#333;">` |
| 引用 | `#666` + 斜体 |
| 图片图注 | `#888` 14px |
| 分割线 | 1px `#eee` |

**HTML 模板**：

```html
<section style="font-size:16px;color:#333;line-height:1.85;letter-spacing:0.5px;padding:0 8px;max-width:100%;word-wrap:break-word;">
  <h1 style="font-size:22px;font-weight:700;text-align:center;margin:20px 0 28px 0;color:#111;line-height:1.5;">{标题}</h1>
  <!-- h2: -->
  <h2 style="font-size:20px;font-weight:700;color:#222;margin:32px 0 16px 0;padding-left:10px;border-left:3px solid #07c160;">{小标题}</h2>
  <!-- p: -->
  <p style="margin:10px 0;text-indent:2em;">{段落}</p>
  <!-- img: -->
  <p style="text-align:center;margin:24px 0;"><img src="{url}" style="max-width:100%;display:block;margin:0 auto;" /><span style="color:#888;font-size:14px;display:block;margin-top:8px;">▲ {描述}</span></p>
</section>
```

---

## 样式 2：科技蓝 `tech-blue`

蓝色系理性克制，适合技术白皮书、数据报告、IT 行业分析。

| 元素 | 样式 |
|------|------|
| 主色 | `#1890ff`（科技蓝） |
| H1 标题 | 22px 加粗居中 `#1a1a2e` |
| H2 小标题 | 19px 加粗 `#1a1a2e`，左侧 3px `#1890ff` 竖条 |
| 正文 | 15px `#2c3e50`，行高 1.9，首行缩进 2em |
| 强调 | `<strong style="color:#1890ff;">`（蓝色高亮） |
| 引用 | `#5a6c7d` + 左侧 2px `#1890ff` 虚线 |
| 图片图注 | `#7f8c8d` 13px |
| 分割线 | 1px `#e8edf2` |

**HTML 模板**：

```html
<section style="font-size:15px;color:#2c3e50;line-height:1.9;letter-spacing:0.3px;padding:0 8px;max-width:100%;word-wrap:break-word;">
  <h1 style="font-size:22px;font-weight:700;text-align:center;margin:20px 0 28px 0;color:#1a1a2e;line-height:1.5;">{标题}</h1>
  <!-- h2: -->
  <h2 style="font-size:19px;font-weight:700;color:#1a1a2e;margin:32px 0 14px 0;padding-left:10px;border-left:3px solid #1890ff;">{小标题}</h2>
  <!-- strong(inline): -->
  <strong style="color:#1890ff;">{强调内容}</strong>
  <!-- blockquote: -->
  <p style="margin:12px 0;padding:8px 12px;border-left:2px dashed #1890ff;color:#5a6c7d;font-size:14px;">{引用}</p>
  <!-- p: -->
  <p style="margin:10px 0;text-indent:2em;">{段落}</p>
  <!-- img: -->
  <p style="text-align:center;margin:24px 0;"><img src="{url}" style="max-width:100%;display:block;margin:0 auto;" /><span style="color:#7f8c8d;font-size:13px;display:block;margin-top:8px;">▲ {描述}</span></p>
</section>
```

---

## 样式 3：暖橙人文风 `warm-orange`

温暖有温度，适合观点评论、行业洞察、人物访谈。

| 元素 | 样式 |
|------|------|
| 主色 | `#e67e22`（暖橙） |
| H1 标题 | 23px 加粗居中 `#2d1b00` |
| H2 小标题 | 19px 加粗，底部 2px `#e67e22` 下划线（`padding-bottom:6px; border-bottom:2px solid #e67e22`） |
| 正文 | 16px `#4a3728`，行高 1.9，首行缩进 2em |
| 强调 | `<strong style="color:#d35400;">` |
| 引用 | `#8b6914` + 背景 `#fef9e7`，圆角 4px |
| 图片图注 | `#b8956a` 13px |
| 分割线 | 1px `#f0e6d3` |

**HTML 模板**：

```html
<section style="font-size:16px;color:#4a3728;line-height:1.9;letter-spacing:0.4px;padding:0 8px;max-width:100%;word-wrap:break-word;">
  <h1 style="font-size:23px;font-weight:700;text-align:center;margin:20px 0 28px 0;color:#2d1b00;line-height:1.5;">{标题}</h1>
  <!-- h2: -->
  <h2 style="font-size:19px;font-weight:700;color:#2d1b00;margin:32px 0 14px 0;padding-bottom:6px;border-bottom:2px solid #e67e22;">{小标题}</h2>
  <!-- strong(inline): -->
  <strong style="color:#d35400;">{强调内容}</strong>
  <!-- blockquote: -->
  <p style="margin:12px 0;padding:10px 14px;background:#fef9e7;border-radius:4px;color:#8b6914;font-size:15px;">{引用}</p>
  <!-- p: -->
  <p style="margin:10px 0;text-indent:2em;">{段落}</p>
  <!-- img: -->
  <p style="text-align:center;margin:24px 0;"><img src="{url}" style="max-width:100%;display:block;margin:0 auto;" /><span style="color:#b8956a;font-size:13px;display:block;margin-top:8px;">▲ {描述}</span></p>
</section>
```

---

## 样式 4：极简黑白风 `minimal-bw`

刘润公众号风格——无装饰、纯文字张力、靠逻辑节奏驱动阅读。

| 元素 | 样式 |
|------|------|
| 主色 | 无（纯黑灰白） |
| H1 标题 | 22px 加粗 `#000`，居中，上下各留大量空白（`margin: 24px 0 32px`） |
| H2 小标题 | 19px 加粗 `#000`，**无任何装饰线**，纯文字 |
| 正文 | 15px `#333`，行高 2.0，**不缩进**（段间空行分隔） |
| 强调 | `<strong style="color:#000;">` |
| 引用 | `#666`，纯文本无底色无边框 |
| 图片图注 | `#999` 12px，居中 |
| 分割线 | 无分割线，靠留白分隔 |

**HTML 模板**：

```html
<section style="font-size:15px;color:#333;line-height:2.0;letter-spacing:0.3px;padding:0 4px;max-width:100%;word-wrap:break-word;">
  <h1 style="font-size:22px;font-weight:700;margin:24px 0 32px 0;color:#000;line-height:1.6;">{标题}</h1>
  <!-- h2: -->
  <h2 style="font-size:19px;font-weight:700;color:#000;margin:36px 0 12px 0;">{小标题}</h2>
  <!-- strong(inline): -->
  <strong style="color:#000;">{强调内容}</strong>
  <!-- blockquote: -->
  <p style="margin:14px 0;color:#666;font-size:14px;">{引用}</p>
  <!-- p: no indent, paragraphs separated by margin -->
  <p style="margin:14px 0;">{段落}</p>
  <!-- img: -->
  <p style="text-align:center;margin:28px 0;"><img src="{url}" style="max-width:100%;display:block;margin:0 auto;" /><span style="color:#999;font-size:12px;display:block;margin-top:6px;">▲ {描述}</span></p>
</section>
```

---

## 样式 5：深空灰 `deep-gray`

沉稳高级灰调，冷静克制，适合深度技术分析、学术期刊风格。

| 元素 | 样式 |
|------|------|
| 主色 | `#6b7b8d`（深空灰） |
| H1 标题 | 21px 加粗居中 `#1a1a1a` |
| H2 小标题 | 18px 半粗 `#1a1a1a`，左侧 3px `#6b7b8d` 竖条 |
| 正文 | 15px `#3d3d3d`，行高 1.9，首行缩进 2em |
| 强调 | `<strong style="color:#1a1a1a;">` |
| 引用 | 淡灰底 + 左侧 3px 灰条，`#57606a` |
| 图片图注 | `#8b949e` 13px |
| 分割线 | 1px `#d0d7de` |

---

## 样式 6：玫瑰金 `rose-gold`

柔和暖色基调，温暖细腻，适合科普传播、行业故事。

| 元素 | 样式 |
|------|------|
| 主色 | `#e8a0b4`（玫瑰金） |
| H1 标题 | 22px 加粗居中 `#4a1a2e` |
| H2 小标题 | 19px 加粗 `#4a1a2e`，左侧 3px `#e8a0b4` 竖条 |
| 正文 | 16px `#5c3d3d`，行高 1.9，首行缩进 2em |
| 强调 | `<strong style="color:#c44569;">` |
| 引用 | 玫瑰粉底 + 左侧 3px 粉条，圆角 4px |
| 图片图注 | `#b08a9a` 13px |
| 分割线 | 1px `#f0d9e0` |

---

## 样式 7：翠柏绿 `cypress-green`

自然深绿色调，沉稳环保，适合能源、环境、双碳、可持续发展主题。

| 元素 | 样式 |
|------|------|
| 主色 | `#2d8a4e`（翠柏绿） |
| H1 标题 | 22px 加粗居中 `#1a3a1a` |
| H2 小标题 | 19px 加粗 `#1a3a1a`，左侧 3px `#2d8a4e` 竖条 |
| 正文 | 15px `#2d3e2d`，行高 1.85，首行缩进 2em |
| 强调 | `<strong style="color:#2d8a4e;">` |
| 引用 | 淡绿底 + 左侧 3px 绿条 |
| 图片图注 | `#6b9b6b` 13px |
| 分割线 | 1px `#c8e6c9` |

---

## 样式参数速查表

| 参数 | 绿色商务 | 科技蓝 | 暖橙人文 | 极简黑白 | 深空灰 | 玫瑰金 | 翠柏绿 |
|------|---------|--------|---------|---------|-------|-------|-------|
| `style_id` | `green-business` | `tech-blue` | `warm-orange` | `minimal-bw` | `deep-gray` | `rose-gold` | `cypress-green` |
| 正文字号 | 16px | 15px | 16px | 15px | 15px | 16px | 15px |
| 正文颜色 | `#333` | `#2c3e50` | `#4a3728` | `#333` | `#3d3d3d` | `#5c3d3d` | `#2d3e2d` |
| 行高 | 1.85 | 1.9 | 1.9 | 2.0 | 1.9 | 1.9 | 1.85 |
| 首行缩进 | 2em | 2em | 2em | **无** | 2em | 2em | 2em |
| H2 装饰 | 左侧绿竖条 | 左侧蓝竖条 | 底部橙下划线 | **无** | 左侧灰竖条 | 左侧粉竖条 | 左侧绿竖条 |
| 强调色 | `#333` | `#1890ff` | `#d35400` | `#000` | `#1a1a1a` | `#c44569` | `#2d8a4e` |
| 引用风格 | 纯灰斜体 | 虚线边框 | 淡黄底圆角 | 纯灰无饰 | 淡灰底+灰条 | 粉底+粉条圆角 | 淡绿底+绿条 |

---

## 使用方式

在 Step 3 写作完成后，根据 PDF 内容类型自动推荐样式，或让用户选择：

```
推荐样式：{style_id}（{理由}）
可选样式：green-business / tech-blue / warm-orange / minimal-bw
```

然后在 Step 4 排版 HTML 时，加载对应样式的完整模板进行生成。
