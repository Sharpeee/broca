#!/usr/bin/python3
import asyncio
from aiohttp import web
from broca.reaper import reaper
from broca.rpc import app

asyncio.ensure_future(reaper())
web.run_app(app, port=9091)
