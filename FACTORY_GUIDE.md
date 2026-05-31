# 内容工厂使用指南

## 三阶段完成状态

### ✅ 阶段一：加固单篇链路
- **去AI味写作指南**：已完成 v2.0 重写，深度优化写作风格
- **发布追踪系统**：`publish_draft.py` 新增 `published_articles.json` 记录
- **3月过滤延伸**：自动过滤3个月内已发布文章，生成"延伸阅读"板块
- **时间字段支持**：`fetch_related_articles.py` 支持按时间范围过滤

### ✅ 阶段二：批量调度工厂
- **factory.py**：完整的批量处理系统
- **MD5去重机制**：避免重复处理相同文件
- **每日5篇限制**：自动限额，过度跳过
- **失败跳过策略**：单个失败不影响其他处理

### ✅ 阶段三：定时自动化
- **WorkBuddy Automation**：每天 9:00 自动触发
- **数据目录结构**：`C:/Users/zyd523/.workbuddy/data/pdf_wechat/`
- **源文件目录**：`E:\pdftowechat/`

---

## 快速开始

### 1. 准备源文件

将 PDF 文件放入 `E:\pdftowechat\` 目录：

```
E:\pdftowechat\
├── 文档1.pdf
├── 文档2.pdf
├── 文档3.pdf
└── ...
```

### 2. 配置环境

确保微信凭证存在：
```bash
cat ~/.workbuddy/wechat_config.json
# 格式: {"appid": "wx...", "appsecret": "..."}
```

### 3. 启动工厂

**立即执行（测试）：**
```bash
cd C:/Users/zyd523/.workbuddy/skills/pdf-to-wechat
python factory.py --dry-run  # 先扫描
python factory.py            # 立即执行
```

**手动指定数量：**
```bash
python factory.py --limit 3  # 处理3篇
python factory.py --force     # 全量处理
```

### 4. 定时任务自动化

已配置每天 9:00 自动运行：
- **任务ID**：automation-1779786941899
- **状态**：ACTIVE
- **执行目录**：`C:/Users/zyd523/.workbuddy/skills/pdf-to-wechat`

---

## 目录结构

```
C:\Users\zyd523\.workbuddy\skills\pdf-to-wechat\
├── factory.py                    # 内容工厂主程序
├── scripts\
│   ├── publish_draft.py          # 统一发布脚本v1.6.0
│   ├── fetch_related_articles.py # 延伸阅读获取v1.1.0
│   ├── extract_pdf.py
│   └── capture_pages.py
├── references\
│   └── writing-guide.md          # 去AI味写作指南v2.0
└── SKILL.md                      # skill文档（需更新）

C:\Users\zyd523\.workbuddy\data\pdf_wechat\
├── processed.json                # MD5去重记录
├── published_articles.json        # 已发布文章索引
└── processed_YYYY-MM-DD.json      # 每日处理记录

E:\pdftowechat\
└── *.pdf                         # 源PDF文件
```

---

## 运行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--dry-run` | 仅扫描，不执行 | `python factory.py --dry-run` |
| `--limit N` | 强制处理数量 | `python factory.py --limit 3` |
| `--force` | 忽略5篇限制 | `python factory.py --force` |

---

## 输出报告

每次运行生成详细报告：

```json
{
  "date": "2026-05-26",
  "total_limit": 5,
  "processed": 3,
  "failed": 0,
  "processed_files": [
    {
      "filename": "文档1.pdf",
      "original_path": "E:\\pdftowechat\\文档1.pdf",
      "result": {
        "status": "ok",
        "title": "文章标题",
        "media_id": "草稿ID",
        "image_count": 5,
        "related_reading_count": 2
      }
    }
  ]
}
```

---

## 故障排查

### 1. 源目录为空
```bash
ls E:\pdftowechat
# 无文件时放入 PDF 文件
```

### 2. 凭证缺失
```bash
cat ~/.workbuddy/wechat_config.json
# 格式：{"appid": "wx...", "appsecret": "..."}
```

### 3. 自动化未触发
```bash
# 手动运行测试
python factory.py --dry-run

# 查看自动化状态
automation_update --mode list
```

### 4. 去重误判
```bash
# 检查去重记录
cat C:/Users/zyd523/.workbuddy/data/pdf_wechat/processed.json
```

---

## 维护操作

### 重置去重记录
```bash
# 备份当前记录
cp processed.json processed_backup.json

# 清空记录启动 fresh
echo '{}' > processed.json
```

### 修改每日限制
```python
# 编辑 factory.py 第10行
"daily_limit": 5,  # 改为所需数量
```

### 更新自动化时间
```bash
automation_update --mode update --id "automation-1779786941899" --rrule "FREQ=DAILY;BYHOUR=14;BYMINUTE=0"
```

---

## 成功标准

✅ **当日处理量**：不超过5篇（可配置）  
✅ **去重准确**：相同文件不会重复处理  
✅ **失败不影响**：单个失败不中断整个流程  
✅ **延伸阅读**：文末自动添加3个月内相关文章  
✅ **去AI味**：文章写作风格自然，无AI指纹  
✅ **定时稳定**：每天9:00自动执行，工作区清理完毕