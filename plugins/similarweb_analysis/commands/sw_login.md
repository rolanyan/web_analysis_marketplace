---
description: Login to SimilarWeb Pro via Google OAuth and refresh cookie
---

Login to SimilarWeb Pro using Google account via dev-browser, then extract and save the authentication cookie.

This command will:
1. Check if the existing cookie is still valid (skip login if yes)
2. Launch dev-browser and navigate to SimilarWeb
3. Click "Sign in with Google" automatically
4. Prompt for Google email and password, then fill them in automatically
5. Handle Google 2FA if needed (falls back to manual browser interaction)
6. Handle SimilarWeb 6-digit device verification if prompted (check Gmail for the code)
7. Extract and save cookie to the plugin's data directory

Run this command when API requests start returning 401/403 errors.
