from dataclasses import dataclass

from opensurplusmanager.models.device import Device


@dataclass
class HTTPGetDevice(Device):
    path: str
