STATUS_MARKER_PREFIX = "[[VOID_STATUS:"
STATUS_MARKER_SUFFIX = "]]"


def status_message(message: str) -> str:
    return f"{STATUS_MARKER_PREFIX}{message}{STATUS_MARKER_SUFFIX}"


TOOL_STATUS_LABELS = {
    "get_time": "Checking current time...",
    "open_app": "Opening application...",
    "search_installed_apps": "Searching installed applications...",
    "set_volume": "Adjusting system volume...",
    "run_terminal_command": "Running terminal command...",
    "get_system_info": "Reading system information...",
    "get_environment_variables": "Reading user folder paths...",
    "set_system_theme": "Changing system theme...",
    "open_settings": "Opening Windows Settings...",
    "set_system_date": "Updating system date...",
    "manage_windows": "Managing open windows...",
    "read_file": "Reading file...",
    "write_file": "Writing file...",
    "search_windows_files": "Searching for files...",
    "list_directory": "Listing directory...",
}


def describe_tool_action(func_name: str, arguments: dict) -> str:
    if func_name == "search_installed_apps":
        query = arguments.get("query", "")
        return f"Searching installed apps for '{query}'..."
    if func_name == "open_app":
        app_name = arguments.get("app_name", "application")
        return f"Opening {app_name}..."
    if func_name == "run_terminal_command":
        from services.terminal import summarize_command

        return summarize_command(arguments.get("command", ""))
    if func_name == "search_windows_files":
        query = arguments.get("query", "")
        return f"Searching for '{query}'..."
    if func_name == "read_file":
        path = arguments.get("path", "")
        return f"Reading {path}..."
    if func_name == "write_file":
        path = arguments.get("path", "")
        return f"Writing to {path}..."
    if func_name == "list_directory":
        path = arguments.get("path", "")
        return f"Listing {path}..."
    return TOOL_STATUS_LABELS.get(func_name, f"Running {func_name.replace('_', ' ')}...")
