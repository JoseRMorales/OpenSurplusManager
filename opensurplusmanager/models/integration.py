from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from opensurplusmanager.core import Core

from .entity import ConsumptionEntity, ControlEntity


@dataclass
class ControlIntegration(ABC):
    core: Core
    turn_on_entities: Dict[str, ControlEntity] = field(init=False, default_factory=dict)
    turn_off_entities: Dict[str, ControlEntity] = field(
        init=False, default_factory=dict
    )
    regulate_entities: Dict[str, ControlEntity] = field(
        init=False, default_factory=dict
    )

    @abstractmethod
    async def turn_on(self, device_name):
        pass

    @abstractmethod
    async def turn_off(self, device_name):
        pass

    @abstractmethod
    async def regulate(self, device_name, power):
        pass


@dataclass
class ConsumptionIntegration(ABC):
    core: Core
    entities: List[ConsumptionEntity] = field(init=False, default_factory=list)
