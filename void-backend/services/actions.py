import time
import uuid

from config import PENDING_ACTION_TTL_SECONDS

CONFIRMATION_REQUIRED_TOOLS = {
    "run_terminal_command",
    "set_volume",
    "set_system_theme",
    "set_system_date",
    "manage_windows",
    "write_file",
}

PENDING_ACTIONS: dict[str, dict] = {}


def queue_action(name: str, arguments: dict) -> tuple[str, str]:
    token = uuid.uuid4().hex
    PENDING_ACTIONS[token] = {
        "name": name,
        "arguments": arguments,
        "created_at": time.time(),
    }
    if name == "run_terminal_command":
        description = f"Run this Windows command:\n{arguments.get('command', '')}"
    elif name == "write_file":
        description = f"Write to file: {arguments.get('path', '')}"
    else:
        description = f"Perform Windows action: {name.replace('_', ' ')}"
    return token, description


def pop_pending_action(token: str) -> dict | None:
    pending = PENDING_ACTIONS.pop(token, None)
    if not pending:
        return None
    if time.time() - pending["created_at"] > PENDING_ACTION_TTL_SECONDS:
        return None
    return pending
