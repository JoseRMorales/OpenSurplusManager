"""HTTP Post integration module."""

from dataclasses import dataclass, field

import aiohttp

from opensurplusmanager.core import Core
from opensurplusmanager.integrations.http_post.entity import HTTPPostEntity
from opensurplusmanager.models.integration import ControlIntegration
from opensurplusmanager.utils import logger


@dataclass
class HTTPPost(ControlIntegration):
    """HTTP Post integration class, inherits from ControlIntegration."""

    client: aiohttp.ClientSession = field(init=False)

    def __load_entities(self):
        """Load entities from the core configuration."""
        for device in self.core.config.get("devices", []):
            entry_type = device["control_integration"]
            logger.debug("Loading device %s", device["name"])
            # Check if exists 'turn_on' in entry type
            if "turn_on" in entry_type and entry_type["turn_on"]["name"] == "http_post":
                self.turn_on_entities[device["name"]] = HTTPPostEntity(
                    name=device["name"],
                    path=entry_type["turn_on"]["path"],
                    method=entry_type["turn_on"]["method"],
                    headers=entry_type["turn_on"]["headers"],
                    body=entry_type["turn_on"]["body"],
                )

            # Check if exists 'turn_off' in entry type
            if (
                "turn_off" in entry_type
                and entry_type["turn_off"]["name"] == "http_post"
            ):
                self.turn_off_entities[device["name"]] = HTTPPostEntity(
                    name=device["name"],
                    path=entry_type["turn_off"]["path"],
                    method=entry_type["turn_off"]["method"],
                    headers=entry_type["turn_off"]["headers"],
                    body=entry_type["turn_off"]["body"],
                )

            # Check if exists 'regulate' in entry type
            if (
                "regulate" in entry_type
                and entry_type["regulate"]["name"] == "http_post"
            ):
                self.regulate_entities[device["name"]] = HTTPPostEntity(
                    name=device["name"],
                    path=entry_type["regulate"]["path"],
                    method=entry_type["regulate"]["method"],
                    headers=entry_type["regulate"]["headers"],
                    body=entry_type["regulate"]["body"],
                )
            device_name = device["name"]
            self.core.add_control_integration(device_name, self)

    def __post_init__(self):
        logger.info("Initializing HTTP Post integration...")
        self.client = aiohttp.ClientSession()
        self.__load_entities()

    async def turn_on(self, device_name: str):
        """
        Turn on the device ordered by the core.

        Parameters
        device_name (str): The name of the device to turn on.
        """
        entity = self.turn_on_entities.get(device_name)
        if entity:
            async with self.client.post(
                entity.path, headers=entity.headers, json=entity.body
            ) as response:
                logger.debug(
                    "Got response from device %s: %s", entity.name, response.status
                )
        else:
            logger.error("Device %s not found in control integration", device_name)

    async def turn_off(self, device_name: str):
        """
        Turn off the device ordered by the core.

        Parameters
        device_name (str): The name of the device to turn off.
        """
        entity = self.turn_off_entities.get(device_name)
        if entity:
            async with self.client.post(
                entity.path, headers=entity.headers, json=entity.body
            ) as response:
                logger.debug(
                    "Got response from device %s: %s", entity.name, response.status
                )
        else:
            logger.error("Device %s not found in control integration", device_name)

    async def regulate(self, device_name: str, power: float):
        """
        Regulate the device ordered by the core.

        Parameters
        device_name (str): The name of the device to regulate.
        power (float): The power to regulate the device to.
        """
        entity = self.regulate_entities.get(device_name)
        # Replace the $power in the body with the power value
        send_body = dict(entity.body)
        for key, value in send_body.items():
            if value == "$power":
                send_body[key] = power
        if entity:
            async with self.client.post(
                entity.path, headers=entity.headers, json=send_body
            ) as response:
                logger.debug(
                    "Got response from device %s: %s", entity.name, response.status
                )
        else:
            logger.error("Device %s not found in control integration", device_name)

    async def close(self):
        """Safe close of the integration."""
        logger.info("Closing HTTP Post integration...")
        await self.client.close()


async def setup(core: Core) -> HTTPPost:
    """
    Method called by main to initialize the HTTP POST integration.

    Parameters:
        core (Core): The core instance.

    Returns:
        HttpGet: The initialized HTTP POST integration to close the integration
        if needed.
    """
    return HTTPPost(core)
