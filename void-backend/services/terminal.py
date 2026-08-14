import re

from config import TERMINAL_COMMAND_TIMEOUT, TERMINAL_LONG_COMMAND_TIMEOUT

LONG_RUNNING_PATTERN = re.compile(
    r"\b("
    r"Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer|curl|wget|"
    r"Expand-Archive|Compress-Archive|tar|unzip|7z|"
    r"npm\s+install|pip\s+install|docker\s+pull|git\s+clone|"
    r"choco\s+install|winget\s+install|dotnet\s+restore|composer\s+install"
    r")\b",
    re.IGNORECASE,
)


def get_command_timeout(command: str) -> int:
    if LONG_RUNNING_PATTERN.search(command or ""):
        return TERMINAL_LONG_COMMAND_TIMEOUT
    return TERMINAL_COMMAND_TIMEOUT


def summarize_command(command: str) -> str:
    cmd = command or ""
    if re.search(r"Invoke-WebRequest|curl|wget|Start-BitsTransfer", cmd, re.IGNORECASE):
        return "Downloading files — this may take a few minutes..."
    if re.search(r"Expand-Archive|unzip|tar|7z", cmd, re.IGNORECASE):
        return "Extracting archive..."
    if re.search(r"New-Item.*Directory|mkdir", cmd, re.IGNORECASE):
        return "Creating folder..."
    if re.search(r"npm\s+install|pip\s+install", cmd, re.IGNORECASE):
        return "Installing packages — please wait..."
    if len(cmd) > 80:
        return f"Running: {cmd[:77]}..."
    return f"Running: {cmd}" if cmd else "Running command..."
