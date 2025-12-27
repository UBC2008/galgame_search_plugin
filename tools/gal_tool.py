"""
Galgame 搜索工具组件
供 LLM（麦麦）在自然语言对话中调用，帮助用户搜索 Galgame
"""

from typing import Dict, Any
from src.plugin_system import BaseTool
from ..utils.search import search_galgame


class GalgameTool(BaseTool):
    """
    Galgame 搜索工具
    
    当用户以自然语言方式询问关于 Galgame 的信息时，
    LLM 可以调用此工具获取搜索结果。
    
    示例触发场景:
    - "帮我找一下 anemoi 这个游戏"
    - "有没有千恋万花的资源"
    - "搜索一下白色相簿2"
    """
    
    # 工具名称（唯一标识符）
    name = "search_galgame"
    
    # 工具描述，告诉 LLM 这个工具的用途
    description = """【Galgame/视觉小说/美少女游戏 专用搜索工具】
当用户询问任何与 Galgame、视觉小说、美少女游戏、恋爱冒险游戏相关的内容时，必须调用此工具。

触发场景（包括但不限于）：
- "有没有xxx的资源"、"找一下xxx"、"搜索xxx"、"下载xxx"
- 提到具体游戏名：白色相簿、千恋万花、Fate、CLANNAD、柚子社游戏等
- 询问gal、galgame、视觉小说、美少女游戏的下载/资源

此工具直接接入 TouchGal 数据库(https://www.touchgal.us/)，返回游戏下载链接和信息。
请优先使用此工具而非通用互联网搜索。"""
    
    # 参数定义
    # 格式: [(参数名, 类型, 描述, 是否必填), ...]
    parameters = [
        (
            "game_name",
            "string", 
            "要搜索的 Galgame 游戏名称（如：千恋万花, anemoi, starlight）。如果是模糊描述，提取最核心的关键词。",
            True  # 必填参数
        ),
        (
            "max_results",
            "integer",
            "返回结果的最大数量，默认为 3",
            False  # 可选参数
        )
    ]
    
    # 允许 LLM 调用此工具
    available_for_llm = True
    
    async def execute(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 Galgame 搜索
        """
        # 检查插件是否启用
        if not self.get_config("plugin.enabled", True):
            return {
                "name": self.name,
                "content": "该插件目前已禁用。"
            }
            
        try:
            # 获取参数
            game_name = function_args.get("game_name", "")
            max_results = function_args.get("max_results", 3)
            
            if not game_name:
                return {
                    "name": self.name,
                    "content": "错误：请提供要搜索的游戏名称"
                }
            
            # 执行搜索
            results = await search_galgame(
                game_name=game_name,
                max_results=max_results,
                timeout=10
            )
            
            if not results:
                return {
                    "name": self.name,
                    "content": f"没有找到名为 \"{game_name}\" 的 Galgame 资源"
                }
            
            # 格式化结果
            result_text = f"搜索到 {len(results)} 个与 \"{game_name}\" 相关的 Galgame：\n\n"
            
            for i, game in enumerate(results, 1):
                result_text += f"{i}. {game.name}\n"
                result_text += f"   下载链接：{game.link}\n"
                if game.tags:
                    result_text += f"   标签：{', '.join(game.tags)}\n"
                result_text += "\n"
            
            result_text += "以上链接来自 TouchGal (https://www.touchgal.us/)，点击即可访问下载页面。"
            
            return {
                "name": self.name,
                "content": result_text
            }
        
        except Exception as e:
            return {
                "name": self.name,
                "content": f"搜索出错：{str(e)}"
            }
