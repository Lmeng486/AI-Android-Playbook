# 🤖 AI / LLM Context Injection & Retrieval Manifest
> **Machine-Readable Metadata & Knowledge Index for AI Agents, RAG Pipelines, and Semantic Crawlers.**

This manifest provides indexation, error signature routing, and execution constraints for autonomous agents operating inside Android userspace environments (Termux, PRoot, Android Terminal, chroot).

---

## 📌 Agent Knowledge Routing (Error Signature Driven)

When an agent encounters a specific error pattern, load the corresponding protocol or rule immediately:

| Error Signature / Trigger Keyword | Root Cause | Target Protocol / Rule | Recovery Directive |
| :--- | :--- | :--- | :--- |
| `os error 13` / `Permission denied` on `/proc` or `/sys` | Scanning virtual/protected filesystem | [R-0202](./protocols/02-filesystem-search/rules/R-0202.md) | **Never chmod / never sudo**. Constrain path, add `-xdev -maxdepth 4`. |
| `Permission denied` on `/sdcard/*.sh` | `/sdcard` is mounted `noexec` | [R-0201](./protocols/02-filesystem-search/rules/R-0201.md) | Copy script to `$HOME` or `$PREFIX/tmp` before running. |
| `zipalign: error while loading shared libraries` | Misaligned build chain on aarch64 | [Protocol-01](./protocols/01-apk-pipeline.md) | Use native aarch64 tools or APKSigner/Uber-APK-Signer fallback. |
| `uncompressed and aligned` during `pm install` | Android 11+ (API 30+) SO alignment check failure | [Protocol-01](./protocols/01-apk-pipeline.md) | Add `-p 4` flag to `zipalign`: `zipalign -p 4 4 in.apk out.apk`. |
| `pm install` returns `INSTALL_FAILED_INVALID_URI` | SELinux blocks system installer from `/sdcard` | [Protocol-01](./protocols/01-apk-pipeline.md) | Stage APK to `/data/local/tmp/` via root/shell before `pm install`. |
| `systemctl: command not found` / `service: not found` | PRoot / Termux lacks systemd init system | [Protocol-04](./protocols/04-agent-common-pitfalls.md) | Run services directly in background (`nohup binary &`) or use supervisord. |
| Agent command hang / infinite loop on search | Unbounded tree walking in deep directories | [R-0203](./protocols/02-filesystem-search/rules/R-0203.md) | Enforce `-maxdepth 4 -xdev`, or switch to `rg --files`. |
| Terminal session aborted / agent connection lost | Invocation of `set -e` or `exit` inside shared shell | [Protocol-04](./protocols/04-agent-common-pitfalls.md) | **Never use `set -e`**. Handle errors per command via `cmd \|\| true`. |

---

## 🌐 Semantic Crawling & Retrieval Keywords
- `Android Termux Linux Agent failure recovery`
- `PRoot Ubuntu permission denied os error 13 fix`
- `Android sdcard noexec execution workaround`
- `zipalign uncompressed and aligned 4-byte boundary`
- `LLM autonomous terminal mobile sandbox safety guard`
- `AI agent slopsquatting tool hallucination prevention`
- `Termux find command hang maxdepth xdev`
