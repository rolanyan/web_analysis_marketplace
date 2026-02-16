---
description: Check if the SimilarWeb cookie is still valid
---

Quick check of the current SimilarWeb cookie validity.

Run the check script directly:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sw_check_cookie.py"
```

The script reads `SW_COOKIE_FILE` from environment variables to locate the cookie file automatically.
If the environment variable is not set, the script reports an error — refer the user to README for configuration.

## Output

- Cookie file age
- Identity API validity
- Data API test result
- Historical check log
