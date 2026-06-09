---
name: pdf-to-wechat
description: 将 PDF 文件转化为微信公众号科普文章并发布到草稿箱（AI 驱动流程）。AI agent 自动提取 PDF 文本、选择关键页面截图、撰写 3000-5000 字专业解读文章、图片自然插入正文、排版后发布到公众号草稿箱。支持 API（AppID/AppSecret）和浏览器操作两种发布模式。每篇文章末尾自动添加引流 GIF。附带 factory.py 批处理辅助脚本（MD5去重/限流），用于扫描 E:\pdftowechat 目录。
version: 2.4.0
agent_created: true
---

# PDF 转公众号科普文章

将 PDF 文件自动转化为排版精美的微信公众号文章，发布到草稿箱。

> ⚠️ **架构说明：本 skill 是 AI 驱动的流程**
>
> 本 skill 的核心由 AI agent 按以下指令执行，**不是全自动 Python 脚本**。
> - 在 WorkBuddy 中调用本 skill 时，AI 会读取 SKILL.md 并逐步完成：提取文本 → 选页截图 → 写文章 → 发布
> - `factory.py` 是**批处理辅助脚本**（MD5去重/5篇限流/失败跳过），它不替代 AI 的写作和发布决策
> - 单独运行 `factory.py` 不会自动发布文章到公众号——它会准备好素材，写作步骤仍需 AI 介入
> - **正确用法**：在 WorkBuddy 对话中说"把 E:\pdftowechat 里的 PDF 发公众号"，AI 会自动按流程执行

## 功能

1. **PDF 解析** - 提取全文文本与页面元信息（pymupdf），纯图片 PDF 自动切换 easyocr
2. **AI 选页截图** - 智能识别含图表/数据的核心页面，整页渲染 PNG
3. **深度写作 v3.0** - 嵌入 humanizer-zh 24 种 AI 模式规避规则，写作 + 去AI味自检双保险
4. **图文融合** - AI 写作时自然决定图片插入位置，文字与截图融为一体
5. **双模式发布** - API（AppID/AppSecret）或浏览器操作，自动适配
6. **截图当封面** - 取 PDF 中最具代表性的一页作为封面图
7. **7 种排版样式** - 绿色商务 / 科技蓝 / 暖橙人文 / 极简黑白 / 深空灰 / 玫瑰金 / 翠柏绿
8. **来源备注** - 文末自动追加 PDF 源文件名
9. **原文链接** - 支持 content_source_url（阅读原文）
10. **内容引导** - AI根据文章内容自然生成引导至原文链接的文案
11. **延伸阅读** - 自动生成3个月内已发布文章链接
12. **发布追踪** - published_articles.json 自动记录
13. **统一发布脚本** - `publish_draft.py` 一键完成
14. **内容工厂** - `factory.py` 批处理辅助（MD5去重/限流/准备素材，写作由 AI 完成）
15. **QC Checklist** - AI agent 自检 + publish_draft.py 自动化校验双保险，5 项质量门禁：标题乱码/###格式/CTA合规/原文链接/图片齐全
16. **底部 GIF 引流** - 每篇文章末尾自动添加公众号引流 GIF（靠左显示），URL 已上传微信永久素材
17. **知识拓展** - 每篇文章末尾自动插入随机推荐文章列表，从 `knowledge_links.txt` 读取数据，随机选5-8篇带链接展示

## 参数设计

| 参数 | 获取方式 | 必填 |
|------|---------|------|
| PDF 文件路径 | 用户提供 | ✅ |
| AppID / AppSecret | 优先读 `~/.workbuddy/wechat_config.json`，问用户补 | API 模式必填 |
| 截图页数上限 | 默认 5，可覆盖 | 可选 |
| 排版样式 | 4 种可选，自动推荐或手动选择，默认 `tech-blue` | 可选 |
| 发布方式 | 草稿/立即发布，默认草稿 | 可选 |
| 来源文件名 | 自动从 PDF 路径提取 | 自动 |
| original_url | config 中配置原文链接 | 可选 |

## 执行流程

> ⚠️ **串行处理规则（硬性要求）**
> 同时处理多个 PDF 时，必须严格按照 **逐一处理、全部完成再换下一个** 的原则：
> - 每篇 PDF 的完整生命周期（Step 1→Step 2→Step 3→Step 3.5→Step 3.6→Step 4→Step 5）必须**一次性走完**
> - 不允许交叉操作（如：不能给 PDF A 截完图就切去写 PDF B 的文章，再回头处理 PDF A 的发布）
> - **禁止并发**：不启动并行任务/多线程/异步处理

