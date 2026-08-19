import datetime
import json
import os
import re
import subprocess

from services.apps import get_app_index, launch_resolved_app, resolve_app, search_installed_apps
from services.paths import get_environment_variables, resolve_file_path
from services.safety import is_blocked_action
from services.terminal import get_command_timeout


def execute_tool(name: str, arguments: dict) -> str:
    if name == "get_time":
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if name == "get_system_info":
        import platform

        import psutil

        try:
            import GPUtil
        except ImportError:
            GPUtil = None

        info = [
            f"OS: {platform.system()} {platform.release()} ({platform.version()})",
            f"Architecture: {platform.machine()}",
            f"Processor: {platform.processor()}",
            f"Total RAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB",
            f"Total OS Disk: {round(psutil.disk_usage('/').total / (1024**3), 2)} GB",
        ]

        if GPUtil:
            for index, gpu in enumerate(GPUtil.getGPUs()):
                info.append(f"GPU {index}: {gpu.name} ({gpu.memoryTotal}MB VRAM)")

        return "\n".join(info)

    if name == "open_app":
        app_name = arguments.get("app_name")
        if not app_name:
            return "Failed to launch app: no app name provided."

        match = resolve_app(app_name)
        if not match:
            get_app_index(force_refresh=True)
            match = resolve_app(app_name)

        if not match:
            return (
                f"Could not find an installed app matching '{app_name}'. "
                "It may not be installed, or may be registered under a different name."
            )
        return launch_resolved_app(match)

    if name == "search_installed_apps":
        query = str(arguments.get("query", "")).strip()
        max_results = int(arguments.get("max_results", 30))
        if not query:
            return "Please provide a search term for installed applications."
        return search_installed_apps(query, max_results)

    if name == "set_volume":
        level = arguments.get("level")
        if level is None:
            return "Failed to set volume: no level provided."

        if str(level).lower() == "max":
            level = 100

        try:
            level = max(0, min(100, int(level)))
            from comtypes import CoInitialize, CoUninitialize
            from pycaw.pycaw import AudioUtilities

            CoInitialize()
            try:
                devices = AudioUtilities.GetSpeakers()
                volume = devices.EndpointVolume
                volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            finally:
                CoUninitialize()

            return f"Successfully set system volume to {level}%"
        except Exception as exc:
            return f"Failed to set volume: {str(exc)}"

    if name == "run_terminal_command":
        command = arguments.get("command")
        if re.search(
            r"\b(dir|where|gci|get-childitem)\b.*(?:/s|-recurse|\\\*)",
            command or "",
            re.IGNORECASE,
        ):
            return (
                "File searches must use Void's dedicated file-search action, not a recursive "
                "terminal command. Please ask Void to find the files by name, type, and optional "
                "drive or folder."
            )
        if is_blocked_action(command):
            return "Blocked: Void is not allowed to delete, remove, or uninstall anything on this system."
        timeout = get_command_timeout(command)
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            output = result.stdout + result.stderr
            if output.strip():
                return f"Executed '{command}'. Output:\n{output}"
            return f"Executed '{command}' successfully with no output."
        except subprocess.TimeoutExpired:
            return (
                f"Command timed out after {timeout} seconds. "
                "Large downloads or installs can take longer — try splitting the task into "
                "separate download and extract steps, or increase TERMINAL_LONG_COMMAND_TIMEOUT in .env."
            )
        except Exception as exc:
            return f"Failed to execute '{command}': {str(exc)}"

    if name == "set_system_theme":
        mode = arguments.get("mode", "").lower()
        if mode not in ["light", "dark"]:
            return "Failed: theme mode must be 'light' or 'dark'."
        import winreg

        try:
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(
                registry,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                0,
                winreg.KEY_SET_VALUE,
            )
            value = 1 if mode == "light" else 0
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, value)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, value)
            winreg.CloseKey(key)
            return f"Successfully set system theme to {mode} mode."
        except Exception as exc:
            return f"Failed to set system theme: {str(exc)}"

    if name == "open_settings":
        page = arguments.get("page", "") or "default"
        try:
            os.startfile(f"ms-settings:{page}")
            return f"Successfully opened Windows Settings for '{page}'."
        except Exception as exc:
            return f"Failed to open settings for '{page}': {str(exc)}"

    if name == "set_system_date":
        date_str = arguments.get("date_string")
        if not date_str:
            return "Failed: No date string provided."
        try:
            ps_command = (
                f"Start-Process powershell -Verb runAs -ArgumentList "
                f"\"-Command Set-Date -Date '{date_str}'\""
            )
            subprocess.run(["powershell", "-Command", ps_command], check=True)
            return (
                "Triggered UAC prompt to set system date. "
                "If the user approved, the date was changed."
            )
        except Exception as exc:
            return f"Failed to set system date: {str(exc)}"

    if name == "manage_windows":
        action = arguments.get("action")
        try:
            if action == "minimize_all":
                subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "(New-Object -ComObject Shell.Application).MinimizeAll()",
                    ],
                    check=True,
                )
                return "Successfully minimized all windows."
            if action == "restore_all":
                subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "(New-Object -ComObject Shell.Application).UndoMinimizeALL()",
                    ],
                    check=True,
                )
                return "Successfully restored all windows."
            return f"Unsupported window action: {action}"
        except Exception as exc:
            return f"Failed to manage windows: {str(exc)}"

    if name == "get_environment_variables":
        return get_environment_variables()

    if name == "read_file":
        path = arguments.get("path")
        if not path:
            return "Failed: No path provided."
        resolved = resolve_file_path(path)
        try:
            with open(resolved, "r", encoding="utf-8") as handle:
                content = handle.read(8000)
            if len(content) == 8000:
                content += "\n\n...[TRUNCATED TO 8000 CHARACTERS]..."
            return f"File content of {resolved}:\n{content}"
        except Exception as exc:
            return f"Failed to read file '{resolved}': {str(exc)}"

    if name == "write_file":
        path = arguments.get("path")
        content = arguments.get("content")
        if not path or content is None:
            return "Failed: Path and content are required."
        resolved = resolve_file_path(path)
        try:
            parent = os.path.dirname(resolved)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(resolved, "w", encoding="utf-8") as handle:
                handle.write(content)
            return f"Successfully wrote to {resolved}."
        except PermissionError:
            return (
                f"Permission denied writing to '{resolved}'. "
                f"Use the user's Desktop path from get_environment_variables "
                f"(DESKTOP_PATH), not C:\\Users\\Public\\Desktop."
            )
        except Exception as exc:
            return f"Failed to write to file '{resolved}': {str(exc)}"

    if name == "search_windows_files":
        query = str(arguments.get("query", "")).strip()
        extension = str(arguments.get("extension", "")).strip().lstrip(".")
        root_path = str(arguments.get("root_path", "")).strip()
        max_results = max(1, min(30, int(arguments.get("max_results", 20))))

        if not query and not extension:
            return "Please provide a filename or file extension to search for."

        if root_path:
            expanded_root = os.path.abspath(os.path.expanduser(root_path))
            if not os.path.isdir(expanded_root):
                return f"The search location '{root_path}' does not exist or is unavailable."
            roots = [expanded_root]
        else:
            user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Public")
            roots = [
                os.path.join(user_profile, folder)
                for folder in ("Desktop", "Documents", "Downloads", "Pictures")
            ]
            roots = [folder for folder in roots if os.path.isdir(folder)]

        matches = []
        query_lower = query.casefold()
        extension_lower = f".{extension.casefold()}" if extension else ""

        try:
            for root in roots:
                for directory, _, files in os.walk(root, onerror=lambda _: None):
                    for filename in files:
                        if query_lower and query_lower not in filename.casefold():
                            continue
                        if extension_lower and not filename.casefold().endswith(extension_lower):
                            continue
                        full_path = os.path.join(directory, filename)
                        try:
                            details = os.stat(full_path)
                            matches.append(
                                (
                                    full_path,
                                    details.st_size,
                                    datetime.datetime.fromtimestamp(details.st_mtime),
                                )
                            )
                        except OSError:
                            continue
                        if len(matches) >= max_results:
                            break
                    if len(matches) >= max_results:
                        break
                if len(matches) >= max_results:
                    break

            if not matches:
                location = root_path or "your common personal folders"
                return f"No matching files were found in {location}."

            return "Found files:\n" + "\n".join(
                f"- {path} ({size} bytes, modified {modified:%Y-%m-%d %H:%M})"
                for path, size, modified in matches
            )
        except Exception as exc:
            return f"Failed to search Windows files: {str(exc)}"

    if name == "list_directory":
        path = arguments.get("path")
        if not path:
            return "Failed: No path provided."
        resolved = resolve_file_path(path)
        try:
            items = []
            for item in os.listdir(resolved):
                full_path = os.path.join(resolved, item)
                items.append(
                    {
                        "name": item,
                        "type": "directory" if os.path.isdir(full_path) else "file",
                    }
                )
            return json.dumps(items, indent=2)
        except Exception as exc:
            return f"Failed to list directory: {str(exc)}"

    return "Unknown tool"
