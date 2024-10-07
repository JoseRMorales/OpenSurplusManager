"""Entity classes for OpenSurplusManager."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .device import Device


@dataclass
class ControlEntity(ABC):
    """
    Model for a control entity. Control integrations entities
    should inherit from this class.
    """

    name: str


class ConsumptionType(Enum):
    """
    Enumerate the different types of consumption entities.
    """

    CONSUMPTION = 1
    PRODUCTION = 2
    SURPLUS = 3
    DEVICE = 4


@dataclass
class ConsumptionEntity(ABC):
    """
    Model for a consumption entity. Consumption integrations entities
    should inherit from this class.
    """

    name: str
    consumption_type: ConsumptionType
    device: Device | None