```
收到 PDF 文件路径（单篇或多篇）
    ↓
【前置检查】读 ~/.workbuddy/wechat_config.json（有则跳过询问）
    │
    ├── 工作区外路径 → 先 cp 到 ASCII 路径（Windows 必做）
    │
    └── 多篇时 → 确认处理顺序（按文件名/用户指定顺序串行）
    ↓
┌─ 对每篇 PDF 逐一执行: ──────────────────────────┐
│                                                    │
│  Step 1: 提取 PDF 文本（pymupdf → 空文字 OCR）      │
│      ↓                                             │
│  Step 2: AI 选页 + 截图（150dpi）                    │
│      ↓                                             │
│  Step 3: AI 生成文章 Markdown（含 [IMG_N] 占位符）    │
│      → 必须加载 writing-guide.md v2.0                  │
│      → 写作时遵循 humanizer-zh 24 种 AI 模式规避规则    │
│      ↓                                                 │
│  Step 3.5: 去AI味自检（humanizer-zh 24项模式扫描）      │
│      → 扫描 AI 模式（夸大意/公式结构/AI词汇/模糊归因等） │
│      → 不通过先润色，通过后进入 QC                      │
│      ↓                                                 │
│  Step 3.6: AI agent 自检（QC 5 项，不通过先修复）       │
│      ↓                                             │
│  Step 4: publish_draft.py 发布（内置自动化 QC 校验）  │
│      → 发布成功后才处理下一篇                        │
│      ↓                                             │
│  Step 5: 记录此篇结果                               │
│                                                    │
└────────────────────────────────────────────────────┘
    ↓
全部完成 → 合并输出摘要报告
```

**v2.1.0 更新**：
- 新增 **Step 3.5 QC Checklist**：AI agent 写作完成后必须自检 4 项（标题乱码/CTA合规/原文链接/图片齐全），自检不通过先修复
- `publish_draft.py` v1.8.0：发布前内置自动化 QC 校验（4 项全过才放行），失败抛 RuntimeError 并列出失败项
- Step 3 模型输出要求明确 `[IMG_N:] 占位符至少 2 个`；**标题直接用 PDF 源文件名**，不另起

**v2.2.0 更新**：
- **CTA 规则调整**：文末 CTA 根据正文知识点做自然延伸（非固定模板），禁止出现 www.203060.com 及「阅读原文」
- **标题规则**：文章标题直接用 PDF 源文件名（去 `.pdf` 后缀），QC 校验标题与文件名一致性
- **url 仅用于 original_url**：www.203060.com 只填在微信公众号「阅读原文」链接字段，不出现在文章正文中
- publish_draft.py QC #2 修正：不再要求正文中出现"阅读原文"/"203060.com"关键词，改为检测禁止词 + 网址不应出现于正文
- **底部 GIF 引流**：publish_draft.py 新增 `FOOTER_GIF_URL` 常量，每篇文章末尾自动插入引流 GIF（靠左显示），上传自微信永久素材
- 注意事项新增 CTA 合规规则及底部 GIF 说明
- **QC 新增第5项**：正文中禁止出现 `###` 及以上标题标记，QC脚本 + AI自检双重校验
- **知识拓展模块**：publish_draft.py 新增 `build_knowledge_extension_html()`，从 `knowledge_links.txt` 读取文章标题和链接，随机选5-8篇插入文末（GIF上方）
- `fetch_material_articles` 默认count提升至50
- 执行流程图中使用框线标记串行循环路径

**v2.3.0 更新**：
- **去AI味增强**：Step 3 嵌入 humanizer-zh 24种AI模式识别指南 + humanize-zh-pro 公众号风格模板
- **新增 Step 3.5 去AI味自检**：写完后运行 humanizer-zh 24 项模式扫描，不通过先润色；原有 QC 步骤移至 Step 3.6

**v2.0.0 更新**：

**v1.5.0 更新**：
- 新增 `scripts/publish_draft.py` 统一发布脚本，封装 token/上传/构建/发布/验证全流程
- 文末自动追加 PDF 来源文件名备注
- 明确 Windows 中文路径处理策略（先 cp 到 ASCII 路径）
- `wechat_config.json` 凭证持久化，后续自动读取无需重复询问
- API 发布固定用 `ensure_ascii=False` + `data=` 模式（标题乱码的根因解法）
- `publish_draft.py` 内置 draft/batchget 标题验证（Latin-1 → UTF-8 修复）

