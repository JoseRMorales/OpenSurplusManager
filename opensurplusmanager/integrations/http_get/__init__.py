import asyncio
from dataclasses import dataclass, field

import aiohttp

from opensurplusmanager.core import Core
from opensurplusmanager.integrations.http_get.entity import HTTPGetEntity
from opensurplusmanager.models.entity import ConsumptionType
from opensurplusmanager.models.integration import ConsumptionIntegration
from opensurplusmanager.utils import logger


@dataclass
class HttpGet(ConsumptionIntegration):
    client: aiohttp.ClientSession = field(init=False)
    timeout: int = field(default=0.2)

    def __load_devices(self):
        if "surplus" in self.core.config and "http_get" in self.core.config["surplus"]:
            surplus = HTTPGetEntity(
                device=None,
                consumption_type=ConsumptionType.SURPLUS,
                name="Surplus",
                **self.core.config["surplus"]["http_get"],
            )
            self.entities.append(surplus)

        for device in self.core.config.get("devices", []):
            integration_name = device["consumption_integration"]["name"]
            if integration_name == "http_get":
                device_config = device["consumption_integration"]
                logger.debug("Loading device %s", device["name"])
                device_name = device["name"]
                device = self.core.get_device(device_name)
                consumption_entity = HTTPGetEntity(
                    consumption_type=ConsumptionType.DEVICE,
                    device=device,
                    **device_config,
                )
                self.entities.append(consumption_entity)

    def __post_init__(self):
        logger.info("Initializing HTTP GET integration...")
        self.client = aiohttp.ClientSession()
        self.__load_devices()

    async def run(self) -> None:
        logger.info("Running HTTP GET integration...")
        while True:
            for entity in self.entities:
                async with self.client.get(entity.path) as response:
                    logger.debug(
                        "Got response from %s: %s",
                        entity.name,
                        response.status,
                    )
                    try:
                        consumption = float(await response.text())
                        if entity.consumption_type == ConsumptionType.SURPLUS:
                            self.core.surplus = consumption
                        elif entity.consumption_type == ConsumptionType.DEVICE:
                            entity.device.consumption = consumption
                    except ValueError:
                        logger.error("Invalid API response for entity %s", entity.name)
            await asyncio.sleep(self.timeout)

    async def close(self) -> None:
        logger.info("Closing HTTP GET integration...")
        await self.client.close()


async def setup(core: Core):
    http_get = HttpGet(core)
    asyncio.create_task(http_get.run())

    return http_get
