---
name: fetch_website_flow_analysis_v2
description: This skill should be used when the user asks to "fetch similarweb data",
  "analyze website traffic", "get referral sources", "similarweb analysis", or wants
  to extract SimilarWeb traffic data for a domain via API with proxy IP rotation.
---

# SimilarWeb Traffic Analysis (v2 — API + Proxy)

Extract website traffic data from SimilarWeb internal APIs with Qingyun proxy IP rotation.
Faster and more stable than v1 (dev-browser).

## Prerequisites

- Python 3.10+ with `requests` package
- All environment variables configured: `PROXY_BIZ_ID`, `PROXY_AUTH_KEY`, `PROXY_AUTH_PWD`, `PROXY_API_URL`, `SW_COOKIE_FILE` (see README)
- Valid SimilarWeb cookie (run `/sw_login` to refresh when expired)

## Parameters

- `domain`: Target domain (e.g. `github.com`), from command arguments
- `--no-proxy`: Optional, skip proxy and connect directly (for local testing)

## Workflow

### Step 1: Preparation

1. Parse domain from arguments. If not provided, ask the user.

2. Check environment variables (unless using `--no-proxy`):

```bash
python3 -c "import os; [print(f'  {k}: {'set' if os.environ.get(k) else 'NOT SET'}') for k in ['PROXY_BIZ_ID','PROXY_AUTH_KEY','PROXY_AUTH_PWD','PROXY_API_URL','SW_COOKIE_FILE']]"
```

All 5 must be set. If any is missing, direct the user to README's environment variable section and stop.

3. Check cookie validity:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sw_check_cookie.py"
```

If cookie is invalid, direct user to run `/sw_login` and stop.

### Step 2: Fetch data

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sw_fetch.py" "{domain}"
```

Or without proxy:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sw_fetch.py" "{domain}" --no-proxy
```

The script will:
- Extract an overseas residential IP from Qingyun proxy pool
- Call 11 SimilarWeb data APIs through the proxy
- Auto-retry with new IP on 403/SSL errors
- Save raw JSON to `web_data/{domain}/raw_api_data.json`
- Save formatted overview to `web_data/{domain}/overview.md`
- Save referral data to `web_data/{domain}/referrals_incoming.csv`

**Checkpoint**: Confirm output files are generated. On 403 errors with valid cookie, the script auto-retries with new IP (up to 3 times).

### Step 3: Report results

**Important: Control context size to avoid the 20MB API request limit.**

- Read `overview.md` and present key metrics summary (visits, ranks, device split, traffic sources)
- Read only the **first 6 lines** of `referrals_incoming.csv` (header + Top 5) and report total row count
- **Never read `raw_api_data.json`** — it contains raw JSON from 11 APIs and may be several MB; loading it will bloat the conversation context
- Report file save paths to the user

## Error Handling

| Error | Resolution |
|-------|-----------|
| Cookie invalid/expired | Direct user to run `/sw_login` |
| Proxy channel busy | Script auto-retries (up to 3 times, 30s apart) |
| Proxy IP blocked by SimilarWeb (403) | Auto-retry with new IP |
| SSL/connection error | Auto-retry with new IP |
| Proxy API unavailable | Suggest `--no-proxy` flag (note IP ban risk) |
| Python/requests not installed | Direct user to install |
