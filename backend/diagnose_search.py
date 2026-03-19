import asyncio
from app.tools.google_places import get_places_tool
from app.db.mongo import MongoDB

async def main():
    await MongoDB.connect()
    
    places = get_places_tool()
    
    print("Testing search_places...")
    results = await places.search_places("tourist attractions in Goa")
    
    print(f"Final results count: {len(results)}")
    for r in results:
         print(f" - {r['name']} ({r.get('user_ratings_total')} ratings)")

    await MongoDB.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
