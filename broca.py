#!/usr/bin/python3
from aiohttp import web
from transmisyn.connection import get_socket
import transmisyn.convert as convert
import asyncio
import json
import flask

def response(_json, result="success", tag=None):
    response = dict()
    response.update(_json)
    response.update({ "result": result })
    if tag:
        response.update({ "tag": tag })
    print("->", response)
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
    # TODO: Get files
    # TODO: Get peers
    # TODO: Get trackers
    return response({
        "arguments": {
            "torrents": [convert.to_torrent(t, fields) for t in torrents]
        }
    })

async def handle(request):
    json = await request.json()
    ws = await get_socket(request.headers.get("Authorization"))
    if not ws:
        return web.Response(status=401,
                text="Authorization incorrect; use " +
                    "username=ws[s]://websocket-uri and password=synapse password")
    print("<-", json)
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
web.run_app(app, port=9091)
