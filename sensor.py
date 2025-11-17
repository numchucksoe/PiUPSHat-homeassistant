from __future__ import annotations
import logging
import aiohttp
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    PERCENTAGE,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    url = entry.data["url"]
    coordinator = PIUPSHATCoordinator(hass, url)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        PIUPSHATSensor(coordinator, "load_voltage_V", "Load Voltage", UnitOfElectricPotential.VOLT, url),
        PIUPSHATSensor(coordinator, "shunt_voltage_V", "Shunt Voltage", UnitOfElectricPotential.VOLT, url),
        PIUPSHATSensor(coordinator, "current_A", "Current", UnitOfElectricCurrent.AMPERE, url),
        PIUPSHATSensor(coordinator, "power_W", "Power", UnitOfPower.WATT, url),
        PIUPSHATSensor(coordinator, "percent", "Percent", PERCENTAGE, url),
    ]
    async_add_entities(sensors, True)


class PIUPSHATCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, url):
        super().__init__(
            hass,
            _LOGGER,
            name=f"PIUPSHAT API {url}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.url = url

    async def _async_update_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, timeout=10) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status}")
                    data = await resp.json()
                    return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")


class PIUPSHATSensor(SensorEntity):
    def __init__(self, coordinator, key, name, unit, url):
        self.coordinator = coordinator
        device_name = self.coordinator.data.get("name")
        self._key = key
        self._attr_name = f"{device_name} PIUPSHAT {name}"
        self._attr_unique_id = f"piupshat_{url}_{key}".replace("://", "_").replace("/", "_")
        self._attr_native_unit_of_measurement = unit
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, url)},
            name=f"PIUPSHAT API {device_name} ({url})",
            manufacturer="BuchananFamily",
        )

    @property
    def native_value(self):
        if self.coordinator.data:
            return self.coordinator.data.get(self._key)
        return None

    async def async_update(self):
        await self.coordinator.async_request_refresh()

