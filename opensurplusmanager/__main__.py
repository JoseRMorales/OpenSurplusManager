"""Main module for the Open Surplus Manager application."""

import asyncio
import importlib
import os
import sys

import yaml

from opensurplusmanager.core import Core
from opensurplusmanager.utils import logger

core = Core()

integrations = []


async def __load_integrations() -> None:
    """Load the integrations for the Open Surplus Manager application."""
    logger.info("Loading integrations...")

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the "integrations" folder relative to the script directory
    integrations_folder = os.path.join(script_dir, "integrations")

    for integration_dir in os.listdir(integrations_folder):
        integration_path = os.path.join(integrations_folder, integration_dir)
        if os.path.isdir(integration_path):
            init_file = os.path.join(integration_path, "__init__.py")
            if os.path.exists(init_file):
                spec = importlib.util.spec_from_file_location("__init__", init_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "setup"):
                    integration = await module.setup(core)
                    if integration is not None:
                        integrations.append(integration)


def __load_config() -> None:
    """Load the configuration for the Open Surplus Manager application."""
    logger.info("Loading configuration...")
    with open("config.yaml", "r", encoding="utf-8") as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
        core.config = config


async def main() -> int:
    """Main entry point for the Open Surplus Manager application."""
    __load_config()
    core.load_config()
    await __load_integrations()
    await core.run()


async def close_integrations() -> None:
    """Close the integrations for the Open Surplus Manager application."""
    logger.info("Closing integrations...")
    for integration in integrations:
        if hasattr(integration, "close"):
            await integration.close()

    logger.info("Integrations closed")


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        asyncio.run(close_integrations())
        logger.info("Shutdown completed")
        sys.exit(0)
