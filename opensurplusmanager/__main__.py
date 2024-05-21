"""Main module for the Open Surplus Manager application."""

import asyncio
import importlib
import os
import sys

import yaml

from opensurplusmanager.core import Core
from opensurplusmanager.utils import logger

core = Core()


async def _load_integrations() -> None:
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
                    await module.setup(core)


def _load_config() -> None:
    """Load the configuration for the Open Surplus Manager application."""
    logger.info("Loading configuration...")
    with open("config.yaml", "r", encoding="utf-8") as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
        core.config = config


async def main() -> int:
    """Main entry point for the Open Surplus Manager application."""
    _load_config()
    core.load_config()
    await _load_integrations()
    await core.run()


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
