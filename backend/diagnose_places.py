"""Simulate exactly what google_places.py does, step by step."""
import asyncio
import httpx
import hashlib
from app.db.mongo import MongoDB, places_cache_collection
from app.core.config import settings

BLACKLIST = {
    "lodging", "travel_agency", "hardware_store", "car_repair", "real_estate_agency",
    "gym", "supermarket", "grocery_or_supermarket", "local_government_office",
    "dentist", "doctor", "veterinary_care", "insurance_agency", "laundry",
    "hair_care", "accounting", "lawyer", "plumber", "electrician", "store",
    "electronics_store", "furniture_store", "clothing_store"
}

async def main():
    await MongoDB.connect()
    api_key = settings.google_places_api_key
    
    # Step 1: Check cache for this exact query
    lat, lng, radius, place_type = 17.385, 78.4867, 5000, "tourist_attraction"
    lat_rounded = round(lat, 3)
    lng_rounded = round(lng, 3)
    key_str = f"search_nearby:{lat_rounded}:{lng_rounded}:{radius}:{place_type}:None"
    query_key = hashlib.md5(key_str.encode()).hexdigest()
    
    cache = places_cache_collection()
    cached = await cache.find_one({"query_key": query_key})
    print(f"=== CACHE CHECK ===")
    print(f"Query key: {query_key}")
    print(f"Cached entry found: {cached is not None}")
    if cached:
        print(f"Cached results count: {len(cached.get('results', []))}")
        print(f"Cached at: {cached.get('cached_at')}")
        # This is likely the problem!
        print(f"\n>>> CACHE HIT - this is what gets returned to the frontend")
        print(f">>> Deleting stale cache entry...")
        await cache.delete_one({"query_key": query_key})
        print(f">>> Deleted!")

    # Step 2: Call Google directly
    print(f"\n=== RAW GOOGLE API CALL ===")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "location": f"{lat},{lng}",
                "radius": radius,
                "type": place_type,
                "key": api_key,
            }
        )
        data = resp.json()
        print(f"Google status: {data.get('status')}")
        print(f"Error message: {data.get('error_message', 'None')}")
        results = data.get("results", [])
        print(f"Raw results count: {len(results)}")
        
        # Step 3: Apply parser
        print(f"\n=== STRICT FILTER (>=20 reviews) ===")
        filtered = []
        for place in results:
            name = place.get("name", "?")
            ratings_count = place.get("user_ratings_total", 0)
            place_types = place.get("types", [])
            
            blacklisted = any(t in BLACKLIST for t in place_types)
            has_exception = "museum" in place_types or "tourist_attraction" in place_types
            
            if ratings_count < 20:
                print(f"  DROPPED (low reviews={ratings_count}): {name}")
                continue
            if blacklisted and not has_exception:
                print(f"  DROPPED (blacklisted): {name}")
                continue
            
            print(f"  KEPT: {name} (reviews={ratings_count})")
            filtered.append(place)
        
        print(f"\nFinal filtered count: {len(filtered)}")
    
    # Also check text search cache
    text_key_str = f"search_places:tourist attractions in Hyderabad:None:5000:None"
    text_query_key = hashlib.md5(text_key_str.encode()).hexdigest()
    text_cached = await cache.find_one({"query_key": text_query_key})
    print(f"\n=== TEXT SEARCH CACHE CHECK ===")
    print(f"Query key: {text_query_key}")
    print(f"Cached entry found: {text_cached is not None}")
    if text_cached:
        print(f"Cached results count: {len(text_cached.get('results', []))}")
        print(f">>> Deleting stale text search cache...")
        await cache.delete_one({"query_key": text_query_key})
        print(f">>> Deleted!")
    
    await MongoDB.disconnect()

asyncio.run(main())
