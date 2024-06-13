from dataclasses import dataclass

from opensurplusmanager.models.entity import ControlEntity


@dataclass
class HTTPPostEntity(ControlEntity):
    name: str
    path: str
    method: str
    body: dict
    headers: dict
