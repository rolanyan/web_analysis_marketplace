---
name: fetch_website_flow_analysis_v2
description: Fetch website traffic data from SimilarWeb via API with proxy IP rotation.
  Trigger phrases include "fetch similarweb data", "analyze website traffic",
  "get referral sources", "similarweb analysis".
---

# SimilarWeb 网站流量分析（v2 — API + 代理方案）

通过 SimilarWeb 内部 API + 青云代理 IP 获取网站流量数据。
比 v1（dev-browser）方案更快、更稳定、更不容易被封。

## 前置条件

- Python 3.10+ 已安装，`requests` 包可用
- 环境变量已配置: `PROXY_KEY`, `PROXY_AUTH_KEY`, `PROXY_AUTH_PWD`（详见 README）
- 有效的 SimilarWeb cookie 文件（过期时运行 `/sw_login` 刷新）

## 参数

- `domain`: 目标域名（如 `github.com`），从命令参数中获取
- `--no-proxy`: 可选，不使用代理直接请求（本地测试用）

## 执行流程

### Step 1: 准备工作

1. 从参数中解析域名，如果未提供则询问用户
2. 确定脚本目录路径。查找本插件的 scripts 目录，可能在以下位置之一：
   - `~/.claude/plugins/cache/*/similarweb_analysis/scripts`
   - `~/Claude/web_analysis_marketplace/plugins/similarweb_analysis/scripts`
   - `~/Claude/claude_code_marketplace/plugins/similarweb_analysis/scripts`
   - `~/.openclaw/extensions/similarweb-analysis/scripts`
   - `~/.openclaw/extensions/*/similarweb_analysis/scripts`

```bash
# 找到插件的 scripts 目录
SCRIPT_DIR="<找到的 scripts 目录绝对路径>"
```

3. 检查环境变量是否已配置（除非使用 `--no-proxy`）：

```bash
python3 -c "import os; [print(f'  {k}: {'已设置' if os.environ.get(k) else '未设置'}') for k in ['PROXY_KEY','PROXY_AUTH_KEY','PROXY_AUTH_PWD']]"
```

如果缺少环境变量，提示用户参考 README 的「环境变量配置」章节，并停止执行。

4. 检查 cookie 有效性：

```bash
python3 "$SCRIPT_DIR/sw_check_cookie.py"
```

如果 cookie 无效，提示用户运行 `/sw_login` 刷新，并停止执行。

### Step 2: 获取数据

运行数据获取脚本：

```bash
python3 "$SCRIPT_DIR/sw_fetch.py" "{domain}"
```

或不用代理：

```bash
python3 "$SCRIPT_DIR/sw_fetch.py" "{domain}" --no-proxy
```

脚本会：
- 从青云代理池提取一个海外住宅 IP
- 通过代理调用 SimilarWeb 11 个数据 API
- 遇到 403/SSL 错误自动换 IP 重试
- 将原始 JSON 保存到 `web_data/{domain}/raw_api_data.json`
- 将格式化的 overview 保存到 `web_data/{domain}/overview.md`
- 将外链数据保存到 `web_data/{domain}/referrals_incoming.csv`

**检查点**: 确认输出文件已生成。如果脚本报错 403 且 cookie 未过期，可能是代理 IP 被封，
脚本会自动换 IP 重试（最多 3 次）。

### Step 3: 汇报结果

读取生成的文件，向用户报告：
- overview.md 的关键数据摘要（总访问量、排名、设备分布、流量来源）
- referrals_incoming.csv 的记录数和 Top 5 来源
- 文件保存路径

## 异常处理

| 异常 | 处理方式 |
|------|---------|
| cookie 无效/过期 | 提示用户运行 `/sw_login` |
| 代理通道占用 | 脚本自动等待重试（最多 3 次，每次 30s） |
| 代理 IP 被 SimilarWeb 封 (403) | 自动换 IP 重试 |
| SSL/连接错误 | 自动换 IP 重试 |
| 代理 API 不可用 | 提示用户加 `--no-proxy` 直连（注意封 IP 风险） |
| Python/requests 未安装 | 提示用户安装 |
