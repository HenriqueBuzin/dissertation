import asyncio
import websockets
import json

async def fetch_all_time_and_consumption():
    uri = "ws://localhost:8766"
    limit = 10
    offset = 0
    message = json.dumps({
        "query": f"""
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
    })
    
    async with websockets.connect(uri) as websocket:
        await websocket.send(message)
        response = await websocket.recv()
        print(response)

asyncio.run(fetch_all_time_and_consumption())
