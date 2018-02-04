from aiohttp import web
from broca.connection import get_socket
from urllib.parse import urlparse, urlunparse
import aiohttp
import asyncio
import base64
import broca.convert as convert
import json

def response(_json, result="success"):
    response = dict()
    response.update(_json)
    response.update({ "result": result })
    return response

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
    resp = {
        "arguments": {
            "torrents": [convert.to_torrent(
                torrent,
                fields,
                [f for f in files if f["torrent_id"] == torrent["id"]],
                [p for p in peers if p["torrent_id"] == torrent["id"]],
                [t for t in trackers if t["torrent_id"] == torrent["id"]]
            ) for torrent in torrents]
        }
    }
    if args.get("ids") == "recently-active":
        resp["arguments"]["removed"] = []
    return response(resp)

async def torrent_remove(ws, **args):
    ids = [convert.get_synapse_id(i) for i in args["ids"]]
    for torrent in ids:
        await ws.send({
            "type": "REMOVE_RESOURCE",
            "id": torrent,
            "artifacts": bool(args.get("delete-local-data"))
        })
    return response({})

async def torrent_set(ws, **args):
    # TODO: no ids field means "all ids"
    ids = [convert.get_synapse_id(i) for i in args["ids"]]
    update = convert.from_torrent(args)
    for torrent in ids:
        await ws.send({
            "type": "UPDATE_RESOURCE",
            "resource": { "id": torrent }.update(update)
        })
    return response({})

async def torrent_start(ws, **args):
    # TODO: no ids field means "all ids"
    ids = [convert.get_synapse_id(i) for i in args["ids"]]
    for torrent in ids:
        await ws.send({ "type": "RESUME_TORRENT", "id": torrent })
    return response({})

async def torrent_stop(ws, **args):
    # TODO: no ids field means "all ids"
    ids = [convert.get_synapse_id(i) for i in args["ids"]]
    for torrent in ids:
        await ws.send({ "type": "PAUSE_TORRENT", "id": torrent })
    return response({})

async def handle(request):
    req = await request.json()
    if not request.headers.get("Authorization"):
        return web.Response(status=401, headers={
            "WWW-Authenticate": 'Basic realm="User Visible Realm" charset="UTF-8"'
        }, text="Expected authorization")
    if not request.headers.get("X-Transmission-Session-Id"):
        return web.Response(status=409, headers={
            "X-Transmission-Session-Id": "TODO implement this right"
        }, text="Expected session ID")
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
        "torrent-set": torrent_set,
        "torrent-start": torrent_start,
        "torrent-start-now": torrent_start,
        "torrent-stop": torrent_stop,
        #"torrent-verify": torrent_verify # TODO Luminarys
    }
    handler = handlers.get(req["method"])
    if not handler:
        return response({}, result="Unknown method")
    resp = await handler(ws, **(req.get("arguments") or {}))
    tag = req.get("tag")
    if tag is not None:
        resp["tag"] = tag
    return web.Response(
            text=json.dumps(resp),
            content_type="application/json")

app = web.Application()
app.router.add_post("/transmission/rpc", handle)
