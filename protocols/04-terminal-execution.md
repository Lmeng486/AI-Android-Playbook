# Protocol-04: 受限终端交互与命令执行避雷准则 (Terminal Execution Rules)

> **目标**：杜绝 AI Agent 在无头终端、受限 Shell 或自动化任务中因“盲目交互式命令”、“长耗时挂起”或“破坏性退出”导致的会话卡死、超时与崩溃。

---

## 💣 常见 AI 踩坑实录 (Terminal Hallucinations)

1. **盲目调用阻塞式交互命令（Interactive Hang）**：
   - AI 发出 `apt install python3` 或 `pkg install git` 时，没有带 `-y` 或静默参数；
   - 终端弹出 `Do you want to continue? [Y/n]`，无头 Agent 无法像人类一样按键盘确认，直接触发 `Timeout (超时取消)`。
2. **在持久化 Shell 中使用 `set -e` 导致会话暴毙**：
   - AI 习惯在脚本开头加 `set -e` 或 `set -o errexit`，但在复用同一个 Context 会话的终端里，只要任意一个探针命令返回非 0（如 `grep` 没匹配到），整个终端底层进程直接退出卡死。
3. **前台运行守护进程（Blocking Daemons）**：
   - AI 指令执行 `python app.py`（内部含有 `uvicorn.run()` 或 `while True`），直接霸占当前前台，导致后续工具无法调用，用户只能强制中断。
4. **包名投毒与幻觉依赖（Package Hallucination）**：
   - 遇到未安装的功能时，AI 凭直觉猜测包名（如 `pip install android-toolset` 或 `apt install apktool-arm64`），遇到找不到包的报错后反复重试轮询。

---

## 🛡️ 终端交互四大军规 (The 4 Rules)

### 规则 1：必须全局开启非交互静默模式
所有包管理命令必须带无交互参数：
```bash
# Ubuntu / Debian
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends <pkg>

# Termux
pkg install -y <pkg>

# Python Pip
pip install --no-cache-dir <pkg>
```

### 规则 2：守护进程必须显式后台化与重定向
凡是 Web 服务、长期监听或后台服务，严禁直接前台执行：
```bash
# ✅ 正确：后台运行并重定向输出，保存 PID 便于管理
nohup python server.py > server.log 2>&1 &
echo $! > server.pid
```

### 规则 3：绝对禁止改变全局 Shell 退出行为
- ❌ 严禁在连贯终端会话中执行：`set -e`、`set -o errexit`。
- ✅ 如果需要错误判断，请使用局部条件运算符：
  ```bash
  mkdir build && cd build || exit 1
  ```

### 规则 4：命令探针防御原则（Probe Before Execute）
在安装或执行未知工具前，必须先探查命令是否存在：
```bash
command -v <tool_name> >/dev/null 2>&1 || { echo "TOOL_NOT_FOUND"; exit 0; }
```