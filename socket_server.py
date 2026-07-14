import asyncio
import ssl
import json
import websockets
from kn_cryptography import ensure_certificate

HOST = "127.0.0.1"
PORT = 443


#Create Certificate

ensure_certificate()



# Configure TLS
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(
    certfile="server.crt",
    keyfile="server.key"
)

clients = set()


async def process_message(message):
    try:
        data = json.loads(message)

        print("Received JSON:")
        print(json.dumps(data, indent=4))

        return json.dumps({
            "status": "ok",
            "received": data
        })

    except json.JSONDecodeError:
        print("Received text:", message)
        return f"ACK: {message}"


async def handler(websocket):
    clients.add(websocket)

    print(f"Connected: {websocket.remote_address}")

    try:
        async for message in websocket:
            print(f"Received: {message}")

            response = await process_message(message)

            await websocket.send(response)

    except websockets.ConnectionClosed:
        print("Connection closed")

    finally:
        clients.remove(websocket)


async def heartbeat():
    while True:
        dead = []

        for client in clients:
            try:
                await client.ping()
            except Exception:
                dead.append(client)

        for client in dead:
            clients.discard(client)

        await asyncio.sleep(30)


async def main():
    server = await websockets.serve(
        handler,
        HOST,
        PORT,
        ssl=ssl_context,
        ping_interval=None
    )

    print(f"WSS server listening on wss://{HOST}:{PORT}")

    await asyncio.gather(
        server.wait_closed(),
        heartbeat()
    )


if __name__ == "__main__":
    asyncio.run(main())