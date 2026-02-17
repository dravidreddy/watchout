from typing import List
from app.db.mongo import MongoDB

async def get_personalized_suggestions(user_id: str) -> List[str]:
    """Get personalized AI suggestions for the user."""
    user = await MongoDB.get_collection("users").find_one({"firebase_id": user_id})
    
    # Default suggestions if no user or prefs
    defaults = [
        "Best weekend trip from your city",
        "Budget-friendly 5-day Kerala plan",
        "Hidden gems in the Western Ghats",
        "Romantic getaway in Rajasthan"
    ]
    
    if not user:
        return defaults

    prefs = user.get("preferences", {})
    style = prefs.get("travel_style")
    budget = prefs.get("budget_range")
    
    if not style and not budget:
        return defaults
    
    suggestions = []
    if style:
        suggestions.append(f"Top 5 {style} spots in India")
        suggestions.append(f"Explore {style} in Northeast India")
    
    if budget:
        suggestions.append(f"Plan a {budget} trip to Leh-Ladakh")
        suggestions.append(f"Best {budget} beach vacations")
        
    # Mix and match
    if style and budget:
        suggestions.append(f"{style} destinations for {budget} budget")
        
    # Ensure at least 4 suggestions
    while len(suggestions) < 4 and defaults:
        d = defaults.pop(0)
        if d not in suggestions:
            suggestions.append(d)
            
    return suggestions[:5]
