import os
import time
import asyncio
import websockets
import json

clients = set()
hosted_state = {"url": None, "start_time": None, "duration": None}


async def broadcast(message):
    """Send a message to all connected clients."""
    to_remove = set()
    for client in clients:
        try:
            await client.send(message)
        except:
            to_remove.add(client)
    clients.difference_update(to_remove)


async def broadcast_listener_count():
    """Notify everyone of the current number of clients."""
    msg = json.dumps({"status": "listeners", "count": len(clients)})
    print(f"[Server] Broadcasting listener count: {len(clients)}")
    await broadcast(msg)


async def reset_hosted_state_after_duration():
    """Reset hosted_state when song expires."""
    while True:
        if hosted_state["url"] and hosted_state["start_time"] and hosted_state["duration"]:
            elapsed = time.time() - hosted_state["start_time"]
            if elapsed >= hosted_state["duration"]:
                print("[Server] Song ended — resetting state.")
                hosted_state["url"] = None
                hosted_state["start_time"] = None
                hosted_state["duration"] = None
                await broadcast(json.dumps({"status": "nothing_hosted"}))
        await asyncio.sleep(1)


async def handler(ws):
    clients.add(ws)
    print(f"[Server] New client connected. Total: {len(clients)}")
    await broadcast_listener_count()

    try:
        # Send current state
        if hosted_state["url"]:
            await ws.send(json.dumps({
                "status": "playing",
                "url": hosted_state["url"],
                "start_time": hosted_state["start_time"],
                "duration": hosted_state["duration"]
            }))
        else:
            await ws.send(json.dumps({"status": "nothing_hosted"}))

        async for message in ws:
            data = json.loads(message)
            if data.get("type") == "HOST":
                url = data.get("url")
                duration = float(data.get("duration", 0))
                hosted_state.update({
                    "url": url,
                    "start_time": time.time(),
                    "duration": duration
                })

                print(f"[Server] Hosting new song: {url} ({duration}s)")
                relay_msg = json.dumps({
                    "status": "playing",
                    "url": url,
                    "start_time": hosted_state["start_time"],
                    "duration": duration
                })
                asyncio.create_task(broadcast(relay_msg))

    except Exception as e:
        print(f"[Server] Error: {e}")
    finally:
        clients.remove(ws)
        print(f"[Server] Client disconnected. Total: {len(clients)}")
        await broadcast_listener_count()


async def main():
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"[Server] Running on port {port}")
        await reset_hosted_state_after_duration()


if __name__ == "__main__":
    asyncio.run(main())
