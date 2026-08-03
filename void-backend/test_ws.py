import asyncio
import websockets

async def main():
    async with websockets.connect('ws://127.0.0.1:8000/ws/system') as ws:
        print(await ws.recv())
        print(await ws.recv())

asyncio.run(main())
