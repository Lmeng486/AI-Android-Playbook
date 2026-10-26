# Protocol-05: 跨环境会话与数据陷阱 (Cross-Environment Session & Data Traps)

> **目标**：收录 2026-10 真机实测发现的 4 类跨环境陷阱——终端会话吞多行、双空间 `/tmp` 隔离、MIUI 后台冻结、API 时间戳语义误判。每条均给出可复现案例与确定性防御方案。
>
> **适用环境**：Android 15 (SDK 35) / aarch64 / MIUI (HyperOS) / proot Ubuntu 24 终端 / AI 工具链驱动的远程会话。

---

## 目录
- [一、Heredoc 黑洞（会话吞多行命令）](#一heredoc-黑洞会话吞多行命令)
- [二、双空间 /tmp 不互通](#二双空间-tmp-不互通)
- [三、MIUI 后台冻结（APP_STANDBY 阻断）](#三miui-后台冻结app_standby-阻断)
- [四、GitHub API 时间戳语义陷阱](#四github-api-时间戳语义陷阱)
- [五、速查表](#五速查表)

---

## 一、Heredoc 黑洞（会话吞多行命令）

### 现象
通过 AI 工具链（MCP / 插件桥）注入的终端会话，会**静默吞掉 heredoc（`<<EOF`）与多行命令**：命令返回"成功"，但实际只有第一行被执行，脚本内容残缺，产生难以排查的静默错误。

### 实测案例
```bash
# 期望：写入 3 行 Python 脚本
python3 - <<'EOF'
import json
d = json.load(open('x.json'))
print(d)
EOF
# 实际：只有 `python3 -` 被执行，stdin 立即 EOF，无输出无报错
```

### 防御准则
1. **长脚本一律先落盘再执行**：用文件工具写入 `.py` / `.sh`，再由终端执行该文件；
2. **短命令单行分号串联**：`cmd1 && cmd2; cmd3`，禁止换行；
3. **引号嵌套**：外层单引号包整个 `-c` 参数，内部一律双引号；
4. **验证习惯**：执行后立即 `echo EXIT:$?` 或输出关键产物确认，不信任"命令成功返回"。

> **Verdict**：100% 复现。根因在工具链的命令注入层，非 shell 本身；换 shell / 换引号风格均无效。

---

## 二、双空间 /tmp 不互通

### 现象
Android 宿主侧与 proot/terminal 侧各自持有独立的 `/tmp`，**互不可见**。Android 侧文件工具写入 `/tmp/foo` 后，proot 内进程读取报 `No such file or directory`；反向同样失败。

### 实测案例
```
Android 侧：create_file /tmp/T.java  → 写入成功
terminal  ：javac /tmp/T.java        → No such file or directory
```

### 防御准则
1. **跨空间中转一律走 `/sdcard`**（两侧均挂载，FUSE 可见）；
2. terminal 侧先 `cp /sdcard/... ./` 到工作目录再操作，避免直接在 sdcard 上编译/执行（`noexec` + FUSE IO 慢，参见 Protocol-01/02）；
3. 临时产物用完即删，不在 `/sdcard` 留中间文件。

---

## 三、MIUI 后台冻结（APP_STANDBY 阻断）

### 现象
Termux 等终端类 App 长期后台后，被 MIUI 网络策略标记为 `APP_STANDBY|APP_BACKGROUND`，**网络请求静默失败**——不是报错，是超时/无响应；前台拉起后自动恢复。

### 实测案例
```
后台 Termux：curl api.github.com → 卡死超时
恢复操作  ：
  am set-standby-bucket com.termux active   # 解除待机限制
  + 拉起 Termux Activity                     # 前台化彻底恢复
```

### 防御准则
1. 长任务前先检查状态：`am get-standby-bucket <pkg>`；
2. 恢复组合拳：`am set-standby-bucket <pkg> active` + 拉起 Activity；
3. 注意：Android `shell`（uid 2000）非 root，操作其他 App 私有目录需 `run-as` 或 Shizuku 通道：

```bash
run-as com.termux env HOME=/data/data/com.termux/files/home \
  PATH=/data/data/com.termux/files/usr/bin sh -c '...'
```

---

## 四、GitHub API 时间戳语义陷阱

### 现象
1. **`updated_at` ≠ `merged_at`**：PR 的 `updated_at` 会被评论、label、关闭等**非合并事件**刷新。列表 API 里"最近更新的 merged PR"极易被误判为"最近合并"。
2. **search API 有索引延迟**：单独依赖 search 结果做时间线判断会得出错误结论。

### 实测案例
```
列表 API：PR #17185  updated_at=2026-10-25T20:37  merged=True
          → 误判：10-25 有合并
直查详情：GET /pulls/17185
          → merged_at=2026-10-23T09:12:04Z（真实合并时间）
          → updated_at 只是被后续评论刷新
```

### 防御准则
1. 判定"是否合并 / 何时合并"，**必须直查 `GET /pulls/{n}` 的 `merged_at`**；
2. 用列表 API（`state=closed&sort=updated`）做**交叉验证**，两源一致才下结论；
3. search API（`is:merged merged:>X`）只用于**初筛规模**，不作为时间线终审；
4. 批量合并行为分析按 `merged_at` 分桶，不按 `updated_at`。

---

## 五、速查表

| 陷阱 | 典型症状 | 一句话防御 |
| :--- | :--- | :--- |
| Heredoc 黑洞 | 命令"成功"但脚本残缺 | 长脚本落盘执行，短命令分号串联 |
| 双空间 /tmp | 文件写成功却读不到 | 跨空间中转走 /sdcard |
| MIUI 后台冻结 | 后台网络静默超时 | set-standby-bucket active + 拉起前台 |
| API 时间戳误判 | 合并时间被评论刷新 | merged_at 直查详情，search 只初筛 |

---
*实测环境：Xiaomi 23013RK75C / Android 15 (SDK 35) / aarch64 / MIUI / proot Ubuntu 24 / Operit 工具链 · 2026-10*
