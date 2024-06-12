from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiohttp import web

from opensurplusmanager.models.device import Device

if TYPE_CHECKING:
    from opensurplusmanager.core import Core

routes = web.RouteTableDef()


@dataclass
class DeviceResponse:
    name: str
    device_type: str
    control_integration: str
    expected_consumption: float
    max_consumption: float | None
    consumption: float
    powered: bool
    cooldown: int | None
    enabled: bool

    @classmethod
    def from_device(cls, device: Device) -> DeviceResponse:
        return cls(
            name=device.name,
            device_type=device.device_type.value,
            control_integration=device.control_integration.__class__.__name__,
            expected_consumption=device.expected_consumption,
            max_consumption=device.max_consumption,
            consumption=device.consumption,
            powered=device.powered,
            cooldown=device.cooldown,
            enabled=device.enabled,
        )


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
                web.get(
                    "/device/{device_name}/consumption", self.get_device_consumption
                ),
                web.get("/device/{device_name}", self.get_device),
                web.get("/devices", self.get_devices),
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

    async def get_device_consumption(self, request):
        device_name = request.match_info["device_name"]
        device: Device | None = self.core.get_device(device_name)
        if not device:
            return web.Response(status=404, text="Device not found")
        return web.json_response({"consumption": device.consumption})

    async def get_device(self, request):
        device_name = request.match_info["device_name"]
        device: Device | None = self.core.get_device(device_name)
        if not device:
            return web.Response(status=404, text="Device not found")
        device_response = DeviceResponse.from_device(device)
        return web.json_response(device_response.__dict__)

    async def get_devices(self, request):
        devices = [
            DeviceResponse.from_device(device) for device in self.core.devices.values()
        ]
        return web.json_response([device.__dict__ for device in devices])


async def api_start(core: Core):
    api = Api(core=core)
    await api.run()
