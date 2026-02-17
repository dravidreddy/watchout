import asyncio
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def test_connection():
    print(f"Testing connection to: {settings.mongodb_uri}")
    print(f"Using Certifi CA: {certifi.where()}")
    
    try:
        # Try with certifi
        client = AsyncIOMotorClient(
            settings.mongodb_uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )
        await client.admin.command("ping")
        print("SUCCESS: Connected with certifi!")
    except Exception as e:
        print(f"FAILURE with certifi: {e}")
        
    try:
        # Try without certifi (current state)
        print("\nTesting without certifi (Baseline)...")
        client_base = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000
        )
        await client_base.admin.command("ping")
        print("SUCCESS: Connected WITHOUT certifi!")
    except Exception as e:
        print(f"FAILURE without certifi: {e}")

    try:
        # Try Localhost
        print("\nTesting LOCALHOST (mongodb://localhost:27017)...")
        client_local = AsyncIOMotorClient(
            "mongodb://localhost:27017",
            serverSelectionTimeoutMS=2000
        )
        await client_local.admin.command("ping")
        print("SUCCESS: Connected to LOCALHOST!")
    except Exception as e:
        print(f"FAILURE LOCALHOST: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
