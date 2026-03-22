# Quic Broadband — Home Assistant Integration

A custom HACS integration for monitoring your [Quic Broadband NZ](https://quic.nz) connection from Home Assistant.

---

## Features

- **Connection status** — live binary sensor showing connected/disconnected
- **Service status** — whether your service is active or suspended
- **Active IPv4 & IPv6** — track your current IPs, get notified if they change
- **Session expiry & RADIUS health** — early warning before a session drop
- **BNG node & circuit ID** — Chorus infrastructure detail for fault diagnosis
- **Network weather map** — Quic's network congestion map as a camera entity, cached and auth-handled internally

---

## Requirements

- Home Assistant 2026.3.0 or newer
- HACS installed
- A Quic Broadband account with an API key (generated in the [Quic account portal](https://quic.nz))

---

## Installation

### Via HACS (recommended)

1. In Home Assistant, go to **HACS → Integrations**
2. Click the three-dot menu → **Custom repositories**
3. Add `https://github.com/kezzkezzkezz/quic-ha-integration` with category **Integration**
4. Click **Download**
5. Restart Home Assistant

### Manual

1. Copy `custom_components/quic/` into your HA `config/custom_components/` directory
2. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Quic Broadband**
3. Enter your API key
4. If you have multiple services, select the one to monitor
5. Done — all entities will appear under a single device

---

## Entities

### Sensors

| Entity | Description |
|---|---|
| Session Type | DHCP or PPPoE |
| Active IPv4 | Current public IPv4 address |
| Active IPv6 | Current IPv6 prefix |
| Service Status | active / suspended |
| Fibre Company | e.g. Chorus |
| Last RADIUS Update | Timestamp of last RADIUS refresh |
| Session Expires | When the current session lease expires |
| BNG Node | Which Quic BNG node you're connected to |
| Circuit ID | Chorus physical port path |

### Binary Sensors

| Entity | Description |
|---|---|
| Connection | On when session status is `connected` |
| Service Active | On when service status is `active` |
| RADIUS Health | Off if RADIUS hasn't updated in 25+ minutes — early warning of an impending drop |

### Camera

| Entity | Description |
|---|---|
| Quic Network Weather Map | Quic's network congestion map, refreshed every 6 minutes |

---

## Example Automations

### Notify on connection drop
```yaml
automation:
  trigger:
    - platform: state
      entity_id: binary_sensor.connection
      to: "off"
  action:
    - service: notify.mobile_app
      data:
        title: "Quic connection down"
        message: "Your broadband connection has dropped."
```

### Notify on IP change
```yaml
automation:
  trigger:
    - platform: state
      entity_id: sensor.active_ipv4
  action:
    - service: notify.mobile_app
      data:
        title: "Quic IP changed"
        message: "New IP: {{ states('sensor.active_ipv4') }}"
```

### Warn on RADIUS health failure
```yaml
automation:
  trigger:
    - platform: state
      entity_id: binary_sensor.radius_health
      to: "off"
  action:
    - service: notify.mobile_app
      data:
        title: "Quic RADIUS warning"
        message: "RADIUS hasn't refreshed in 25 minutes — connection may drop soon."
```

---

## Dashboard Card

Add the weather map to your dashboard:
```yaml
type: picture-entity
entity: camera.quic_network_weather_map
show_name: true
show_state: false
```

---

## Update Interval

Session data is polled every **5 minutes**, matching Quic's server-side cache TTL. The weather map is cached for **6 minutes**, also matching Quic's cache TTL. These are intentional — polling faster will return the same data and adds unnecessary load.

---

## Issues & Contributions

Found a bug? Open an issue or PR at [github.com/kezzkezzkezz/quic-ha-integration](https://github.com/kezzkezzkezz/quic-ha-integration/issues).

---

## Disclaimer

This integration is unofficial and not affiliated with or endorsed by Quic Broadband NZ. Use at your own risk.
