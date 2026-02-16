---
description: Login to SimilarWeb Pro via Google OAuth and refresh cookie
---

Login to SimilarWeb Pro using Google account via dev-browser, then extract and save the authentication cookie.

## Step 1: Check existing cookie

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sw_check_cookie.py"
```

If cookie is still valid, skip the login flow.

## Step 2: Login (when cookie is invalid)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sw_login.py"
```

The login script will:
1. Read `SW_COOKIE_FILE` environment variable for cookie save path
2. Launch dev-browser and navigate to SimilarWeb
3. Click "Sign in with Google" automatically
4. Prompt for Google email and password, then fill them in automatically
5. Handle Google 2FA if needed (falls back to manual browser interaction)
6. Handle SimilarWeb 6-digit device verification if prompted (check Gmail for the code)
7. Extract and save cookie to `SW_COOKIE_FILE` path

Run this command when API requests start returning 401/403 errors.
