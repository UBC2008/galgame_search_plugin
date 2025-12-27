# Galgame 搜索插件 (Galgame Search Plugin)

一个适用于 MaiBot 的 Galgame 搜索插件，集成 TouchGal 和 ShionLib 两大资源库，帮助你快速找到心仪的游戏资源。
## ！使用须知

- **本插件由ai完成**
- **在QQ群内发送gal网站链接有封号风险，请在信任环境启用**

## ✨ 功能特性

- **多源搜索**：整合 [TouchGal](https://www.touchgal.us/)  和 [ShionLib](https://shionlib.com/)  搜索结果。
- **智能识别**：支持自然语言询问（如："有没有白色相簿2的资源"），无需死记命令。
- **关键词扩展**：利用 LLM 自动扩展搜索关键词，提高搜索命中率。
- **命令模式**：提供 `/gal` 快捷命令。

## 🖥️ 安装方法

1. 将 `galgame_search` 文件夹移动到 MaiBot 的 `plugins` 目录下。
2. 重启 MaiBot。

## 📖 使用指南

### 1. 自然语言搜索

直接在聊天中询问即可，插件会自动识别意图：

- "有没有千恋万花的资源？"
- "帮我找一下白色相簿2"
- "搜索美少女万华镜"
- "找个galgame叫anemoi"

### 2. 命令搜索

使用 `/gal` 命令进行精确搜索：

```bash
/gal 游戏名
# 例如：
/gal 白色相簿2
```

## ⚙️ 配置说明


首次加载插件后，MaiBot 会在插件目录下自动生成 `config.toml`，默认值如下：

```toml
[plugin]
# 是否启用插件
enabled = True

[search]
# 搜索结果最大数量
max_results = 5

# 搜索超时时间（秒）
timeout = 10

# LLM 扩展关键词最大数量 (设置为 0 时不启用)
max_keywords = 5
```

如需修改，请在自动生成后编辑该文件。

## 🔌 组件说明

| 组件类型 | 标识符 | 说明 |
|---------|--------|------|
| **Action** | `search_galgame` | 负责处理自然语言触发的搜索请求 |
| **Command** | `/gal` | 处理指令式搜索 |
| **Tool** | `search_galgame` | 供 LLM 主动调用的工具接口 |

## 🛠️ 数据来源

本插件搜索结果来自以下网站，仅做数据聚合：
- [TouchGal](https://www.touchgal.us/) - 可能是最好的 Galgame 资源站
- [ShionLib](https://shionlib.com/) - 视觉小说/Galgame 档案库

## ⚖ 许可证

MIT License