---

### Step 0: 前置准备

**1. 路径处理（Windows 必做）**

PDF 路径含中文字符时，必须先复制到纯 ASCII 路径：

```bash
mkdir -p C:/temp/wechat_article
cp "原始中文路径/文件.pdf" C:/temp/wechat_article/output.pdf
```

后续所有操作使用 `C:/temp/wechat_article/output.pdf`。

**2. 凭证检查**

```bash
cat ~/.workbuddy/wechat_config.json
```

格式：
```json
{"appid": "wx...", "appsecret": "..."}
```

有则直接使用，无则在 Step 4 发布前向用户索要并自动保存。

---

### Step 1: 提取 PDF 文本

先尝试 pymupdf 提取：

```bash
pip install pymupdf  # 首次
python {skillDir}/scripts/extract_pdf.py <pdf_path>
```

输出 JSON：
- `info`：PDF 标题、作者、总页数
- `pages[]`：每页的 `page_num`、`word_count`、`has_images`、`text`
- `total_text_length`：全文总词数

**如果 `total_text_length == 0`** → PDF 是纯图片（扫描件/PPT 幻灯片），自动切换到 easyocr 流程：

1. 渲染所有页面为 PNG（200dpi）：
   ```bash
   python {skillDir}/scripts/capture_pages.py <pdf_path> --pages 1-<N> --dpi 200
   ```

2. ⚠️ 截图目录可能含中文 → 已在 Step 0 处理（PDF 在 ASCII 路径，截图目录也是 ASCII）

3. easyocr 逐页提取：
   ```bash
   pip install easyocr  # 首次（首次运行自动下载模型约 120MB）
   ```
   ```python
   import easyocr, os, json
   reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
   for i in range(1, total_pages + 1):
       path = f"{screenshot_dir}/page_{i:03d}.png"
       result = reader.readtext(path, detail=0)
       text = '\n'.join(result)
   ```

4. OCR 结果写入 Markdown 文件作为后续写作素材

**性能**：约 6-7 秒/页（CPU），16 页约 2 分钟。

---

### Step 2: AI 选页与截图

选页标准：
1. 含图表/数据的页面优先（有 `has_images` 或文本含大量数字/百分比）
2. 结构性内容（编号列表 > 5 条、分类框架、流程描述）
3. 避开纯封面、目录、鸣谢、附录页
4. 第一张标记为封面图

默认选 5 页，DPI 150：

```bash
python {skillDir}/scripts/capture_pages.py <pdf_path> --pages <1,4,7,9,12> --dpi 150
```

> 若 Step 1 已做过全页截图（纯图片 PDF），此处仅需挑出关键页码，DPI 150 的文章图可复用 200dpi 的截图（微信会压缩，差异不大）。

---

### Step 3: AI 一次性生成完整文章（嵌入去AI味规则）

生成前**必须**加载 `references/writing-guide.md` 和 `references/styles.md`。writing-guide v2.0 包含严格去AI味规则。

**可选的写作风格**：在 config 中设置 `"writing_style": "khazix"` 可切换至卡兹克公众号风格（详见 steps.md 中 "卡兹克风格" 部分）。不设置时使用默认专业解读风格。

**写在写作指令里的去AI味规则（直接嵌入 prompt）：**

写作时必须规避以下 24 种 AI 模式，这是**硬性要求**，不是建议：

**一、内容模式**
1. **禁止夸大意义** — 不要用"标志着/证明了/体现了/至关重要/核心作用/关键转折点"等词拔高普通事实。直接陈述事实本身。
2. **禁止模糊归因** — 不要写"行业报告显示/专家认为/观察者指出"而没有具体来源。要么给出来源，要么删掉。
3. **禁止以 -ing 结尾的肤浅分析** — 不要用"……，凸显了……/反映了……/推动了……"这种空洞句式。
4. **禁止宣传式语言** — 不要用"引人入胜的/令人叹为观止的/必读的/开创性的"等广告词。
5. **禁止"挑战与展望"公式化段落** — 如果必须写挑战，用具体数据和案例说话，不要用"尽管取得了显著成就，但仍面临若干挑战……"这种套话。

