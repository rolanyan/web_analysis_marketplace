# Web Analysis Marketplace

为从各网站爬取数据定制的 Claude Code 插件市场。

## 概述

本仓库是一个 Claude Code 插件市场，专注于网站数据爬取和分析场景。每个插件针对特定网站或数据分析需求提供定制化的命令、Agent 和技能。

## 项目结构

```
web_analysis_marketplace/
├── .claude-plugin/plugin.json   # 市场元数据
├── plugins/                      # 插件目录
│   └── <plugin-name>/           # 各插件子目录
├── CLAUDE.md                     # Claude Code 上下文
├── README.md
├── LICENSE
└── .gitignore
```

## 插件列表

> 暂无插件，待添加。

## 安装使用

### 方式一：符号链接

```bash
ln -s /path/to/web_analysis_marketplace/plugins/<plugin-name> ~/.claude/plugins/<plugin-name>
```

### 方式二：直接克隆

```bash
git clone <repo-url>
cd web_analysis_marketplace
```

## 开发新插件

1. 在 `plugins/` 下创建新目录
2. 添加 `plugin.json` 定义插件元数据
3. 添加 `README.md` 编写文档
4. 根据需要添加 `commands/`、`agents/`、`skills/`、`hooks/`、`scripts/` 目录

详细规范参见 [CLAUDE.md](CLAUDE.md)。

## 许可证

MIT License
