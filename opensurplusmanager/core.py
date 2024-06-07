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
    # How much surplus power is left in a normal case.
    # Positive is a surplus, negative is grid consumption.
    surplus_margin = 100
    # In case of a power peak where grid power is needed, how much
    # is tolerated before turning off devices.
    grid_margin = 100
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

    def total_devices_consumption(self):
        return sum(
            device.expected_consumption if device.powered else 0
            for device in self.__devices.values()
        )

    async def __turn_on_priority(self, available_power: float):
        devices = list(self.__devices.values())
        for device in devices:
            if device.device_type == DeviceType.SWITCH:
                if device.expected_consumption < available_power and not device.powered:
                    await device.turn_on()
                    available_power -= device.expected_consumption
            elif device.device_type == DeviceType.REGULATED:
                if not device.powered:
                    await device.turn_on()

                if available_power > device.expected_consumption:
                    device_power = (
                        device.max_consumption
                        if available_power > device.max_consumption
                        else available_power
                    )
                    await device.regulate(device_power)
                    available_power -= device_power

    async def __turn_off_priority(self, exceeded_power: float):
        devices = list(self.__devices.values())
        for device in reversed(devices):
            if device.powered and device.consumption > device.expected_consumption:
                if device.device_type == DeviceType.SWITCH:
                    await device.turn_off()
                    exceeded_power -= device.expected_consumption

                elif device.device_type == DeviceType.REGULATED:
                    if (
                        exceeded_power
                        > device.consumption - device.expected_consumption
                    ):
                        await device.turn_off()
                        exceeded_power -= device.expected_consumption
                    else:
                        await device.regulate(device.consumption - exceeded_power)
                        break

            if exceeded_power < 0:
                break

    async def focused_load(self):
        surplus = self.surplus - self.surplus_margin
        if surplus > 0:
            await self.__turn_on_priority(surplus)
        elif self.surplus < (-self.grid_margin):
            await self.__turn_off_priority(self.surplus + self.surplus_margin)

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

    def get_device(self, name: str) -> Device:
        return self.__devices.get(name, None)
