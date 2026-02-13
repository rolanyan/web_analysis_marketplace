---
name: fetch_website_flow_analysis
description: This skill should be used when user wants to fetch/analyze website traffic data from SimilarWeb, extract website overview, or get referral/backlink data for a domain. Trigger phrases include "fetch similarweb data", "analyze website traffic", "get referral sources", "similarweb analysis".
---

# SimilarWeb 网站流量分析

从 SimilarWeb Pro 自动提取指定域名的网站表现概览和外链来源数据。

## 前置条件

- dev-browser 插件已安装
- 用户已通过 dev-browser 登录过 SimilarWeb Pro（浏览器 session 持久化）

## 参数

- `domain`: 目标域名（如 `github.com`），从命令参数中获取

## 执行流程

### Step 1: 准备工作

1. 从参数中解析域名，如果未提供则询问用户
2. 设置路径变量：

```bash
PLUGIN_DIR="$(find ~/.claude/plugins/cache -path "*/similarweb_analysis/scripts" -type d 2>/dev/null | head -1)"
if [ -z "$PLUGIN_DIR" ]; then
  PLUGIN_DIR="$(find ~/Claude/claude_code_marketplace -path "*/similarweb_analysis/scripts" -type d 2>/dev/null | head -1)"
fi
DEV_BROWSER_DIR="$(find ~/.claude/plugins/cache -path "*/dev-browser/skills/dev-browser" -type d 2>/dev/null | head -1)"
```

3. 创建输出目录：

```bash
OUTPUT_DIR="web_data/{domain}"
mkdir -p "$OUTPUT_DIR"
```

4. 确保 dev-browser server 已运行：

```bash
bash "$PLUGIN_DIR/ensure_browser.sh" "$DEV_BROWSER_DIR"
```

### Step 2: 提取网站表现数据

执行 fetch_overview.ts 提取页面文本：

```bash
cd "$DEV_BROWSER_DIR" && npx tsx "$PLUGIN_DIR/fetch_overview.ts" "{domain}" > "$OUTPUT_DIR/overview_raw.txt" 2>/dev/null
```

检查输出文件是否有内容（至少 500 字符），如果过短说明页面未加载或未登录。

然后执行 parse_overview.ts 解析为 Markdown：

```bash
cd "$DEV_BROWSER_DIR" && npx tsx "$PLUGIN_DIR/parse_overview.ts" "{domain}" "$OUTPUT_DIR/overview_raw.txt" "$OUTPUT_DIR"
```

**检查点**: 确认 `web_data/{domain}/overview.md` 已生成且内容合理。读取文件向用户简要展示关键指标。

### Step 3: 提取外链数据

执行 fetch_referrals.ts 提取页面文本：

```bash
cd "$DEV_BROWSER_DIR" && npx tsx "$PLUGIN_DIR/fetch_referrals.ts" "{domain}" > "$OUTPUT_DIR/referrals_raw.txt" 2>/dev/null
```

然后执行 parse_referrals.ts 解析为 CSV：

```bash
cd "$DEV_BROWSER_DIR" && npx tsx "$PLUGIN_DIR/parse_referrals.ts" "{domain}" "$OUTPUT_DIR/referrals_raw.txt" "$OUTPUT_DIR"
```

**检查点**: 确认 `web_data/{domain}/referrals_incoming.csv` 已生成且行数合理。

### Step 4: 汇报结果

向用户报告：
- overview.md 的关键数据摘要（总访问量、排名等）
- referrals_incoming.csv 的记录数和 Top 5 来源
- 文件保存路径

## 异常处理

| 异常 | 处理方式 |
|------|---------|
| dev-browser server 未运行 | ensure_browser.sh 会自动启动并等待 ready |
| 弹窗遮挡页面 | 脚本内自动检测并关闭 "关闭" 按钮 |
| 页面加载超时或内容过短 | 重试一次（再等 5 秒），仍失败则报告用户检查登录状态 |
| 未登录 SimilarWeb | 提示用户参考 README.md 的首次登录说明手动登录 |
| 提取数据为空 | 保存原始文本供用户排查，建议检查 SimilarWeb 账号状态 |
| 解析脚本报错 | 原始文本已保存在 *_raw.txt，可以手动分析或调整解析脚本 |
