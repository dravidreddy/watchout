import asyncio
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

async def seed():
    print(f"Connecting to MongoDB at {settings.mongodb_uri}...")
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    collection = db.destinations
    
    # Clear existing
    print("Clearing existing destinations...")
    await collection.delete_many({})
    
    destinations = [
        {
            "name": "Leh, Ladakh",
            "description": "High-altitude desert with stunning lakes and ancient monasteries.",
            "image_url": "https://images.unsplash.com/photo-1581793745862-99f5737672c1?auto=format&fit=crop&q=80&w=800",
            "category": ["Adventure", "Scenic"],
            "rating": 4.9,
            "location": {"type": "Point", "coordinates": [77.5771, 34.1526]},
            "is_trending": True,
            "tags": ["mountains", "trekking", "monasteries"],
            "created_at": datetime.utcnow()
        },
        {
            "name": "Varanasi, Uttar Pradesh",
            "description": "One of the oldest living cities in the world, the spiritual capital of India.",
            "image_url": "https://images.unsplash.com/photo-1561361058-c24cecae35ca?auto=format&fit=crop&q=80&w=800",
            "category": ["Spiritual", "Cultural"],
            "rating": 4.7,
            "location": {"type": "Point", "coordinates": [82.9739, 25.3176]},
            "is_trending": True,
            "tags": ["ghats", "spirituality", "history"],
            "created_at": datetime.utcnow()
        },
        {
            "name": "Munnar, Kerala",
            "description": "Rolling hills, tea plantations, and pristine waterfalls in the Western Ghats.",
            "image_url": "https://images.unsplash.com/photo-1593693397690-362cb9666fc2?auto=format&fit=crop&q=80&w=800",
            "category": ["Nature", "Relaxation"],
            "rating": 4.8,
            "location": {"type": "Point", "coordinates": [77.0595, 10.0889]},
            "is_trending": True,
            "tags": ["tea estates", "hills", "western ghats"],
            "created_at": datetime.utcnow()
        },
        {
            "name": "Hampi, Karnataka",
            "description": "UNESCO World Heritage site featuring boulders and ancient temple ruins.",
            "image_url": "https://images.unsplash.com/photo-1590050752117-23a9d7fc217c?auto=format&fit=crop&q=80&w=800",
            "category": ["Historical", "Adventure"],
            "rating": 4.8,
            "location": {"type": "Point", "coordinates": [76.4600, 15.3350]},
            "is_trending": False,
            "tags": ["ruins", "history", "boulders"],
            "created_at": datetime.utcnow()
        },
        {
            "name": "Goa",
            "description": "Famous palm-fringed beaches, nightlife, and Portuguese heritage.",
            "image_url": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&q=80&w=800",
            "category": ["Beach", "Party"],
            "rating": 4.5,
            "location": {"type": "Point", "coordinates": [73.8567, 15.2993]},
            "is_trending": True,
            "tags": ["beaches", "seafood", "nightlife"],
            "created_at": datetime.utcnow()
        },
        {
            "name": "Rishikesh, Uttarakhand",
            "description": "The Yoga Capital of the world, settled on the banks of the Ganges.",
            "image_url": "https://images.unsplash.com/photo-1598254825946-b6017bca307a?auto=format&fit=crop&q=80&w=800",
            "category": ["Adventure", "Spiritual"],
            "rating": 4.7,
            "location": {"type": "Point", "coordinates": [78.2676, 30.0869]},
            "is_trending": False,
            "tags": ["yoga", "rafting", "ganges"],
            "created_at": datetime.utcnow()
        },
        {
            "name": "Jaisalmer, Rajasthan",
            "description": "The Golden City, known for its yellow sandstone architecture and desert safaris.",
            "image_url": "https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?auto=format&fit=crop&q=80&w=800",
            "category": ["Historic", "Desert"],
            "rating": 4.6,
            "location": {"type": "Point", "coordinates": [70.9126, 26.9157]},
            "is_trending": True,
            "tags": ["fort", "desert", "rajasthan"],
            "created_at": datetime.utcnow()
        }
    ]
    
    await collection.insert_many(destinations)
    print(f"✅ Seeded {len(destinations)} destinations")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed())
