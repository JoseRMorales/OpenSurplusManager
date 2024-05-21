from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from opensurplusmanager.core import Core

routes = web.RouteTableDef()


@dataclass
class Api:
    core: Core

    def __init__(self, core: Core):
        self.core = core

    async def run(self):
        app = web.Application()
        app.add_routes(
            [
                web.get("/", self.hello),
            ]
        )
        app.add_routes(routes)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", 8080)
        await site.start()

        while True:
            await asyncio.sleep(3600)  # sleep forever

    async def hello(self, request):
        return web.Response(text="Hello, world")


async def api_start(core: Core):
    api = Api(core=core)
    await api.run()
