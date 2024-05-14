"""Core"""

import asyncio
from dataclasses import dataclass, field

from opensurplusmanager.models.device import Device


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
        print(f"Added device {device.name} to core")
