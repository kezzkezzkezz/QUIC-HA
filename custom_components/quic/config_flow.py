import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_API_KEY, CONF_SERVICE_ID, SERVICES_ENDPOINT


@config_entries.HANDLERS.register(DOMAIN)
class QuicConfigFlow(config_entries.ConfigFlow):
    VERSION = 1

    _api_key: str
    _service_ids: list

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            self._api_key = user_input[CONF_API_KEY]
            session = async_get_clientsession(self.hass)
            try:
                resp = await session.get(
                    SERVICES_ENDPOINT,
                    headers={"X-API-Key": self._api_key},
                )
                if resp.status == 403:
                    errors["base"] = "invalid_auth"
                elif resp.status != 200:
                    errors["base"] = "cannot_connect"
                else:
                    data = await resp.json()
                    self._service_ids = data.get("serviceIds", [])
                    if not self._service_ids:
                        errors["base"] = "no_services"
                    elif len(self._service_ids) == 1:
                        return self._create_entry(self._service_ids[0])
                    else:
                        return await self.async_step_select_service()
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def async_step_select_service(self, user_input=None):
        if user_input is not None:
            return self._create_entry(user_input[CONF_SERVICE_ID])

        return self.async_show_form(
            step_id="select_service",
            data_schema=vol.Schema({
                vol.Required(CONF_SERVICE_ID): vol.In(self._service_ids)
            }),
        )

    def _create_entry(self, service_id: str):
        return self.async_create_entry(
            title=f"Quic — {service_id}",
            data={CONF_API_KEY: self._api_key, CONF_SERVICE_ID: service_id},
        )
