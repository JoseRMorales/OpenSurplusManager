"""Core"""

import asyncio
from dataclasses import dataclass, field

from opensurplusmanager.models.device import Device
from opensurplusmanager.utils import logger


@dataclass
class Core:
    consumption = 0
    production = 0
    surplus = 0
    config = {}
    __devices: list = field(default_factory=list)

    async def core_loop(self):
        while True:
            print("Running core loop...")
            self.print()
            await asyncio.sleep(1)

    def print(self):
        print("Core:")
        print(f"Surplus: {self.surplus}")
        print("Devices:")
        for device in self.__devices:
            print(f"  {device.name}: {device.consumption}")
        print()

    def add_device(self, device: Device):
        self.__devices.append(device)
        logger.info("Added device %s to core", device.name)
