"""Config flow for NIU integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .api import NiuAPI, NiuAuthError, NiuConnectionError
from .const import (
    AVAILABLE_SENSORS,
    SENSOR_NAMES_ZH,
    CONF_MONITORED_VARIABLES,
    CONF_SCAN_INTERVAL,
    CONF_SCOOTER_ID,
    DEFAULT_MONITORED_VARIABLES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCOOTER_ID,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    get_conf,
)

_LOGGER = logging.getLogger(__name__)


def _sensors_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[selector.SelectOptionDict(value=k, label=SENSOR_NAMES_ZH[k]) for k in AVAILABLE_SENSORS],
            multiple=True,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _interval_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=MIN_SCAN_INTERVAL,
            max=MAX_SCAN_INTERVAL,
            step=30,
            unit_of_measurement="s",
            mode=selector.NumberSelectorMode.BOX,
        )
    )


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SCOOTER_ID, default=DEFAULT_SCOOTER_ID): int,
    }
)

STEP_SENSORS_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_MONITORED_VARIABLES, default=DEFAULT_MONITORED_VARIABLES
        ): _sensors_selector(),
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): _interval_selector(),
    }
)


def _validate_sensors(monitored_variables: list[str]) -> str | None:
    """返回错误码，None 表示通过。"""
    if not monitored_variables:
        return "no_sensors_selected"
    if any(s not in AVAILABLE_SENSORS for s in monitored_variables):
        return "invalid_sensors"
    return None


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    api = NiuAPI(
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
    )

    try:
        token = await hass.async_add_executor_job(api.get_token)
        if not token:
            raise NiuAuthError("Failed to get authentication token")

        vehicles = await hass.async_add_executor_job(api.get_vehicles_info, token)
        if not vehicles or "data" not in vehicles or "items" not in vehicles["data"]:
            raise NiuConnectionError("Failed to get vehicles information")

        items = vehicles["data"]["items"]
        scooter_id = data.get(CONF_SCOOTER_ID, DEFAULT_SCOOTER_ID)
        if scooter_id >= len(items):
            raise NiuConnectionError(
                f"滑板车 ID {scooter_id} 超出范围（账号下共 {len(items)} 辆）"
            )

        scooter_name = items[scooter_id]["scooter_name"]

        return {
            "title": f"小牛电动车 - {scooter_name}",
            "token": token,
            "scooter_id": scooter_id,
            "scooter_name": scooter_name,
            "sn_id": items[scooter_id]["sn_id"],
        }

    except NiuAuthError as err:
        raise InvalidAuth from err
    except NiuConnectionError as err:
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.exception("Unexpected error during validation")
        raise CannotConnect from err
    finally:
        await hass.async_add_executor_job(api.close)


class NiuConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NIU integration."""

    VERSION = 1
    _input_data: dict[str, Any]

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> NiuOptionsFlowHandler:
        """Get the options flow for this handler."""
        # 不传 config_entry：HA 2024.11 起框架会自己注入
        return NiuOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                self._input_data = {**user_input, **info}
                return await self.async_step_sensors()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the sensors selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            monitored_variables = user_input.get(CONF_MONITORED_VARIABLES, [])
            error = _validate_sensors(monitored_variables)
            if error:
                errors["base"] = error
            else:
                unique_id = f"niu_scooter_{self._input_data['sn_id']}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                config_data = {
                    CONF_USERNAME: self._input_data[CONF_USERNAME],
                    CONF_PASSWORD: self._input_data[CONF_PASSWORD],
                    CONF_SCOOTER_ID: self._input_data[CONF_SCOOTER_ID],
                    CONF_MONITORED_VARIABLES: monitored_variables,
                    CONF_SCAN_INTERVAL: int(
                        user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    ),
                }

                return self.async_create_entry(
                    title=self._input_data["title"], data=config_data
                )

        return self.async_show_form(
            step_id="sensors", data_schema=STEP_SENSORS_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfigure step."""
        errors: dict[str, str] = {}
        config_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            try:
                user_input[CONF_SCOOTER_ID] = config_entry.data[CONF_SCOOTER_ID]
                await validate_input(self.hass, user_input)
                self._input_data = {**config_entry.data, **user_input}
                return await self.async_step_reconfigure_sensors()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME, default=config_entry.data[CONF_USERNAME]
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfigure sensors step."""
        errors: dict[str, str] = {}
        config_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            monitored_variables = user_input.get(CONF_MONITORED_VARIABLES, [])
            error = _validate_sensors(monitored_variables)
            if error:
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(
                    config_entry,
                    unique_id=config_entry.unique_id,
                    data={
                        **config_entry.data,
                        CONF_USERNAME: self._input_data[CONF_USERNAME],
                        CONF_PASSWORD: self._input_data[CONF_PASSWORD],
                        CONF_MONITORED_VARIABLES: monitored_variables,
                        CONF_SCAN_INTERVAL: int(
                            user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                        ),
                    },
                    reason="reconfigure_successful",
                )

        return self.async_show_form(
            step_id="reconfigure_sensors",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MONITORED_VARIABLES,
                        default=get_conf(
                            config_entry,
                            CONF_MONITORED_VARIABLES,
                            DEFAULT_MONITORED_VARIABLES,
                        ),
                    ): _sensors_selector(),
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=get_conf(
                            config_entry, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): _interval_selector(),
                }
            ),
            errors=errors,
        )


class NiuOptionsFlowHandler(OptionsFlow):
    """Handle NIU options.

    注意这里没有 __init__：HA 2024.11 起 OptionsFlow.config_entry 由框架
    以只读属性形式注入，基座那种 `self.config_entry = config_entry` 的写法
    先是告警，在更新的 HA 上会直接抛 AttributeError。
    """

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            monitored_variables = user_input.get(CONF_MONITORED_VARIABLES, [])
            error = _validate_sensors(monitored_variables)
            if error:
                errors["base"] = error
            elif not errors:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_MONITORED_VARIABLES: monitored_variables,
                        CONF_SCAN_INTERVAL: int(
                            user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                        ),
                    },
                )

        # 默认值走 get_conf：原版只读 data，导致改过一次 options 后
        # 表单里显示的还是最初的值。
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_MONITORED_VARIABLES,
                    default=get_conf(
                        self.config_entry,
                        CONF_MONITORED_VARIABLES,
                        DEFAULT_MONITORED_VARIABLES,
                    ),
                ): _sensors_selector(),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=get_conf(
                        self.config_entry, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): _interval_selector(),
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=data_schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
