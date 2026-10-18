# Global Chat

A small in-memory WebSocket chat with text, emoji, and image messages.

## Run

Install Python 3.10+ and `websockets`, then run `python backend.py`. Serve `index.html` through any static web server. On a local server at a different address, open the page with `?server=ws://localhost:8765`.

The published GitHub Pages client connects directly to this repository's dedicated Railway service at `wss://global-chat-production-eaa2.up.railway.app`. An optional `?server=wss://YOUR_SERVER_ADDRESS` overrides that address for testing.

Messages and images are kept in memory, with the most recent 50 replayed to new visitors. They disappear when the server restarts. Images are limited to 700 KB and PNG, JPEG, GIF, or WebP. The emoji picker uses Unicode emoji characters, so it needs no external pack or CDN.

## Test

`python -m unittest`