**二、语言模式**
6. **禁用 AI 高频词汇** — 此外/值得注意的是/综上所述/与……保持一致/至关重要/深入探讨/深入分析/赋能/抓手/底层逻辑/充满活力的/持久的/增强/培养/突出（动词）/复杂/复杂性/关键（形容词）/格局/关键性的/证明/强调/宝贵的。
7. **避免系动词回避** — 不要用"作为/代表/标志着/充当"代替简单的"是"。能用"是"的地方就不要用其他词。
8. **禁止否定式排比** — 不要用"这不仅……更是……""不只是……而是……"结构。
9. **禁止三段式法则** — 不要强行将信息分成三组。两项或四项都可以，三项是 AI 最常用的。
10. **禁止刻意换词** — 同一事物全文用同一名称，不要在同义词之间来回切换。
11. **禁止"从 X 到 Y"虚假范围** — 不要滥用"从……到……"结构来制造全面假象。

**三、风格模式**
12. **破折号限制** — 全文破折号不超过 2 个。AI 极爱滥用破折号冒充力度。
13. **无粗体滥用** — 不要用 ** 加粗普通术语，只加粗真正需要强调的极少数词。
14. **禁止内联标题列表** — 不要用"**关键词：** 值"这种格式的列表项。
15. **禁止 emoji 滥用** — 全文 emoji 不超过 1 个，标题和正文中不使用 emoji。

**四、交流模式**
16. **禁止谄媚语气** — 不要用"好问题/您说得完全正确/当然！"等讨好式语言。
17. **禁止知识截止日期免责** — 不要写"截至目前/根据我掌握的信息/虽然具体信息有限"。
18. **删除填充短语** — 不要使用"为了实现这一目标/在这个时间点/值得注意的是/需要指出的是"。
19. **删除过度限定** — 去掉"可能/也许/某种程度上/可以被认为"等不必要的修饰。
20. **禁止通用积极结论** — 文末不要写"未来充满希望/激动人心的时代即将到来"等空洞表态。

**五、结构规则**
21. **连续三个句子不能长度相同** — 长短句交替，避免机械节奏。
22. **段落结尾不能都是简洁单行** — 变换段落结束方式。
23. **信任读者** — 不解释隐喻和比喻，直接说。
24. **给文本注入灵魂** — 有观点、有态度、允许适当的"我"视角（"我认为……"），不要像维基百科一样中立无趣。

---

**卡兹克风格（writing_style="khazix"）**：加载 khazix-writer skill 后，上述 24 条规则继续执行，额外增加：

- **开头**：禁止"前几天跟朋友聊天"等 AI 常见虚构场景。从真实个人行为切入（"翻了两遍""读到一份报告"）
- **结构**：不按"第一章第二节"组织，选一个核心洞察深挖，不走马观花逐一罗列
- **语气**：有真实情绪——"有点焦虑""这个数据让我意外"都好，不能完全中性
- **态度**：敢下判断。"这才是真功夫""我觉得这个方案站不住"
- **知识输出**：不是"报告介绍了X种方案"，而是"我琢磨了一下，关键其实在Y"
- **无小标题**：正文不用 `##` 分节，一口气顺下来，靠口语化转场衔接板块
- **无冒号/无破折号/无引号**：正文禁止使用全角冒号、长破折号、双引号（用「」替代）
- **结尾**：不要总结式收束，以个人观点/情绪表态收尾
- **总纲**："有见识的普通人在认真聊一件打动他的事"

---

**模型输入**：
1. PDF 源文件名（去掉 `.pdf` 后缀即文章标题）
2. 作者、总页数
3. 提取的全文文本（或 OCR 结果）
4. 截图页码列表及每页内容概要
5. 写作指南 + 样式参考

**模型输出要求**：
- **标题直接用 PDF 源文件名**（去掉 `.pdf` 后缀，取文件主体部分），不另起新标题
- 输出完整 Markdown 格式文章（一次性，不分段生成）
- 含 `[IMG_N: 描述]` 占位符（**至少 2 个，建议 4-6 个**）
- 字数：3000-5000 字
- 风格：专业解读型，去除AI味
- 结构：开篇(200-300字) → 正文(2500-4000字，2-4小标题) → 收尾CTA(100-200字)
- **CTA 要求**：根据正文内容、知识点做自然延伸（如指出研究方向、未解决的问题、行业趋势），**不是固定模板**；正文中**不得出现**「www.203060.com」「阅读原文」等网址引导语；不得出现诱导性词汇（转发、分享等）
- 文章写入文件（如 `article.md`）

