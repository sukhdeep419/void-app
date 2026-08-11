import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from services.system import get_system_metrics

app = FastAPI(title="Void AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel

from typing import List

class ChatMessage(BaseModel):
    role: str
    content: str

class CommandRequest(BaseModel):
    messages: List[ChatMessage]

@app.get("/")
def read_root():
    return {"status": "Void Backend Running"}

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

import datetime
import subprocess

# ---------------------------------------------------------------------------
# Dynamic app resolution
#
# Instead of a hardcoded alias map, we ask Windows for every launchable app
# (Store/UWP apps AND traditional desktop apps) via Get-StartApps, cache the
# result, and fuzzy-match whatever the user/AI says against that real index.
# This means it works for whatever is actually installed on the machine,
# with no manual maintenance required.
# ---------------------------------------------------------------------------
import difflib
import re
import time

_app_cache = {"apps": [], "last_refresh": 0}

# Void must never perform file, app, or system removal operations.
_BLOCKED_ACTION_PATTERN = re.compile(
    r"\b(delete|deleting|remove|removing|uninstall|uninstalling|erase|erasing|wipe|wiping|format|del|rd|rmdir|rm)\b",
    re.IGNORECASE,
)


def is_blocked_action(text: str) -> bool:
    return bool(_BLOCKED_ACTION_PATTERN.search(text or ""))
CACHE_TTL = 300  # seconds; refresh every 5 minutes, or force refresh on demand


def _load_installed_apps():
    """Ask Windows for every launchable app (Store + desktop) via Get-StartApps."""
    ps_script = "Get-StartApps | ConvertTo-Json -Compress"
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):  # PowerShell returns a single object, not a list, if there's only 1 app
        data = [data]
    return [{"name": a["Name"], "id": a["AppID"]} for a in data if "Name" in a and "AppID" in a]


def get_app_index(force_refresh: bool = False):
    now = time.time()
    if force_refresh or (now - _app_cache["last_refresh"] > CACHE_TTL) or not _app_cache["apps"]:
        _app_cache["apps"] = _load_installed_apps()
        _app_cache["last_refresh"] = now
    return _app_cache["apps"]


def _normalise_app_name(value: str) -> str:
    """Return a comparable app name while preserving meaningful words."""
    return " ".join(re.findall(r"[\w]+", value.casefold(), flags=re.UNICODE))


def resolve_app(query: str):
    """Resolve an app conservatively, never choosing a weak fuzzy match.

    Short names such as ``teams`` can otherwise score similarly to unrelated
    applications. Exact and complete-word matches take priority.
    """
    apps = get_app_index()
    if not apps:
        return None

    normalised_query = _normalise_app_name(query)
    if not normalised_query:
        return None

    indexed_apps = [(app, _normalise_app_name(app["name"])) for app in apps]

    # The user named the application exactly (for example, "Teams").
    exact_matches = [app for app, name in indexed_apps if name == normalised_query]
    if exact_matches:
        return exact_matches[0]

    # Match complete words only. This finds "Microsoft Teams" for "teams",
    # while avoiding partial-character matches in unrelated app names.
    query_words = normalised_query.split()
    whole_word_matches = []
    for app, name in indexed_apps:
        name_words = name.split()
        if any(name_words[i:i + len(query_words)] == query_words
               for i in range(len(name_words) - len(query_words) + 1)):
            whole_word_matches.append((app, name_words))

    if whole_word_matches:
        # Prefer "Microsoft Teams" over "Teams Machine-Wide Installer".
        whole_word_matches.sort(key=lambda candidate: (len(candidate[1]), candidate[0]["name"]))
        return whole_word_matches[0][0]

    # Typo tolerance is useful, but only for a strong match. The old 0.4
    # cutoff allowed requests such as "teams" to select Notepad.
    names = [name for _, name in indexed_apps]
    matches = difflib.get_close_matches(normalised_query, names, n=1, cutoff=0.78)
    if matches:
        matched_name = matches[0]
        return next(app for app, name in indexed_apps if name == matched_name)

    return None


def launch_resolved_app(app: dict) -> str:
    app_id = app["id"]
    try:
        if "!" in app_id:
            # UWP/Store app — launch via shell:AppsFolder using its AppUserModelID
            subprocess.run(f'explorer.exe shell:AppsFolder\\{app_id}', shell=True)
        else:
            # Desktop app — AppID here is a real path (.exe or .lnk), Windows resolves it directly
            os.startfile(app_id)
        return f"Successfully launched {app['name']}"
    except Exception as e:
        return f"Failed to launch {app['name']}: {str(e)}"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current time and date.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open any application installed on the user's Windows PC by its common name (e.g. 'teams', 'notepad', 'spotify'). The system will resolve the closest matching installed app automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name of the app to open, as the user referred to it (e.g. 'teams', 'calculator')"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Set the system volume level on Windows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "The volume level from 0 to 100."
                    }
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_terminal_command",
            "description": "Execute an arbitrary command in the Windows terminal (PowerShell or cmd). Use this to perform system tasks like closing apps, managing files, clearing folders, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command line string to execute."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get detailed hardware and operating system configuration of the user's PC.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


