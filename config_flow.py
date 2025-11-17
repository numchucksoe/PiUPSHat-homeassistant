from homeassistant import config_entries
import voluptuous as vol
import aiohttp
import asyncio
from .const import DOMAIN

class PIUPSHATFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            url = user_input["url"]

            # Test API reachability
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as resp:
                        if resp.status != 200:
                            errors["base"] = f"http_{resp.status}"
                        else:
                            await resp.json()
            except asyncio.TimeoutError:
                errors["base"] = "timeout"
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"PIUPSHAT ({url})",
                    data=user_input,
                )

        data_schema = vol.Schema({
            vol.Required("url", default="http://192.168.2.158:5000/api/read"): str
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

