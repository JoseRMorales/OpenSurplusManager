"""MQTT Subscribe integration module."""

import asyncio
from dataclasses import dataclass, field

import aiomqtt

from opensurplusmanager.core import Core
from opensurplusmanager.exceptions import IntegrationInitializationError
from opensurplusmanager.integrations.mqtt_sub.entity import MQTTSubEntity
from opensurplusmanager.models.entity import ConsumptionType
from opensurplusmanager.models.integration import ConsumptionIntegration
from opensurplusmanager.utils import logger


@dataclass
class MQTTSub(ConsumptionIntegration):
    """MQTT Subscribe integration class, inherits from ConsumptionIntegration."""

    client: aiomqtt.Client = field(init=False)

    def __load_entities(self):
        """Load entities from the core configuration."""
        if "surplus" in self.core.config and "mqtt_sub" in self.core.config["surplus"]:
            surplus = MQTTSubEntity(
                device=None,
                consumption_type=ConsumptionType.SURPLUS,
                name="Surplus",
                **self.core.config["surplus"]["mqtt_sub"],
            )
            self.entities.append(surplus)

        for device in self.core.config.get("devices", []):
            integration_name = device["consumption_integration"]["name"]
            if integration_name == "mqtt_sub":
                device_config = device["consumption_integration"]
                logger.debug("Loading device %s", device["name"])
                device_name = device["name"]
                device = self.core.get_device(device_name)
                consumption_entity = MQTTSubEntity(
                    consumption_type=ConsumptionType.DEVICE,
                    device=device,
                    **device_config,
                )
                self.entities.append(consumption_entity)

    def __post_init__(self):
        logger.info("Initializing MQTT Subscribe integration...")
        try:
            hostname = self.core.config["integrations"]["mqtt_sub"]["hostname"]
        except KeyError as e:
            raise IntegrationInitializationError("Hostname not found in config") from e
        username = self.core.config["integrations"]["mqtt_sub"].get("username", None)
        password = self.core.config["integrations"]["mqtt_sub"].get("password", None)
        port = self.core.config["integrations"]["mqtt_sub"].get("port", 1883)
        self.client = aiomqtt.Client(
            hostname=hostname,
            identifier="opensurplusmanager",
            username=username,
            password=password,
            port=port,
        )
        self.__load_entities()

    async def run(self):
        """
        Indefinitely runs the MQTT Subscribe integration. It will subscribe to the
        configured entities and update the core with the consumption values.
        """
        logger.info("Running MQTT Subscribe integration...")
        for entity in self.entities:
            try:
                async with self.client:
                    await self.client.subscribe(entity.topic)
                    logger.debug("Subscribed to topic %s", entity.topic)
                    async for message in self.client.messages:
                        logger.debug(
                            "Got message from %s: %s",
                            entity.name,
                            message.payload.decode(),
                        )
                        try:
                            consumption = float(message.payload.decode())
                            if entity.consumption_type == ConsumptionType.SURPLUS:
                                self.core.surplus = consumption
                            elif entity.consumption_type == ConsumptionType.DEVICE:
                                entity.device.consumption = consumption
                        except ValueError:
                            logger.error(
                                "Error parsing consumption value from message: %s",
                                message.payload,
                            )
            except aiomqtt.exceptions.MqttError as e:
                logger.error("Error subscribing to topic %s: %s", entity.topic, e)

    async def close(self):
        """Close the MQTT Subscribe integration."""
        logger.info("Closing MQTT Subscribe integration...")


async def setup(core: Core) -> MQTTSub:
    """
    Method called by main to initialize the MQTT subscription integration.

    Parameters:
        core (Core): The core instance.

    Returns:
        HttpGet: The initialized MQTT subscription integration to close the integration
        if needed.
    """
    mqtt_sub = MQTTSub(core)
    asyncio.create_task(mqtt_sub.run())

    return mqtt_sub
