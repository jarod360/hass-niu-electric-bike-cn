# 小牛电动车集成

小牛电动车集成将车辆数据接入 Home Assistant。使用小牛中国大陆账号即可查看电池电量、里程、位置、行程，以及前后轮最近上报的胎压和胎温。集成直连小牛国内服务。轮询默认每 300 秒一次，可在选项中调整。

## 安装

### HACS（推荐）

1. HACS → 集成 → 右上角 ⋯ → Custom repositories
2. Repository 填 `https://github.com/jarod360/hass-niu-ebik-cn`，Type 选 `Integration`
3. ADD → 搜索 `小牛电动车` → 下载
4. 重启 Home Assistant

### 手动

把 `custom_components/niu` 整个目录复制到 HA 的 `config/custom_components/`，重启。

装好后：设置 → 设备与服务 → 添加集成 → 搜索 `NIU`。

---

## 前后轮胎压和胎温

在「设置 → 设备与服务 → 小牛电动车 → 选项」中勾选 前轮胎压、后轮胎压、前轮胎温、后轮胎温。胎压使用 bar，胎温使用 °C。每个轮询周期只额外查询一次所选车辆，四项共用结果。轮胎暂时断连时显示云端最后一次上报的读数，连接状态和上报时间可在实体属性中查看。未配对或缺少读数时显示未知。

数据来自小牛 App 的只读车辆接口 `GET /v5/tire_gauge/realtime`，使用已有账号会话和车辆 SN。小牛公开的 [Vehicle Skill](https://github.com/niu-team/niu-vehicle-skills/blob/main/niu-vehicle/SKILL.md) 提供电量、续航、充电、位置和里程等摘要，其字段表未列出胎压和胎温。首次启用时，可在车辆刚上报后对照 App 核对前后轮读数。

## 配置

首次添加时输入小牛账号、密码和车辆序号（从 0 开始）。在选项中勾选需要的传感器并设置轮询间隔。已有安装可直接覆盖升级。

## 上游和许可

本项目基于 ivanphz/hass-niu-scooter-cn、hasscc/home-assistant-niu-component 和 marcelwestrahome/home-assistant-niu-component。上游快照见 `upstream/`。授权见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
