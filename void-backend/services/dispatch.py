from dataclasses import dataclass
from typing import Literal

from models import ChatMessage
from services.actions import CONFIRMATION_REQUIRED_TOOLS, queue_action
from services.consent import user_gave_explicit_consent
from services.safety import is_blocked_action
from services.tool_definitions import TOOL_NAMES
from services.tools import execute_tool


@dataclass
class ToolDispatchResult:
    kind: Literal["blocked", "confirm", "result", "unknown"]
    message: str = ""
    token: str = ""
    description: str = ""
    result: str = ""


def dispatch_tool(
    func_name: str,
    arguments: dict,
    messages: list[ChatMessage] | None = None,
) -> ToolDispatchResult:
    """Route a tool call through safety checks and the confirmation gate."""
    if func_name not in TOOL_NAMES:
        return ToolDispatchResult(kind="unknown", message=f"Unknown tool: {func_name}")

    if func_name == "run_terminal_command" and is_blocked_action(arguments.get("command", "")):
        return ToolDispatchResult(
            kind="blocked",
            message="I can't delete, remove, or uninstall anything on your system.",
        )

    if func_name in CONFIRMATION_REQUIRED_TOOLS:
        if messages and user_gave_explicit_consent(messages):
            result = execute_tool(func_name, arguments)
            return ToolDispatchResult(kind="result", result=result)

        token, description = queue_action(func_name, arguments)
        return ToolDispatchResult(kind="confirm", token=token, description=description)

    result = execute_tool(func_name, arguments)
    return ToolDispatchResult(kind="result", result=result)
