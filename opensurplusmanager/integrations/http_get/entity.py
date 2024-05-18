from dataclasses import dataclass

from opensurplusmanager.models.consumption import ConsumptionSensor


@dataclass
class HTTPGetEntity(ConsumptionSensor):
    name: str
    path: str
