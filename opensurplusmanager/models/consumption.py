from dataclasses import dataclass


@dataclass
class ConsumptionEntity:
    consumption = 0


@dataclass
class ConsumptionSensor:
    consumption_entity: ConsumptionEntity

    def get_consumption(self):
        return self.consumption_entity.consumption

    def set_consumption(self, consumption):
        self.consumption_entity.consumption = consumption
