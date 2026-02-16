---
description: Login to SimilarWeb Pro and refresh cookie for API access
---

Login to SimilarWeb Pro using dev-browser, then extract and save the authentication cookie.

This command will:
1. Check if the existing cookie is still valid (skip login if yes)
2. If expired, open SimilarWeb in dev-browser
3. Handle device verification (ask user for verification code)
4. Extract and save cookie to the plugin's data directory

Run this command when API requests start returning 403 errors.
