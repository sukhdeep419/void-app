import json
import re
import threading
import time
from typing import Generator, Iterable

from config import GROQ_API_KEY, GROQ_MODEL
from models import ChatMessage
from services.context import trim_messages_for_api
from services.dispatch import ToolDispatchResult, dispatch_tool
from services.error_recovery import parse_failed_generation
from services.images import describe_images
from services.status import describe_tool_action, status_message
from services.tool_definitions import TOOLS
from services.tools import execute_tool

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a futuristic, intelligent AI assistant named Void. "
        "You must ALWAYS reply conversationally to the user and keep a history of the previous chats in mind. "
        "When you need to perform an action, you MUST use the native JSON tool-calling API. "
        "CRITICAL: NEVER output tool names or raw tool call strings in your text response. "
        "Do not write things like `<function=...>`, `function=...`, or `(get_time)` in your conversational replies. "
        "CRITICAL: When you receive data back from a tool (like system info or time), you MUST clearly present that data to the user in your response! Do not just say you successfully retrieved it; actually tell the user what the data is. "
        "SAFETY RULE: Never delete, remove, uninstall, erase, wipe, or format anything. Refuse those requests clearly. "
        "APPROVAL RULE: System-changing tools (terminal commands, file writes, volume, theme, etc.) use exactly ONE approval step via the app's Approve/Cancel buttons. "
        "NEVER ask conversationally whether to proceed — do not say 'Would you like me to', 'Let me know', 'Shall I', or similar. "
        "When the user requests an action, call the matching tool immediately; the UI shows the approval prompt. "
        "If the user already replied yes/go ahead/approve to a prior message, call the tool right away (their consent is already recorded). "
        "AGENT RULE: Choose the appropriate tool from the user's intent. Use search_installed_apps when the user asks about installed applications, software categories, or how many apps they have. ALWAYS use search_windows_files for requests to find files on disk (not installed apps). Set root_path when the user names a drive or folder, and use extension when the user names a file type. Never use run_terminal_command for file searching or listing. Never delete, remove, uninstall, erase, wipe, or format anything. "
        "For large downloads or installs (WordPress, npm, etc.), prefer splitting into separate steps: create folder, download file, then extract — rather than one chained command. "
        "FILE RULE: Before write_file to Desktop, call get_environment_variables and use DESKTOP_PATH. "
        "Never write to C:\\Users\\Public\\Desktop — that is not the signed-in user's desktop."
    ),
}

HEARTBEAT_TOOLS = {"run_terminal_command", "search_windows_files", "search_installed_apps"}


def _chunk_stream(text: str, chunk_size: int = 4) -> Generator[str, None, None]:
    for index in range(0, len(text), chunk_size):
        yield text[index : index + chunk_size]
        time.sleep(0.01)


def _stream_natural_reply(client, messages_payload: list[dict]) -> Generator[str, None, None]:
    yield status_message("Preparing reply...")
    stream_response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=trim_messages_for_api(messages_payload),
        stream=True,
        tool_choice="none",
    )
    for chunk in stream_response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def _yield_dispatch(dispatch: ToolDispatchResult) -> Generator[str, None, bool]:
    if dispatch.kind == "blocked":
        yield dispatch.message
        return True
    if dispatch.kind == "confirm":
        yield f"[[VOID_CONFIRM:{dispatch.token}]]{dispatch.description}"
        return True
    if dispatch.kind == "unknown":
        yield dispatch.message
        return True
    return False


def _run_tool_with_heartbeats(func_name: str, arguments: dict) -> Generator[str, None, str]:
    label = describe_tool_action(func_name, arguments)
    yield status_message(label)

    if func_name not in HEARTBEAT_TOOLS:
        return execute_tool(func_name, arguments)

    result_box: dict[str, str] = {}
    done = threading.Event()

    def worker():
        result_box["value"] = execute_tool(func_name, arguments)
        done.set()

    threading.Thread(target=worker, daemon=True).start()
    elapsed = 0
    while not done.wait(5):
        elapsed += 5
        yield status_message(f"{label.rstrip('.')} ({elapsed}s elapsed)")

    return result_box["value"]


def _build_chat_history(
    messages: Iterable[ChatMessage],
) -> Generator[str, None, list[dict]]:
    chat_history = []
    for message in messages:
        content = message.content
        role = "assistant" if message.role == "ai" else message.role

        if role == "user" and message.images:
            yield status_message("Analyzing attached images...")
            image_analysis = describe_images(message.images)
            content += f"\n\n[Attached image analysis from Gemini:\n{image_analysis}]"

        if role == "assistant" and (
            "[Groq Error:" in content or "function=" in content or "<function=" in content
        ):
            content = "I processed your request using my internal tools."

        if role in ["user", "assistant"]:
            chat_history.append({"role": role, "content": content})
        else:
            chat_history.append(
                {"role": "user", "content": f"[{role.upper()} RESULT]: {content}"}
            )
    return chat_history


