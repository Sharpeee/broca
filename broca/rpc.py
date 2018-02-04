from aiohttp import web
from broca.connection import get_socket
import asyncio
import broca.convert as convert
import json

def response(_json, result="success", tag=None):
    response = dict()
    response.update(_json)
    response.update({ "result": result })
    if tag:
        response.update({ "tag": tag })
    return web.Response(
            text=json.dumps(response),
            content_type="application/json")

async def session_get(ws, **args):
    server = (await ws.get_resources("server"))[0]
    return response({
        "arguments": convert.to_session(server)
    })

async def torrent_get(ws, **args):
    if "ids" in args:
        # TODO: Support getting specific infohashes
        # TODO: Support recently active (probably by faking it)
        pass
    fields = args.get("fields")
    torrents = (await ws.get_resources("torrent"))
    files = (await ws.get_resources("file"))
    peers = (await ws.get_resources("peer"))
    trackers = (await ws.get_resources("tracker"))
    torrents = sorted(torrents, key=lambda t: t.get("name"))
    return response({
        "arguments": {
            "torrents": [convert.to_torrent(
                torrent,
                fields,
                [f for f in files if f["torrent_id"] == torrent["id"]],
                [p for p in peers if p["torrent_id"] == torrent["id"]],
                [t for t in trackers if t["torrent_id"] == torrent["id"]]
            ) for torrent in torrents]
        }
    })

async def handle(request):
    json = await request.json()
    ws = await get_socket(request.headers.get("Authorization"))
    if not ws:
        return web.Response(status=401,
                text="Authorization incorrect; use " +
                    "username=ws[s]://websocket-uri and password=synapse password")
    handlers = {
        "session-get": session_get,
        "torrent-get": torrent_get,
    }
    handler = handlers.get(json["method"])
    if not handler:
        return response({}, result="Unknown method")
    return await handler(ws, **(json.get("arguments") or {}))

app = web.Application()
app.router.add_post("/transmission/rpc", handle)
