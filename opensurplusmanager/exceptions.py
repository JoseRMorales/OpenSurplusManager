"""Custom exceptions for Open Surplus Manager."""


class IntegrationInitializationError(Exception):
    """Raised when an error occurs during the initialization of an integration."""


class InvalidDeviceType(Exception):
    """Raised when an invalid device type is used."""


class IntegrationConnectionError(Exception):
    """Raised when an error occurs when managin a device connection."""
