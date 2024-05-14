from dataclasses import dataclass

from .integration import Integration


@dataclass
class Device:
    name: str
    integration: Integration
