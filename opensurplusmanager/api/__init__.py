from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from json import JSONDecodeError
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

        api_app = web.Application()
        api_app.add_routes(
            [
                web.get("/", self.hello),
                web.get("/core", self.get_core_state),
                web.get(
                    "/device/{device_name}/consumption", self.get_device_consumption
                ),
                web.get("/device/{device_name}", self.get_device),
                web.get("/devices", self.get_devices),
                web.get("/surplus", self.get_surplus),
                web.post("/surplus_margin", self.set_surplus_margin),
                web.post("/grid_margin", self.set_grid_margin),
                web.post("/idle_power", self.set_idle_power),
                web.post(
                    "/device/{device_name}/max_consumption",
                    self.set_device_max_consumption,
                ),
                web.post(
                    "/device/{device_name}/expected_consumption",
                    self.set_device_expected_consumption,
                ),
                web.post("/device/{device_name}/cooldown", self.set_device_cooldown),
            ]
        )
        api_app.add_routes(routes)

        app.add_subapp("/api", api_app)

        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv("PORT", "8080"))
        host = os.getenv("HOST", "0.0.0.0")
        site = web.TCPSite(runner, host, port)
        await site.start()

        while True:
            await asyncio.sleep(3600)  # sleep forever

    async def hello(self, _) -> web.Response:
        return web.json_response({"message": "Hello, World!"})

    async def get_core_state(self, _) -> web.Response:
        state = {
            "surplus": self.core.surplus,
            "surplus_margin": self.core.surplus_margin,
            "grid_margin": self.core.grid_margin,
            "idle_power": self.core.idle_power,
        }
        return web.json_response(state)

    async def get_surplus(self, _) -> web.Response:
        return web.json_response({"surplus": self.core.surplus})

    async def get_device_consumption(self, request: web.Request) -> web.Response:
        device_name = request.match_info["device_name"]
        device: Device | None = self.core.get_device(device_name)
        if not device:
            return web.Response(status=404, text="Device not found")
        return web.json_response({"consumption": device.consumption})

    async def get_device(self, request: web.Request) -> web.Response:
        device_name = request.match_info["device_name"]
        device: Device | None = self.core.get_device(device_name)
        if not device:
            return web.Response(status=404, text="Device not found")
        device_response = DeviceResponse.from_device(device)
        return web.json_response(device_response.__dict__)

    async def get_devices(self, _) -> web.Response:
        devices = [
            DeviceResponse.from_device(device) for device in self.core.devices.values()
        ]
        return web.json_response([device.__dict__ for device in devices])

    async def set_surplus_margin(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            value = data["surplus_margin"]
        except (JSONDecodeError, KeyError, TypeError):
            return web.Response(status=400, text="Invalid JSON")
        self.core.surplus_margin = value
        return web.json_response({"surplus_margin": self.core.surplus_margin})

    async def set_grid_margin(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            value = data["grid_margin"]
        except (JSONDecodeError, KeyError, TypeError):
            return web.Response(status=400, text="Invalid JSON")
        self.core.grid_margin = value
        return web.json_response({"grid_margin": self.core.grid_margin})

    async def set_idle_power(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            value = data["idle_power"]
        except (JSONDecodeError, KeyError, TypeError):
            return web.Response(status=400, text="Invalid JSON")
        self.core.idle_power = value
        return web.json_response({"idle_power": self.core.idle_power})

    async def set_device_max_consumption(self, request: web.Request) -> web.Response:
        device_name = request.match_info["device_name"]
        try:
            data = await request.json()
            value = data["max_consumption"]
        except (JSONDecodeError, KeyError, TypeError):
            return web.Response(status=400, text="Invalid JSON")
        device = self.core.get_device(device_name)
        if not device:
            return web.Response(status=404, text="Device not found")
        device.max_consumption = value
        return web.json_response({"max_consumption": device.max_consumption})

    async def set_device_expected_consumption(
        self, request: web.Request
    ) -> web.Response:
        device_name = request.match_info["device_name"]
        data = await request.json()
        device = self.core.get_device(device_name)
        if not device:
            return web.Response(status=404, text="Device not found")
        device.expected_consumption = data["expected_consumption"]
        return web.json_response({"expected_consumption": device.expected_consumption})

    async def set_device_cooldown(self, request: web.Request) -> web.Response:
        device_name = request.match_info["device_name"]
        try:
            data = await request.json()
            value = data["cooldown"]
        except (JSONDecodeError, KeyError, TypeError):
            return web.Response(status=400, text="Invalid JSON")
        device = self.core.get_device(device_name)
        if not device:
            return web.Response(status=404, text="Device not found")
        device.cooldown = value
        return web.json_response({"cooldown": device.cooldown})


async def api_start(core: Core):
    api = Api(core=core)
    await api.run()
