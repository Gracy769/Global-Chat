"""Small in-memory WebSocket chat server."""

import asyncio
import base64
import json
import os
import re
import time

import websockets

PORT = int(os.environ.get("PORT", "8765"))
HOST = os.environ.get("HOST", "0.0.0.0")
CONNECTIONS = set()
CHAT_HISTORY = []
MAX_HISTORY = 50
MAX_IMAGE_BYTES = 700_000
MAX_WIRE_BYTES = 1_100_000
IMAGE_RE = re.compile(r"^data:image/(png|jpeg|gif|webp);base64,([A-Za-z0-9+/]+={0,2})$")
SIGNATURES = {
    "png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    "jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    "gif": lambda data: data.startswith((b"GIF87a", b"GIF89a")),
    "webp": lambda data: data.startswith(b"RIFF") and data[8:12] == b"WEBP",
}


def validate_message(raw):
    """Return a safe chat message, or None for invalid input."""
    if not isinstance(raw, str) or len(raw) > MAX_WIRE_BYTES:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    user, text, image = data.get("user"), data.get("text", ""), data.get("image")
    if not isinstance(user, str) or not 3 <= len(user.strip()) <= 30:
        return None
    if not isinstance(text, str) or len(text) > 2000:
        return None
    text = text.strip()
    if image is not None:
        if not isinstance(image, str):
            return None
        match = IMAGE_RE.fullmatch(image)
        if not match or len(match.group(2)) > (MAX_IMAGE_BYTES * 4 // 3 + 8):
            return None
        try:
            binary = base64.b64decode(match.group(2), validate=True)
        except (ValueError, base64.binascii.Error):
            return None
        if not binary or len(binary) > MAX_IMAGE_BYTES or not SIGNATURES[match.group(1)](binary):
            return None
    if not text and image is None:
        return None
    return {"user": user.strip(), "text": text, "image": image, "timestamp": time.time()}


async def handler(websocket):
    CONNECTIONS.add(websocket)
    try:
        for message in CHAT_HISTORY:
            await websocket.send(json.dumps(message))
        async for raw in websocket:
            message = validate_message(raw)
            if message is None:
                continue
            CHAT_HISTORY.append(message)
            del CHAT_HISTORY[:-MAX_HISTORY]
            payload = json.dumps(message)
            peers = tuple(CONNECTIONS)
            results = await asyncio.gather(*(peer.send(payload) for peer in peers), return_exceptions=True)
            for peer, result in zip(peers, results):
                if isinstance(result, Exception):
                    CONNECTIONS.discard(peer)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CONNECTIONS.discard(websocket)


async def main():
    print(f"Global Chat listening on {HOST}:{PORT}")
    async with websockets.serve(handler, HOST, PORT, max_size=MAX_WIRE_BYTES):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
