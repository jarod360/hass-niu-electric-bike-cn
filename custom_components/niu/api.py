"""API client for NIU integration."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import requests

from .const import (
    APP_ID,
    APP_VERSION,
    API_BASE_URL,
    ACCOUNT_BASE_URL,
    LOGIN_URI,
    MOTOINFO_ALL_API_URI,
    MOTOINFO_LIST_API_URI,
    MOTOR_BATTERY_API_URI,
    MOTOR_INDEX_API_URI,
    THUMB_CDN_HOST,
    TRACK_LIST_API_URI,
)

_LOGGER = logging.getLogger(__name__)

# (连接超时, 读取超时)
# 原版统一用 timeout=30，意味着网络不通时每次要干等 30 秒。
# 连接超时拆出来设短一点，故障能更快暴露，也不会把 HA 的执行器线程占太久。
DEFAULT_TIMEOUT = (10, 30)


class NiuAuthError(Exception):
    """认证失败：账号密码错误，或 token 失效。"""


class NiuConnectionError(Exception):
    """网络不可达，或服务端返回了非预期结果。"""


class NiuAPI:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.language = "zh-CN"
        self.timezone = "Asia/Shanghai"
        self._token: str | None = None
        self._session = requests.Session()
        self._session.trust_env = False

    @property
    def account_base_url(self) -> str:
        return ACCOUNT_BASE_URL

    @property
    def api_base_url(self) -> str:
        return API_BASE_URL

    @property
    def _ua_full(self) -> str:
        """模拟小牛 App 的完整 UA。clientIdentifier 决定服务端按哪个区处理。"""
        return (
            f"manager/{APP_VERSION} (android; IN2020 11);"
            f"lang={self.language};"
            f"clientIdentifier=Domestic;"
            f"timezone={self.timezone};"
            f"model=IN2020;deviceName=IN2020;ostype=android"
        )

    @property
    def _ua_short(self) -> str:
        """轨迹接口用的简短 UA。"""
        return f"manager/1.0.0 (identifier);clientIdentifier=Domestic"

    def _request(
        self,
        method: str,
        url: str,
        *,
        token: str | None = None,
        ua: str | None = None,
        expect_status_field: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """统一的请求出口，负责超时、异常归类、状态码判定。"""
        headers: dict[str, str] = dict(kwargs.pop("headers", {}) or {})
        if token:
            headers["token"] = token
        headers.setdefault("Accept-Language", self.language)
        if ua:
            headers["user-agent"] = ua

        try:
            response = self._session.request(
                method, url, headers=headers, timeout=DEFAULT_TIMEOUT, **kwargs
            )
        except requests.exceptions.RequestException as err:
            raise NiuConnectionError(f"请求 {url} 失败 ({type(err).__name__})") from err

        if response.status_code in (401, 403):
            raise NiuAuthError(f"{url} 鉴权被拒 (HTTP {response.status_code})")
        if response.status_code != 200:
            raise NiuConnectionError(f"{url} 返回 HTTP {response.status_code}")

        try:
            data = response.json()
        except ValueError as err:
            raise NiuConnectionError(f"{url} 的响应不是合法 JSON") from err

        if expect_status_field and data.get("status") != 0:
            message = str(data.get("desc") or data.get("message") or "未知错误")
            # token 过期时小牛会在 message 里带 token 字样，归类成鉴权错误
            # 让 coordinator 去触发重新登录，而不是当成网络故障做退避。
            if "token" in message.lower():
                raise NiuAuthError(f"{url} 提示 token 无效: {message}")
            raise NiuConnectionError(f"{url} 返回业务错误: {message}")

        return data

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------

    def get_token(self) -> str:
        """登录换取 access_token。密码按 MD5 传，两区一致。"""
        url = self.account_base_url + LOGIN_URI
        payload = {
            "account": self.username,
            "password": hashlib.md5(self.password.encode("utf-8")).hexdigest(),
            "grant_type": "password",
            "scope": "base",
            "app_id": APP_ID,
        }

        # 登录接口不返回 status 字段，单独关掉校验
        data = self._request("POST", url, data=payload, expect_status_field=False)

        try:
            self._token = data["data"]["token"]["access_token"]
        except (KeyError, TypeError) as err:
            message = str(data.get("desc") or data.get("message") or "响应结构异常")
            raise NiuAuthError(f"登录失败: {message}") from err

        if not self._token:
            raise NiuAuthError("登录成功但没拿到 access_token")
        return self._token

    def get_vehicles_info(self, token: str) -> dict[str, Any]:
        """车辆列表。这个接口也不带 status 字段。"""
        return self._request(
            "GET",
            self.api_base_url + MOTOINFO_LIST_API_URI,
            token=token,
            ua=self._ua_full,
            expect_status_field=False,
        )

    def get_battery_info(self, sn: str, token: str) -> dict[str, Any]:
        return self._request(
            "GET",
            self.api_base_url + MOTOR_BATTERY_API_URI,
            token=token,
            ua=self._ua_full,
            params={"sn": sn},
        )

    def get_motor_info(self, sn: str, token: str) -> dict[str, Any]:
        return self._request(
            "GET",
            self.api_base_url + MOTOR_INDEX_API_URI,
            token=token,
            ua=self._ua_full,
            params={"sn": sn},
        )

    def get_overall_info(self, sn: str, token: str) -> dict[str, Any]:
        return self._request(
            "POST",
            self.api_base_url + MOTOINFO_ALL_API_URI,
            token=token,
            ua=self._ua_full,
            headers={"Content-Type": "application/json"},
            json={"sn": sn},
        )

    def get_tire_info(self, sn: str, token: str) -> dict[str, Any]:
        return self._request(
            "GET", self.api_base_url + "/v5/tire_gauge/realtime",
            token=token, ua=self._ua_full, params={"sn": sn},
        )

    def get_track_info(self, sn: str, token: str) -> dict[str, Any]:
        return self._request(
            "POST",
            self.api_base_url + TRACK_LIST_API_URI,
            token=token,
            ua=self._ua_short,
            json={"index": "0", "pagesize": 10, "sn": sn},
        )

    def rewrite_thumb_url(self, url: str | None) -> str | None:
        if not url:
            return url
        url = url.replace(THUMB_CDN_HOST, "app-api.niu.com")
        return url

    def close(self) -> None:
        """释放连接池，在集成卸载时调用。"""
        try:
            self._session.close()
        except Exception:  # pragma: no cover - 清理失败不该影响卸载
            _LOGGER.debug("关闭 NIU session 时出错", exc_info=True)
