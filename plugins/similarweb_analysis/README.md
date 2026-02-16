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

v2 方案需要配置以下环境变量。在 `~/.claude/.env` 或 shell profile（`~/.zshrc` / `~/.bashrc`）中添加：

```bash
# 青云代理 IP 池（v2 必需）
export PROXY_KEY="你的代理产品Key"
export PROXY_AUTH_KEY="你的AuthKey"
export PROXY_AUTH_PWD="你的AuthPwd"

# 可选: 代理 API 地址（默认 https://overseas.proxy.qg.net/get）
# export PROXY_API_URL="https://overseas.proxy.qg.net/get"

# 可选: 自定义 cookie 文件路径（默认在插件 data/ 目录下）
# export SW_COOKIE_FILE="/path/to/sw_cookies.txt"
```

| 环境变量 | 必需 | 说明 |
|---------|------|------|
| `PROXY_KEY` | v2 必需 | 青云代理产品 Key |
| `PROXY_AUTH_KEY` | v2 必需 | 青云代理认证 AuthKey |
| `PROXY_AUTH_PWD` | v2 必需 | 青云代理认证 AuthPwd |
| `PROXY_API_URL` | 可选 | 代理 API 地址，默认海外住宅池 |
| `SW_COOKIE_FILE` | 可选 | 自定义 cookie 文件路径 |

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
/sw_login

# 检查 cookie 是否有效
/sw_check_cookie

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
| `/sw_login` | 登录 SimilarWeb 并刷新 cookie |
| `/sw_check_cookie` | 检查 cookie 有效性 |
