import asyncio
from dataclasses import dataclass, field

import aiohttp

from opensurplusmanager.core import Core
from opensurplusmanager.integrations.http_get.device import HTTPGetDevice
from opensurplusmanager.integrations.http_get.sensor import HTTPGetSensor
from opensurplusmanager.models.integration import Integration
from opensurplusmanager.models.sensor import SensorType


@dataclass
class HttpGet(Integration):
    core: Core
    devices: list = field(default_factory=list)
    consumption: HTTPGetSensor = None
    production: HTTPGetSensor = None
    surplus: HTTPGetSensor = None

    def _load_devices(self):
        if "surplus" in self.core.config and "http_get" in self.core.config["surplus"]:
            surplus_sensor = HTTPGetSensor(
                sensor_type=SensorType.SURPLUS,
                **self.core.config["surplus"]["http_get"],
            )
            self.surplus = surplus_sensor

        for device in self.core.config.get("devices", []):
            print(device)
            integration_name = device["consumption_integration"]["name"]
            if integration_name == "http_get":
                device_config = device["consumption_integration"]
                print(f"Loading device {device['name']}...")
                device = HTTPGetDevice(
                    name=device["name"],
                    path=device_config["path"],
                    integration=self,
                )
                self.devices.append(device)
                self.core.add_device(device)

    def __init__(self, core: Core):
        self.core = core
        self.devices = []
        print("Running HTTP GET setup...")
        self._load_devices()

    async def run(self) -> None:
        print("Running HTTP GET integration...")
        while True:
            async with aiohttp.ClientSession() as session:
                if self.surplus:
                    async with session.get(self.surplus.path) as response:
                        print("Got response from surplus sensor:", response.status)
                        # Set the surplus value
                        # Convert the response to a float
                        try:
                            self.core.surplus = float(await response.text())
                        except ValueError:
                            print("Invalid API response for surplus sensor")

                for device in self.devices:
                    async with session.get(device.path) as response:
                        print("Got response from device:", response.status)
                        # Set the device consumption value
                        # Convert the response to a float
                        try:
                            device.consumption = float(await response.text())
                        except ValueError:
                            print("Invalid API response for device")
            await asyncio.sleep(5)

    async def get_consumption(self, device_name):
        pass

    async def turn_on(self, device_name):
        pass

    async def turn_off(self, device_name):
        pass


async def setup(core: Core) -> bool:
    http_get = HttpGet(core)
    asyncio.create_task(http_get.run())

    return True
