from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import QuicCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: QuicCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        QuicConnectionBinarySensor(coordinator, entry),
        QuicServiceActiveBinarySensor(coordinator, entry),
        QuicRadiusHealthBinarySensor(coordinator, entry),
    ])


class QuicBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator: QuicCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.data["service_id"])},
            "name": f"Quic Broadband — {self._entry.data['service_id']}",
            "manufacturer": "Quic",
            "model": self.coordinator.data.get("service", {}).get("lfc", "Fibre"),
        }


class QuicConnectionBinarySensor(QuicBaseBinarySensor):
    _attr_name = "Connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_connected"

    @property
    def is_on(self):
        return self.coordinator.data.get("status") == "connected"

    @property
    def extra_state_attributes(self):
        return {
            "status": self.coordinator.data.get("status"),
            "session_type": self.coordinator.data.get("sessionType"),
        }


class QuicServiceActiveBinarySensor(QuicBaseBinarySensor):
    _attr_name = "Service Active"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_service_active"

    @property
    def is_on(self):
        return self.coordinator.data.get("service", {}).get("status") == "active"

    @property
    def extra_state_attributes(self):
        service = self.coordinator.data.get("service", {})
        return {
            "entity": service.get("entity"),
            "entity_unique_id": service.get("entityUniqueId"),
            "asid": service.get("asid"),
        }


class QuicRadiusHealthBinarySensor(QuicBaseBinarySensor):
    """Goes off (False) if RADIUS hasn't updated in over 25 minutes — session about to drop."""
    _attr_name = "RADIUS Health"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:shield-check"

    RADIUS_STALE_THRESHOLD_SECONDS = 25 * 60  # 25 minutes

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_radius_health"

    @property
    def is_on(self):
        parsed = self.coordinator.data.get("_parsed_last_radius")
        if parsed is None:
            return False
        age = (dt_util.utcnow() - parsed).total_seconds()
        return age < self.RADIUS_STALE_THRESHOLD_SECONDS

    @property
    def extra_state_attributes(self):
        parsed = self.coordinator.data.get("_parsed_last_radius")
        if parsed:
            age = (dt_util.utcnow() - parsed).total_seconds()
            return {
                "last_update": parsed.isoformat(),
                "age_seconds": round(age),
                "threshold_seconds": self.RADIUS_STALE_THRESHOLD_SECONDS,
            }
        return {}
