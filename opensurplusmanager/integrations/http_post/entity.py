"""Entity for HTTP Post control."""

from dataclasses import dataclass

from opensurplusmanager.models.entity import ControlEntity


@dataclass
class HTTPPostEntity(ControlEntity):
    """Model for a HTTP Post control entity, inherits from ControlEntity."""

    name: str
    path: str
    method: str
    body: dict
    headers: dict
