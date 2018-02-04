from aiohttp import web
from broca.connection import get_socket
from urllib.parse import urlparse, urlunparse
import aiohttp
import asyncio
import base64
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
    server = (await ws.get_resources_by_kind("server"))[0]
    return response({
        "arguments": convert.to_session(server)
    })

async def upload_torrent(ws, **args):
    data = base64.b64decode(args["metainfo"])
    msg = {
        "type": "UPLOAD_TORRENT",
        "size": len(data),
    }
    if args["download-dir"]:
        msg["path"] = args["download-dir"]
    if args["paused"]:
        msg["start"] = not args["paused"]
    serial = await ws.send(msg)
    async for offer in ws.expect(1, serial=serial):
        break
    uri = urlparse(ws.uri)
    if uri.scheme == "wss":
        uri = uri._replace(scheme="https")
    elif uri.scheme == "ws":
        uri = uri._replace(scheme="http")
    async with aiohttp.ClientSession() as session: 
        async with session.request("POST", urlunparse(uri),
                headers={ "Authorization": f"Bearer {offer['token']}" },
                data=data) as resp:
            if resp.status != 204:
                return response({}, result=f"Synapse returned {resp.status}")
    async for extant in ws.expect(1, type="RESOURCES_EXTANT", serial=serial):
        break
    torrent = (await ws.get_resources(extant["ids"]))[0]
    return response({
        "torrent-added": convert.to_torrent(torrent)
    })

async def torrent_add(ws, **args):
    if "metainfo" in args:
        return await upload_torrent(ws, **args)
    if "filename" in args:
        pass # TODO: magnet links
    return response({}, result="Invalid torrent-add request")

async def torrent_get(ws, **args):
    if "ids" in args:
        # TODO: Support getting specific infohashes
        # TODO: Support recently active (probably by faking it)
        pass
    fields = args.get("fields")
    torrents = (await ws.get_resources_by_kind("torrent"))
    files = (await ws.get_resources_by_kind("file"))
    peers = (await ws.get_resources_by_kind("peer"))
    trackers = (await ws.get_resources_by_kind("tracker"))
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

async def torrent_remove(ws, **args):
    ids = [convert.get_synapse_id(i) for i in args["ids"]]
    for torrent in ids:
        await ws.send({
            "type": "REMOVE_RESOURCE",
            "id": torrent,
            "artifacts": bool(args.get("delete-local-data"))
        })
    return response({})

async def handle(request):
    json = await request.json()
    ws = await get_socket(request.headers.get("Authorization"))
    if not ws:
        return web.Response(status=401,
                text="Authorization incorrect; use " +
                    "username=ws[s]://websocket-uri and password=synapse password")
    handlers = {
        "session-get": session_get,
        "torrent-add": torrent_add,
        "torrent-get": torrent_get,
        "torrent-remove": torrent_remove,
    }
    handler = handlers.get(json["method"])
    if not handler:
        return response({}, result="Unknown method")
    return await handler(ws, **(json.get("arguments") or {}))

app = web.Application()
app.router.add_post("/transmission/rpc", handle)
