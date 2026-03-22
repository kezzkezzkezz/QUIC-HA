from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
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
        QuicSessionTypeSensor(coordinator, entry),
        QuicActiveIPv4Sensor(coordinator, entry),
        QuicActiveIPv6Sensor(coordinator, entry),
        QuicServiceStatusSensor(coordinator, entry),
        QuicLFCSensor(coordinator, entry),
        QuicLastRadiusUpdateSensor(coordinator, entry),
        QuicSessionExpiresSensor(coordinator, entry),
        QuicBNGNodeSensor(coordinator, entry),
        QuicCircuitIDSensor(coordinator, entry),
    ])


class QuicBaseSensor(CoordinatorEntity, SensorEntity):
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


class QuicSessionTypeSensor(QuicBaseSensor):
    _attr_name = "Session Type"
    _attr_icon = "mdi:swap-horizontal"

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_session_type"

    @property
    def native_value(self):
        return self.coordinator.data.get("sessionType")


class QuicActiveIPv4Sensor(QuicBaseSensor):
    _attr_name = "Active IPv4"
    _attr_icon = "mdi:ip-network"

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_active_ipv4"

    @property
    def native_value(self):
        return self.coordinator.data.get("activeIPv4Prefix")

    @property
    def extra_state_attributes(self):
        return {
            "prefix_length": self.coordinator.data.get("activeIPv4PrefixLength"),
        }


class QuicActiveIPv6Sensor(QuicBaseSensor):
    _attr_name = "Active IPv6"
    _attr_icon = "mdi:ip-network-outline"

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_active_ipv6"

    @property
    def native_value(self):
        return self.coordinator.data.get("activeIPv6Prefix")

    @property
    def extra_state_attributes(self):
        return {
            "prefix_length": self.coordinator.data.get("activeIPv6PrefixLength"),
        }


class QuicServiceStatusSensor(QuicBaseSensor):
    _attr_name = "Service Status"
    _attr_icon = "mdi:check-network"

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_service_status"

    @property
    def native_value(self):
        return self.coordinator.data.get("service", {}).get("status")


class QuicLFCSensor(QuicBaseSensor):
    _attr_name = "Fibre Company"
    _attr_icon = "mdi:fiber-optic"

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_lfc"

    @property
    def native_value(self):
        return self.coordinator.data.get("service", {}).get("lfc")


class QuicLastRadiusUpdateSensor(QuicBaseSensor):
    _attr_name = "Last RADIUS Update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check"

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_last_radius"

    @property
    def native_value(self):
        return self.coordinator.data.get("_parsed_last_radius")

    @property
    def extra_state_attributes(self):
        parsed = self.coordinator.data.get("_parsed_last_radius")
        if parsed:
            age = (dt_util.utcnow() - parsed).total_seconds()
            return {"age_seconds": round(age)}
        return {}


class QuicSessionExpiresSensor(QuicBaseSensor):
    _attr_name = "Session Expires"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-end"

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_session_expires"

    @property
    def native_value(self):
        return self.coordinator.data.get("_parsed_expires")

    @property
    def extra_state_attributes(self):
        parsed = self.coordinator.data.get("_parsed_expires")
        if parsed:
            remaining = (parsed - dt_util.utcnow()).total_seconds()
            return {"remaining_seconds": round(remaining)}
        return {}


class QuicBNGNodeSensor(QuicBaseSensor):
    _attr_name = "BNG Node"
    _attr_icon = "mdi:server-network"

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_bng_node"

    @property
    def native_value(self):
        return self.coordinator.data.get("pppPayload", {}).get("nasIdentifier")

    @property
    def extra_state_attributes(self):
        ppp = self.coordinator.data.get("pppPayload", {})
        return {
            "nas_ip": ppp.get("nasIPAddress"),
            "nas_port": ppp.get("nasPort"),
            "nas_port_type": ppp.get("nasPortType"),
        }


class QuicCircuitIDSensor(QuicBaseSensor):
    _attr_name = "Circuit ID"
    _attr_icon = "mdi:transit-connection-variant"

    @property
    def unique_id(self):
        return f"quic_{self._entry.data['service_id']}_circuit_id"

    @property
    def native_value(self):
        return self.coordinator.data.get("pppPayload", {}).get("adslAgentCircuitId")

    @property
    def extra_state_attributes(self):
        ppp = self.coordinator.data.get("pppPayload", {})
        return {
            "remote_id": ppp.get("adslAgentRemoteId"),
        }
