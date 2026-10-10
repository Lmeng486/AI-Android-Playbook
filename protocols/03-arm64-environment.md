# Protocol-03: ARM64 (aarch64) 依赖与环境适配决策树 (Environment Rules)

> **目标**：规范 AI 在 aarch64 移动终端环境中的依赖解析、二进制获取与软件选型，避免拉取 PC 独占包、x86 架构二进制或无法在无 X11/Wayland 桌面下运行的依赖。

---

## 💣 常见 AI 踩坑实录 (Architecture & Dep Failures)

1. **架构幻觉（Arch Hallucination）**：
   - AI 直接使用固定 URL 下载包含 `x86_64` 或 `amd64` 的预编译 binary（如 GitHub Release asset），导致执行时报 `cannot execute binary file: Exec format error`。
2. **PC 独占图形/输入库强行安装**：
   - AI 生成 Python 脚本时，依赖 `pynput`（需要 X11/Windows Hook）、`pyvirtualcam`（需要 OBS/v4l2loopback 桌面内核驱动）、`mouse` / `keyboard` 等。在手机终端纯命令行沙盒中跑必然触发 `ImportError` 或底层 Display 连接失败。
3. **Rust / C++ 源码长耗时编译导致超时挂起**：
   - 没有对应的 ARM64 prebuilt wheel 时，`pip install` 自动回退到从源码编译（例如某些版本的 `scipy`, `cryptography`, `tokenizers`），直接吃满手机小核心导致手机滚烫、耗尽内存被 OOM Killer 杀掉或终端会话超时。

---

## 🛡️ 适配准则 (Adaptation Principles)

### 1. 架构变量动态识别
所有下载命令必须显式提取架构变量，绝不能硬编码 `x86_64`：
```bash
ARCH=$(uname -m)
case "$ARCH" in
  aarch64|arm64)
    PKG_ARCH="arm64" ;;
  x86_64)
    PKG_ARCH="amd64" ;;
  *)
    echo "Unsupported arch: $ARCH" && exit 1 ;;
esac
```

### 2. 桌面依赖与移动替代对照表
当大模型试图实现以下功能时，必须强制切换技术栈：

| PC 惯性思维依赖 (禁止) | 为什么在手机终端报错 | 移动端正确替代方案 |
| :--- | :--- | :--- |
| `pynput` / `pyautogui` | 无 X11 Server，无法监听/模拟全局鼠标键盘 | 手机端无障碍服务（AutoJs / handsets / Operit UI 接口） |
| `pyvirtualcam` | 无虚拟摄像头内核驱动节点 | 本地生成图片/视频文件，通过文件管理或 HTTP 局域网流转 |
| `tkinter` / `PyQt5` | 无原生桌面显示环境 | 启动本地 Web 服务（FastAPI/Flask），在手机浏览器中访问 UI |
| `sounddevice` / `pyaudio` | PRoot / Termux 默认无 ALSA 设备直通 | 使用音频文件生成后调用 `termux-media-player` 或 Termux:API 播放 |

### 3. Python 轮子安全策略
- 尽量优先使用系统包管理器编译好的二进制轮子（如 Termux 中的 `pkg install python-numpy`、Ubuntu 里的 `apt install python3-scipy`），避免直接 `pip install` 触发庞大的源码编译流水线。