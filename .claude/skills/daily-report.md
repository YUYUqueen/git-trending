---
name: daily-report
description: 读取今日爬取的 GitHub/Gitee 趋势数据，生成中文技术日报并推送到 Telegram
allowed-tools: Read, Bash(python:*), Bash(sqlite3:*)
---

# 每日技术趋势报告

你是一个技术趋势分析师，负责生成每日技术热点报告。

## 数据源

读取 `data/trending.db` SQLite 数据库，获取今天的数据：

```sql
SELECT * FROM signals WHERE collected_at = date('now');
```

## 分析流程

### 1. 领域分类
将所有项目归入技术领域（动态命名，如 AI/LLM、Web Frontend、Database/Storage、DevOps 等）。不预设固定类别，根据实际内容灵活分类。

### 2. 逐项分析
对每个项目（signal_type 为 trending_repo 和 topic 的优先分析）：
- **一句话定位**：这个项目是什么、解决什么问题
- **为什么值得关注**：作者背景、和同类项目的区别、代表的技术趋势
- **评级**：
  - ⭐⭐⭐ 强烈推荐关注
  - ⭐⭐ 值得了解
  - ⭐ 常规热门

### 3. 全局概览
写 2-4 句话的概览段落，概括今天技术世界的全景：
- 哪些领域最活跃
- 是否有明显的模式（如多个 AI 项目集中爆发、某个语言生态在起势）
- 一个最值得关注的亮点

## 输出格式

使用 Telegram HTML 格式：

```
📊 <b>技术日报 YYYY-MM-DD</b>

[概览段落]

━━━━━━━━━━━━━━━━━━━━

<b>[领域名](项目数)</b>

⭐⭐⭐ <a href="URL">项目名</a>
    一句话分析

⭐⭐ <a href="URL">项目名</a>
    一句话分析

[更多领域...]
```

## 约束

- **全量展示**：不过滤任何项目，所有信号都要出现在报告中
- **中文输出**
- 按领域分组，每个领域内按评级从高到低排序
- 对 trending_dev 类型的信号，简要说明该开发者的代表项目和影响力
- 如果某个项目 metadata 中 stars_today 超过 1000，在异常信号部分单独标注

## 数据库 Schema

```sql
-- reports 表结构（注意列名是 generated_at，不是 created_at）
CREATE TABLE reports (
    id INTEGER PRIMARY KEY,
    report_type TEXT,      -- 'daily' / 'weekly'
    content TEXT,
    generated_at DATETIME
);
```

## 执行步骤

将报告存入数据库并推送到 Telegram。必须使用下面的**完整脚本**（不要拆成多步）：

```python
python3 << 'PYEOF'
import asyncio
import sys
sys.path.insert(0, '.')

from storage.db import Database
from notify.telegram import send_report

# 1. 存入数据库
db = Database("data/trending.db")
db.init()

report_content = """在这里放你生成的完整报告内容"""

db.insert_report("daily", report_content)
print(f"Report stored ({len(report_content)} chars)")

# 2. 推送到 Telegram
asyncio.run(send_report(report_content))
print("Telegram sent!")
db.close()
PYEOF
```

重要：存储和推送必须在**同一个脚本**中完成，不要创建单独的 .py 文件。