def execute_tool(name: str, arguments: dict) -> str:
    if name == "get_time":
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif name == "get_system_info":
        import platform
        import psutil
        try:
            import GPUtil
        except ImportError:
            GPUtil = None

        info = []
        info.append(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
        info.append(f"Architecture: {platform.machine()}")
        info.append(f"Processor: {platform.processor()}")

        mem = psutil.virtual_memory()
        info.append(f"Total RAM: {round(mem.total / (1024**3), 2)} GB")

        disk = psutil.disk_usage('/')
        info.append(f"Total OS Disk: {round(disk.total / (1024**3), 2)} GB")

        if GPUtil:
            gpus = GPUtil.getGPUs()
            for i, gpu in enumerate(gpus):
                info.append(f"GPU {i}: {gpu.name} ({gpu.memoryTotal}MB VRAM)")

        return "\n".join(info)
    elif name == "open_app":
        app_name = arguments.get("app_name")
        if not app_name:
            return "Failed to launch app: no app name provided."

        match = resolve_app(app_name)
        if not match:
            # One retry with a forced refresh, in case the app was just installed
            # or the cache is stale.
            get_app_index(force_refresh=True)
            match = resolve_app(app_name)

        if not match:
            return (
                f"Could not find an installed app matching '{app_name}'. "
                f"It may not be installed, or may be registered under a different name."
            )
        return launch_resolved_app(match)
    elif name == "set_volume":
        level = arguments.get("level")
        if level is None:
            return "Failed to set volume: no level provided."

        if str(level).lower() == "max":
            level = 100

        try:
            level = max(0, min(100, int(level)))
            from pycaw.pycaw import AudioUtilities
            from comtypes import CoInitialize, CoUninitialize

            CoInitialize()
            try:
                devices = AudioUtilities.GetSpeakers()
                volume = devices.EndpointVolume
                scalar_level = level / 100.0
                volume.SetMasterVolumeLevelScalar(scalar_level, None)
            finally:
                CoUninitialize()

            return f"Successfully set system volume to {level}%"
        except Exception as e:
            return f"Failed to set volume: {str(e)}"
    elif name == "run_terminal_command":
        command = arguments.get("command")
        if is_blocked_action(command):
            return "Blocked: Void is not allowed to delete, remove, or uninstall anything on this system."
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
            output = result.stdout + result.stderr
            return f"Executed '{command}'. Output:\n{output}" if output.strip() else f"Executed '{command}' successfully with no output."
        except Exception as e:
            return f"Failed to execute '{command}': {str(e)}"
    return "Unknown tool"


@app.post("/api/command")
async def execute_command(request: CommandRequest):
    import requests, json, time, re

    latest_user_message = next(
        (message.content for message in reversed(request.messages) if message.role == "user"),
        "",
    )


    chat_history = []
    for m in request.messages:
        content = m.content
        role = m.role
        if role == "ai":
            role = "assistant"

        if role == "assistant" and ("[Groq Error:" in content or "function=" in content or "<function=" in content):
            # Hide hallucinated errors from the model's history so it doesn't repeat them
            content = "I processed your request using my internal tools."

        if role in ["user", "assistant"]:
            chat_history.append({"role": role, "content": content})
        else:
            # Map invalid roles (like past 'tool' outputs) to user messages so Groq doesn't crash
            chat_history.append({"role": "user", "content": f"[{role.upper()} RESULT]: {content}"})

    system_prompt = {
        "role": "system",
        "content": (
            "You are a futuristic, intelligent AI assistant named Void. "
            "You must ALWAYS reply conversationally to the user and keep a history of the previous chats in mind. "
            "When you need to perform an action, you MUST use the native JSON tool-calling API. "
            "CRITICAL: NEVER output tool names or raw tool call strings in your text response. "
            "Do not write things like `<function=...>`, `function=...`, or `(get_time)` in your conversational replies. "
            "CRITICAL: When you receive data back from a tool (like system info or time), you MUST clearly present that data to the user in your response! Do not just say you successfully retrieved it; actually tell the user what the data is. SAFETY RULE: Never delete, remove, uninstall, erase, wipe, or format anything. Refuse those requests clearly and do not call a tool for them."
        )
    }
    messages_payload = [system_prompt] + chat_history

    def generate_groq_stream():
        from groq import Groq
        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages_payload,
                tools=TOOLS,
                stream=False
            )

            message = response.choices[0].message
            if message.tool_calls:
                clean_tool_calls = []
                for t in message.tool_calls:
                    clean_tool_calls.append({
                        "id": t.id,
                        "type": "function",
                        "function": {
                            "name": t.function.name,
                            "arguments": t.function.arguments
                        }
                    })
                messages_payload.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": clean_tool_calls
                })

                tool_results = []
                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    result = execute_tool(func_name, arguments)
                    tool_results.append(result)
                    messages_payload.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

                # The action is complete. Ask for a text-only explanation so
                # the model cannot issue another tool call and end the stream
                # without any visible reply.
                final_response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=messages_payload,
                    stream=False
                )
                final_content = final_response.choices[0].message.content or ""
                if not final_content.strip():
                    final_content = (
                        "I completed the request, but couldn't prepare a summary. "
                        "Here is the result:\n" + "\n\n".join(tool_results)
                    )

                for i in range(0, len(final_content), 4):
                    yield final_content[i:i+4]
                    time.sleep(0.01)
            else:
                content = message.content or ""

                # Check for leaked tool call syntax by looking for known tool names near JSON
                known_tools = "|".join([t["function"]["name"] for t in TOOLS])
                match = re.search(fr'({known_tools})[^\w\{{]*(\{{.*?\}})', content, re.DOTALL)

                if match:
                    func_name = match.group(1)
                    try:
                        arguments = json.loads(match.group(2))
                        result = execute_tool(func_name, arguments)

                        # Add the leaked response and the tool result to the payload
                        messages_payload.append({
                            "role": "assistant",
                            "content": content
                        })
                        messages_payload.append({
                            "role": "user",
                            "content": f"[System: The tool '{func_name}' was executed with result:\n{result}\n\nReply to the user naturally in their language. You MUST include and format this result data in your reply! Do not just say you retrieved it.]"
                        })

                        # Call Groq again to get a natural conversational response
                        stream_response = client.chat.completions.create(
                            model="openai/gpt-oss-120b",
                            messages=messages_payload,
                            tools=TOOLS,
                            stream=True
                        )
                        for chunk in stream_response:
                            if chunk.choices[0].delta.content:
                                yield chunk.choices[0].delta.content
                        return
                    except Exception:
                        pass

                # If no leaked tool call, stream the normal text
                for i in range(0, len(content), 4):
                    yield content[i:i+4]
                    time.sleep(0.01)
        except Exception as e:
            error_str = str(e)
            with open("error.log", "w") as f:
                f.write(error_str)

            # Recover tool calls from both legacy error text and Groq's
            # ``failed_generation`` payload used by tool_use_failed responses.
            func_name = None
            arguments = None
            try:
                import ast
                match = re.search(r'function=(\w+)[^\w\{]*(\{.*?\})', error_str, re.DOTALL)
                if match:
                    func_name = match.group(1)
                    args_str = match.group(2).replace('\\"', '"').replace("\\'", "'")
                    arguments = json.loads(args_str)
                else:
                    payload_start = error_str.find("{")
                    if payload_start != -1:
                        error_payload = ast.literal_eval(error_str[payload_start:])
                        failed_generation = error_payload.get("error", {}).get("failed_generation", "")
                        try:
                            generated_call = json.loads(failed_generation)
                            func_name = generated_call.get("name")
                            arguments = generated_call.get("arguments")
                        except json.JSONDecodeError:
                            # Some provider errors embed a PowerShell command
                            # with unescaped inner quotes, making this JSON
                            # invalid even though the intended tool call is clear.
                            name_match = re.search(r'"name"\s*:\s*"([^"]+)"', failed_generation)
                            command_match = re.search(
                                r'"command"\s*:\s*"(.*)"\s*}\s*}$',
                                failed_generation,
                                re.DOTALL,
                            )
                            if name_match and command_match:
                                func_name = name_match.group(1)
                                arguments = {"command": command_match.group(1).replace('\\"', '"')}

                valid_tool_names = {tool["function"]["name"] for tool in TOOLS}
                if func_name in valid_tool_names and isinstance(arguments, dict):
                    result = execute_tool(func_name, arguments)
                    fallback_msg = f"I executed '{func_name}' directly due to an API format error. Result:\n{result}"
                    for i in range(0, len(fallback_msg), 4):
                        yield fallback_msg[i:i+4]
                        time.sleep(0.01)
                    return
            except Exception:
                pass

            yield "\nI'm sorry, I encountered an internal API error while processing your request. Please try again."

    return StreamingResponse(generate_groq_stream(), media_type="text/plain")


@app.websocket("/ws/system")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def send_metrics():
        try:
            while True:
                metrics = get_system_metrics()
                await websocket.send_text(json.dumps(metrics))
                await asyncio.sleep(1)  # Broadcast every 1 second
        except Exception:
            pass

    # Start the sending task
    send_task = asyncio.create_task(send_metrics())

    try:
        # Waiting for messages will immediately detect a disconnect
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("Client disconnected gracefully")
    except Exception as e:
        print(f"Error in websocket connection: {e}")
    finally:
        # Ensure the sending task is cancelled when the client disconnects
        send_task.cancel()