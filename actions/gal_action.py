"""
Galgame 搜索 Action 组件
使用关键词匹配实现自然语言触发搜索
"""

import json
import re
from typing import Tuple, Optional, List

from src.plugin_system import BaseAction, ActionActivationType, ChatMode, llm_api
from ..utils.search import search_galgame, format_search_results


class GalSearchAction(BaseAction):
    """
    Galgame 搜索 Action
    
    当用户以自然语言方式询问 Galgame 相关内容时自动触发。
    支持关键词匹配和 LLM 智能判断双模式。
    """
    
    # 激活设置
    activation_type = ActionActivationType.KEYWORD  # 默认使用关键词激活
    focus_activation_type = ActionActivationType.LLM_JUDGE  # Focus模式使用LLM判定
    normal_activation_type = ActionActivationType.KEYWORD  # Normal模式使用关键词激活
    mode_enable = ChatMode.ALL
    parallel_action = False
    
    # 动作基本信息
    action_name = "search_galgame"
    action_description = (
        "搜索 Galgame（美少女游戏/视觉小说）的下载资源。"
        "当用户询问游戏资源、下载链接、或提到具体游戏名称时触发。"
        "数据来源：TouchGal (https://www.touchgal.us/)，一般不需要挂梯"
    )
    
    # 关键词设置（用于 Normal 模式快速响应）
    activation_keywords = [
        # 搜索动作关键词
        "找gal", "搜gal", "galgame", "gal游戏", "美少女游戏", "视觉小说",
        "有没有", "有什么", "找一下", "搜一下", "帮我找", "帮忙找",
        "下载", "资源", "汉化", "补丁",
        # 常见游戏名
        "白色相簿", "千恋万花", "樱之诗", "魔审", "柚子社",
        "fate", "clannad", "星空列车", "夏日口袋", "sabbat",
        "仟之刃", "灰色系列", "eden", "ef", "muv-luv",
    ]
    
    # LLM 判定提示词（用于 Focus 模式精确理解）
    llm_judge_prompt = """
判定是否需要搜索 Galgame 资源的条件：

**需要搜索的场景：**
1. 用户询问某个 Galgame/视觉小说/美少女游戏的下载资源
2. 用户问"有没有xxx的资源"、"帮我找xxx游戏"
3. 用户提到具体的 Galgame 名称并询问相关信息
4. 用户询问汉化补丁、资源下载等

**不需要搜索的场景：**
1. 纯粹讨论游戏剧情、角色，不涉及下载需求
2. 询问游戏攻略、评价
3. 一般性闲聊
4. 刚刚已经搜索过相同游戏
"""
    
    keyword_case_sensitive = False
    
    # 动作参数定义
    action_parameters = {
        "game_name": "用户想要搜索的 Galgame 游戏名称（必填）",
    }
    
    # 动作使用场景
    action_require = [
        "当用户询问 Galgame 游戏资源或下载时使用",
        "提到具体游戏名称并表达寻找意图时使用",
        "不要频繁重复搜索同一游戏",
    ]
    associated_types = ["text"]
    
    async def _expand_keywords(self, game_name: str, max_keywords: int = 5) -> List[str]:
        """使用 LLM 扩展搜索关键词"""
        keywords = [game_name]
        
        # 如果 max_keywords 设置为 0 或更小，不启用扩展
        if max_keywords <= 0:
            return keywords
            
        try:
            models = llm_api.get_available_models()
            if not models:
                return keywords
            
            model_config = models.get("tool_use")
            if not model_config:
                model_config = list(models.values())[0]
            
            prompt = f"""你是一个 Galgame 游戏搜索助手。用户想搜索游戏："{game_name}"

请分析这个名称，生成 {max_keywords - 1} 个可能的搜索关键词变体，帮助提高搜索成功率。
考虑：
- 游戏缩写的原称（如"魔审"的原称"魔法少女的魔女审判"）
- 游戏的简称/缩写（如"魔法少女的魔女审判"可缩写为"魔审"）
- 可能的错别字修正

只返回一个 JSON 数组，包含关键词字符串，不要任何解释。
示例格式：["关键词1", "关键词2", "关键词3"]"""

            success, content, _, _ = await llm_api.generate_with_model(
                prompt=prompt,
                model_config=model_config,
                temperature=0.3,
                max_tokens=1024
            )
            
            if success and content:
                try:
                    content = content.strip()
                    if content.startswith("```"):
                        content = content.split("\n", 1)[-1]
                        content = content.rsplit("```", 1)[0]
                    
                    expanded = json.loads(content.strip())
                    if isinstance(expanded, list):
                        for kw in expanded:
                            if isinstance(kw, str) and kw.strip() and kw.strip() != game_name:
                                keywords.append(kw.strip())
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
        
        return keywords[:max_keywords]
    
    def _extract_game_name(self, text: str) -> Optional[str]:
        """从用户消息中提取游戏名称"""
        if not text:
            return None
        
        # 移除常见的前缀词
        prefixes = [
            "有没有", "有什么", "帮我找", "帮忙找", "找一下", "搜一下",
            "想找", "想要", "求", "谁有", "哪里有", "在哪",
            "的资源", "的下载", "的汉化", "的补丁", "galgame", "gal",
        ]
        
        result = text.strip()
        for prefix in prefixes:
            result = result.replace(prefix, " ")
        
        # 清理并提取核心名称
        result = " ".join(result.split())
        result = result.strip()
        
        # 如果结果太短或太长，尝试其他方法
        if len(result) < 2:
            return text.strip()[:50]  # 回退到原始文本
        
        return result[:50] if result else None
    
    async def execute(self) -> Tuple[bool, Optional[str]]:
        """执行 Galgame 搜索"""
        
        # 检查插件是否启用
        if not self.get_config("plugin.enabled", True):
            return False, "插件已禁用"
            
        # 获取游戏名参数
        game_name = self.action_data.get("game_name", "").strip()
        
        # 如果参数为空，尝试从消息中提取
        if not game_name and self.action_message:
            message_text = getattr(self.action_message, 'processed_plain_text', '')
            if message_text:
                game_name = self._extract_game_name(message_text)
        
        if not game_name:
            await self.send_text("请告诉我你想找哪个 Galgame？")
            return False, "游戏名为空"
        
        try:
            # 从配置获取参数
            max_results = self.get_config("search.max_results", 5)
            timeout = self.get_config("search.timeout", 10)
            max_keywords = self.get_config("search.max_keywords", 5)
            
            # 扩展关键词
            keywords = await self._expand_keywords(game_name, max_keywords)
            
            # 多关键词搜索
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
            
            all_results = all_results[:max_results]
            
            # 发送结果
            message = format_search_results(all_results)
            await self.send_text(message)
            
            return True, f"搜索 {game_name}，找到 {len(all_results)} 个结果"
        
        except Exception as e:
            await self.send_text(f"搜索出错：{str(e)}")
            return False, f"搜索失败: {str(e)}"
