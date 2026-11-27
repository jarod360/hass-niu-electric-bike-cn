# 小牛电动车

小牛电动车可通过本集成接入 Home Assistant。使用小牛中国大陆账号即可查看电池电量、里程、位置、行程，以及前后轮最近上报的胎压和胎温。集成直连小牛国内服务。轮询默认每 300 秒一次，可在选项中调整。

## 安装

### Marketplace（Home Assistant 2026.11 及以上）

1. 打开「设置 → Marketplace」，选择「从链接添加」。
2. 输入 `https://github.com/jarod360/hass-niu-electric-bike-cn`，安装「小牛电动车」。
3. 安装或升级后，按 Marketplace 提示重启 Home Assistant。

### HACS

1. HACS → 集成 → 右上角 ⋯ → Custom repositories
2. Repository 填 `https://github.com/jarod360/hass-niu-electric-bike-cn`，Type 选 `Integration`
3. ADD → 搜索 `小牛电动车` → 下载
4. 重启 Home Assistant

### 手动

把 `custom_components/niu` 整个目录复制到 HA 的 `config/custom_components/`，重启。

装好后：设置 → 设备与服务 → 添加集成 → 搜索 `NIU`。

---

## 可用数据

集成提供 30 个可选车辆传感器。经 Marketplace 安装时，HA 会另有一个「小牛电动车」更新实体，用于检查和安装新版本。

| 分类 | 可选传感器 |
| --- | --- |
| 电池与充电 | 动力电池电量、温度、温度描述、电池等级、充电次数、充电状态、剩余时间、中央控制器电池 |
| 车辆状态 | 连接状态、车辆连接、锁定状态、当前速度、预估续航 |
| 位置 | 经纬度、GPS 精度指标（HDOP） |
| 骑行与总计 | 骑行距离、骑行时间、累计里程、使用天数 |
| 最近一次行程 | 开始和结束时间、行驶距离、平均速度、骑行时长、轨迹缩略图 |
| 轮胎 | 前轮和后轮的胎压（bar）及胎温（°C） |

在「设置 → 设备与服务 → 小牛电动车 → 选项」选择要启用的传感器。读数取决于车辆支持的功能及最近一次上报。轮胎暂时断开时显示云端最后一次上报的读数，实体属性可查看连接状态和上报时间。未配对或没有读数时显示未知。

## 配置

首次添加时输入小牛账号、密码和车辆序号（从 0 开始）。在选项中勾选需要的传感器并设置轮询间隔。已有安装可直接升级，原有账号、车辆配置和实体 ID 会继续使用。设备名称读取小牛账号中的车辆昵称，例如「兰博基牛」。集成条目的默认标题为「NIU Electric Bike - 车辆昵称」。

## 上游和许可

本项目基于 ivanphz/hass-niu-scooter-cn、hasscc/home-assistant-niu-component 和 marcelwestrahome/home-assistant-niu-component。上游快照见 `upstream/`。授权见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
