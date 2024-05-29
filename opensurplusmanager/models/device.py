from dataclasses import dataclass, field
from enum import StrEnum

from .integration import ControlIntegration


class DeviceType(StrEnum):
    SWITCH = "switch"


@dataclass
class Device:
    name: str
    device_type: DeviceType
    expected_consumption: float
    control_integration: ControlIntegration
    powered: bool = field(default=False)
    consumption: float = field(default=0, init=False)

    async def turn_on(self):
        await self.control_integration.turn_on(device_name=self.name)
        self.powered = True

    async def turn_off(self):
        await self.control_integration.turn_off(device_name=self.name)
        self.powered = False

    def add_control_integration(self, integration: ControlIntegration):
        self.control_integration = integration
