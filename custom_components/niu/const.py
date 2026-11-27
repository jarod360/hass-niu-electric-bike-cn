"""Constants for the NIU integration."""


DOMAIN = "niu"

# --------------------------------------------------------------------------
# 配置项
# --------------------------------------------------------------------------
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCOOTER_ID = "scooter_id"
CONF_MONITORED_VARIABLES = "monitored_variables"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCOOTER_ID = 0
DEFAULT_MONITORED_VARIABLES = ["BatteryCharge"]

# 轮询间隔（秒）。原版写死 30 秒，对云端 API 来说过于激进，
# 4 个接口 × 2 次/分钟 = 8 req/min 长期不停，容易触发服务端风控。
DEFAULT_SCAN_INTERVAL = 300
MIN_SCAN_INTERVAL = 60
MAX_SCAN_INTERVAL = 3600

# 失败退避：连续失败时把轮询间隔按 2^n 拉长，最多拉到基准值的 8 倍
MAX_BACKOFF_FACTOR = 8

# token 最长复用时间（秒），到点强制重新登录
TOKEN_MAX_AGE = 12 * 3600

# --------------------------------------------------------------------------
# API 路径
# --------------------------------------------------------------------------
LOGIN_URI = "/v3/api/oauth2/token"
MOTOR_BATTERY_API_URI = "/v3/motor_data/battery_info"
MOTOR_INDEX_API_URI = "/v5/scooter/motor_data/index_info"
MOTOINFO_LIST_API_URI = "/v5/scooter/list"
MOTOINFO_ALL_API_URI = "/motoinfo/overallTally"
TRACK_LIST_API_URI = "/v5/track/list/v2"

APP_ID = "niu_ktdrr960"
# 上游 marcelwestrahome 主线已升到 4.10.4，原 hasscc 版写死在 4.6.48
APP_VERSION = "4.10.4"

# 轨迹缩略图的国内 CDN 域名，两个区服都需要重写掉
ACCOUNT_BASE_URL = "https://account.niu.com"
API_BASE_URL = "https://app-api.niu.com"
THUMB_CDN_HOST = "app-api.niucache.com"


# --------------------------------------------------------------------------
# 传感器分组
# --------------------------------------------------------------------------
SENSOR_TYPE_BAT = "BAT"
SENSOR_TYPE_MOTO = "MOTO"
SENSOR_TYPE_DIST = "DIST"
SENSOR_TYPE_OVERALL = "TOTAL"
SENSOR_TYPE_POS = "POSITION"
SENSOR_TYPE_TRACK = "TRACK"

SENSOR_TYPE_TIRE = "TIRE"
TIRE_SENSORS = (
    "FrontTirePressure",
    "FrontTireTemperature",
    "RearTirePressure",
    "RearTireTemperature",
)

AVAILABLE_SENSORS = [
    *TIRE_SENSORS,
    "BatteryCharge",
    "Isconnected",
    "TimesCharged",
    "temperatureDesc",
    "Temperature",
    "BatteryGrade",
    "CurrentSpeed",
    "ScooterConnected",
    "IsCharging",
    "IsLocked",
    "TimeLeft",
    "EstimatedMileage",
    "centreCtrlBatt",
    "HDOP",
    "Longitude",
    "Latitude",
    "Distance",
    "RidingTime",
    "totalMileage",
    "DaysInUse",
    "LastTrackStartTime",
    "LastTrackEndTime",
    "LastTrackDistance",
    "LastTrackAverageSpeed",
    "LastTrackRidingtime",
    "LastTrackThumb",
]

SENSOR_NAMES_ZH = {
    "FrontTirePressure": "前轮胎压",
    "FrontTireTemperature": "前轮胎温",
    "RearTirePressure": "后轮胎压",
    "RearTireTemperature": "后轮胎温",
    "BatteryCharge": "电池电量",
    "Isconnected": "连接状态",
    "TimesCharged": "充电次数",
    "temperatureDesc": "温度描述",
    "Temperature": "电池温度",
    "BatteryGrade": "电池等级",
    "CurrentSpeed": "当前速度",
    "ScooterConnected": "电动车连接",
    "IsCharging": "充电状态",
    "IsLocked": "锁定状态",
    "TimeLeft": "剩余时间",
    "EstimatedMileage": "预估里程",
    "centreCtrlBatt": "中央控制器电池",
    "HDOP": "GPS精度",
    "Longitude": "经度",
    "Latitude": "纬度",
    "Distance": "距离",
    "RidingTime": "骑行时间",
    "totalMileage": "总里程",
    "DaysInUse": "使用天数",
    "LastTrackStartTime": "最后行程开始时间",
    "LastTrackEndTime": "最后行程结束时间",
    "LastTrackDistance": "最后行程距离",
    "LastTrackAverageSpeed": "最后行程平均速度",
    "LastTrackRidingtime": "最后行程骑行时间",
    "LastTrackThumb": "最后行程缩略图",
}


def get_conf(config_entry, key, default=None):
    """读取配置项：options 优先于 data。

    """
    if config_entry.options and key in config_entry.options:
        return config_entry.options[key]
    return config_entry.data.get(key, default)
