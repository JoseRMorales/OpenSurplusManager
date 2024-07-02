from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opensurplusmanager.core import Core

from opensurplusmanager.utils import logger

from .integration import ControlIntegration


class DeviceType(StrEnum):
    SWITCH = "switch"
    REGULATED = "regulated"


class InvalidDeviceType(Exception):
    pass


class IntegrationConnectionError(Exception):
    pass


class Device:
    name: str
    core: Core
    device_type: DeviceType
    expected_consumption: float
    __expected_consumption: float
    max_consumption: float
    __max_consumption: float
    cooldown: int
    __cooldown: int
    consumption: float = 0
    powered: bool = False
    enabled: bool = True
    control_integration: ControlIntegration | None = None

    def __init__(
        self,
        name: str,
        core: Core,
        device_type: DeviceType,
        expected_consumption: float,
        max_consumption: float | None = None,
        cooldown: int | None = None,
    ):
        self.name = name
        self.core = core
        self.device_type = device_type
        self.__expected_consumption = expected_consumption
        self.__max_consumption = max_consumption
        self.__cooldown = cooldown

    @property
    def max_consumption(self):
        return self.__max_consumption

    @max_consumption.setter
    def max_consumption(self, value):
        logger.info("Setting max consumption for device %s to %s", self.name, value)
        self.__max_consumption = value
        device_config = self.core.config.get("devices", [])
        for device in device_config:
            if device["name"] == self.name:
                device["max_consumption"] = value
                self.core.save_config()
                break

    @property
    def expected_consumption(self):
        return self.__expected_consumption

    @expected_consumption.setter
    def expected_consumption(self, value):
        logger.info(
            "Setting expected consumption for device %s to %s", self.name, value
        )
        self.__expected_consumption = value
        device_config = self.core.config.get("devices", [])
        for device in device_config:
            if device["name"] == self.name:
                device["expected_consumption"] = value
                self.core.save_config()
                break

    @property
    def cooldown(self):
        return self.__cooldown

    @cooldown.setter
    def cooldown(self, value):
        logger.info("Setting cooldown for device %s to %s", self.name, value)
        self.__cooldown = value
        device_config = self.core.config.get("devices", [])
        for device in device_config:
            if device["name"] == self.name:
                device["cooldown"] = value
                self.core.save_config()
                break

    async def turn_on(self):
        try:
            await self.control_integration.turn_on(device_name=self.name)
        except Exception as e:
            logger.error("Error turning on device %s: %s", self.name, e)
            raise IntegrationConnectionError() from e
        self.powered = True
        await self.__start_cooldown()

    async def turn_off(self):
        try:
            await self.control_integration.turn_off(device_name=self.name)
        except Exception as e:
            logger.error("Error turning off device %s: %s", self.name, e)
            raise IntegrationConnectionError() from e
        self.powered = False
        await self.__start_cooldown()

    async def regulate(self, power: float):
        if self.device_type != DeviceType.REGULATED:
            raise InvalidDeviceType(f"Device {self.name} is not regulated")

        try:
            await self.control_integration.regulate(device_name=self.name, power=power)
        except Exception as e:
            logger.error("Error regulating device %s: %s", self.name, e)
            raise IntegrationConnectionError() from e

    def add_control_integration(self, integration: ControlIntegration):
        self.control_integration = integration

    async def __start_cooldown(self):
        if self.cooldown:
            logger.info("Starting cooldown for device %s", self.name)
            self.enabled = False
            await asyncio.sleep(self.cooldown)
            self.enabled = True
