TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current time and date.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": (
                "Open any application installed on the user's Windows PC by its common name "
                "(e.g. 'teams', 'notepad', 'spotify'). The system will resolve the closest "
                "matching installed app automatically."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": (
                            "The name of the app to open, as the user referred to it "
                            "(e.g. 'teams', 'calculator')"
                        ),
                    }
                },
                "required": ["app_name"],
            },
        },
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
                        "description": "The volume level from 0 to 100.",
                    }
                },
                "required": ["level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_terminal_command",
            "description": (
                "Run a Windows command only for a narrowly scoped system task. Never use this "
                "tool to search, list, locate, or enumerate files; use search_windows_files or "
                "list_directory for those tasks. Never use it to delete, remove, uninstall, "
                "erase, wipe, or format."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command line string to execute.",
                    }
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": (
                "Get detailed hardware and operating system configuration of the user's PC."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_system_theme",
            "description": "Change the Windows system theme to Light or Dark mode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "description": "The theme mode to apply: 'light' or 'dark'.",
                    }
                },
                "required": ["mode"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_settings",
            "description": (
                "Open a specific Windows Settings page (e.g. 'display', 'bluetooth', "
                "'network', 'personalization')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {
                        "type": "string",
                        "description": (
                            "The settings page to open. Examples: 'display', 'bluetooth', "
                            "'network', 'about'."
                        ),
                    }
                },
                "required": ["page"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_system_date",
            "description": (
                "Change the Windows system date and time. This will trigger a UAC prompt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date_string": {
                        "type": "string",
                        "description": (
                            "The new date and time to set, in a format Windows PowerShell "
                            "recognizes (e.g., '2025-01-01 14:30:00')."
                        ),
                    }
                },
                "required": ["date_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "manage_windows",
            "description": (
                "Manage active application windows on the desktop (minimize all or restore)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": (
                            "The action to perform: 'minimize_all' or 'restore_all'."
                        ),
                    }
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Securely read the text contents of a file on the system. "
                "Output is capped to prevent overflow."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The absolute path to the file to read.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a new text file or overwrite an existing one.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The absolute path to the file to write.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_windows_files",
            "description": (
                "Search local Windows drives for files by name. This is read-only. Use it when "
                "the user asks to find files; never use a terminal command for file search."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Part of the filename to find, without a path.",
                    },
                    "extension": {
                        "type": "string",
                        "description": "Optional extension such as pdf, docx, or xlsx.",
                    },
                    "root_path": {
                        "type": "string",
                        "description": (
                            "Optional drive or folder to search, e.g. F:\\ or "
                            "C:\\Users\\Admin\\Documents. Defaults to the user's profile folders."
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum matches to return, 1 to 30.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List all files and folders in a specified directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The absolute path to the directory to list.",
                    }
                },
                "required": ["path"],
            },
        },
    },
]

TOOL_NAMES = {tool["function"]["name"] for tool in TOOLS}
