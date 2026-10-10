#!/usr/bin/env python3
"""
Minimal Android Playbook Harness Interceptor Prototype (Zero-Dependency)
Implements dual-track runtime defense:
  1. Pre-execution interception (Command regex pattern guard)
  2. Post-execution error-driven injection (Captures stderr -> injects rule body)
  3. Rule expiry & decay inspection (Honors meta.json)
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
PROTOCOLS_DIR = BASE_DIR / "protocols"

class PlaybookInterceptor:
    def __init__(self, protocol="02-filesystem-search"):
        self.proto_dir = PROTOCOLS_DIR / protocol
        self.rules_dir = self.proto_dir / "rules"
        self.meta = self._load_json(self.proto_dir / "meta.json")
        self.patterns = self._load_json(self.proto_dir / "rules_index.json")

    def _load_json(self, path):
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_decay_warning(self):
        """Check if rules have exceeded their verified lifespan."""
        verified_date_str = self.meta.get("verified_on", {}).get("verified_at")
        expires_days = self.meta.get("expires_after_days", 180)
        if verified_date_str:
            verified_date = datetime.strptime(verified_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            delta_days = (datetime.now(timezone.utc) - verified_date).days
            if delta_days > expires_days:
                return f"[WARNING: Rules verified {delta_days} days ago (exceeds {expires_days}d threshold). Android OS updates may alter behavior.]\n"
        return ""

    def pre_execute(self, command: str) -> dict:
        """Pre-execution guard: inspects command before running."""
        # Check noexec execution on sdcard
        if re.search(r"(chmod\s+\+x.*(/sdcard|/storage/emulated/0))|((/sdcard|/storage/emulated/0)/[^\s]+\.sh)", command):
            rule_content = self.read_rule("R-0201")
            return {
                "allowed": False,
                "reason": "sdcard_noexec_violation",
                "message": "[PRE-GUARD BLOCK]: /sdcard is mounted with noexec. Execution will fail.",
                "injected_rule": rule_content
            }
        
        # Check unbounded find on root or proc/sys
        if re.search(r"find\s+(/|/proc|/sys|/data)\b(?!.*(-maxdepth|-xdev))", command):
            rule_content = self.read_rule("R-0202")
            return {
                "allowed": False,
                "reason": "root_proc_scan_violation",
                "message": "[PRE-GUARD BLOCK]: Unbounded scan on system/pseudo directories will abort with permission errors.",
                "injected_rule": rule_content
            }

        return {"allowed": True}

    def post_execute(self, command: str, stderr: str) -> dict:
        """Post-execution recovery: checks stderr and injects rule on match."""
        if not stderr:
            return {"injected": False}

        matched_rule = None
        if "os error 13" in stderr or ("Permission denied" in stderr and ("/proc" in stderr or "/sys" in stderr)):
            matched_rule = "R-0202"
        elif "Permission denied" in stderr and ("/sdcard" in command or "/storage" in command):
            matched_rule = "R-0201"
        elif "timed out" in stderr or "killed" in stderr:
            matched_rule = "R-0204"

        if matched_rule:
            rule_text = self.read_rule(matched_rule)
            decay_note = self.get_decay_warning()
            return {
                "injected": True,
                "rule_id": matched_rule,
                "context_payload": f"{decay_note}### [RECOVERY DIRECTIVE TRIGGERED: {matched_rule}]\n{rule_text}"
            }

        return {"injected": False}

    def read_rule(self, rule_id: str) -> str:
        rule_file = self.rules_dir / f"{rule_id}.md"
        if rule_file.exists():
            return rule_file.read_text(encoding="utf-8")
        return f"Rule {rule_id} not found."

if __name__ == "__main__":
    interceptor = PlaybookInterceptor()
    
    # Demonstration 1: Pre-execution block
    test_cmd = "chmod +x /sdcard/script.sh && /sdcard/script.sh"
    print(f"[*] Testing Pre-execution with command: '{test_cmd}'")
    pre_res = interceptor.pre_execute(test_cmd)
    if not pre_res["allowed"]:
        print(f" -> BLOCKED! Message: {pre_res['message']}")
        print(f" -> Auto-injected Rule Preview:\n{pre_res['injected_rule'][:120]}...\n")

    # Demonstration 2: Post-execution error capture
    test_err = "find: '/proc/1/net': Permission denied (os error 13)"
    print(f"[*] Testing Post-execution with stderr: '{test_err}'")
    post_res = interceptor.post_execute("find / -name '*.txt'", test_err)
    if post_res["injected"]:
        print(f" -> RECOVERY TRIGGERED! Target: {post_res['rule_id']}")
        print(f" -> Injected Payload:\n{post_res['context_payload'][:160]}...\n")