def _friendly_api_error(error_str: str) -> str:
    lowered = error_str.lower()
    if (
        "413" in error_str
        or "too large" in lowered
        or "tokens per minute" in lowered
        or ("token" in lowered and "limit" in lowered)
    ):
        return (
            "This conversation is too large for the AI to process — usually because an "
            "earlier reply included a very long log or file dump. Click **New Chat** and "
            "ask again about just the latest result."
        )
    if "rate_limit" in lowered or "rate limit" in lowered:
        return "The AI service is temporarily rate-limited. Please wait a few seconds and try again."
    if "tool_use_failed" in lowered or "tool choice is none" in lowered:
        return (
            "I had trouble finishing that action through the AI API. "
            "Click **New Chat** and ask again — file creation should work with a fresh conversation."
        )
    return "I'm sorry, I encountered an internal API error while processing your request. Please try again."


def generate_groq_stream(messages: list[ChatMessage]) -> Generator[str, None, None]:
    if not GROQ_API_KEY:
        yield "The AI backend is not configured. Set GROQ_API_KEY in void-backend/.env and restart the server."
        return

    from groq import Groq

    yield status_message("Thinking...")

    history_builder = _build_chat_history(messages)
    chat_history = []
    try:
        while True:
            item = next(history_builder)
            yield item
    except StopIteration as stop:
        chat_history = stop.value

    messages_payload = trim_messages_for_api([SYSTEM_PROMPT] + chat_history)

    try:
        yield status_message("Planning response...")
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages_payload,
            tools=TOOLS,
            stream=False,
        )

        message = response.choices[0].message
        if message.tool_calls:
            clean_tool_calls = []
            for tool_call in message.tool_calls:
                clean_tool_calls.append(
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                )
            messages_payload.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": clean_tool_calls,
                }
            )

            tool_results = []
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                dispatch = dispatch_tool(func_name, arguments, messages)
                handled = False
                for chunk in _yield_dispatch(dispatch):
                    yield chunk
                    handled = True
                if handled:
                    return

                tool_runner = _run_tool_with_heartbeats(func_name, arguments)
                result = None
                try:
                    while True:
                        item = next(tool_runner)
                        yield item
                except StopIteration as stop:
                    result = stop.value

                tool_results.append(result)
                messages_payload.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

            yield status_message("Summarizing results...")
            final_response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=trim_messages_for_api(messages_payload),
                stream=False,
                tool_choice="none",
            )
            final_content = final_response.choices[0].message.content or ""
            if not final_content.strip():
                final_content = (
                    "I completed the request, but couldn't prepare a summary. "
                    "Here is the result:\n" + "\n\n".join(tool_results)
                )

            yield from _chunk_stream(final_content)
            return

        content = message.content or ""
        known_tools = "|".join(tool["function"]["name"] for tool in TOOLS)
        match = re.search(fr"({known_tools})[^\w\{{]*(\{{.*?\}})", content, re.DOTALL)

        if match:
            func_name = match.group(1)
            try:
                arguments = json.loads(match.group(2))
                dispatch = dispatch_tool(func_name, arguments, messages)
                for chunk in _yield_dispatch(dispatch):
                    yield chunk
                    return

                tool_runner = _run_tool_with_heartbeats(func_name, arguments)
                result = None
                try:
                    while True:
                        item = next(tool_runner)
                        yield item
                except StopIteration as stop:
                    result = stop.value

                messages_payload.append({"role": "assistant", "content": content})
                messages_payload.append(
                    {
                        "role": "user",
                        "content": (
                            f"[System: The tool '{func_name}' was executed with result:\n{result}\n\n"
                            "Reply to the user naturally in their language. You MUST include and format "
                            "this result data in your reply! Do not just say you retrieved it.]"
                        ),
                    }
                )

                yield from _stream_natural_reply(client, messages_payload)
                return
            except Exception:
                pass

        yield from _chunk_stream(content)

    except Exception as exc:
        error_str = str(exc)
        with open("error.log", "w", encoding="utf-8") as handle:
            handle.write(error_str)

        try:
            func_name, arguments = parse_failed_generation(error_str)
            if func_name and isinstance(arguments, dict):
                if func_name == "search_windows_files" and arguments.get("extension") == "exe":
                    func_name = "search_installed_apps"
                    arguments = {
                        "query": arguments.get("query", "app"),
                        "max_results": arguments.get("max_results", 30),
                    }

                dispatch = dispatch_tool(func_name, arguments, messages)
                for chunk in _yield_dispatch(dispatch):
                    yield chunk
                    return

                tool_runner = _run_tool_with_heartbeats(func_name, arguments)
                result = None
                try:
                    while True:
                        item = next(tool_runner)
                        yield item
                except StopIteration as stop:
                    result = stop.value

                recovery_payload = trim_messages_for_api(messages_payload) + [
                    {
                        "role": "user",
                        "content": (
                            f"[System tool result for '{func_name}']:\n{result}\n\n"
                            "Reply naturally to the user. Present the data clearly. "
                            "Do not mention API errors or internal tool names."
                        ),
                    }
                ]
                from groq import Groq

                recovery_client = Groq(api_key=GROQ_API_KEY)
                yield from _stream_natural_reply(recovery_client, recovery_payload)
                return
        except Exception:
            pass

        yield _friendly_api_error(error_str)
