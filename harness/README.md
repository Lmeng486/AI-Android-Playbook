# 🛡️ AI-Android-Playbook Harness Interceptor

A zero-dependency, ultra-lightweight Python middleware designed to bridge **AI Agent Shell Execution** and **Playbook Safety Protocols**.

---

## 🎯 What it does

1. **Pre-execution Interception (命令发出前拦截)**
   - Regex pattern matches known disastrous commands (e.g., `chmod +x /sdcard/foo.sh` or unconstrained `find /`).
   - Rejects the execution immediately and supplies the Agent with safe alternatives from `protocols/`.

2. **Post-execution Recovery (命令失败后自愈)**
   - Captures `stderr` keywords (`os error 13`, `Permission denied`, `timed out`).
   - Automatically loads and injects the corresponding Markdown rule body into the next prompt context.

3. **Decay & Expiry Warning (规则老化告警)**
   - Checks `meta.json` timestamp against actual calendar days.
   - Attaches expiry warnings when verified lifespan is exceeded.

---

## 🚀 Quick Start

```bash
python3 harness/interceptor.py
```

### Programmatic Integration

```python
from harness.interceptor import PlaybookInterceptor

interceptor = PlaybookInterceptor()

# 1. Before executing command
check = interceptor.pre_execute(agent_command)
if not check["allowed"]:
    # Block and feedback to Agent
    agent_session.feed_system_message(check["message"])
    agent_session.feed_system_message(check["injected_rule"])
    return

# 2. After executing command (on failure)
if exit_code != 0:
    recovery = interceptor.post_execute(agent_command, stderr_output)
    if recovery["injected"]:
        agent_session.feed_system_message(recovery["context_payload"])
```