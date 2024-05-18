from abc import ABC, abstractmethod


class ControlIntegration(ABC):
    @abstractmethod
    async def turn_on(self, device_name):
        pass

    @abstractmethod
    async def turn_off(self, device_name):
        pass

    @abstractmethod
    async def regulate(self, device_name, power):
        pass
