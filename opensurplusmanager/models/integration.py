"""Integration abstract classes for consumption and control entities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List

from .entity import ConsumptionEntity, ControlEntity

if TYPE_CHECKING:
    from opensurplusmanager.core import Core


@dataclass
class ControlIntegration(ABC):
    """Model for a control integration."""

    core: Core
    turn_on_entities: Dict[str, ControlEntity] = field(init=False, default_factory=dict)
    turn_off_entities: Dict[str, ControlEntity] = field(
        init=False, default_factory=dict
    )
    regulate_entities: Dict[str, ControlEntity] = field(
        init=False, default_factory=dict
    )

    @abstractmethod
    async def turn_on(self, device_name: str):
        """
        Abstract method to turn on a device.

        Parameters:
        device_name (str): The name of the device to turn on.
        """

    @abstractmethod
    async def turn_off(self, device_name: str):
        """
        Abstract method to turn off a device.

        Parameters:
        device_name (str): The name of the device to turn off.
        """

    @abstractmethod
    async def regulate(self, device_name: str, power: float):
        """
        Abstract method to regulate a device.

        Parameters:
        device_name (str): The name of the device to regulate.
        power (float): The power to regulate the device to.
        """


@dataclass
class ConsumptionIntegration(ABC):
    """Model for a consumption integration."""

    core: Core
    entities: List[ConsumptionEntity] = field(init=False, default_factory=list)
