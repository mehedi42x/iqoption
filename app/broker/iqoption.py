"""Fail-closed placeholder for IQ Option connectivity.

No official, secure API implementation was verified for this project. The inspected
community client disables TLS certificate verification, so it is intentionally not
imported or wrapped here. This adapter must not silently fall back to insecure TLS.
"""


class IQOptionIntegrationUnavailable(RuntimeError):
    pass


class IQOptionBroker:
    def __init__(self, email: str = "", password: str = "") -> None:
        # Avoid retaining or logging credentials while the adapter is unavailable.
        raise IQOptionIntegrationUnavailable(
            "Live IQ Option access is disabled: no secure, supported broker adapter is configured. "
            "Use BROKER_MODE=paper; do not install an unverified client or disable TLS checks."
        )
