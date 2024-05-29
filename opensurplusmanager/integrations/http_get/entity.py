from dataclasses import dataclass

from opensurplusmanager.models.entity import ConsumptionEntity


@dataclass
class HTTPGetEntity(ConsumptionEntity):
    path: str
