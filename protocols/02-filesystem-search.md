# Protocol-02: 移动端受限文件搜索防暴毙军规 (Filesystem Search Rules)

> **目标**：规范 AI 在安卓终端（PRoot / Termux / 宿主 Linux）环境下的文件探测行为，杜绝全盘扫描导致的 `Permission denied (os error 13)` 异常、无限卡死及上下文额度浪费。

---

## 💣 常见 AI 踩坑实录 (Search Hallucinations)

1. **盲目从根目录 `/` 递归扫描**：AI 想要找一个叫 `config.json` 的文件，常常直接生成：
   ```bash
   find / -name "config.json"
   # 或
   grep -rn "config" /
   ```
   **后果**：直接撞上 Linux 虚拟文件系统 `/proc`、`/sys` 或 Android 保护分区 `/data`，触发系统级 `os error 13: Permission denied`。工具调用被截断，且 AI 容易误以为是“自己权限不足”而反复请求 sudo，陷入僵局。
2. **扫描过宽的 `/sdcard`**：`/sdcard`（外置存储）包含数十万由各类 App 产生的缓存和隐藏文件。无限制深度递归会导致搜索耗时数分钟甚至超时，拖垮 Agent 任务流。
3. **`noexec` 脚本执行认知缺失**：AI 在 `/sdcard` 目录下写出脚本后，通知用户或自身执行 `./run.sh`，直接报 `Permission denied`。

---

## 🛡️ 防御性搜索三原则 (The 3 Golden Rules)

### 规则 1：圈定具体业务子目录 (Target Specific Subdirectories)
严禁以 `/` 或宽泛的 `/sdcard` 作为起始点。必须收窄到具体的业务目录：
- 下载区：`/sdcard/Download`
- 文档区：`/sdcard/Documents`
- 代码工作区：`/root/projects` 或 Termux 的 `$HOME`

### 规则 2：强制增加深度限制 (Enforce Depth Limit)
在所有 `find` 命令中，默认必须带上 `-maxdepth`（建议 2~4）：
```bash
# ✅ 正确做法
find /sdcard/Download -maxdepth 3 -type f -name "*.apk"
```

### 规则 3：先探路，后扫描 (List Before Grep)
先通过 `ls -la` 确认目标目录存在且具备读权限，再做定位，避免直接对未知目录进行深度文本 grep。

---

## 📋 脚本执行避坑指引 (noexec Bypass)

`/sdcard`、`/storage/emulated/0` 在几乎所有现代 Android 系统中都带有 `noexec` 挂载属性。

- ❌ **错误执行方式**：
  ```bash
  chmod +x /sdcard/test.sh && /sdcard/test.sh
  # 依然会报 Permission denied！
  ```
- ✅ **正确执行方式**：
  显式调用解释器执行：
  ```bash
  bash /sdcard/test.sh
  python /sdcard/main.py
  ```