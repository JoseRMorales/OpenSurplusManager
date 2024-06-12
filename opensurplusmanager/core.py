"""Core"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict

import opensurplusmanager.api as api
from opensurplusmanager.models.device import (
    Device,
    DeviceType,
    IntegrationConnectionError,
)
from opensurplusmanager.models.integration import ControlIntegration
from opensurplusmanager.utils import logger


@dataclass
class Core:
    consumption = 0
    production = 0
    __surplus = 0
    # How much surplus power is left in a normal case.
    # Positive is a surplus, negative is grid consumption.
    surplus_margin: float | None = field(default=100)
    # In case of a power peak where grid power is needed, how much
    # is tolerated before turning off devices.
    grid_margin: float | None = field(default=100)
    config: Dict = field(default_factory=dict)

    devices: Dict[str, Device] = field(default_factory=dict)

    @property
    def surplus(self):
        return self.__surplus

    @surplus.setter
    def surplus(self, value):
        logger.info("Setting surplus to %s", value)
        self.__surplus = value
        asyncio.create_task(self.__update())

    async def __turn_on_priority(self, available_power: float):
        devices = list(self.devices.values())
        for device in filter(lambda x: x.enabled, devices):
            if device.device_type == DeviceType.SWITCH:
                if device.expected_consumption < available_power and not device.powered:
                    try:
                        await device.turn_on()
                    except IntegrationConnectionError:
                        continue
                    available_power -= device.expected_consumption
            elif device.device_type == DeviceType.REGULATED:
                if not device.powered and available_power > device.expected_consumption:
                    try:
                        await device.turn_on()
                    except IntegrationConnectionError:
                        continue
                    device_power = (
                        device.max_consumption
                        if available_power > device.max_consumption
                        else available_power
                    )
                    try:
                        await device.regulate(device_power)
                    except IntegrationConnectionError:
                        continue
                    available_power -= device_power
                elif device.powered:
                    total_device_power = device.consumption + available_power
                    device_power = (
                        device.max_consumption
                        if total_device_power > device.max_consumption
                        else total_device_power
                    )
                    try:
                        await device.regulate(device_power)
                    except IntegrationConnectionError:
                        continue
                    added_power = device_power - device.consumption
                    available_power -= added_power

    async def __turn_off_priority(self, exceeded_power: float):
        devices = reversed(self.devices.values())
        for device in filter(lambda x: x.enabled, devices):
            if device.powered and device.consumption >= 100:
                if device.device_type == DeviceType.SWITCH:
                    try:
                        await device.turn_off()
                    except IntegrationConnectionError:
                        continue
                    exceeded_power -= device.expected_consumption

                elif device.device_type == DeviceType.REGULATED:
                    if (
                        exceeded_power
                        > device.consumption - device.expected_consumption
                    ):
                        try:
                            await device.turn_off()
                        except IntegrationConnectionError:
                            continue
                        exceeded_power -= device.expected_consumption
                    else:
                        await device.regulate(device.consumption - exceeded_power)
                        break

            if exceeded_power < 0:
                break

    async def __update(self):
        logger.info("Core is running")
        self.__debug()
        surplus = self.surplus - self.surplus_margin
        if surplus > 0:
            await self.__turn_on_priority(surplus)
        elif self.surplus < (-self.grid_margin):
            await self.__turn_off_priority(-(surplus))

    def __debug(self):
        logger.debug("Core debug:")
        logger.debug("Surplus: %s", self.surplus)
        logger.debug("Devices:")
        for device in self.devices.values():
            logger.debug("  %s:", device.name)
            logger.debug("    Powered: %s", device.powered)
            logger.debug("    Expected consumption: %s", device.expected_consumption)
            logger.debug("    Consumption: %s", device.consumption)
            logger.debug("    Max consumption: %s", device.max_consumption)
            logger.debug("    Enabled: %s", device.enabled)

    def add_control_integration(self, name: str, integration: ControlIntegration):
        if name in self.devices:
            self.devices[name].control_integration = integration
        logger.info("Added control integration to device %s to core", name)

    async def run(self):
        await api.api_start(self)

    def load_config(self):
        self.grid_margin = self.config.get("grid_margin", self.grid_margin)
        self.surplus_margin = self.config.get("surplus_margin", self.surplus_margin)

        devices = self.config.get("devices", [])

        for device in devices:
            name = device["name"]
            device_type = DeviceType(device["type"])
            expected_consumption = device["expected_consumption"]
            max_consumption = device.get("max_consumption", None)
            cooldown = device.get("cooldown", None)
            new_device = Device(
                name=name,
                device_type=device_type,
                expected_consumption=expected_consumption,
                control_integration=None,
                max_consumption=max_consumption,
                cooldown=cooldown,
            )
            self.devices[name] = new_device
            logger.info("Added device %s to core", name)

    def get_device(self, name: str) -> Device | None:
        return self.devices.get(name, None)
