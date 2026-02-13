# Web Analysis Marketplace

为从各网站爬取和分析数据定制的 Claude Code 插件市场。

## 项目结构

```
web_analysis_marketplace/
├── .claude-plugin/
│   └── plugin.json          # 市场级别元数据
├── plugins/                  # 所有插件目录
│   └── <plugin-name>/       # 每个插件一个子目录
│       ├── plugin.json      # 插件元数据
│       ├── README.md        # 插件文档
│       ├── commands/        # 斜杠命令定义
│       ├── agents/          # 专业 AI agent 定义
│       ├── skills/          # 技能定义和代码示例
│       ├── hooks/           # 事件钩子脚本
│       └── scripts/         # 工具脚本
├── CLAUDE.md                # Claude Code 上下文文档
├── README.md                # 项目说明
├── LICENSE                  # MIT 许可证
└── .gitignore
```

## 插件开发规范

### 创建新插件

在 `plugins/` 目录下创建新的子目录，至少包含：

1. **`plugin.json`** - 插件元数据（name, version, description）
2. **`README.md`** - 插件文档说明
3. **`commands/`** - 至少一个斜杠命令

### 插件 plugin.json 模板

```json
{
  "name": "plugin-name",
  "version": "0.1.0",
  "description": "插件描述",
  "author": {
    "name": "yanqiang"
  },
  "commands": [],
  "agents": [],
  "skills": [],
  "hooks": [],
  "permissions": ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
}
```

### 命令文件格式 (commands/*.md)

```markdown
---
description: 命令描述
---

命令执行逻辑和指导说明
```

## 通用最佳实践

- 使用 Playwright MCP 进行浏览器自动化
- 使用 DuckDuckGo MCP 进行搜索
- 爬取数据时注意网站的 robots.txt 和速率限制
- 敏感数据（cookies、credentials）不要提交到仓库
- 爬取的原始数据放在 `data/raw/`（已 gitignore）
