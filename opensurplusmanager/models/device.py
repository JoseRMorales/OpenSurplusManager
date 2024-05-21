from dataclasses import dataclass
from enum import StrEnum

from .consumption import ConsumptionEntity
from .integration import ControlIntegration


class DeviceType(StrEnum):
    SWITCH = "switch"


@dataclass
class Device:
    powered = False
    name: str
    device_type: DeviceType
    expected_consumption: float
    control_integration: ControlIntegration
    consumption_entity: ConsumptionEntity

    def get_consumption(self):
        return self.consumption_entity.consumption

    async def turn_on(self):
        await self.control_integration.turn_on(device_name=self.name)
        self.powered = True

    async def turn_off(self):
        await self.control_integration.turn_off(device_name=self.name)
        self.powered = False