**Step 3.5: 去AI味自检（写完后必须执行）**

写作完成后，AI agent 必须加载 `humanizer-zh` skill 的 24 种 AI 模式清单，对文章逐项扫描。**自检不通过必须润色修复，不能跳过。**

| # | 检查项 | AI 特征 | 修复方法 |
|---|--------|---------|---------|
| 1 | 夸大意义 | "标志着/证明了/体现了/核心作用/关键转折点"等空话 | 删掉空话，直接陈述事实 |
| 2 | 虚假知名度 | "行业报告显示/专家认为"无具体来源 | 删掉或加具体来源 |
| 3 | -ing 肤浅分析 | "……，凸显了/反映了/推动了……" | 删掉后半句，直接给结论 |
| 4 | 宣传语言 | "引人入胜/必读的/开创性的" | 换成中性表达或删除 |
| 5 | 公式化挑战 | "尽管取得了成就，但仍面临挑战" | 用具体案例替代套话 |
| 6 | AI 高频词 | 此外/值得注意的是/综上所述/赋能/抓手/底层逻辑 | 查找替换 |
| 7 | 系动词回避 | "作为/代表/标志着/充当"代替"是" | 改成"是" |
| 8 | 否定排比 | "不仅……更是……" | 拆成两个简单句 |
| 9 | 三段式 | 强行三组并列 | 改为两项或四项 |
| 10 | 刻意换词 | 同一事物不同名字 | 全文统一名称 |
| 11 | 虚假范围 | "从……到……" | 删掉或具体化 |
| 12 | 破折号过多 | 全文 > 2 个破折号 | 删除多余的 |
| 13 | 粗体滥用 | 术语加粗 | 只保留必要加粗 |
| 14 | 内联标题列表 | "**关键词：** 值" | 改写为普通段落 |
| 15 | emoji 滥用 | >1 个 emoji | 删除多余的 |
| 16 | 谄媚语气 | "好问题/您说得完全正确" | 删掉 |
| 17 | 知识截止免责 | "截至目前/据我所知" | 删掉 |
| 18 | 填充短语 | "值得注意的是/需要指出的是" | 直接删除 |
| 19 | 过度限定 | "可能/某种程度上/可以被认为" | 去掉不必要的 |
| 20 | 通用积极结尾 | "未来充满希望/激动人心的时代" | 用具体内容替代 |
| 21 | 句子节奏均匀 | 连续 3 句长度相同 | 打断其中一句 |
| 22 | 段落结尾单一 | 每段都以单行收束 | 变换方式 |
| 23 | 过度解释 | 解释隐喻/比喻 | 信任读者，删掉解释 |
| 24 | 无灵魂 | 像维基百科般中立无趣 | 加入观点和态度 |

**去AI味自检通过后，进入 Step 3.6 QC 校验。**

**写作完成后，AI agent 必须执行自检清单（QC Checklist）：** ⚠️

| # | 检查项 | 标准 | 失败处理 |
|---|--------|------|---------|
| 1 | 文章题目无乱码 | 题目无 `\\u` 转义、无 `�`、无不打印字符、无超出 BMP 的字符；**且与 PDF 源文件名一致** | 修复后重写 |
| 2 | 文章格式 | 正文无 `###` 及以上标题标记（只用 `#` 和 `##`） | 改为 `##` 或调整结构 |
| 3 | 尾部 CTA 段落 | 根据正文知识点做自然延伸（非固定模板）；**不得出现**「www.203060.com」「阅读原文」等网址引导语；**不得出现**「转发」「分享到朋友圈」「必须转」等诱导性词汇 | 补写或修改 CTA |
| 4 | 原文链接 | config.json 中 `original_url` 必须设为 `"https://www.203060.com"`（不出现在文章正文） | 修正 config |
| 5 | 图片配置齐全 | `[IMG_N:]` 占位符 ≥ 2 个；截图文件与页码对应；封面页序号=image_pages[0] | 补占位符或截图 |

> **自检不通过 → AI agent 必须修复后才能进 Step 4，不能跳过。**

