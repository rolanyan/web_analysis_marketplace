# Web Analysis Marketplace

A plugin marketplace for automated website traffic data extraction. Works with both **Claude Code** and **OpenClaw**.

## What It Does

Automatically fetches website traffic data from SimilarWeb Pro — including visits, rankings, engagement metrics, geographic distribution, traffic sources, and top referral domains.

**Example**: run `/fetch_website_flow_analysis_v2 github.com` and get a structured overview + referral CSV in seconds.

## Quick Start

### Claude Code

```bash
# 1. Install the marketplace and plugin
/plugin marketplace add rolanyan/web_analysis_marketplace
/plugin install similarweb_analysis@rolanyan/web_analysis_marketplace

# 2. Restart Claude Code, then login to SimilarWeb
/similarweb_analysis:sw_login

# 3. Configure all environment variables (see "Environment Variables" section below)

# 4. Fetch data
/similarweb_analysis:fetch_website_flow_analysis_v2 github.com
```

### OpenClaw

```bash
# 1. Install the plugin
cd plugins/similarweb_analysis && npm install

# 2. Add plugin to OpenClaw config
openclaw config set plugins.load.paths '["path/to/web_analysis_marketplace/plugins/similarweb_analysis"]'

# 3. Configure all environment variables (see "Environment Variables" section below)
#    Additionally set OpenClaw plugin config:
openclaw config set plugins.entries.similarweb-analysis.config.proxyKey "$PROXY_KEY"
openclaw config set plugins.entries.similarweb-analysis.config.proxyAuthKey "$PROXY_AUTH_KEY"
openclaw config set plugins.entries.similarweb-analysis.config.proxyAuthPwd "$PROXY_AUTH_PWD"

# 4. Login to SimilarWeb (requires dev-browser, run manually)
python3 plugins/similarweb_analysis/scripts/sw_login.py

# 5. Fetch data (in OpenClaw conversation)
> 帮我获取 github.com 的流量数据
# Agent automatically calls similarweb_fetch(domain: "github.com")
```

## Prerequisites

- **Python 3.10+** with `requests` package
- **SimilarWeb Pro account** (cookie-based authentication)
- **Proxy IP pool** (Qingyun residential proxy recommended for v2)
- **dev-browser plugin** (Claude Code only, required for `/sw_login`)

## Login Flow

The `/sw_login` command (or `python3 scripts/sw_login.py`) handles SimilarWeb authentication:

1. Checks if existing cookie is still valid
2. Launches dev-browser and navigates to SimilarWeb
3. Clicks "Sign in with Google" automatically
4. Prompts you for Google email and password (password input is hidden)
5. Fills Google credentials automatically (two-step: email → password)
6. Handles Google 2FA if needed (falls back to manual browser interaction)
7. Handles SimilarWeb 6-digit device verification code if prompted
8. Extracts and saves the session cookie

Run this whenever API requests start returning 401/403 errors.

## Available Commands

### Claude Code

| Command | Description |
|---------|-------------|
| `/similarweb_analysis:fetch_website_flow_analysis_v2` | Fetch data via API + proxy (recommended) |
| `/similarweb_analysis:fetch_website_flow_analysis` | Fetch data via browser automation (fallback) |
| `/similarweb_analysis:sw_login` | Login to SimilarWeb and refresh cookie |
| `/similarweb_analysis:sw_check_cookie` | Check cookie validity |

### OpenClaw

| Tool | Description |
|------|-------------|
| `similarweb_fetch` | Fetch domain traffic data (calls `sw_fetch.py`) |
| `similarweb_check_cookie` | Check cookie validity (calls `sw_check_cookie.py`) |

Note: `sw_login` requires interactive terminal input (Google credentials, verification code) and cannot run as a non-interactive OpenClaw tool. Run `python3 scripts/sw_login.py` directly in your terminal when cookie expires.

## Output

Data is saved to `web_data/{domain}/`:

| File | Content |
|------|---------|
| `overview.md` | Traffic overview — visits, ranks, engagement, geography, traffic sources |
| `referrals_incoming.csv` | Top 100 referral domains with industry, rank, traffic share |
| `raw_api_data.json` | Raw JSON from 11 SimilarWeb APIs (v2 only) |

## Environment Variables

All 5 variables must be configured before first use. Set them in `~/.claude/.env` or your shell profile (`~/.zshrc` / `~/.bashrc`):

```bash
# Qingyun proxy IP pool
export PROXY_KEY="your-proxy-key"
export PROXY_AUTH_KEY="your-auth-key"
export PROXY_AUTH_PWD="your-auth-pwd"
export PROXY_API_URL="https://overseas.proxy.qg.net/get"

# SimilarWeb cookie file path
export SW_COOKIE_FILE="/path/to/sw_cookies.txt"
```

| Variable | Description |
|----------|-------------|
| `PROXY_KEY` | Qingyun proxy product key |
| `PROXY_AUTH_KEY` | Qingyun proxy auth key |
| `PROXY_AUTH_PWD` | Qingyun proxy auth password |
| `PROXY_API_URL` | Qingyun proxy API endpoint |
| `SW_COOKIE_FILE` | SimilarWeb cookie file path |

For OpenClaw, additionally set via `openclaw config set plugins.entries.similarweb-analysis.config.*`.

## Project Structure

```
web_analysis_marketplace/
├── .claude-plugin/              # Claude Code marketplace metadata
│   ├── plugin.json
│   └── marketplace.json
├── plugins/
│   └── similarweb_analysis/     # SimilarWeb plugin
│       ├── .claude-plugin/      #   Claude Code plugin metadata
│       ├── openclaw.plugin.json #   OpenClaw plugin metadata
│       ├── package.json         #   OpenClaw npm package
│       ├── index.ts             #   OpenClaw tool registration
│       ├── commands/            #   Claude Code slash commands
│       ├── skills/              #   Shared skill definitions
│       ├── scripts/             #   Python scripts (shared by both platforms)
│       │   ├── sw_login.py      #     Google OAuth login + cookie extraction
│       │   ├── sw_fetch.py      #     Data fetching via API + proxy
│       │   ├── sw_check_cookie.py   # Cookie validity check
│       │   ├── similarweb_api.py    # SimilarWeb API client
│       │   └── proxy_pool.py        # Qingyun proxy pool client
│       ├── data/                #   Cookie and logs (gitignored)
│       └── web_data/            #   Fetched data output
├── CLAUDE.md
├── README.md
└── LICENSE (MIT)
```

## License

MIT
