"""
Galgame 搜索工具模块
支持从 TouchGal 和 ShionLib 网站搜索 Galgame
"""

import re
import aiohttp
import asyncio
from typing import List, Dict, Optional
from urllib.parse import quote


# ========== 网站配置 ==========

# TouchGal 配置
TOUCHGAL_BASE_URL = "https://www.touchgal.us"
TOUCHGAL_SEARCH_API = f"{TOUCHGAL_BASE_URL}/api/search"

# ShionLib 配置
SHIONLIB_BASE_URL = "https://shionlib.com"
SHIONLIB_SEARCH_URL = f"{SHIONLIB_BASE_URL}/zh/search/game"

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ========== 数据类 ==========

class GalgameInfo:
    """Galgame 游戏信息数据类"""
    
    def __init__(
        self,
        name: str,
        link: str,
        source: str = "unknown",
        tags: List[str] = None,
        rating: Optional[float] = None
    ):
        self.name = name
        self.link = link
        self.source = source  # 来源：touchgal / shionlib
        self.tags = tags or []
        self.rating = rating
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "name": self.name,
            "link": self.link,
            "source": self.source,
            "tags": self.tags,
            "rating": self.rating
        }
    
    def format_message(self) -> str:
        """格式化为消息文本"""
        parts = [f"🎮 {self.name}"]
        parts.append(f"📎 {self.link}")
        
        if self.tags:
            parts.append(f"🏷️ {' | '.join(self.tags)}")
        
        if self.rating:
            parts.append(f"⭐ 评分: {self.rating}")
        
        return "\n".join(parts)


# ========== TouchGal 搜索 ==========

