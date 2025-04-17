"""
Centralized helper for sending anonymised events to PostHog.

Usage
-----
    from spongecake.telemetry.posthog_service import Telemetry

    Telemetry.capture(
        event="agent.action_called",
        properties={"action_name": "click", "duration_ms": 123}
    )

Design notes
------------
* 100 % optional – set ``SPONGECAKE_DISABLE_TELEMETRY=true`` **or**
  ``SPONGECAKE_TELEMETRY=false`` to turn it off.
* Logs only when ``SPONGECAKE_TELEMETRY_DEBUG=1``.
* User‑ID is a random UUID stored at ``~/.cache/spongecake/telemetry_user_id``.
* Relies on the PostHog Python client’s built‑in async queue, so calls are non‑blocking.
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Any, Callable, TypeVar

from dotenv import load_dotenv
from posthog import Posthog

load_dotenv()

# --------------------------------------------------------------------------- #
# Helper: simple singleton decorator
# --------------------------------------------------------------------------- #
T = TypeVar("T")


def _singleton(cls: Callable[..., T]) -> Callable[..., T]:
    _instance: T | None = None

    def _wrapper(*args: Any, **kwargs: Any) -> T:  # noqa: D401
        nonlocal _instance
        if _instance is None:
            _instance = cls(*args, **kwargs)
        return _instance

    return _wrapper


# --------------------------------------------------------------------------- #
# Module‑level constants
# --------------------------------------------------------------------------- #
_PROJECT_API_KEY = 'phc_lgUc6tFsgkO4oTZi7CjQIk2SNk49JjptqxT2gYaOREC'
_HOST = 'https://us.i.posthog.com'

_USER_ID_FILE = Path.home() / ".cache" / "spongecake" / "telemetry_user_id"

_DISABLE = os.getenv("SPONGECAKE_DISABLE_TELEMETRY", "").lower() == "true" or (
    os.getenv("SPONGECAKE_TELEMETRY", "true").lower() == "false"
)
_DEBUG = os.getenv("SPONGECAKE_TELEMETRY_DEBUG") == "1"

# --------------------------------------------------------------------------- #
# Logging setup
# --------------------------------------------------------------------------- #
_log = logging.getLogger("spongecake.telemetry.posthog")
if _DEBUG:
    logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")
    _log.debug("Debug logging ON (SPONGECAKE_TELEMETRY_DEBUG=1)")


# --------------------------------------------------------------------------- #
# Telemetry service
# --------------------------------------------------------------------------- #
@_singleton
class Telemetry:
    """Singleton wrapper around the PostHog client."""

    def __init__(self) -> None:  # noqa: D401
        self._client: Posthog | None
        if _DISABLE:
            _log.debug("Telemetry globally disabled via env‑vars.")
            self._client = None
        else:
            _log.info(
                "Anonymised telemetry enabled "
                "(see https://docs.spongecake.ai/development/telemetry)."
            )
            self._client = Posthog(
                project_api_key=_PROJECT_API_KEY,
                host=_HOST,
                disable_geoip=False,
            )

            # Silence PostHog’s noisy logger unless debugging
            if not _DEBUG:
                logging.getLogger("posthog").disabled = True

        self._user_id: str | None = None

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def capture(self, event: str, properties: dict[str, Any] | None = None) -> None:
        """Send ``event`` with ``properties`` (non‑blocking)."""
        if not self._client:
            return

        props: dict[str, Any] = {**(properties or {})}

        if _DEBUG:
            _log.debug("Event: %-24s %s", event, props)

        try:
            self._client.capture(self.user_id, event, props)
        except Exception as exc:  # noqa: BLE001
            _log.debug("Failed to send event %s (%s)", event, exc)

    # ------------------------------------------------------------------ #
    # Lazy‑generated anonymous user‑ID
    # ------------------------------------------------------------------ #
    @property
    def user_id(self) -> str:  # noqa: D401
        """Return a stable, anonymous UUID for this machine."""
        if self._user_id:
            return self._user_id

        try:
            if _USER_ID_FILE.exists():
                self._user_id = _USER_ID_FILE.read_text()
            else:
                _USER_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
                self._user_id = uuid.uuid4().hex
                _USER_ID_FILE.write_text(self._user_id)

        except Exception:  # noqa: BLE001
            self._user_id = "UNKNOWN"  # fallback: still counts distinct events

        return self._user_id
