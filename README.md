# Phone Speaker Bridge · 手机当电脑的 WiFi 音响

把 Windows 电脑正在播放的声音，通过同一局域网传到手机浏览器。手机可以直接用扬声器播放，也可以通过已连接的 AirPods、有线耳机等设备收听。

这是我基于 **[Azec-Zuckerberg/pc-audio-to-iphone](https://github.com/Azec-Zuckerberg/pc-audio-to-iphone)** 做的个人实践项目，由 **Codex 和豆包辅助调试与整理**。原作者提供音频传输、网页接收和反向麦克风的核心实现；我的扩展主要围绕 Windows 下的启动体验和采集异常恢复。感谢原作者以 MIT 协议开放源码。

> 改动以本地保留的基础副本为比较基准，未取得原始 Git 提交记录，不能据此断言与上游当前版本的全部差异。详见 [来源与改动说明](docs/UPSTREAM.md)。

## 为什么做这个

想让手边的手机临时充当电脑音响，也想试试借助 Codex 和豆包，把已有开源项目调整成自己日常更方便启动的小工具。电脑端运行 Python 服务，手机端打开网页，不需要为这个项目额外安装手机 App。

```text
电脑声音 → WASAPI 回环采集 → WebRTC / Opus → WiFi → 手机浏览器 → 手机扬声器 / 耳机
手机麦克风 → WebRTC / Opus → 电脑播放设备（或虚拟音频线）
```

## 在原项目基础上做了什么

| 部分 | 基础副本已经具备 | 本项目的扩展与发布整理 |
| --- | --- | --- |
| 音频传输 | WASAPI 回环采集、WebRTC / Opus、浏览器播放 | 沿用核心传输实现 |
| 手机网页 | Listen / Mic、START、缓冲统计、屏幕唤醒请求 | 原网页保持一致，未重新设计界面 |
| 采集故障 | 采集出错后退出采集线程，需人工重启 | 关闭失效流并尝试重新打开同一采集设备 |
| Windows 启动 | 可手动运行的基础源码 | 统一双击启动、首次安装依赖、兼容旧启动文件名 |
| 桌面入口 | 基础副本未包含快捷方式生成器 | 提供 `make-shortcut.vbs`，自动使用当前目录与当前用户桌面 |
| 端口占用 | 服务启动时报错 | 提前检查并提示换端口；发布版不强制结束其他程序 |
| 文档与分发 | 英文说明与 MIT 许可 | 中文文档、来源对照、历史差异补丁、排除本机文件 |

本地实践版本曾用 `netstat` 和 PowerShell 自动清理端口，并增加等待和启动提示。本次发布改为**检测占用并提示处理**，避免误停其他应用。[历史差异补丁](docs/local-enhancements.patch)保留了修改对照，其中的旧端口清理代码仅供阅读。

基础副本中还保留了一个自动安装依赖的 `start.cmd`，无法确认它来自上游还是之前的本地辅助工作；本项目不把这一思路声称为原创。各项归属详见 [UPSTREAM.md](docs/UPSTREAM.md)。

## 开始使用

### 环境

- Windows 10 / 11，建议 Python **3.12**，安装时加入 PATH。
- 电脑至少有一个启用的音频输出设备。
- 手机与电脑在同一可信局域网，网络允许设备互相访问。

### 双击启动

下载并解压本仓库，双击 **`start.cmd`**。

首次运行会创建 `.venv` 并安装依赖，需要联网；之后启动复用环境。若安装失败，窗口保留错误信息。

在手机浏览器打开终端实际显示的局域网地址，例如 `https://192.168.1.42:8080`，选择 **Listen**，点击 **START**，然后在电脑播放声音。

声音从手机当前音频输出播放。若想用手机扬声器，请确认手机没有把声音路由到耳机。

### 命令行启动

```powershell
git clone https://github.com/shaoyeaichangge/phone-speaker-bridge.git
cd phone-speaker-bridge
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

按 `Ctrl+C` 或关闭终端停止服务。`run-airpods-bridge.cmd` 和 `.bat` 是兼容入口，会转交给 `start.cmd`。

### 桌面快捷方式

双击 `make-shortcut.vbs`，会在当前用户桌面创建快捷方式。移动项目目录后，请重新生成。Windows 若禁用了 VBScript，直接使用 `start.cmd` 即可。

## 常用参数

```powershell
# 查看设备：只列举，不启动服务
.\.venv\Scripts\python.exe server.py --list-devices

# 采集指定回环设备，编号以本机列表为准
.\.venv\Scripts\python.exe server.py --device 7

# 默认端口被占用时，改用其他端口
start.cmd --port 9000

# 把手机麦克风播放到指定电脑输出设备
start.cmd --mic-device 30
```

**Mic 模式继承自基础项目。** 要让会议软件把手机识别成可选择的麦克风，还需要自行配置虚拟音频线；本服务不会自动新增 Windows 麦克风设备。

## 使用边界与排查

- **证书**：服务在本机生成自签名证书，浏览器可能提示不受信任。麦克风模式需要安全上下文。请自行核对地址与证书；项目不自动修改系统或浏览器的信任设置。
- **局域网**：当前服务没有连接鉴权，适合可信局域网，不适合直接暴露到公网。
- **连接不上**：核对两端网络、终端打印的 IP、系统对 Python 的网络访问设置，以及路由器是否隔离设备。
- **端口占用**：关闭之前的服务窗口或使用 `--port 9000`；本版本不会终止占用端口的其他程序。
- **连接正常但无声**：确认电脑正在播放、输出设备正确且音量足够；电脑静音也会影响 WASAPI 回环声音。
- **更换输出设备**：自动恢复针对同一设备的暂时故障；切换默认输出设备后仍应重启服务。
- **锁屏或切后台**：手机浏览器可能挂起音频，请保持网页在前台；唤醒锁并非所有设备都支持。
- **延迟**：受网络、浏览器缓冲和蓝牙耳机影响。本仓库没有新的端到端实测数据，不承诺固定毫秒数。

## 项目文件与验证

```text
server.py                    采集、故障重试、信令与 HTTPS
index.html                   基础项目的手机网页
start.cmd                    Windows 启动入口
run-airpods-bridge.cmd/.bat   旧入口兼容包装
make-shortcut.vbs            桌面快捷方式生成器
requirements.txt             基础副本的依赖版本
verify.py                    基础副本的流健康检查
tests/                       启动与恢复逻辑的单元检查
docs/UPSTREAM.md             来源与贡献边界
docs/local-enhancements.patch 本地实践版本相对基础副本的差异
```

安装依赖后运行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`verify.py` 在服务运行时执行，会播放测试音，并检查有声、静音两个阶段的包率和时间戳。它需要真实音频设备，不能替代手机端听音验证。验证结果记录在 [VALIDATION.md](docs/VALIDATION.md)。

## 致谢与许可

- 原项目：[Azec-Zuckerberg/pc-audio-to-iphone](https://github.com/Azec-Zuckerberg/pc-audio-to-iphone)。
- 本地实践与维护：[@shaoyeaichangge](https://github.com/shaoyeaichangge)。
- AI 辅助：Codex、豆包；现有资料不足以准确归属每一段修改，因此作项目级说明。

沿用 **[MIT License](LICENSE)**，保留原作者版权声明。来源与扩展边界见 [UPSTREAM.md](docs/UPSTREAM.md)。
