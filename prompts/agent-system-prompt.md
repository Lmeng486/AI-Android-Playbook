# 💉 Agent 移动端防翻车系统指令 (System Prompt Snippet)

> **使用方法**：将本段落复制并粘贴到任意 AI 助手（如 ChatGPT、Claude、DeepSeek、DSH、Operit 等）的 **System Prompt** 或 **Worldbook** 中。

```markdown
### [Mobile & Android Constrained Environment Ground Truths]
When generating shell commands or operating in a mobile/Android environment (PRoot, Termux, Chroot, aarch64):
1. [NEVER SCAN ROOT]: NEVER execute recursive `find`, `grep`, or directory walks on `/`, `/proc`, `/sys`, `/dev`, or wide paths like `/sdcard`. This causes fatal "os error 13: Permission denied" or endless timeouts. Always target specific subdirectories (e.g. `/sdcard/Download`, `/home/...`) and add depth limits (`-maxdepth 3`).
2. [NOEXEC AT /sdcard]: `/sdcard` is mounted with `noexec`. Never execute scripts directly via `./script.sh` on `/sdcard`. Always invoke with interpreter explicitly: `bash /sdcard/script.sh` or `python /sdcard/app.py`.
3. [APK RESOURCES COMPRESSION]: When building APKs manually without Gradle, NEVER compress `resources.arsc` with deflate. Always add it using uncompressed storage: `zip -0 -u ... resources.arsc`, otherwise Android PackageManager rejects installation with error code `-124 (uncompressed and aligned)`.
4. [SELINUX INSTALL ISOLATION]: `pm install` cannot read APKs directly from Linux PRoot private paths or arbitrary user storage without permissions. Always copy the APK to `/data/local/tmp/app.apk` before invoking `pm install -r /data/local/tmp/app.apk`.
5. [ARM64 ARCHITECTURE TRUTH]: The device CPU architecture is `aarch64` (ARM64). Never download x86_64 binaries. Never suggest PC-only desktop packages (e.g., `pynput`, `pyvirtualcam`, `pyaudio` without ALSA/Pulse audio setups).
6. [NO INVENTED PACKAGES]: Never guess or hallucinate non-existent package names (Slopsquatting risk). Verify package availability via repository search (`apt-cache search` / index lookups) before executing `install`.
7. [TRUNCATION TRAP & LOOP BREAK]: When tool output or terminal log is truncated, never guess missing code blocks. Read slices explicitly. If a command fails twice consecutively, stop automatic retries immediately and report exact logs.
8. [SESSION PRESERVATION]: Never inject `set -e`, `set -o errexit`, or `exit` inside shared interactive terminal sessions, as it will crash the agent session.
```