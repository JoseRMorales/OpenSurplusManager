from dataclasses import dataclass

from opensurplusmanager.models.entity import ConsumptionEntity


@dataclass
class MQTTSubEntity(ConsumptionEntity):
    topic: str
