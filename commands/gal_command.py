"""
/gal 命令组件
用于响应用户的 Galgame 搜索命令
"""

import json
from typing import Tuple, Optional, List
from src.plugin_system import BaseCommand, llm_api
from ..utils.search import search_galgame, format_search_results


class GalCommand(BaseCommand):
    """
    Galgame 搜索命令
    
    使用方式: /gal <游戏名>
    示例: /gal anemoi
    """
    
    # 命令名称（唯一标识符）
    command_name = "gal_search"
    
    # 命令描述
    command_description = "搜索 Galgame 游戏资源"
    
    # 命令匹配的正则表达式
    # 匹配 /gal 后面跟着的游戏名，支持中英文和各种符号
    command_pattern = r"^/gal\s+(?P<game_name>.+)$"
    
    async def _expand_keywords(self, game_name: str, max_keywords: int = 5) -> List[str]:
        """
        使用 LLM 扩展搜索关键词
        """
        keywords = [game_name]  # 始终包含原始关键词
        
        # 如果 max_keywords 设置为 0 或更小，不启用扩展
        if max_keywords <= 0:
            return keywords
        
        try:
            # 获取可用模型
            models = llm_api.get_available_models()
            if not models:
                return keywords
            
            # 使用主要回复模型 replyer
            model_config = models.get("tool_use")
            if not model_config:
                # 如果没有 replyer，回退到第一个可用模型
                model_config = list(models.values())[0]
            
            # 构建提示词
            prompt = f"""你是一个 Galgame 游戏搜索助手。用户想搜索游戏："{game_name}"

请分析这个名称，生成 {max_keywords - 1} 个可能的搜索关键词变体，帮助提高搜索成功率。
考虑：
- 游戏缩写的原称（如"魔审"的原称"魔法少女的魔女审判"）
- 游戏的简称/缩写（如"魔法少女的魔女审判"可缩写为"魔审"）
- 可能的错别字修正

只返回一个 JSON 数组，包含关键词字符串，不要任何解释。
示例格式：["关键词1", "关键词2", "关键词3"]"""

            # 调用 LLM 生成
            success, content, _, _ = await llm_api.generate_with_model(
                prompt=prompt,
                model_config=model_config,
                temperature=0.3,
                max_tokens=328
            )
            
            if success and content:
                # 尝试解析 JSON
                try:
                    # 清理可能的 markdown 代码块
                    content = content.strip()
                    if content.startswith("```"):
                        content = content.split("\n", 1)[-1]
                        content = content.rsplit("```", 1)[0]
                    
                    expanded = json.loads(content.strip())
                    if isinstance(expanded, list):
                        # 添加扩展关键词（去重）
                        for kw in expanded:
                            if isinstance(kw, str) and kw.strip() and kw.strip() != game_name:
                                keywords.append(kw.strip())
                except json.JSONDecodeError:
                    pass  # 解析失败则忽略，使用原始关键词
        
        except Exception:
            pass  # 出错则忽略，使用原始关键词
        
        return keywords[:max_keywords]  # 最多 max_keywords 个关键词
    
    async def execute(self) -> Tuple[bool, Optional[str], bool]:
        """
        执行搜索命令
        
        Returns:
            Tuple[bool, str, bool]:
            - 第一个 bool: 是否成功执行
            - 第二个 str: 执行结果消息（用于日志）
            - 第三个 bool: 是否需要阻止消息继续处理
        """
        # 检查插件是否启用
        if not self.get_config("plugin.enabled", True):
            return False, "插件已禁用", False
            
        try:
            # 从正则匹配中获取游戏名参数
            game_name = self.matched_groups.get("game_name", "").strip()
            
            if not game_name:
                await self.send_text("❌ 请提供要搜索的游戏名称\n用法: /gal <游戏名>")
                return True, "缺少游戏名参数", True
            
            # 从配置获取搜索参数
            max_results = self.get_config("search.max_results", 5)
            timeout = self.get_config("search.timeout", 10)
            max_keywords = self.get_config("search.max_keywords", 5)
            
            # 使用 LLM 扩展关键词
            keywords = await self._expand_keywords(game_name, max_keywords)
            
            # 使用多个关键词搜索，合并去重结果
            all_results = []
            seen_links = set()
            
            for keyword in keywords:
                results = await search_galgame(
                    game_name=keyword,
                    max_results=max_results,
                    timeout=timeout
                )
                
                for r in results:
                    if r.link not in seen_links:
                        seen_links.add(r.link)
                        all_results.append(r)
            
            # 限制总结果数量
            all_results = all_results[:max_results]
            
            # 格式化并发送结果
            message = format_search_results(all_results)
            await self.send_text(message)
            
            return True, f"成功搜索 {game_name}（关键词: {keywords}），找到 {len(all_results)} 个结果", True
        
        except Exception as e:
            error_msg = f"❌ 搜索出错：{str(e)}"
            await self.send_text(error_msg)
            return False, f"搜索失败: {str(e)}", True
