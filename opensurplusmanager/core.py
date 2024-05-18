"""Core"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict

from opensurplusmanager.models.consumption import ConsumptionEntity
from opensurplusmanager.models.device import Device
from opensurplusmanager.utils import logger


@dataclass
class Core:
    consumption = 0
    production = 0
    surplus = 0
    config = {}
    __devices: Dict[str, Device] = field(default_factory=dict)

    async def core_loop(self):
        while True:
            print("Running core loop...")
            self.print()
            for device in self.__devices.values():
                if self.surplus < 1500:
                    await device.turn_off()
                else:
                    await device.turn_on()

            await asyncio.sleep(1)

    def print(self):
        print("Core:")
        print(f"Surplus: {self.surplus}")
        print("Devices:")
        print(self.__devices)
        print()

    def add_consumption_entity(self, name: str, entity: ConsumptionEntity):
        if name in self.__devices:
            self.__devices[name].consumption_entity = entity
        else:
            new_device = Device(
                name=name, consumption_entity=entity, control_integration=None
            )
            self.__devices[name] = new_device
        logger.info("Added consumption entity to device %s to core", entity)

    def add_control_integration(self, name: str, integration):
        if name in self.__devices:
            self.__devices[name].control_integration = integration
        else:
            new_device = Device(
                name=name, consumption_entity=None, control_integration=integration
            )
            self.__devices[name] = new_device
        logger.info("Added control integration to device %s to core", name)
