import asyncio
from dataclasses import dataclass, field
from typing import List

import aiohttp

from opensurplusmanager.core import Core
from opensurplusmanager.integrations.http_get.entity import HTTPGetEntity
from opensurplusmanager.integrations.http_get.sensor import HTTPGetSensor
from opensurplusmanager.models.consumption import ConsumptionEntity
from opensurplusmanager.models.sensor import SensorType
from opensurplusmanager.utils import logger


@dataclass
class HttpGet:
    core: Core
    entities: List[HTTPGetEntity] = field(default_factory=list)
    production: HTTPGetSensor = None
    surplus: HTTPGetSensor = None

    def __load_devices(self):
        if "surplus" in self.core.config and "http_get" in self.core.config["surplus"]:
            surplus_sensor = HTTPGetSensor(
                sensor_type=SensorType.SURPLUS,
                **self.core.config["surplus"]["http_get"],
            )
            self.surplus = surplus_sensor

        for device in self.core.config.get("devices", []):
            integration_name = device["consumption_integration"]["name"]
            if integration_name == "http_get":
                device_config = device["consumption_integration"]
                logger.debug("Loading device %s", device["name"])
                consumption_entity = ConsumptionEntity()
                entity = HTTPGetEntity(
                    name=device["name"],
                    path=device_config["path"],
                    consumption_entity=consumption_entity,
                )
                self.entities.append(entity)
                self.core.add_consumption_entity(entity.name, consumption_entity)

    def __init__(self, core: Core):
        logger.info("Initializing HTTP GET integration...")
        self.core = core
        self.entities: List[HTTPGetEntity] = []
        self.__load_devices()

    async def run(self) -> None:
        logger.info("Running HTTP GET integration...")
        while True:
            async with aiohttp.ClientSession() as session:
                if self.surplus:
                    async with session.get(self.surplus.path) as response:
                        logger.debug(
                            "Got response from surplus sensor: %s", response.status
                        )
                        # Set the surplus value
                        # Convert the response to a float
                        try:
                            self.core.surplus = float(await response.text())
                        except ValueError:
                            logger.error("Invalid API response for surplus sensor")

                entity: HTTPGetEntity
                for entity in self.entities:
                    async with session.get(entity.path) as response:
                        logger.debug(
                            "Got response from device %s: %s",
                            entity.name,
                            response.status,
                        )
                        # Set the device consumption value
                        # Convert the response to a float
                        try:
                            consumption = float(await response.text())
                            entity.set_consumption(consumption)
                            logger.debug(
                                "Got consumption from device %s: %s",
                                entity.name,
                                entity.get_consumption(),
                            )
                        except ValueError:
                            logger.error(
                                "Invalid API response for device %s", entity.name
                            )
            await asyncio.sleep(1)


async def setup(core: Core) -> bool:
    http_get = HttpGet(core)
    asyncio.create_task(http_get.run())

    return True
