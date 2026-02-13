# SimilarWeb Analysis Plugin

从 SimilarWeb Pro 自动提取指定域名的网站表现概览和外链来源数据。

## 功能

- **网站表现概览**: 提取总访问量、排名、参与度、地理分布、流量来源渠道、搜索、外链、社交等数据，输出为 `overview.md`
- **外链来源表格**: 提取 Top 100 外链来源域名、行业、排名、流量份额、变动，输出为 `referrals_incoming.csv`

## 前置依赖

### 1. 安装 dev-browser 插件

本插件依赖 [dev-browser](https://github.com/SawyerHood/dev-browser) 插件提供的 Playwright 浏览器自动化能力。

```bash
/plugin marketplace add sawyerhood/dev-browser
/plugin install dev-browser@sawyerhood/dev-browser
```

### 2. 首次使用: 登录 SimilarWeb Pro

由于 SimilarWeb Pro 需要登录账号，首次使用前需要手动登录:

1. 执行命令让浏览器打开 SimilarWeb Pro 页面（会自动启动 dev-browser server）
2. 如果发现页面需要登录，**终止当前 Claude Code 会话**（Ctrl+C）
3. 在浏览器中**手动完成 SimilarWeb Pro 登录**
4. 登录成功后，**不要关闭浏览器**
5. 重新启动 Claude Code，执行 `/clear` 后再次运行命令

浏览器会话数据会持久化保存，后续使用无需重复登录。

## 使用方法

```
/similarweb_analysis:fetch_website_flow_analysis stackoverflow.com 
```

## 输出

数据保存在 `web_data/{domain}/` 目录下:

- `overview.md` — 网站表现概览（Markdown 格式）
- `referrals_incoming.csv` — 外链来源表格（CSV 格式）
- `overview_raw.txt` — 概览页原始文本（备份）
- `referrals_raw.txt` — 外链页原始文本（备份）
