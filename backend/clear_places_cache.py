import asyncio
from app.db.mongo import MongoDB, places_cache_collection

async def main():
    await MongoDB.connect()
    cache = places_cache_collection()
    res = await cache.delete_many({})
    print(f"Deleted {res.deleted_count} cache entries")
    await MongoDB.disconnect()

asyncio.run(main())
