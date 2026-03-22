from datetime import timedelta
import logging

from aiohttp import ClientResponseError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import SESSION_ENDPOINT, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


def parse_quic_date(obj: dict):
    """Extract datetime from Quic's {'$date': '...'} timestamp format."""
    if obj and "$date" in obj:
        return dt_util.parse_datetime(obj["$date"])
    return None


class QuicCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_key: str, service_id: str):
        self.api_key = api_key
        self.service_id = service_id
        super().__init__(
            hass,
            _LOGGER,
            name=f"Quic {service_id}",
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

    async def _async_update_data(self):
        session = async_get_clientsession(self.hass)
        try:
            resp = await session.get(
                SESSION_ENDPOINT,
                params={"service": self.service_id},
                headers={"X-API-Key": self.api_key},
            )
            resp.raise_for_status()
            data = await resp.json()

            # Pre-parse timestamps so sensors don't have to
            data["_parsed_last_radius"] = parse_quic_date(data.get("lastRadiusUpdate"))
            data["_parsed_expires"] = parse_quic_date(data.get("sessionExpiresAt"))

            return data

        except ClientResponseError as err:
            if err.status == 403:
                raise UpdateFailed("Invalid API key or service not authorized") from err
            raise UpdateFailed(f"HTTP error {err.status}") from err
        except Exception as err:
            raise UpdateFailed(f"Connection error: {err}") from err
