from datetime import datetime
from urllib.parse import quote
from uuid import uuid4
import asyncio
import base64
import json
import string
import websockets

synapse_pool = dict()

class Connection():
    def __init__(self, uri, ws):
        self.uuid = uuid4()
        self.ws = ws
        self.uri = uri
        self.serial = 1
        self.future = None
        self.futures = dict()
        self.last_update = datetime.utcnow()

    async def get_extant(self, kind):
        serial = await self.send({
            "type": "FILTER_SUBSCRIBE",
            "kind": kind
        })
        async for resources in self.expect(1, serial=serial):
            break
        # TODO: Unsubscribe
        # https://github.com/Luminarys/synapse/issues/62
        return resources

    async def get_resources_by_kind(self, kind):
        ids = (await self.get_extant(kind))["ids"]
        return await self.get_resources(ids)

    async def get_resources(self, ids):
        serial = await self.send({
            "type": "GET_RESOURCES",
            "ids": ids
        })
        async for update in self.expect(1, type="UPDATE_RESOURCES", ids=ids):
            break
        return update["resources"]

    async def send(self, msg):
        serial = self.serial
        msg.update({
            "serial": serial
        })
        self.serial += 1
        await self.ws.send(json.dumps(msg))
        return serial

    async def expect(self, count, **kwargs):
        """Asyncronously yields `count` messages characteristic of `kwargs`"""
        while count != 0:
            future = asyncio.Future()
            self.futures[json.dumps(kwargs)] = future
            yield await future
            count -= 1

    async def recv(self):
        msg = json.loads(await self.ws.recv())
        for _kwargs in list(self.futures.keys()):
            kwargs = json.loads(_kwargs)
            passed = True
            for k in kwargs:
                if k == "ids" and msg["type"] == "UPDATE_RESOURCES":
                    if not all(r["id"] in kwargs[k] for r in msg["resources"]):
                        passed = False
                        break
                elif not k in msg or k in msg and msg[k] != kwargs[k]:
                    passed = False
                    break
            if passed:
                self.futures[_kwargs].set_result(msg)
                del self.futures[_kwargs]

    async def run(self):
        while True:
            try:
                await self.recv()
            except:
                return

def get_connection_details(auth):
    # note: this is pretty hacky.
    if not auth:
        return None, None
    if not auth.startswith("Basic "):
        return None, None
    auth = base64.b64decode(auth[6:]).decode()
    uri = ""
    if auth.startswith("ws://"):
        uri = "ws://"
        auth = auth[5:]
    elif auth.startswith("wss://"):
        uri = "wss://"
        auth = auth[6:]
    else:
        return None, None
    _uri, password = auth.split(":", 1)
    uri = uri + _uri
    if ":" in password:
        port, _password = password.split(":", 1)
        if all(c in string.digits for c in port):
            uri += ":" + port
            password = _password
    return uri, password

async def get_socket(auth):
    uri, password = get_connection_details(auth)
    if not uri or not password:
        return None
    socket = synapse_pool.get(uri)
    if not socket:
        try:
            ws = await websockets.connect(
                    f"{uri}?password={quote(password)}")
        except Exception as ex:
            print(ex)
            return None
        socket = Connection(uri, ws)
        synapse_pool[uri] = socket
        socket.future = socket.run()
        print(f"Established connection {socket.uuid} to {uri}")
        asyncio.ensure_future(socket.future)
    return socket
