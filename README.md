# 📊 LLM Usage Collector

> 🧮 **把散落在 11 个 AI Agent 里的 Token 账单，收成一张终端仪表盘**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![rich](https://img.shields.io/badge/UI-rich-8A2BE2)](https://github.com/Textualize/rich)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](.)
[![Agents](https://img.shields.io/badge/agents-11%20covered-orange)](#-支持的-agent)

---

## ✨ 简介

LLM Usage Collector 是一款本地 AI Agent 用量聚合工具，自动扫描本机所有 AI 编程助手的 Token 调用数据，生成统一的终端报表。

**支持的 Agent** 🤖

| Agent | 数据格式 | 存储位置 |
|-------|---------|---------|
| 🟠 Claude Code | JSONL | `~/.claude/projects/**/*.jsonl` |
| 🟣 Pi Agent | JSONL | `~/.pi/agent/sessions/**/*.jsonl` |
| 🍍 Oh My Pi (omp) | JSONL | `~/.omp/agent/sessions/**/*.jsonl` |
| 🔶 Qoder | JSONL | `~/.qoder-cn/projects/**/*.jsonl` |
| 🔵 Hermes 桌面版 | SQLite | `%LOCALAPPDATA%\Hermes Agent CN Desktop\data\hermes-home\state.db` |
| 🩵 Hermes 终端版 | SQLite | `%LOCALAPPDATA%\hermes\state.db` |
| 🟢 OpenCode | SQLite | `~/.local/share/opencode/opencode.db` |
| 🟡 ZCode（智谱） | SQLite | `~/.zcode/cli/db/db.sqlite` |
| ⚫ Codex | JSONL | `~/.codex/sessions/**/rollout-*.jsonl` |
| 🔴 MiMo Desktop | SQLite | `~/.local/share/mimocode/mimocode.db` |
| 🐳 DSH（DeepSeek Harness） | JSON (+zstd 会话日志) | `~/.dsh/storages/session_projcache.json`、`~/.dsh/sessions/**/session.jsonl.zstd` |
| 🟦 Copilot CLI | JSONL | `~/.copilot/session-state/**/events.jsonl` |

---

## 🚀 安装

### 📦 前置条件

- 🐍 Python 3.10+
- 🎨 rich 库

### 🛠️ 安装步骤

```bash
cd LLM-Usage-Collector
pip install -r requirements.txt
```

无需其他配置，首次运行即自动扫描全部历史数据。

---

## 🎮 使用方法

### 🏁 基本用法

```bash
python main.py
```

运行后自动扫描所有 Agent，输出终端报表。

### ⌨️ 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--json` | 输出 JSON 格式（适合脚本处理） | `python main.py --json` |
| `--agent <名称>` | 按 Agent 名称过滤 | `python main.py --agent claude` |
| `--days <天数>` | 指定每日趋势的天数（默认 30） | `python main.py --days 7` |

### 🔍 过滤示例

```bash
# 只看 Claude Code
python main.py --agent claude

# 只看 ZCode
python main.py --agent zcode

# 只看 Hermes（桌面+终端合并）
python main.py --agent hermes

# 最近 7 天趋势
python main.py --days 7

# JSON 输出到文件
python main.py --json > usage_report.json
```

---

## 📈 报表说明

### 🗂️ 总览卡片

```
┌─────────────────┐  ┌─────────────────┐
│ 1773.8M         │  │ 488.0M / 7.7M   │
│ Total Tokens    │  │ Input / Output  │
└─────────────────┘  └─────────────────┘
┌─────────────────┐  ┌─────────────────┐
│ 1276.4M / 1.7M  │  │ $16.98          │
│ Cache R / W     │  │ Total Cost      │
└─────────────────┘  └─────────────────┘
```

| 卡片 | 含义 |
|------|------|
| 🧮 Total Tokens | 所有 Agent 的 Token 总量（含 Cache） |
| 📥📤 Input / Output | 新输入 / 模型输出 |
| 📦 Cache R / W | 缓存读取 / 缓存写入 |
| 💵 Total Cost | 估算总费用（美元） |
| 🔁 Requests | 总请求次数 |
| 💬 Sessions | 总会话数 |
| 🤖 Agents | Agent 数量 |
| ⏳ Time Span | 数据时间跨度 |

### 🤖 By Agent 表格

按 Agent 汇总的 Token 用量、费用、请求数。Hermes 分为 Desktop 和 Terminal 两行。

### 🧠 By Model 表格

按模型名称汇总的 Top 15，包含 Token 用量、费用、请求数。

### 📅 Daily Trend

最近 N 天（默认 14 天）的每日用量柱状图，包含 Token 量、费用、请求数。

---

## 💰 费用说明

| Agent | 费用数据来源 | 说明 |
|-------|------------|------|
| 🟣 Pi Agent | 本地 `cost.total` | Pi 自带计费，精确 |
| 🍍 Oh My Pi (omp) | 本地 `usage.cost.total` | MiMo 端点 `models.yml` 配 `cost: 0`，记 0；自定义端点填了价格即可累计 |
| 🔶 Qoder | 无 | 积分（credits）计费非美元；qfmodel 网关 token 常回传 0，Cost 显示 `-`，请求数正常 |
| 🟢 OpenCode | 本地 `session.cost` | OpenCode 自带计费 |
| 🔵 Hermes | `estimated_cost_usd` | Hermes 估算，部分为 0（免费套餐） |
| 🟠 Claude Code | 无 | 通过中转站调用，无本地费用记录 |
| 🟡 ZCode | 无 | 智谱 CodingPlan 免费额度内 |
| ⚫ Codex | 无 | 本地无费用记录，显示 `-` |
| 🐳 DSH | 无 | DeepSeek 官方额度，本地不记费用 |
| 🟦 Copilot CLI | 无 | 订阅额度（premium requests），本地不记美元费用 |

费用显示 `-` 表示该 Agent 无本地计费数据。

---

## 🗣️ 在 Agent 中调用

本机 Agent 已通过 skill `llm-usage` / AGENTS.md / 记忆桥接统一接入。

### 🟠 Claude Code

```
/usage
```

或说：「查看用量统计」

### 🟢 OpenCode

说：「查看用量统计」「usage」「token 用量」

### 🔵 Hermes

说：「查看各 Agent 模型调用用量」

### ⚫ Codex / 🟡 ZCode / 🔴 MiMo / 🐳 DSH / 🟦 Copilot / 🍍 OMP / 🔶 Qoder

说：「查看用量统计」，Agent 按全局指令执行 `main.py`。

---

## 🧾 JSON 输出格式

```json
{
  "totals": {
    "total_input": 487512098,
    "total_output": 7714591,
    "total_cache_read": 1275984237,
    "total_tokens": 1772918099,
    "total_cost": 16.98,
    "total_requests": 4062,
    "unique_sessions": 295
  },
  "by_agent": {
    "Claude Code": { ... },
    "Pi Agent": { ... },
    "Hermes (Hermes-Desktop)": { ... },
    "OpenCode": { ... },
    "ZCode": { ... }
  },
  "by_model": { ... },
  "by_date": { ... }
}
```

可用于接入 Grafana、自建仪表盘等。

---

## 🗄️ 数据保留说明

| Agent | 默认保留策略 | 影响 |
|-------|------------|------|
| 🟠 Claude Code | **30 天后删除** session 文件 | 历史数据可能不完整 |
| 🟣 Pi Agent | 永久保留 | 完整 |
| 🍍 Oh My Pi (omp) | 永久保留（JSONL） | 完整 |
| 🔶 Qoder | 永久保留（JSONL） | 完整 |
| 🔵 Hermes | 永久保留（SQLite） | 完整 |
| 🟢 OpenCode | 永久保留（SQLite） | 完整 |
| 🟡 ZCode | 永久保留（SQLite） | 完整 |
| ⚫ Codex | 永久保留（JSONL） | 完整 |
| 🐳 DSH | 永久保留（projcache + 会话日志） | 完整 |
| 🟦 Copilot CLI | 永久保留（events.jsonl，仅含已 shutdown 的会话汇总） | 完整 |

**建议**：如需保留 Claude Code 历史，在 `~/.claude/settings.json` 中设置：

```json
{
  "cleanupPeriodDays": 9999999999
}
```

---

## ❓ 常见问题

### Q: 报错 `No usage data found`

所有 Agent 的本地数据目录均不存在。确认各 Agent 已安装并至少运行过一次。

### Q: Hermes 显示 0 条记录

检查 `%LOCALAPPDATA%\Hermes Agent CN Desktop\data\hermes-home\state.db` 是否存在。终端版检查 `%LOCALAPPDATA%\hermes\state.db`。

### Q: ZCode 显示 0 条记录

检查 `~/.zcode/cli/db/db.sqlite` 是否存在。ZCode 需至少完成过一次对话。

### Q: 费用显示全是 `-`

大部分 Agent（Claude Code、ZCode、Hermes）通过中转站或免费套餐调用，本地不记录费用。Pi 和 OpenCode 有精确费用。

### Q: 想定期自动汇总

可用 Windows Task Scheduler 设置定时任务：

```powershell
# 每天 23:00 自动跑一次，结果保存到 reports\
powershell -NoProfile -ExecutionPolicy Bypass -File .\daily-report.ps1
# 或注册计划任务（在项目目录下执行）：
schtasks /create /tn "LLM-Usage-Daily" /tr "%CD%\daily-report.cmd" /sc daily /st 23:00
```

---

## 🗂️ 项目结构

```
LLM-Usage-Collector/
├── 🚪 main.py           # 入口
├── 🪟 usage.cmd         # Windows 一键启动
├── 💻 usage.ps1         # PowerShell 启动
├── 🌙 daily-report.cmd  # 每日 JSON 报表入口
├── 🌙 daily-report.ps1  # 每日 JSON 报表脚本
├── 📁 reports/          # 定时报表输出
├── 📋 requirements.txt  # 依赖（rich）
├── collectors/
│   ├── 📦 __init__.py
│   ├── 🧱 base.py       # 统一数据模型 UsageRecord
│   ├── 🟠 claude.py     # Claude Code 采集器
│   ├── 🟣 pi.py         # Pi Agent 采集器
│   ├── 🔵 hermes.py     # Hermes 采集器（桌面+终端）
│   ├── 🟢 opencode.py   # OpenCode 采集器
│   ├── 🟡 zcode.py      # ZCode（智谱）采集器
│   ├── ⚫ codex.py      # Codex 采集器
│   ├── 🔴 mimo.py       # MiMo Desktop 采集器
│   ├── 🐳 dsh.py        # DSH（DeepSeek Harness）采集器
│   ├── 🟦 copilot.py    # GitHub Copilot CLI 采集器
│   ├── 🍍 omp.py        # Oh My Pi (omp) 采集器
│   └── 🔶 qoder.py      # Qoder（阿里）采集器
├── 🧩 aggregator.py     # 聚合引擎
└── 🎨 display.py        # Rich 终端报表
```

---

## 🧩 扩展新 Agent

在 `collectors/` 下新建文件，继承 `UsageRecord` 数据模型，实现 `collect()` 方法返回 `List[UsageRecord]`：

```python
from .base import UsageRecord

class NewAgentCollector:
    name = "NewAgent"

    def collect(self) -> list[UsageRecord]:
        records = []
        # 解析你的数据源
        records.append(UsageRecord(
            agent=self.name,
            model="model-name",
            timestamp=datetime.now(),
            input_tokens=12345,
            output_tokens=6789,
        ))
        return records
```

然后在 `collectors/__init__.py` 和 `main.py` 中注册即可。

---

## 📄 License

[MIT](./LICENSE) © Dream22180971
