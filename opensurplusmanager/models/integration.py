from abc import ABC, abstractmethod


class Integration(ABC):
    @abstractmethod
    def get_consumption(self, device_name):
        pass

    @abstractmethod
    def turn_on(self, device_name):
        pass

    @abstractmethod
    def turn_off(self, device_name):
        pass
