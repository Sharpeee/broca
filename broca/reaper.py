import asyncio
from broca.connection import synapse_pool
from datetime import datetime, timedelta

async def reaper():
    print("Starting reaper")
    while True:
        await asyncio.sleep(30)
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        for uri in synapse_pool:
            conn = synapse_pool[uri]
            if conn.last_update < cutoff:
                print(f"Reaping {conn.uuid}")
                conn.future.cancel()
