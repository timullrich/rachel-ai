"""Action mapping for GTAF runtime context."""

from __future__ import annotations

import re
from typing import Any, Dict


_WRITE_COMMANDS = {
    "rm",
    "mv",
    "cp",
    "chmod",
    "chown",
    "mkdir",
    "rmdir",
    "truncate",
    "tee",
    "touch",
}
_READ_COMMANDS = {"ls", "cat", "head", "tail", "grep", "find", "stat", "du"}
_NETWORK_COMMANDS = {"curl", "wget", "ping", "ssh", "scp", "nc", "nmap"}
_SYSTEM_COMMANDS = {"shutdown", "reboot", "kill", "pkill", "systemctl", "launchctl"}
_PROCESS_COMMANDS = {"ps", "top", "pgrep", "date", "whoami", "uname"}
_WRITE_RE = re.compile(r"(^|\s)(\d?>{1,2})\s*\S")


def build_action_id(function_name: str, arguments: Dict[str, Any]) -> str:
    """Builds a stable action id for policy matching."""
    if function_name == "execute_command":
        command = str(arguments.get("command", "")).strip()
        return f"execute_command:{_classify_command(command)}"

    operation = arguments.get("operation")
    if isinstance(operation, str) and operation.strip():
        return f"{function_name}:{operation.strip().lower()}"

    return function_name


def _classify_command(command: str) -> str:
    if not command:
        return "unknown"

    normalized = command.strip().lower()
    tokens = re.findall(r"[a-zA-Z0-9_.:/-]+", normalized)
    if not tokens:
        return "unknown"

    cmd = tokens[0]

    if cmd in _SYSTEM_COMMANDS:
        return "system_control"
    if cmd in _NETWORK_COMMANDS:
        return "network"
    if cmd == "sed" and re.search(r"\s-i(\s|$)", normalized):
        return "filesystem_write"
    if cmd == "echo" and _WRITE_RE.search(normalized):
        return "filesystem_write"
    if _WRITE_RE.search(normalized):
        return "filesystem_write"
    if cmd in _WRITE_COMMANDS:
        return "filesystem_write"
    if cmd in _READ_COMMANDS:
        return "filesystem_read"
    if cmd in _PROCESS_COMMANDS:
        return "process_info"

    return "unknown"
