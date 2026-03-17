# Git Trending Intelligence Tool

每日自动爬取 GitHub + Gitee 热点内容的技术情报系统。

## 项目结构

- `crawlers/` — 数据爬虫（GitHub Trending、GitHub API、Gitee）
- `storage/db.py` — SQLite 数据库操作
- `notify/telegram.py` — Telegram Bot 推送
- `config.py` — 从环境变量和 .env 文件加载配置
- `main.py` — 爬虫入口（`python main.py crawl`）

## 数据库

SQLite 文件在 `data/trending.db`，三张表：
- `signals` — 原始爬取数据（每天每个项目一条）
- `analyses` — LLM 分析结果
- `reports` — 生成的日报/周报存档

## 关键约束

- 所有报告使用**中文**输出
- 报告必须**全量展示**所有项目，不做过滤
- Telegram 消息使用 **HTML** 格式，单条上限 4096 字符
- 时区：内部 UTC，显示北京时间（UTC+8）

## 可用工具

- `storage.db.Database` — 数据库 CRUD
- `notify.telegram.send_report(text)` — 发送 Telegram 消息
- `notify.telegram.send_alert(text)` — 发送告警消息
