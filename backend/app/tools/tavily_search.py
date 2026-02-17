"""
Watchout Backend - Tavily Search API Tool
"""
import httpx
from typing import Optional, List, Dict, Any

from app.core.config import settings


class TavilySearchTool:
    """
    MCP Tool wrapper for Tavily AI Search API.
    Provides AI-ready search results for travel research.
    """
    
    BASE_URL = "https://api.tavily.com/search"
    
    def __init__(self):
        self.api_key = settings.tavily_api_key
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        include_answer: bool = True,
        max_results: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Perform a search query.
        
        Args:
            query: Search query
            search_depth: "basic" or "advanced"
            include_answer: Whether to include AI-generated answer
            max_results: Maximum number of results
        
        Returns:
            Search results with optional AI answer
        """
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "include_answer": include_answer,
            "max_results": max_results
        }
        
        try:
            response = await self.client.post(
                self.BASE_URL,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "answer": data.get("answer"),
                "results": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "content": r.get("content"),
                        "score": r.get("score")
                    }
                    for r in data.get("results", [])
                ]
            }
            
        except Exception as e:
            print(f"Tavily search error: {e}")
            return None
    
    async def search_travel_info(
        self,
        destination: str,
        topic: str = "things to do"
    ) -> Optional[Dict[str, Any]]:
        """
        Search for travel-specific information.
        
        Args:
            destination: Travel destination
            topic: What to search (e.g., "things to do", "best restaurants")
        
        Returns:
            AI-generated travel information
        """
        query = f"{topic} in {destination} India travel guide"
        return await self.search(query, search_depth="advanced")
    
    async def verify_attraction(
        self,
        place_name: str,
        city: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify and get details about an attraction.
        
        Args:
            place_name: Name of the place
            city: City where it's located
        
        Returns:
            Verified information about the place
        """
        query = f"{place_name} {city} India opening hours ticket price"
        return await self.search(query, max_results=3)
    
    async def get_travel_tips(
        self,
        destination: str,
        month: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get travel tips for a destination.
        
        Args:
            destination: Travel destination
            month: Optional month for seasonal tips
        
        Returns:
            Travel tips and recommendations
        """
        if month:
            query = f"travel tips {destination} India in {month} what to pack weather"
        else:
            query = f"travel tips {destination} India safety what to know"
        
        return await self.search(query, search_depth="advanced")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
_tavily_tool: Optional[TavilySearchTool] = None


def get_tavily_tool() -> TavilySearchTool:
    """Get or create the Tavily tool instance."""
    global _tavily_tool
    if _tavily_tool is None:
        _tavily_tool = TavilySearchTool()
    return _tavily_tool
