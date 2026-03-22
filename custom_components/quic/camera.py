import logging
from datetime import timedelta

from aiohttp import ClientResponseError
from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_API_KEY, WEATHERMAP_ENDPOINT, WEATHERMAP_CACHE_SECONDS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([QuicWeatherMapCamera(hass, entry)])


class QuicWeatherMapCamera(Camera):
    _attr_name = "Quic Network Weather Map"
    _attr_icon = "mdi:map-legend"
    _attr_is_streaming = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__()
        self.hass = hass
        self._entry = entry
        self._api_key = entry.data[CONF_API_KEY]
        self._cached_image: bytes | None = None
        self._cache_expiry = None

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_weathermap"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.data["service_id"])},
            "name": f"Quic Broadband — {self._entry.data['service_id']}",
            "manufacturer": "Quic",
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        from homeassistant.util import dt as dt_util

        now = dt_util.utcnow()

        # Return cached image if still fresh
        if self._cached_image and self._cache_expiry and now < self._cache_expiry:
            return self._cached_image

        # Fetch fresh image
        session = async_get_clientsession(self.hass)
        try:
            resp = await session.get(
                WEATHERMAP_ENDPOINT,
                headers={"X-API-Key": self._api_key},
            )
            resp.raise_for_status()
            self._cached_image = await resp.read()
            self._cache_expiry = now + timedelta(seconds=WEATHERMAP_CACHE_SECONDS)
            return self._cached_image

        except ClientResponseError as err:
            _LOGGER.error("Failed to fetch Quic weather map: HTTP %s", err.status)
            return self._cached_image  # return stale image rather than nothing
        except Exception as err:
            _LOGGER.error("Failed to fetch Quic weather map: %s", err)
            return self._cached_image
