import asyncio
import websockets
import sys

async def test():
    uri = "ws://127.0.0.1:8001/api/chat/ws/test-final"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            # The chat endpoint might not send an immediate greeting, 
            # so let's try to send a ping or just wait for 2 seconds.
            # wait_for 2 seconds
            await asyncio.sleep(2)
            print("Connection stayed open for 2 seconds.")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(test())
