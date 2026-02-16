---
description: Check if the SimilarWeb cookie is still valid
---

Quick check of the current SimilarWeb cookie validity.

## 执行方式

先定位脚本目录，然后运行：

```bash
SCRIPT_DIR="$(find ~/.claude/plugins/cache -path "*/similarweb_analysis/*/scripts" -type d 2>/dev/null | head -1)"
[ -z "$SCRIPT_DIR" ] && SCRIPT_DIR="$(find ~/Claude -path "*/similarweb_analysis/scripts" -type d 2>/dev/null | head -1)"
python3 "$SCRIPT_DIR/sw_check_cookie.py"
```

直接复制运行上面的命令即可，**不需要手动搜索路径**。

脚本通过环境变量 `SW_COOKIE_FILE` 自动定位 cookie 文件，**不需要手动查找 cookie 路径**。

如果环境变量未设置，脚本会报错提示，此时引导用户参考 README 配置环境变量。

## 输出说明

- Cookie 文件年龄
- Identity API 是否正常
- 数据 API 测试结果
- 历史检查日志
