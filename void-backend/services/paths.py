import os

KNOWN_FOLDERS = {
    "desktop": "Desktop",
    "documents": "Documents",
    "downloads": "Downloads",
    "pictures": "Pictures",
}


def get_user_profile() -> str:
    return os.environ.get("USERPROFILE") or os.environ.get("HOME") or ""


def get_desktop_path() -> str:
    profile = get_user_profile()
    if profile:
        return os.path.join(profile, "Desktop")
    return os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop")


def resolve_file_path(path: str) -> str:
    """Normalize user paths and redirect Public Desktop to the signed-in user's Desktop."""
    if not path:
        return path

    cleaned = path.strip().strip('"').strip("'")
    expanded = os.path.expandvars(os.path.expanduser(cleaned))

    profile = get_user_profile()
    public_root = os.environ.get("PUBLIC", "C:\\Users\\Public")

    if profile:
        public_desktop = os.path.join(public_root, "Desktop")
        user_desktop = os.path.join(profile, "Desktop")
        normalized = expanded.replace("/", "\\")
        if normalized.casefold().startswith(public_desktop.casefold()):
            expanded = user_desktop + normalized[len(public_desktop) :]

    if profile and not os.path.isabs(expanded):
        expanded = os.path.join(profile, expanded)

    return os.path.normpath(os.path.abspath(expanded))


def get_environment_variables() -> str:
    profile = get_user_profile()
    keys = [
        "USERPROFILE",
        "USERNAME",
        "HOMEPATH",
        "PUBLIC",
        "APPDATA",
        "LOCALAPPDATA",
        "TEMP",
    ]
    lines = [f"{key}={os.environ[key]}" for key in keys if os.environ.get(key)]

    if profile:
        for folder in KNOWN_FOLDERS.values():
            lines.append(f"{folder.upper()}_PATH={os.path.join(profile, folder)}")

    return "\n".join(lines) if lines else "No environment variables available."
