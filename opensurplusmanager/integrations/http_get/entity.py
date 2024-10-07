"""Entity for HTTP GET consumption."""

from dataclasses import dataclass

from opensurplusmanager.models.entity import ConsumptionEntity


@dataclass
class HTTPGetEntity(ConsumptionEntity):
    """Model for a HTTP GET consumption entity, inherits from ConsumptionEntity."""

    path: str
