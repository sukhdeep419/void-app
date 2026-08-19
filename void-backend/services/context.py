MAX_MESSAGE_CHARS = 3000
MAX_HISTORY_MESSAGES = 14


def _truncate_content(content: str) -> str:
    if len(content) <= MAX_MESSAGE_CHARS:
        return content
    return content[:MAX_MESSAGE_CHARS] + "\n\n...[truncated to fit context limit]..."


def trim_messages_for_api(messages: list[dict]) -> list[dict]:
    """Keep recent history and cap message size so Groq requests stay within limits."""
    if not messages:
        return messages

    system_messages = [message for message in messages if message.get("role") == "system"]
    conversational = [message for message in messages if message.get("role") != "system"]

    if len(conversational) > MAX_HISTORY_MESSAGES:
        conversational = conversational[-MAX_HISTORY_MESSAGES:]

    trimmed: list[dict] = []
    for message in system_messages + conversational:
        copy = dict(message)
        content = copy.get("content")
        if isinstance(content, str):
            copy["content"] = _truncate_content(content)
        trimmed.append(copy)

    return trimmed
