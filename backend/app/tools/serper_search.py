"""
Watchout Backend - Serper Search API Tool (Fallback)
"""
import httpx
from typing import Optional, List, Dict, Any

from app.core.config import settings


class SerperSearchTool:
    """
    MCP Tool wrapper for Serper API.
    Used as fallback when Tavily is unavailable.
    Returns raw Google search results.
    """
    
    BASE_URL = "https://google.serper.dev/search"
    
    def __init__(self):
        self.api_key = settings.serper_api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        country: str = "in"
    ) -> Optional[Dict[str, Any]]:
        """
        Perform a Google search via Serper.
        
        Args:
            query: Search query
            num_results: Number of results to return
            country: Country code for localized results
        
        Returns:
            Search results
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results,
            "gl": country
        }
        
        try:
            response = await self.client.post(
                self.BASE_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "organic": [
                    {
                        "title": r.get("title"),
                        "link": r.get("link"),
                        "snippet": r.get("snippet"),
                        "position": r.get("position")
                    }
                    for r in data.get("organic", [])
                ],
                "knowledge_graph": data.get("knowledgeGraph"),
                "answer_box": data.get("answerBox")
            }
            
        except Exception as e:
            print(f"Serper search error: {e}")
            return None
    
    async def search_places(
        self,
        query: str,
        location: str
    ) -> Optional[Dict[str, Any]]:
        """
        Search for places via Serper.
        
        Args:
            query: Place query
            location: Location context
        
        Returns:
            Place search results
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": f"{query} in {location}",
            "type": "places",
            "gl": "in"
        }
        
        try:
            response = await self.client.post(
                "https://google.serper.dev/places",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "places": [
                    {
                        "title": p.get("title"),
                        "address": p.get("address"),
                        "rating": p.get("rating"),
                        "reviews": p.get("ratingCount"),
                        "type": p.get("type"),
                        "phone": p.get("phoneNumber"),
                        "website": p.get("website")
                    }
                    for p in data.get("places", [])
                ]
            }
            
        except Exception as e:
            print(f"Serper places error: {e}")
            return None
    
    async def search_images(
        self,
        query: str,
        num_results: int = 5
    ) -> Optional[List[Dict[str, str]]]:
        """
        Search for images.
        
        Args:
            query: Image search query
            num_results: Number of images to return
        
        Returns:
            List of image results
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results,
            "gl": "in"
        }
        
        try:
            response = await self.client.post(
                "https://google.serper.dev/images",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "title": img.get("title"),
                    "imageUrl": img.get("imageUrl"),
                    "link": img.get("link")
                }
                for img in data.get("images", [])[:num_results]
            ]
            
        except Exception as e:
            print(f"Serper images error: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
_serper_tool: Optional[SerperSearchTool] = None


def get_serper_tool() -> SerperSearchTool:
    """Get or create the Serper tool instance."""
    global _serper_tool
    if _serper_tool is None:
        _serper_tool = SerperSearchTool()
    return _serper_tool
