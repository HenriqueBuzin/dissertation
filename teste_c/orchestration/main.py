import asyncio
import aiohttp
import json

async def fetch_all_time_and_consumption():
    uri = "http://localhost:8766/graphql"  # Ajuste para o endpoint HTTP correto
    limit = 10
    offset = 0
    query = f"""
    {{
        consumptionData(limit: {limit}, offset: {offset}) {{
            date
            time
            consumptionKwhPerMinute
            type
            id
        }}
    }}
    """
    
    async with aiohttp.ClientSession() as session:
        async with session.post(uri, json={'query': query}) as response:
            result = await response.text()
            print(result)

asyncio.run(fetch_all_time_and_consumption())
