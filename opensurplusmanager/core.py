"""Core"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict

import opensurplusmanager.api as api
from opensurplusmanager.models.device import Device, DeviceType
from opensurplusmanager.models.integration import ControlIntegration
from opensurplusmanager.utils import logger


@dataclass
class Core:
    consumption = 0
    production = 0
    __surplus = 0
    config = {}
    balanced = False

    __devices: Dict[str, Device] = field(default_factory=dict)

    @property
    def surplus(self):
        return self.__surplus

    @surplus.setter
    def surplus(self, value):
        logger.info("Setting surplus to %s", value)
        self.__surplus = value
        asyncio.create_task(self.update())

    async def balanced_load(self):
        pass

    async def focused_load(self):
        devices = list(self.__devices.values())
        if self.surplus > 0:
            for device in devices:
                left_surplus = self.surplus
                if device.expected_consumption < left_surplus and not device.powered:
                    left_surplus -= device.expected_consumption
                    await device.turn_on()
        else:
            for device in reversed(devices):
                left_surplus = self.surplus
                if device.powered:
                    await device.turn_off()

                left_surplus += device.expected_consumption
                if left_surplus >= 0:
                    break

    async def update(self):
        logger.info("Core is running")
        if self.balanced:
            await self.balanced_load()
        else:
            await self.focused_load()
        self.print()

    def print(self):
        print("Core:")
        print(f"Surplus: {self.surplus}")
        print("Devices:")
        for device in self.__devices.values():
            print(f"  {device.name}:")
            print(f"    Powered: {device.powered}")
            print(f"    Expected consumption: {device.expected_consumption}")
            print(f"    Consumption: {device.consumption}")
        print()

    def add_control_integration(self, name: str, integration: ControlIntegration):
        if name in self.__devices:
            self.__devices[name].control_integration = integration
        logger.info("Added control integration to device %s to core", name)

    async def run(self):
        await api.api_start(self)

    def load_config(self):
        devices = self.config.get("devices", [])

        for device in devices:
            name = device["name"]
            device_type = DeviceType(device["type"])
            expected_consumption = device["expected_consumption"]
            new_device = Device(
                name=name,
                device_type=device_type,
                expected_consumption=expected_consumption,
                control_integration=None,
            )
            self.__devices[name] = new_device
            logger.info("Added device %s to core", name)

    def get_device(self, name: str):
        return self.__devices.get(name, None)