async def search_touchgal(
    game_name: str,
    max_results: int = 5,
    timeout: int = 10
) -> List[GalgameInfo]:
    """从 TouchGal 搜索 Galgame"""
    results = []
    
    try:
        query_string_json = f'[{{"type":"keyword","name":"{game_name}"}}]'
        
        payload = {
            "queryString": query_string_json,
            "limit": max_results,
            "searchOption": {
                "searchInIntroduction": False,
                "searchInAlias": True,
                "searchInTag": False
            },
            "page": 1,
            "selectedType": "all",
            "selectedLanguage": "all",
            "selectedPlatform": "all",
            "sortField": "resource_update_time",
            "sortOrder": "desc",
            "selectedYears": ["all"],
            "selectedMonths": ["all"]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                TOUCHGAL_SEARCH_API,
                json=payload,
                headers={**DEFAULT_HEADERS, "Referer": TOUCHGAL_BASE_URL},
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                galgames = data.get("galgames", [])
                
                for game in galgames:
                    game_id = game.get("uniqueId")
                    if not game_id:
                        continue
                    
                    results.append(GalgameInfo(
                        name=game.get("name", "未知游戏"),
                        link=f"{TOUCHGAL_BASE_URL}/{game_id}",
                        source="TouchGal",
                        tags=game.get("tags", []),
                        rating=game.get("averageRating", 0)
                    ))
    except Exception as e:
        print(f"TouchGal 搜索出错: {e}")
    
    return results


# ========== ShionLib 搜索 ==========

async def search_shionlib(
    game_name: str,
    max_results: int = 5,
    timeout: int = 10
) -> List[GalgameInfo]:
    """从 ShionLib 搜索 Galgame (解析 HTML)"""
    results = []
    
    try:
        search_url = f"{SHIONLIB_SEARCH_URL}?q={quote(game_name)}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                search_url,
                headers={**DEFAULT_HEADERS, "Referer": SHIONLIB_BASE_URL},
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                
                # 解析 Next.js 页面中的 __NEXT_DATA__ JSON
                # 格式: <script id="__NEXT_DATA__" type="application/json">...</script>
                next_data_match = re.search(
                    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    html,
                    re.DOTALL
                )
                
                if next_data_match:
                    import json
                    try:
                        next_data = json.loads(next_data_match.group(1))
                        games = next_data.get("props", {}).get("pageProps", {}).get("games", [])
                        
                        for game in games[:max_results]:
                            game_id = game.get("id")
                            if not game_id:
                                continue
                            
                            # 标题优先使用中文名，其次日文名
                            title = game.get("name_cn") or game.get("name") or "未知游戏"
                            
                            results.append(GalgameInfo(
                                name=title,
                                link=f"{SHIONLIB_BASE_URL}/zh/game/{game_id}",
                                source="ShionLib",
                                tags=[],
                                rating=None
                            ))
                    except json.JSONDecodeError:
                        pass
                
                # 备用方案：HTML 正则解析
                if not results:
                    # 匹配 <a class="block group" href="/zh/game/{id}">...<h3>标题</h3>...</a>
                    pattern = r'<a[^>]*href="/zh/game/(\d+)"[^>]*>.*?<h3[^>]*>([^<]+)</h3>'
                    matches = re.findall(pattern, html, re.DOTALL)
                    
                    for match in matches[:max_results]:
                        game_id = match[0]
                        title = match[1].strip()
                        
                        results.append(GalgameInfo(
                            name=title,
                            link=f"{SHIONLIB_BASE_URL}/zh/game/{game_id}",
                            source="ShionLib",
                            tags=[],
                            rating=None
                        ))
    except Exception as e:
        print(f"ShionLib 搜索出错: {e}")
    
    return results


# ========== 统一搜索接口 ==========

async def search_galgame(
    game_name: str,
    max_results: int = 5,
    timeout: int = 10
) -> List[GalgameInfo]:
    """
    从多个来源搜索 Galgame，合并结果
    
    Args:
        game_name: 要搜索的游戏名称
        max_results: 每个来源的最大返回结果数量
        timeout: 请求超时时间（秒）
    
    Returns:
        GalgameInfo 对象列表（合并去重后）
    """
    # 并行搜索两个来源
    touchgal_task = search_touchgal(game_name, max_results, timeout)
    shionlib_task = search_shionlib(game_name, max_results, timeout)
    
    touchgal_results, shionlib_results = await asyncio.gather(
        touchgal_task, shionlib_task,
        return_exceptions=True
    )
    
    # 处理异常情况
    if isinstance(touchgal_results, Exception):
        touchgal_results = []
    if isinstance(shionlib_results, Exception):
        shionlib_results = []
    
    # 合并结果（TouchGal 优先，因为有下载资源）
    all_results = list(touchgal_results) + list(shionlib_results)
    
    # 按名称去重（保留第一个出现的）
    seen_names = set()
    unique_results = []
    for game in all_results:
        # 简化名称用于去重
        simple_name = game.name.lower().replace(" ", "").replace("-", "")
        if simple_name not in seen_names:
            seen_names.add(simple_name)
            unique_results.append(game)
    
    return unique_results[:max_results * 2]  # 最多返回两倍结果


def format_search_results(results: List[GalgameInfo]) -> str:
    """
    将搜索结果格式化为适合发送的消息
    
    Args:
        results: GalgameInfo 对象列表
    
    Returns:
        格式化的消息字符串
    """
    if not results:
        return "😔 没有找到相关的 Galgame，请尝试其他关键词"
    
    lines = [f"🔍 找到 {len(results)} 个相关 Galgame：", ""]
    
    for i, game in enumerate(results, 1):
        source_icon = "📦" if game.source == "TouchGal" else "📚"
        lines.append(f"【{i}】{game.name} {source_icon}")
        lines.append(f"    📎 {game.link}")
        if game.tags:
            lines.append(f"    🏷️ {' | '.join(game.tags)}")
        lines.append("")
    
    lines.append("📦 = TouchGal | 📚 = ShionLib")
    lines.append("💡 点击链接即可访问下载页面")
    
    return "\n".join(lines)

