"""
Galgame 搜索插件 - 从 TouchGal 网站搜索 Galgame 资源
支持 /gal 命令搜索、自然语言 Action 触发、LLM Tool 调用
"""

from typing import List, Tuple, Type
from src.plugin_system import BasePlugin, register_plugin, ComponentInfo
from src.plugin_system.base.config_types import ConfigField


@register_plugin
class GalgameSearchPlugin(BasePlugin):
    """Galgame 搜索插件 - 帮助用户搜索 Galgame 游戏资源"""

    # 插件基本信息
    plugin_name = "galgame_search"
    enable_plugin = True
    
    # 依赖列表
    dependencies = []
    python_dependencies = ["aiohttp"]
    
    # 配置文件
    config_file_name = "config.toml"
    config_schema = {
        "plugin": {
            "enabled": ConfigField(
                type=bool,
                default=True,
                description="是否启用插件"
            )
        },
        "search": {
            "max_results": ConfigField(
                type=int,
                default=5,
                description="搜索结果最大数量"
            ),
            "timeout": ConfigField(
                type=int, 
                default=10,
                description="搜索超时时间（秒）"
            ),
            "max_keywords": ConfigField(
                type=int,
                default=5,
                description="LLM 扩展关键词最大数量"
            )
        }
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """返回插件包含的组件列表"""
        from .commands.gal_command import GalCommand
        from .tools.gal_tool import GalgameTool
        from .actions.gal_action import GalSearchAction
        
        return [
            # 注册 Galgame 搜索 Action（自然语言触发）
            (GalSearchAction.get_action_info(), GalSearchAction),
            # 注册 /gal 命令组件
            (GalCommand.get_command_info(), GalCommand),
            # 注册 Galgame 搜索工具（供 LLM 调用）
            (GalgameTool.get_tool_info(), GalgameTool)
        ]
