---
name: fetch_website_flow_analysis
description: This skill should be used when the user asks to "fetch similarweb data via browser",
  "analyze website traffic with dev-browser", or needs the browser-based (v1) SimilarWeb
  data extraction method. This is the fallback method when API approach is unavailable.
---

# SimilarWeb Traffic Analysis (v1 — Browser Automation)

Extract website traffic data from SimilarWeb Pro via dev-browser automation.
This is the fallback method; prefer v2 (API + proxy) when available.

## Prerequisites

- dev-browser plugin installed
- User has logged into SimilarWeb Pro via dev-browser (persistent browser session)

## Parameters

- `domain`: Target domain (e.g. `github.com`), from command arguments

## Workflow

### Step 1: Preparation

1. Parse domain from arguments. If not provided, ask the user.

2. Set path variables:

```bash
PLUGIN_SCRIPTS="${CLAUDE_PLUGIN_ROOT}/scripts"
DEV_BROWSER_DIR="$(find ~/.claude/plugins/cache -path "*/dev-browser/*/skills/dev-browser" -type d 2>/dev/null | head -1)"
```

3. Create output directory:

```bash
OUTPUT_DIR="web_data/{domain}"
mkdir -p "$OUTPUT_DIR"
```

4. Ensure dev-browser server is running:

```bash
bash "$PLUGIN_SCRIPTS/ensure_browser.sh" "$DEV_BROWSER_DIR"
```

### Step 2: Extract website performance data

Run fetch_overview.ts to extract page text:

```bash
cd "$DEV_BROWSER_DIR" && npx tsx "$PLUGIN_SCRIPTS/fetch_overview.ts" "{domain}" > "$OUTPUT_DIR/overview_raw.txt" 2>/dev/null
```

Check output file has content (at least 500 characters). If too short, the page may not have loaded or user is not logged in.

Then run parse_overview.ts to convert to Markdown:

```bash
cd "$DEV_BROWSER_DIR" && npx tsx "$PLUGIN_SCRIPTS/parse_overview.ts" "{domain}" "$OUTPUT_DIR/overview_raw.txt" "$OUTPUT_DIR"
```

**Checkpoint**: Confirm `web_data/{domain}/overview.md` is generated with reasonable content. Read and briefly show key metrics to the user.

### Step 3: Extract referral data

Run fetch_referrals.ts to extract page text:

```bash
cd "$DEV_BROWSER_DIR" && npx tsx "$PLUGIN_SCRIPTS/fetch_referrals.ts" "{domain}" > "$OUTPUT_DIR/referrals_raw.txt" 2>/dev/null
```

Then run parse_referrals.ts to convert to CSV:

```bash
cd "$DEV_BROWSER_DIR" && npx tsx "$PLUGIN_SCRIPTS/parse_referrals.ts" "{domain}" "$OUTPUT_DIR/referrals_raw.txt" "$OUTPUT_DIR"
```

**Checkpoint**: Confirm `web_data/{domain}/referrals_incoming.csv` is generated with reasonable row count.

### Step 4: Report results

**Important: Control context size to avoid the 20MB API request limit.**

- Read `overview.md` and present key metrics summary
- Read only the **first 6 lines** of `referrals_incoming.csv` (header + Top 5) and report total row count
- **Never read `raw_api_data.json`** — it may be several MB and will bloat conversation context
- Report file save paths to the user

## Error Handling

| Error | Resolution |
|-------|-----------|
| dev-browser server not running | ensure_browser.sh auto-starts and waits for ready |
| Popup blocking page | Scripts auto-detect and close "Close" buttons |
| Page load timeout or content too short | Retry once (wait 5s), then report and suggest checking login status |
| Not logged into SimilarWeb | Direct user to README's first-login instructions |
| Extracted data empty | Raw text is saved in *_raw.txt for manual inspection |
| Parse script error | Raw text is preserved, can be manually analyzed |
