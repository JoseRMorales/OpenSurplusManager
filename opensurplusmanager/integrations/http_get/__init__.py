"""HTTP GET integration module."""

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
    """HTTP GET integration class, inherits from ConsumptionIntegration."""

    client: aiohttp.ClientSession = field(init=False)
    __timeout: int = field(default=30)

    def __load_entities(self):
        """Load entities from the core configuration."""
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
        self.__load_entities()
        self.__timeout = self.core.config["integrations"]["http_get"].get(
            "timeout", self.__timeout
        )

    async def run(self):
        """Indefinitely runs the HTTP GET integration. Every `timeout` seconds, it will
        query the configured entities."""
        logger.info("Running HTTP GET integration...")
        while True:
            for entity in self.entities:
                try:
                    async with self.client.get(entity.path) as response:
                        logger.debug(
                            "Got response from %s: %s. Content: %s",
                            entity.name,
                            response.status,
                            await response.text(),
                        )
                        try:
                            consumption = float(await response.text())
                            if entity.consumption_type == ConsumptionType.SURPLUS:
                                self.core.surplus = consumption
                            elif entity.consumption_type == ConsumptionType.DEVICE:
                                entity.device.consumption = consumption
                        except ValueError:
                            logger.error(
                                "Invalid API response for entity %s", entity.name
                            )
                except (
                    aiohttp.ClientConnectionError,
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                ):
                    logger.error(
                        "Could not connect to %s from entity %s. Trying again in %ss",
                        entity.path,
                        entity.name,
                        self.__timeout,
                    )
            await asyncio.sleep(self.__timeout)

    async def close(self):
        """Safely closes the HTTP GET integration"""
        logger.info("Closing HTTP GET integration...")
        await self.client.close()


async def setup(core: Core) -> HttpGet:
    """
    Method called by main to initialize the HTTP GET integration.

    Parameters:
        core (Core): The core instance.

    Returns:
        HttpGet: The initialized HTTP GET integration to close the integration
        if needed.
    """
    http_get = HttpGet(core)
    asyncio.create_task(http_get.run())

    return http_get
