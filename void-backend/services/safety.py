import re

_BLOCKED_ACTION_PATTERN = re.compile(
    r"\b(delete|deleting|remove|removing|uninstall|uninstalling|erase|erasing|wipe|wiping|format|del|rd|rmdir|rm)\b",
    re.IGNORECASE,
)


def is_blocked_action(text: str) -> bool:
    return bool(_BLOCKED_ACTION_PATTERN.search(text or ""))
