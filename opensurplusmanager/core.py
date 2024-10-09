"""This file contains the main logic for the application."""

import asyncio
import os
from dataclasses import dataclass, field
from typing import Dict

import yaml

from opensurplusmanager.api import Api
from opensurplusmanager.models.device import (
    Device,
    DeviceType,
    IntegrationConnectionError,
)
from opensurplusmanager.models.integration import ControlIntegration
from opensurplusmanager.utils import logger

config_file_name = os.getenv("CONFIG_FILE", "config.yaml")


@dataclass
class Core:
    """
    The core of the Open Surplus Manager application. Contains
    the attributes and methods to manage the devices and integrations.
    """

    consumption = 0
    production = 0
    __surplus = 0
    # How much surplus power is left in a normal case.
    # Positive is a surplus, negative is grid consumption.
    __surplus_margin: float | None = field(default=100)
    # In case of a power peak where grid power is needed, how much
    # is tolerated before turning off devices.
    __grid_margin: float | None = field(default=100)
    config: Dict = field(default_factory=dict)
    __idle_power: float = field(default=100)
    devices: Dict[str, Device] = field(default_factory=dict)
    api: Api | None = None

    @property
    def surplus(self) -> float:
        """The surplus power available."""
        return self.__surplus

    @surplus.setter
    def surplus(self, value):
        """Set the surplus power available. Creates a task to update the devices."""
        logger.info("Setting surplus to %s", value)
        self.__surplus = value
        asyncio.create_task(self.__update())

    @property
    def surplus_margin(self) -> float:
        """
        The margin of surplus power left. Positive is a surplus,
        negative is grid consumption.
        """
        return self.__surplus_margin

    @surplus_margin.setter
    def surplus_margin(self, value):
        """Set the surplus_margin. Updates the config and saves it."""
        logger.info("Setting surplus margin to %s", value)
        self.__surplus_margin = value
        self.config["surplus_margin"] = value
        self.save_config()

    @property
    def grid_margin(self) -> float:
        """The margin of grid power to tolerate before turning off devices."""
        return self.__grid_margin

    @grid_margin.setter
    def grid_margin(self, value):
        """Set the grid_margin. Updates the config and saves it."""
        logger.info("Setting grid margin to %s", value)
        self.__grid_margin = value
        self.config["grid_margin"] = value
        self.save_config()

    @property
    def idle_power(self) -> float:
        """
        The idle power consumption of the devices.
        Some devices may have a consumption even when turned off.
        """
        return self.__idle_power

    @idle_power.setter
    def idle_power(self, value):
        """
        Set the idle power consumption of the devices.
        Updates the config and saves it.
        """
        logger.info("Setting idle power to %s", value)
        self.__idle_power = value
        self.config["idle_power"] = value
        self.save_config()

    async def __turn_on_priority(self, available_power: float):
        """
        Turn on devices in priority order until there is no more power left.
        The priority is based on the order of the devices in the config file.

        Depending on the device type, the device will be turned on or regulated.

        Parameters:
        available_power (float): The power available to turn on devices.
        """
        devices = list(self.devices.values())
        for device in filter(lambda x: x.enabled, devices):
            if device.device_type == DeviceType.SWITCH:
                if device.expected_consumption < available_power and not device.powered:
                    try:
                        await device.turn_on()
                    except IntegrationConnectionError:
                        continue
                    available_power -= device.expected_consumption
            elif device.device_type == DeviceType.REGULATED:
                if device.expected_consumption < available_power and not device.powered:
                    try:
                        await device.turn_on()
                    except IntegrationConnectionError:
                        continue
                    device_power = (
                        device.max_consumption
                        if available_power > device.max_consumption
                        else available_power
                    )
                    try:
                        await device.regulate(device_power)
                    except IntegrationConnectionError:
                        continue
                    available_power -= device_power
                elif device.powered and device.consumption > self.idle_power:
                    total_device_power = device.consumption + available_power
                    device_power = (
                        device.max_consumption
                        if total_device_power > device.max_consumption
                        else total_device_power
                    )
                    try:
                        await device.regulate(device_power)
                    except IntegrationConnectionError:
                        continue
                    added_power = device_power - device.consumption
                    available_power -= added_power

    async def __turn_off_priority(self, exceeded_power: float):
        """
        Turn off devices in priority order until the exceeded power is 0.

        Depending on the device type, the device will be turned off or regulated.

        Parameters:
        exceeded_power (float): The power that needs to be turned off.
        """
        devices = reversed(self.devices.values())
        for device in filter(lambda x: x.enabled, devices):
            if device.powered and device.consumption > self.idle_power:
                if device.device_type == DeviceType.SWITCH:
                    try:
                        await device.turn_off()
                    except IntegrationConnectionError:
                        continue
                    exceeded_power -= device.expected_consumption

                elif device.device_type == DeviceType.REGULATED:
                    if (
                        exceeded_power
                        > device.consumption - device.expected_consumption
                    ):
                        try:
                            await device.turn_off()
                        except IntegrationConnectionError:
                            continue
                        exceeded_power -= device.expected_consumption
                    else:
                        await device.regulate(device.consumption - exceeded_power)
                        break

            if exceeded_power < 0:
                break

    async def __update(self):
        """
        Every time the surplus is updated this method is called so devices
        can be turned on/off or regulated based on the new surplus data
        available.
        """
        logger.info("Core is running")
        self.__debug()
        if self.surplus > 0:
            await self.__turn_on_priority(self.surplus)
        elif self.surplus < (-self.grid_margin):
            await self.__turn_off_priority(-self.surplus + self.surplus_margin)

    def __debug(self):
        """
        Print debug information about the core and devices. Only
        prints if the logger is in debug
        """
        logger.debug("Core debug:")
        logger.debug("Surplus: %s", self.surplus)
        logger.debug("Devices:")
        for device in self.devices.values():
            logger.debug("  %s:", device.name)
            logger.debug("    Powered: %s", device.powered)
            logger.debug("    Expected consumption: %s", device.expected_consumption)
            logger.debug("    Consumption: %s", device.consumption)
            logger.debug("    Max consumption: %s", device.max_consumption)
            logger.debug("    Enabled: %s", device.enabled)

    def add_control_integration(self, name: str, integration: ControlIntegration):
        """
        Add a control integration to a device in the core. When a new device is loaded
        from a integration it will call this method to add the integration to the
        device. With this the device can be controlled by the integration from the core.

        Parameters:
        name (str): The name of the device to add the integration to.
        integration (ControlIntegration): The integration to add to the device.
        """
        if name in self.devices:
            self.devices[name].control_integration = integration
        logger.info("Added control integration to device %s to core", name)

    async def run(self):
        """Entry point for the core. This method will start the API."""
        api = Api(core=self)
        self.api = api
        await api.run()

    def load_config(self):
        """
        Loads the configuration loaded by the core into the attributes and devices
        of the core object.
        """
        self.__grid_margin = self.config.get("grid_margin", self.grid_margin)
        self.__surplus_margin = self.config.get("surplus_margin", self.surplus_margin)

        devices = self.config.get("devices", [])

        for device in devices:
            name = device["name"]
            device_type = DeviceType(device["type"])
            expected_consumption = device["expected_consumption"]
            max_consumption = device.get("max_consumption", None)
            cooldown = device.get("cooldown", None)
            new_device = Device(
                name=name,
                core=self,
                device_type=device_type,
                expected_consumption=expected_consumption,
                max_consumption=max_consumption,
                cooldown=cooldown,
            )
            self.devices[name] = new_device
            logger.info("Added device %s to core", name)

    def save_config(self):
        """Creates a task to save the configuration to the config file."""
        logger.info("Saving config...")
        asyncio.create_task(self.__save_config_task())

    async def __save_config_task(self):
        """Saves the configuration to the config file."""
        with open(config_file_name, "w", encoding="utf-8") as file:
            yaml.dump(self.config, file, default_flow_style=False)

    def get_device(self, name: str) -> Device | None:
        """
        Get a device by name from the core.

        Parameters:
        name (str): The name of the device to get.

        Returns:
        Device: The device with the name given.
        """
        return self.devices.get(name, None)
