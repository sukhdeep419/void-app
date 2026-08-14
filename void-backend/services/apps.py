import difflib
import json
import os
import re
import subprocess
import time

from config import APP_CACHE_TTL_SECONDS

_app_cache = {"apps": [], "last_refresh": 0}


def _load_installed_apps():
    """Ask Windows for every launchable app (Store + desktop) via Get-StartApps."""
    ps_script = "Get-StartApps | ConvertTo-Json -Compress"
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    return [
        {"name": app["Name"], "id": app["AppID"]}
        for app in data
        if "Name" in app and "AppID" in app
    ]


def get_app_index(force_refresh: bool = False):
    now = time.time()
    if (
        force_refresh
        or (now - _app_cache["last_refresh"] > APP_CACHE_TTL_SECONDS)
        or not _app_cache["apps"]
    ):
        _app_cache["apps"] = _load_installed_apps()
        _app_cache["last_refresh"] = now
    return _app_cache["apps"]


def _normalise_app_name(value: str) -> str:
    return " ".join(re.findall(r"[\w]+", value.casefold(), flags=re.UNICODE))


def resolve_app(query: str):
    apps = get_app_index()
    if not apps:
        return None

    normalised_query = _normalise_app_name(query)
    if not normalised_query:
        return None

    indexed_apps = [(app, _normalise_app_name(app["name"])) for app in apps]

    exact_matches = [app for app, name in indexed_apps if name == normalised_query]
    if exact_matches:
        return exact_matches[0]

    query_words = normalised_query.split()
    whole_word_matches = []
    for app, name in indexed_apps:
        name_words = name.split()
        if any(
            name_words[i : i + len(query_words)] == query_words
            for i in range(len(name_words) - len(query_words) + 1)
        ):
            whole_word_matches.append((app, name_words))

    if whole_word_matches:
        whole_word_matches.sort(key=lambda candidate: (len(candidate[1]), candidate[0]["name"]))
        return whole_word_matches[0][0]

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
            subprocess.run(f"explorer.exe shell:AppsFolder\\{app_id}", shell=True)
        else:
            os.startfile(app_id)
        return f"Successfully launched {app['name']}"
    except Exception as exc:
        return f"Failed to launch {app['name']}: {str(exc)}"
