import asyncio
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
from app.db.mongo import MongoDB, agent_runs_collection

async def main():
    await MongoDB.connect()
    runs_col = agent_runs_collection()
    
    print("Fetching last 3 agent runs...")
    cursor = runs_col.find().sort("created_at", -1).limit(3)
    
    async for run in cursor:
        print(f"\nRun ID: {run.get('_id')}")
        print(f"Status: {run.get('status')}")
        print(f"Error: {run.get('error')}")
        print(f"Traceback: {run.get('traceback')}")
        
    await MongoDB.disconnect()

asyncio.run(main())
