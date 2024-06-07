from dataclasses import dataclass, field
from enum import StrEnum

from .integration import ControlIntegration


class DeviceType(StrEnum):
    SWITCH = "switch"
    REGULATED = "regulated"


class InvalidDeviceType(Exception):
    pass


@dataclass
class Device:
    name: str
    device_type: DeviceType
    control_integration: ControlIntegration
    expected_consumption: float
    max_consumption: float | None = field(default=None, init=False)
    powered: bool = field(default=False)
    consumption: float = field(default=0, init=False)

    async def turn_on(self):
        await self.control_integration.turn_on(device_name=self.name)
        self.powered = True

    async def turn_off(self):
        await self.control_integration.turn_off(device_name=self.name)
        self.powered = False

    async def regulate(self, power: float):
        if self.device_type != DeviceType.REGULATED:
            raise InvalidDeviceType(f"Device {self.name} is not regulated")

        await self.control_integration.regulate(device_name=self.name, power=power)

    def add_control_integration(self, integration: ControlIntegration):
        self.control_integration = integration
