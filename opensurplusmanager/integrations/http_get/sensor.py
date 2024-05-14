from dataclasses import dataclass

from opensurplusmanager.models.sensor import Sensor


@dataclass
class HTTPGetSensor(Sensor):
    path: str
