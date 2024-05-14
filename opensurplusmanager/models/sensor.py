from dataclasses import dataclass
from enum import Enum


class SensorType(Enum):
    CONSUMPTION = 1
    PRODUCTION = 2
    SURPLUS = 3


@dataclass
class Sensor:
    sensor_type: SensorType
