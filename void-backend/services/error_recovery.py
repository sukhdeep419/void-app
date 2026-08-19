import ast
import json
import re


def _parse_failed_generation_json(failed_generation: str) -> tuple[str | None, dict | None]:
    try:
        generated = json.loads(failed_generation)
        name = generated.get("name")
        arguments = generated.get("arguments")
        if name and isinstance(arguments, dict):
            return name, arguments
    except json.JSONDecodeError:
        pass

    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', failed_generation)
    if not name_match:
        return None, None

    func_name = name_match.group(1)
    args_start = failed_generation.find('"arguments"')
    if args_start == -1:
        return func_name, None

    brace_start = failed_generation.find("{", args_start)
    if brace_start == -1:
        return func_name, None

    depth = 0
    for index in range(brace_start, len(failed_generation)):
        char = failed_generation[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    arguments = json.loads(failed_generation[brace_start : index + 1])
                    if isinstance(arguments, dict):
                        return func_name, arguments
                except json.JSONDecodeError:
                    break
                break

    return func_name, None


def parse_failed_generation(error_str: str) -> tuple[str | None, dict | None]:
    """Recover tool name/arguments from Groq tool_use_failed error payloads."""
    dict_marker = " - "
    if dict_marker in error_str:
        dict_part = error_str.split(dict_marker, 1)[-1].strip()
        try:
            payload = ast.literal_eval(dict_part)
            failed = payload.get("error", {}).get("failed_generation")
            if isinstance(failed, str):
                return _parse_failed_generation_json(failed)
        except (SyntaxError, ValueError, TypeError):
            pass

    match = re.search(r"function=(\w+)[^\w\{]*(\{.*\})", error_str, re.DOTALL)
    if match:
        func_name = match.group(1)
        args_str = match.group(2).replace('\\"', '"').replace("\\'", "'")
        try:
            return func_name, json.loads(args_str)
        except json.JSONDecodeError:
            return func_name, None

    fg_match = re.search(r"['\"]failed_generation['\"]\s*:\s*['\"]", error_str)
    if fg_match:
        start = fg_match.end()
        quote = error_str[fg_match.end() - 1]
        escaped = False
        for index in range(start, len(error_str)):
            char = error_str[index]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == quote:
                failed_generation = error_str[start:index]
                failed_generation = failed_generation.encode("utf-8").decode("unicode_escape")
                return _parse_failed_generation_json(failed_generation)

    return None, None