**禁止事项**（详见 writing-guide.md）：
- ❌ 禁用"值得注意的是/综上所述/我们可以看到/赋能/抓手/底层逻辑"
- ❌ 禁用"首先其次再次最后"机械枚举
- ❌ 每段结尾不写"小结"——直接说结论
- ❌ 文末不加话题标签，全文emoji不超过1个
- ❌ 不编造 PDF 中没有的数据
- ❌ 不写"本文由 AI 生成"类字样
- ❌ **禁止 `###` 及以上标题**，结构只用 `#`（文章主标题）和 `##`（章节标题）

---

### Step 4: 统一发布（publish_draft.py）

**推荐使用统一脚本**，一步完成所有 API 操作：

```bash
python {skillDir}/scripts/publish_draft.py <config.json>
```

**config.json 格式（v2.0）**：

```json
{
    "article_md": "C:/temp/wechat_article/article.md",
    "screenshot_dir": "C:/temp/wechat_article/screenshots/",
    "title": "文章标题（≤64字符）",
    "style": "tech-blue",
    "source_filename": "原始PDF文件名.pdf",
    "cover_page": 1,
    "image_pages": [1, 4, 7, 9, 12],
    "related_reading": true,
    "data_dir": "C:/Users/zyd523/.workbuddy/data/pdf_wechat",
    "original_url": "https://www.203060.com",
    "appid": "wx...",
    "appsecret": "..."
}
```

> `appid` / `appsecret` 可选：不填时自动从 `~/.workbuddy/wechat_config.json` 读取。

**脚本内部流程**：

```
1. 读取凭证（config → wechat_config.json）
2. GET /cgi-bin/token → access_token
3. 发布前 QC 校验（4 项全过才继续，否则抛错终止）
   ├─ QC① 标题无乱码
   ├─ QC② 尾部 CTA 合规（有引导语、无诱导词）
   ├─ QC③ original_url 指向 https://www.203060.com
   └─ QC④ 图片齐全（截图文件存在 + md 有 [IMG_N:] 占位符）
4. POST /cgi-bin/material/add_material → 封面 media_id
5. POST /cgi-bin/media/uploadimg × N → 图片 URL 列表
6. 解析 Markdown → 替换 [IMG_N] → 构建样式化 HTML
7. 文末：来源备注 → 延伸阅读
8. POST /cgi-bin/draft/add（ensure_ascii=False + data=） → 草稿 media_id
9. 记录到 published_articles.json
10. GET /cgi-bin/draft/batchget → 验证标题无乱码
```

**输出 JSON**：

```json
{
    "status": "ok",
    "media_id": "草稿ID",
    "cover_media_id": "封面素材ID",
    "title": "实际标题",
    "verified_title": "验证后标题",
    "image_count": 5,
    "related_reading_count": 2
}
```

#### 手动 API 模式（不使用脚本时）

若因某种原因需要手动调用：

1. **获取 token**：`GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}`

2. **上传封面**（永久素材）：`POST https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={TOKEN}&type=image`

3. **上传正文图片**：`POST https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={TOKEN}`

4. **构建 HTML** 并发布草稿：

   ⚠️ **必须用 `ensure_ascii=False` + `data=` 参数**，详见「Python JSON 中文乱码陷阱」节。

   ```python
   payload = {"articles": [{"title": "...", "content": "...", "thumb_media_id": "..."}]}
   body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
   requests.post(url, data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
   ```

   请求体不填 `author` 字段（避免偶发的 45110 长度限制）。

#### 浏览器模式

无 AppID/AppSecret 时使用：

1. 生成的 HTML 文件 → 全选复制
2. 登录 mp.weixin.qq.com → 新建图文
3. 粘贴 HTML → 在对应位置上传本地截图
4. 封面图选 page_001.png
5. 保存草稿

---

### 内容工厂（factory.py）

> ⚠️ `factory.py` 是批处理辅助脚本，不是全自动工具。
> 它负责：MD5去重、5篇限流、失败跳过、文件准备。
> **写作和发布仍需 AI agent 按本 SKILL.md 流程执行。**
> 单独运行 `factory.py` 只会准备素材，不会自动发布文章。

批量处理 `E:\pdftowechat` 目录下的 PDF 文件，自动调用完整发布流程。

```bash
python {skillDir}/factory.py            # 立即执行（默认5篇）
python {skillDir}/factory.py --dry-run  # 仅扫描
python {skillDir}/factory.py --limit 3  # 处理3篇
python {skillDir}/factory.py --force    # 忽略限制全量处理
```

