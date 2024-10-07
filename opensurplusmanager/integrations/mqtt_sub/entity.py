"""Entity for MQTT subscription consumption."""

from dataclasses import dataclass

from opensurplusmanager.models.entity import ConsumptionEntity


@dataclass
class MQTTSubEntity(ConsumptionEntity):
    """
    Model for a MQTT subscription consumption entity, inherits from
    ConsumptionEntity.
    """

    topic: str
