# SimilarWeb Analysis Plugin

从 SimilarWeb Pro 自动提取指定域名的网站表现概览和外链来源数据。

## 方案选择

| 方案 | 命令 | 说明 |
|------|------|------|
| **v2（推荐）** | `/fetch_website_flow_analysis_v2` | API + 代理 IP，快速稳定 |
| v1（备用） | `/fetch_website_flow_analysis` | dev-browser 浏览器自动化 |

## 功能

- **网站表现概览**: 总访问量、排名、参与度、地理分布、流量来源渠道、搜索、外链、社交等，输出为 `overview.md`
- **外链来源表格**: Top 100 外链来源域名、行业、排名、流量份额、变动，输出为 `referrals_incoming.csv`

## 环境变量配置

首次使用前，必须配置以下 5 个环境变量。在 `~/.claude/.env` 或 shell profile（`~/.zshrc` / `~/.bashrc`）中添加：

```bash
# 青云代理 IP 池
export PROXY_KEY="你的代理产品Key"
export PROXY_AUTH_KEY="你的AuthKey"
export PROXY_AUTH_PWD="你的AuthPwd"
export PROXY_API_URL="https://overseas.proxy.qg.net/get"

# SimilarWeb cookie 文件路径
export SW_COOKIE_FILE="/path/to/sw_cookies.txt"
```

| 环境变量 | 说明 |
|---------|------|
| `PROXY_KEY` | 青云代理产品 Key |
| `PROXY_AUTH_KEY` | 青云代理认证 AuthKey |
| `PROXY_AUTH_PWD` | 青云代理认证 AuthPwd |
| `PROXY_API_URL` | 青云代理 API 地址 |
| `SW_COOKIE_FILE` | SimilarWeb cookie 文件路径 |

## 前置依赖

### v2 方案（API + 代理）

- Python 3.10+，`requests` 包已安装
- 环境变量已配置（见上方）
- 有效的 SimilarWeb cookie（运行 `/sw_login` 获取）

### v1 方案（浏览器）

- [dev-browser](https://github.com/SawyerHood/dev-browser) 插件已安装
- 手动登录 SimilarWeb Pro

## 使用方法

### v2 方案（推荐）

```bash
# 首次使用: 登录并获取 cookie
/similarweb_analysis:sw_login

# 检查 cookie 是否有效
/similarweb_analysis:sw_check_cookie

# 获取数据
/similarweb_analysis:fetch_website_flow_analysis_v2 stackoverflow.com
```

### v1 方案（备用）

```bash
/similarweb_analysis:fetch_website_flow_analysis stackoverflow.com
```

## 输出

数据保存在 `web_data/{domain}/` 目录下:

### v2 输出
- `overview.md` — 网站表现概览（Markdown 格式）
- `referrals_incoming.csv` — 外链来源表格（CSV 格式）
- `raw_api_data.json` — 11 个 API 的原始 JSON 数据

### v1 输出
- `overview.md` — 网站表现概览（Markdown 格式）
- `referrals_incoming.csv` — 外链来源表格（CSV 格式）
- `overview_raw.txt` — 概览页原始文本
- `referrals_raw.txt` — 外链页原始文本

## 辅助命令

| 命令 | 说明 |
|------|------|
| `/similarweb_analysis:sw_login` | 登录 SimilarWeb 并刷新 cookie |
| `/similarweb_analysis:sw_check_cookie` | 检查 cookie 有效性 |

---

## OpenClaw 平台支持

本插件同时支持 Claude Code 和 OpenClaw 两个平台，共享 `scripts/` 和 `skills/` 目录。

### OpenClaw 安装

1. 将插件目录加入 OpenClaw 的插件加载路径：

```bash
openclaw config set plugins.load.paths '["~/Claude/web_analysis_marketplace/plugins/similarweb_analysis"]'
```

2. 配置代理凭据（通过 OpenClaw plugin config）：

```bash
openclaw config set plugins.entries.similarweb-analysis.config.proxyKey "你的代理产品Key"
openclaw config set plugins.entries.similarweb-analysis.config.proxyAuthKey "你的AuthKey"
openclaw config set plugins.entries.similarweb-analysis.config.proxyAuthPwd "你的AuthPwd"
```

3. 确认插件已加载：

```bash
openclaw plugins list
# 应看到 similarweb-analysis
```

### OpenClaw 注册的工具

| 工具 | 说明 |
|------|------|
| `similarweb_fetch` | 获取域名流量数据（调用 `sw_fetch.py`） |
| `similarweb_check_cookie` | 检查 cookie 有效性（调用 `sw_check_cookie.py`） |

`sw_login` 需要终端交互输入（Google 邮箱、密码、验证码），无法作为非交互式 OpenClaw 工具运行。Cookie 过期时请在终端直接运行 `python3 scripts/sw_login.py`。

### OpenClaw 使用示例

在 OpenClaw 对话中，agent 会自动调用注册的工具：

```
> 帮我获取 github.com 的流量数据
# agent 自动调用 similarweb_fetch(domain: "github.com")
```