**功能**：
- MD5 去重（`processed.json`），相同文件不重复处理
- 每日 5 篇限流（可配置），到量自动停止
- 失败跳过继续
- 自动复制到 ASCII 路径
- 自动判断纯图片/文本 PDF
- 发布完成后记录到 `published_articles.json`

**数据目录**：`C:/Users/zyd523/.workbuddy/data/pdf_wechat/`

---

### Step 5: 完成报告

```
✅ PDF → 公众号文章 完成

文件：{PDF文件名}
总页数：{N}，截图：{M}张
文章标题：{标题}
正文字数：{X}字
图片数量：{Y}张
原文链接：{URL}
延伸阅读：{N}篇
发布模式：API / 浏览器
草稿 ID：{media_id}
状态：已保存到草稿箱

下一步：登录 mp.weixin.qq.com → 内容管理 → 草稿箱 → 预览/发布
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| `pymupdf` (fitz) | PDF 文本提取 + 页面截图 |
| `easyocr` | 纯图片 PDF 的 OCR 文字提取 |
| `requests` | API 模式调用微信接口 |
| `scripts/publish_draft.py` | **统一发布**：token→上传→构建→发布→验证 |
| `scripts/extract_pdf.py` | PDF 文本提取 |
| `scripts/capture_pages.py` | PDF 页面截图 |
| `scripts/fetch_related_articles.py` | 拉取已发布文章生成延伸阅读 |
| `factory.py` | **内容工厂**：批量MD5去重/5篇限流/失败跳过 |
| `references/writing-guide.md` | **去AI味写作指南 v2.0** |
| `baoyu-post-to-wechat` skill (可选) | 浏览器模式发布 |

---

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| `pymupdf` 未安装 | `pip install pymupdf` |
| `easyocr` 未安装 | `pip install easyocr`（首次自动下载模型 ~120MB） |
| PDF 打开失败 | 检查文件路径、文件是否加密/损坏 |
| **PDF 文本为空（纯图片 PDF）** | 自动切换 easyocr 流程（见 Step 1） |
| **easyocr cv2 中文路径报错** | 必须先把 PDF 和截图放到纯 ASCII 路径（见 Step 0） |
| API access_token 获取失败 | 检查 AppID/AppSecret 是否正确、IP 是否在白名单 |
| API 上传图片失败 | 图片 < 10MB，PNG 格式，检查 token 有效期 |
| **API draft/add 标题乱码** | 用 `ensure_ascii=False` + `data=` 代替 `json=`（publish_draft.py 已内置） |
| API draft/add 45166 invalid content | 检查是否嵌入了 mp.weixin.qq.com 链接 |
| API draft/add 45003/45110 | 不填 `author` 字段，标题截断 ≤64 字符（publish_draft.py 已内置） |
| API 40001 invalid credential | token 过期，重新获取，IP漂移需加白名单 |
| **draft/batchget 返回 Latin-1 乱码** | 终端显示问题，`.encode('latin-1').decode('utf-8')` 修复可验证 |
| IP不在白名单 | 登录 mp.weixin.qq.com → 设置 → IP白名单添加当前IP |
| JSON config source_filename 报错 | 文件名不能含未转义的双引号，使用中文全角引号替代 |
| 浏览器模式未登录 | 提示用户手动扫码登录 mp.weixin.qq.com |
| 截图质量不佳 | 调整 `--dpi`（OCR 用 200，文章图用 150） |

---

### 纯图片 PDF 处理

当 `extract_pdf.py` 返回 `total_text_length: 0` 或大部分页面 `word_count: 0` 时，PDF 是纯图片扫描件/幻灯片，文本层为空。

**完整流程**（publish_draft.py 前置步骤）：

1. **确保 PDF 在 ASCII 路径**（Step 0）
2. **渲染全页截图**（200dpi）：
   ```bash
   python scripts/capture_pages.py <pdf_path> --pages 1-<N> --dpi 200
   ```
3. **easyocr 逐页 OCR**：
   ```python
   import easyocr
   reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
   for i in range(1, N+1):
       text = reader.readtext(f'screenshots/page_{i:03d}.png', detail=0)
   ```
4. OCR 文字写入 Markdown → 作为 Step 3 文章生成的素材
5. 用 `publish_draft.py` 完成后续发布

**easyocr 安装**：
```bash
pip install easyocr
```
首次运行自动下载模型（中文+英文约 120MB），需联网。

**性能**：约 6-7 秒/页（CPU），GPU 可显著加速。

---

### HTML 生成常见陷阱

以下两个 bug 在 Markdown → HTML 内联转换时极易发生（publish_draft.py 已内置防护）：

**陷阱 1：序号列表中的 `**bold**` 未转换**

原因：`stripped` 在 bold 转换之前计算，导致 `content` 中仍保留原始 `**`。

```python
# ❌ 错误
content = numbered_match.group(2)  # content 含原始 **
# ✅ 正确
content = convert_bold(numbered_match.group(2))
```

**陷阱 2：多行图片 HTML 被循环再次包裹 `<p>`**

原因：图片 HTML 跨多行时，第 2-N 行被当作普通段落再次包裹。

```python
# ✅ 正确：图片 HTML 必须单行输出
return f'<p style="..."><img src="..." /><span>▲ ...</span></p>'
```

**验证清单**（HTML 生成后自查）：
- `full_html.count('**') == 0`（无残留 Markdown bold 语法）
- `'<p><p' not in full_html`（无段落嵌套）
- `full_html.count('<strong') >= 期望 bold 数量`

---

### Python JSON 中文乱码陷阱 🔴

**这是最常见的草稿箱标题乱码根因。** `requests.post(url, json=payload)` 内部调用 `json.dumps(payload, ensure_ascii=True)`，会将中文转为 `\uXXXX` 转义序列。微信 API 收到后**不解码这些转义序列**，直接当普通文本存入数据库。

```python
# ❌ 错误：json= 参数内部 ensure_ascii=True → \uXXXX 字面串存入微信
requests.post(url, json=payload)

