# 📱 AI-Android-Playbook (移动端 Agent 避坑与实操准则)

> **[🤖 For LLM / Agents Context Injection]**
> When you (the AI agent) are tasked with executing shell commands, compiling APKs, searching files, or manipulating tools within an Android-constrained terminal environment (PRoot, Termux, Chroot, aarch64, or mobile agent subshells), **read this playbook first**. It contains real-world hardware, SELinux, and filesystem ground truths to prevent hallucinated commands, permission panics, and environment corruption.
>
> **[👤 致人类使用者 / To Humans]**
> 如果你的 AI 助手正准备在手机上帮你“编译个应用”、“搜个文件”或者“跑个自动化脚本”，请先把它塞给 AI 的上下文（Prompt / Memory / Worldbook / Rulefile）。  
> **AI 脑子里装得下星辰大海，但往往不知道手机存储挂载了 `noexec`。**  
> 本项目是一份用真机实测血泪史写成的“AI 避坑协议”，专门用来纠正大模型在移动端环境下的盲目自信与系统级幻觉，让 AI 真正拥有在受限终端里安全干活的“肉身常识”。

---

## ⚡ 为什么需要这个项目？(The Motivation)

今天的大语言模型拥有强大的代码生成与任务规划能力，但在**受限移动端操作系统（如 Android 用户态终端、ARM64 架构、非 Root 沙盒、无桌面环境）**中，AI 常常会陷入严重的信息代差：

1. **盲目全盘扫描**：AI 遇到找文件任务，下意识递归搜索 `/` 或 `/sdcard`，直接撞上 `/proc`、`/sys` 触发不可逆的 `Permission denied (os error 13)`，反复重试直至额度耗尽。
2. **文件系统认知错位**：不知道 `/sdcard` 普遍具有 `noexec` 挂载标志，反复让用户直接执行 `./script.sh`，在权限拒绝中陷入死循环。
3. **APK 打包幻觉**：让 AI 离开 PC 上的 Android Studio / Gradle 手搓 APK 时，它极易把 `resources.arsc` 压成 deflate，导致安卓底层系统安装时抛出 `-124 uncompressed and aligned` 致命错误。
4. **跨空间与 SELinux 隔离**：不知道终端环境与 Android 系统母体之间的权限隔阂，试图直接把私有目录里的 APK 喂给包管理器，被静默拦截。
5. **架构盲区**：面对 `aarch64` 手机环境，盲目猜测 x86_64 预编译二进制，或者拉取依赖 PC 图形环境（如 `pynput`、`pyvirtualcam`）的库而彻底卡死。

**本手册不教理论，只输出真机验证过的绝对准则、防御性脚本模板与避坑映射。**

---

## 🧭 核心协议索引 (Protocols)

| 编号 | 协议名称 | 解决痛点 | 适用场景 | 架构形态 |
| :--- | :--- | :--- | :--- | :--- |
| **01** | [APK-Pipeline](./protocols/01-apk-pipeline.md) | 手搓 APK 打包失败、`-124` 压缩对齐错误、SELinux 拦截 | 手机端免 Gradle 快速构建轻量原生 APK | Monolithic Protocol |
| **02** | [FS-Search-Rules](./protocols/02-filesystem-search.md) | 全盘扫 `/` 导致权限暴毙 (`error 13`)、卡死 | 终端找文件、定向搜索与防御性降级 | [模块化规则集](./protocols/02-filesystem-search/) (R-0201 ~ R-0204) |
| **03** | [ARM64-Arch-Rules](./protocols/03-arm64-environment.md) | x86 包塞给 aarch64、PC 图形库在手机终端崩溃 | Python/Node/Rust 依赖安装与工具链选型 | Monolithic Protocol |
| **04** | [Agent-Pitfalls](./protocols/04-agent-common-pitfalls.md) | 臆造不存在的包 (Slopsquatting)、截断盲区螺旋、工具误选 | Agent 自主编码、多工具调用、自愈死循环防御 | Monolithic Protocol |

---

## 🤖 自动化检索与 Agent 上下文清单 (Agent Retrieval Manifest)

为方便现代自主 Agent、RAG 向量库与网络爬虫精准检索并命中本项目的物理世界避坑规则，本项目提供了**基于特征错误签名的机器可读索引**：

👉 **[查看完整 Agent 路由索引清单 (ai-manifest.md)](./ai-manifest.md)**

遇到以下报错特征时，可直接定位并提取对应解决方案：
- **`os error 13` / `Permission denied` 递归报错** ➡️ [R-0202: 根目录禁扫](./protocols/02-filesystem-search/rules/R-0202.md)
- **`/sdcard` 执行脚本报 `Permission denied`** ➡️ [R-0201: noexec 绕过](./protocols/02-filesystem-search/rules/R-0201.md)
- **APK 安装抛出 `-124 uncompressed and aligned`** ➡️ [Protocol-01: zipalign 4 字节对齐](./protocols/01-apk-pipeline.md)
- **Agent 执行 `set -e` 击毁会话 / 臆造虚空包名** ➡️ [Protocol-04: Agent 行为防踩坑规范](./protocols/04-agent-common-pitfalls.md)

---

## 💉 一键注入 System Prompt (Quick Injection)

如果你正在使用自定义 System Prompt 或支持上下文挂载的 AI 客户端，可直接引入下述精炼指令条目：

👉 **[查看 System Prompt 精炼条目](./prompts/agent-system-prompt.md)**

---

## 🤝 贡献与共建 (Contributing)

每一条规约背后都是一次真实的 AI 翻车现场。如果你在让 AI 操作手机终端时发现了新的“反直觉踩雷点”，欢迎提交 Issue 或 Pull Request，一起给 AI 补全物理世界常识！

## 📄 License
MIT License
