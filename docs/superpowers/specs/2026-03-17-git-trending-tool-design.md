# Git 热点技术情报系统 — 设计文档

## 概述

每日自动爬取 GitHub + Gitee 热点内容，通过 LLM 分析生成结构化报告，推送至 Telegram。数据存入 SQLite 支持历史查询和趋势分析。

## 目标

建立个人技术情报系统，核心价值不是信息搬运，而是：
- **全量有序**：所有热点按领域分组呈现，不遗漏、不过滤
- **LLM 分析**：每个项目附带一句话定位和"为什么值得关注"
- **趋势洞察**：周报汇总持续趋势，过滤一日噪音

## 数据源

### 平台
- **GitHub**：全球最大开源社区，反映全球技术趋势
- **Gitee**：国内最大代码托管平台，反映国内开发者关注方向

### 采集维度

| 维度 | GitHub | Gitee |
|------|--------|-------|
| Trending Repos | 爬取 github.com/trending（无官方 API） | Gitee API /v5/projects/trending |
| 热门开发者 | 爬取 github.com/trending/developers | 从热门项目提取作者 |
| Topics | GitHub API /search/repositories 按 topic + stars 排序 | 按标签搜索 |
| 热门 Issues | GitHub API /search/issues 按 reactions 排序 | API 搜索按评论数排序 |

### 采集频率
- 每天 UTC 0:00（北京时间 8:00）运行一次
- GitHub Actions cron 触发

### 反爬策略
- GitHub API：Personal Access Token，速率限制 5000 次/小时
- GitHub Trending 页面：httpx + BeautifulSoup 解析 HTML
- Gitee：API Token 认证
- 请求间隔 1-2 秒
- GitHub Trending HTML 解析需加结构验证，DOM 变更时触发告警而非静默失败
- Gitee Trending 接口需在实现时验证，若无专用 API 则改用搜索接口（按 stars + 创建时间排序）

## 统一信号模型

所有数据源输出统一格式，方便后续扩展新源：

```python
@dataclass
class Signal:
    source: str          # "github" / "gitee"
    source_id: str       # 唯一标识，如 "github:repo:owner/name" / "github:issue:owner/name#123"
    signal_type: str     # "trending_repo" / "trending_dev" / "topic" / "hot_issue"
    title: str
    url: str
    description: str
    metadata: dict       # stars, forks, language, stars_today, author_info...
    raw_content: str     # README 内容（截取前 3000 字符，用于 LLM 分析）
    collected_at: datetime
```

新增数据源 = 新增一个爬虫文件，输出 Signal 列表，其他代码不需要修改。

## LLM 分析层

### 分析流程

1. **领域分类**（批量）：LLM 将所有项目归入领域（AI/LLM、Web、数据库等），纯动态分类，不预设固定类别
2. **逐项分析**：读取 README，生成一句话定位、为什么值得关注、趋势判断
3. **全局概览**：输入当天所有分析结果，生成"今天技术世界发生了什么"概览段落
4. **周报**（每周一额外执行）：输入本周 7 天数据，生成趋势总结

### LLM 选型
- 日常分析：Claude Haiku — 便宜快速，摘要分类足够
- 周报总结：Claude Sonnet — 更强的归纳和洞察能力
- 通过环境变量配置模型，可随时切换

### Prompt 管理
- 所有 prompt 放在 `prompts/` 目录，Markdown 文件管理
- 方便迭代调优，不硬编码在代码里

### 成本估算
- README 截取前 3000 字符控制 token 消耗
- 每月约 $5-9（日常分析 ~$4-7 + 分类/概览 ~$0.3 + 周报 ~$0.5）

## 数据存储

### SQLite

```sql
-- 原始信号（同一项目每天一条记录，支持追踪连续上榜）
CREATE TABLE signals (
    id INTEGER PRIMARY KEY,
    source TEXT,
    source_id TEXT,        -- 唯一标识如 "github:repo:owner/name"
    signal_type TEXT,
    title TEXT,
    url TEXT,
    description TEXT,
    metadata JSON,
    raw_content TEXT,      -- README 截取前 3000 字符
    collected_at DATE,
    UNIQUE(source_id, collected_at)  -- 同一项目同一天只存一条
);

-- LLM 分析结果
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY,
    signal_id INTEGER REFERENCES signals(id) UNIQUE,  -- 每条信号只分析一次
    domain TEXT,
    summary TEXT,
    insight TEXT,
    trend_status TEXT,
    analyzed_at DATETIME
);

-- 报告存档
CREATE TABLE reports (
    id INTEGER PRIMARY KEY,
    report_type TEXT,      -- daily / weekly
    content TEXT,
    generated_at DATETIME
);
```