# ✅ 正确：ensure_ascii=False + data= 手动编码
body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
requests.post(url, data=body,
    headers={'Content-Type': 'application/json; charset=utf-8'})
```

**Shell Heredoc 额外陷阱**：Windows Git Bash 的 heredoc 传中文给 Python 时可能被终端转码破坏。最稳妥的方式是**先 Write JSON 文件 → Python 读取 → 发布**，而不是在命令中内联中文 payload。

**验证方法**：`draft/batchget` 返回的 title 若是 Latin-1 mojibake 格式，用 `.encode('latin-1').decode('utf-8')` 修复后应显示正确中文。

---

### WeChat API 标题/作者异常限制

偶发情况下，微信 `draft/add` 对大 payload 文章会出现异常限制：

| 症状 | 错误码 | 策略 |
|------|--------|------|
| 标题 >8 字符 | 45003 | publish_draft.py 自动截断 ≤64，若仍失败则手动缩至 8 字符 |
| 作者名字被拒 | 45110 | publish_draft.py 默认不填 `author` 字段 |

---

### Token 续期

`access_token` 有效期 2 小时。ocr 耗时较长时 token 可能在图片上传阶段过期。

- `publish_draft.py` 在发布前**重新获取 token**，不依赖之前的 token
- 若上传过程遇 `40001`，重新获取后继续

---

## 注意事项

- 微信图片上传 < 10MB，300dpi A4 截图约 2-5MB
- 每篇文章配图 ≤ 10 张（微信限制）
- 标题自动截断 ≤ 64 字符
- 不填 `author` 字段（避免 45110 异常）
- `wechat_config.json` 凭证保存在 `~/.workbuddy/` 下，后续自动读取
- Windows 环境所有文件路径必须在纯 ASCII 目录下（easyocr cv2 限制）
- JSON config 中 source_filename 不能含未转义双引号
- IP白名单漂移属常态问题，每次运行可能需重新添加新IP
- **CTA 段落规则**：文末必须根据正文知识点做自然延伸引导，**不得出现** www.203060.com 及「阅读原文」等固定模板，**不得**出现「转发」「分享到朋友圈」「必须转」「扩散」等诱导性词汇（违反微信公众号运营规范）
- **底部 GIF 引流**：publish_draft.py 自动在每篇文章末尾添加引流 GIF（靠左显示），URL 硬编码在 `FOOTER_GIF_URL` 常量中，上传自微信永久素材
- **知识拓展**：在 `E:\pdftowechat\knowledge_links.txt` 中维护文章标题和链接（格式：`标题|url`，每行一条），publish_draft.py 自动读取并随机选5-8条插入文末
- **标题规则**：直接用 PDF 源文件名（去 `.pdf` 后缀），不另起标题
