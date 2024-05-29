from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .device import Device


@dataclass
class ControlEntity(ABC):
    name: str


class ConsumptionType(Enum):
    CONSUMPTION = 1
    PRODUCTION = 2
    SURPLUS = 3
    DEVICE = 4


@dataclass
class ConsumptionEntity(ABC):
    name: str
    consumption_type: ConsumptionType
    device: Device | None
