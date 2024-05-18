from dataclasses import dataclass

from .consumption import ConsumptionEntity
from .integration import ControlIntegration


@dataclass
class Device:
    name: str
    control_integration: ControlIntegration
    consumption_entity: ConsumptionEntity

    def get_consumption(self):
        return self.consumption_entity.consumption

    async def turn_on(self):
        await self.control_integration.turn_on(device_name=self.name)

    async def turn_off(self):
        await self.control_integration.turn_off(device_name=self.name)
