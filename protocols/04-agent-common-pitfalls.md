# Protocol-04: AI Agent 行为陷阱与幻觉防范规范 (Agent Pitfalls & Hallucination Defense)

> **目标**：梳理现代 LLM / 编码 Agent 在终端自动化与代码编写中最常出现的 7 大致命错误模式，并提供确定性的工程防御方案。

---

## 目录
- [一、Slopsquatting（依赖包名臆造与供应链陷阱）](#一slopsquatting依赖包名臆造与供应链陷阱)
- [二、Hallucination Spiral（局部上下文致盲与幻觉螺旋）](#二hallucination-spiral局部上下文致盲与幻觉螺旋)
- [三、Tool Misrouting（工具膨胀引发的误选与参数幻觉）](#三tool-misrouting工具膨胀引发的误选与参数幻觉)
- [四、Requirement Conflicting（需求冲突与拆东墙补西墙）](#四requirement-conflicting需求冲突与拆东墙补西墙)
- [五、Hallucinated Actions（虚空命令与未经探测的假设执行）](#五hallucinated-actions虚空命令与未经探测的假设执行)
- [六、Silent Destruction（未捕获的副作用与盲目覆盖）](#六silent-destruction未捕获的副作用与盲目覆盖)
- [七、System Service Assumption（桌面/服务器守护进程认知错位）](#七system-service-assumption桌面服务器守护进程认知错位)

---

### 一、Slopsquatting（依赖包名臆造与供应链陷阱）
- **现象**：Agent 遇到未知功能时，会凭空“发明”一个看似合理的库名（例如 `pip install python-android-tool` 或 `apt install termux-audio-player`）。不仅导致报错，甚至可能命中黑客预先抢注的恶意投毒包。
- **避坑准则**：
  1. **严禁凭常识猜测包名**：在执行安装前，强制先用 `pip search`（或官方索引 API）、`apt-cache search <keyword>` 验证真实存在。
  2. **锁定核心依赖列表**：优先采用 Python 标准库或经过验证的已知主流库。

---

### 二、Hallucination Spiral（局部上下文致盲与幻觉螺旋）
- **现象**：当终端或工具返回内容因长度被截断（Truncated）时，Agent 往往“脑补”丢失的代码段或类定义，臆造不存在的函数并在其上不断堆叠修改。修改失败后再次脑补，陷入长达数十轮的自我修复死循环（Self-Correction Spiral）。
- **避坑准则**：
  1. **截断警报**：看到输出带有 `... [truncated]` 或行号不连续时，严禁直接生成补丁代码。
  2. **分段取证**：必须先使用带行号范围的切片读取（如 `read_file_part` 或 `sed -n '100,150p'`），获取真实物理上下文后再动笔。
  3. **三次熔断原则**：同一逻辑若连续 2 次运行报错，立即停止自动重试，向用户如实汇报现场日志。

---

### 三、Tool Misrouting（工具膨胀引发的误选与参数幻觉）
- **现象**：当上下文内暴露的工具超过 15~20 个时，LLM 对工具 schema 的理解力急剧下降，高频出现“工具选错”、“必填参数漏传”、“自造不存在的参数字段”。
- **避坑准则**：
  1. **单一用途优先**：不要试图在一个工具调用中塞入复合意图。
  2. **参数防御验证**：调用工具前确认参数结构，禁止传递未经定义的属性。

---

### 四、Requirement Conflicting（需求冲突与拆东墙补西墙）
- **现象**：学术统计中，**Requirement Conflicting 是 LLM 代码生成中占比最高的逻辑缺陷**。模型在修补局部 Bug 时，往往无意识地覆盖或推翻了此前设定的全局约束（如将非阻塞异步改为了阻塞同步、破坏了原本的异常捕获机制）。
- **避坑准则**：
  1. **局部精准替换**：修改文件时优先使用精确的局部匹配替换（`edit_file` / diff patch），禁止无脑整文件重写。
  2. **重做前回归约束**：每次修改前重读系统初始需求与不可变原则。

---

### 五、Hallucinated Actions（虚空命令与未经探测的假设执行）
- **现象**：Agent 直接假定某个目录存在、某程序已在后台运行或某个端口已开启，未执行任何感知动作便直接运行高风险写操作。
- **避坑准则**：
  1. **先探测后下刀 (Probe before Act)**：
     - 写文件前：先确认父目录是否存在。
     - 改配置前：先备份或确认原文件哈希。
     - 调接口前：先确认端口处于 LISTEN 状态。

---

### 六、Silent Destruction（未捕获的副作用与盲目覆盖）
- **现象**：语法上没有任何报错（Syntax Error: None），但执行了具有破坏性副作用的操作（如重定向 `>` 覆盖了核心文件、清空了环境变量或使用 `set -e` 导致交互式子终端异常崩溃退出）。
- **避坑准则**：
  1. **持久终端禁忌**：严禁在共享交互式终端内使用 `set -e` / `exit`，这会直接击毁托管 Session。
  2. **采用追加或临时文件缓冲**：核心文件写入先至 `.tmp`，校验成功后再原子性替换。

---

### 七、System Service Assumption（桌面/服务器守护进程认知错位）
- **现象**：习惯性调用 `systemctl start xxx`、`service xxx restart`、`journalctl`，或认为存在 `cron` 常驻服务。在移动容器（PRoot/Chroot/Termux）中，这些守护进程管理机制绝大多数不可用。
- **避坑准则**：
  1. **进程前台/显式后台化**：移动受限环境下用 `nohup <cmd> > /tmp/out.log 2>&1 &` 或子进程代理代替系统服务。
  2. **日志重定向**：手工定向到具体路径文件，不依赖系统日志中心。