### 持久化策略
- 使用 GitHub Releases 存储 SQLite 文件（非 git commit），避免仓库体积膨胀
- 每次运行：下载最新 release 中的 db → 写入新数据 → 上传新 release
- 备选方案：若 release 方式不稳定，可切换到 GitHub Actions artifact 或 S3

### 选型理由
- 单文件，无需数据库服务器
- 日均几十条数据，无性能问题
- 全量保留，不做清理，数据积累本身是价值

## 推送与报告

### Telegram Bot

**日报（每天 8:00）：**
- 概览段落：一段话概括今天技术世界的全景
- 按领域分组：每个领域下列出所有项目，附 LLM 分析
- 星级标注：⭐⭐⭐ 强烈推荐 / ⭐⭐ 值得了解 / ⭐ 常规热门（LLM 综合判断）
- 异常信号：增长曲线异常的项目单独标注
- Web 详情链接（V2）

**周报（每周一 8:00）：**
- 本周全景总结
- 持续霸榜项目（连续 3 天+）
- 新兴信号（某领域多个新项目同时出现）
- 领域热度排行（可视化柱状图）
- 退热项目（上周热门本周消失）

**消息格式：**
- HTML 模式（排版控制更精确）
- 4096 字符限制，超长拆成多条顺序发送

## 项目结构

```
git-trending/
├── .github/
│   └── workflows/
│       ├── daily.yml          # 每日爬取 + 分析 + 推送
│       └── weekly.yml         # 每周一周报（不重新爬取，仅分析过去 7 天已有数据）
├── crawlers/
│   ├── base.py                # Signal 数据模型
│   ├── github_trending.py     # GitHub Trending 爬虫
│   ├── github_api.py          # GitHub API（Issues/Topics）
│   └── gitee.py               # Gitee 爬虫
├── analyzer/
│   ├── llm.py                 # LLM 调用封装（Claude API）
│   ├── classifier.py          # 领域分类
│   └── reporter.py            # 日报/周报生成
├── storage/
│   └── db.py                  # SQLite 操作封装
├── notify/
│   └── telegram.py            # Telegram Bot 推送
├── prompts/
│   ├── classify.md            # 分类 prompt
│   ├── analyze.md             # 单项分析 prompt
│   ├── daily_overview.md      # 日报概览 prompt
│   └── weekly_report.md       # 周报 prompt
├── data/
│   └── trending.db            # SQLite 数据库文件
├── config.py                  # 配置（Token 等从环境变量读）
├── main.py                    # 入口：爬取 → 分析 → 存储 → 推送
└── requirements.txt
```

### 依赖
- `httpx` — HTTP 请求
- `beautifulsoup4` — HTML 解析
- `anthropic` — Claude API
- `python-telegram-bot` — Telegram 推送
- `sqlite3` — 标准库

### GitHub Actions
- Secrets：`GITHUB_TOKEN`、`GITEE_TOKEN`、`ANTHROPIC_API_KEY`、`TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`
- 数据库通过 GitHub Releases 持久化（不 commit 二进制文件）
- 失败时发 Telegram 告警

## 错误处理

### 流水线策略
- 各爬虫模块独立运行，单个失败不阻塞其他模块
- 部分爬取成功时：正常存储已获取的数据，日报中标注缺失的数据源
- LLM 分析失败时：信号数据照常存储，跳过分析，下次运行时补分析未分析的信号
- Telegram 发送失败时：报告已持久化在 reports 表中，不丢失

### 重试策略
- API 调用失败：指数退避重试 3 次（1s → 2s → 4s）
- GitHub Trending HTML 解析失败：发告警（可能是 DOM 结构变更，需要人工修复爬虫）

### 时区
- 所有内部时间使用 UTC
- Telegram 推送显示北京时间（UTC+8）
- "今日"数据边界：UTC 00:00 ~ 23:59
- 周报边界：周一 UTC 00:00 开始

### Dry-run 模式
- `--dry-run` 参数：跑完全流程但不发送 Telegram、不上传数据库
- 用于本地调试和验证

## 部署策略
- V1：GitHub Actions 全自动，零服务器成本
- V2（需要 Web 界面时）：加 VPS 跑 FastAPI，SQLite 迁移上去

## 未来迭代方向（已验证，待实施）

### V2：多渠道情报聚合
- 加入 Hacker News（性价比最高的第二源）
- 后续可加：Reddit、Twitter/X、Dev.to/Medium、ArXiv
- 话题聚类：同一技术跨源归拢
- 架构已预留：统一 Signal 模型

### V3：智能分析升级
- Stars 增长加速度追踪
- 连锁信号识别
- 知名开发者动作监控
- 技术雷达自动生成（Adopt / Trial / Assess / Hold）

### V3+：个性化（智能排序，非过滤）
- 用户画像 + Telegram 👍/👎 反馈学习
- LLM 相关性评分
- 全量不删减，只影响排序和概览侧重点
