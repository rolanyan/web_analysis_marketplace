---
description: Login to SimilarWeb Pro via Google OAuth and refresh cookie
---

Login to SimilarWeb Pro using Google account via dev-browser, then extract and save the authentication cookie.

## 前置步骤：定位脚本目录并检查 cookie

```bash
SCRIPT_DIR="$(find ~/.claude/plugins/cache -path "*/similarweb_analysis/*/scripts" -type d 2>/dev/null | head -1)"
[ -z "$SCRIPT_DIR" ] && SCRIPT_DIR="$(find ~/Claude -path "*/similarweb_analysis/scripts" -type d 2>/dev/null | head -1)"
python3 "$SCRIPT_DIR/sw_check_cookie.py"
```

直接复制运行上面的命令即可，**不需要手动搜索路径**。脚本通过环境变量 `SW_COOKIE_FILE` 自动定位 cookie 文件。如果 cookie 仍有效，跳过后续登录流程。

## 登录流程（cookie 无效时）

1. 读取 `SW_COOKIE_FILE` 环境变量确定 cookie 保存路径
2. Launch dev-browser and navigate to SimilarWeb
3. Click "Sign in with Google" automatically
4. Prompt for Google email and password, then fill them in automatically
5. Handle Google 2FA if needed (falls back to manual browser interaction)
6. Handle SimilarWeb 6-digit device verification if prompted (check Gmail for the code)
7. Extract and save cookie to `SW_COOKIE_FILE` 指定的路径

Run this command when API requests start returning 401/403 errors.
