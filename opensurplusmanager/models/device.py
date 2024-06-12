import asyncio
from dataclasses import dataclass, field
from enum import StrEnum

from opensurplusmanager.utils import logger

from .integration import ControlIntegration


class DeviceType(StrEnum):
    SWITCH = "switch"
    REGULATED = "regulated"


class InvalidDeviceType(Exception):
    pass


class IntegrationConnectionError(Exception):
    pass


@dataclass
class Device:
    name: str
    device_type: DeviceType
    control_integration: ControlIntegration
    expected_consumption: float
    max_consumption: float | None = field(default=None)
    powered: bool = field(default=False)
    consumption: float = field(default=0, init=False)
    cooldown: int | None = field(default=None)
    enabled: bool = field(default=True)

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
