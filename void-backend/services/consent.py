import re

from models import ChatMessage

AFFIRMATIVE_PATTERN = re.compile(
    r"^(?:"
    r"yes|yeah|yep|yup|sure|ok|okay|k|"
    r"go ahead|do it|approve|approved|proceed|"
    r"please do|please go ahead|confirm|confirmed|"
    r"absolutely|affirmative|sounds good|"
    r"that(?:'s| is) fine|that works|go for it|make it so"
    r")(?:[,.!?\s]+.*)?$",
    re.IGNORECASE,
)


def user_gave_explicit_consent(messages: list[ChatMessage]) -> bool:
    """True when the latest user message is a clear go-ahead (e.g. 'yes' after a prior question)."""
    latest = ""
    for message in reversed(messages):
        if message.role == "user":
            latest = message.content.strip()
            break

    if not latest:
        return False

    if AFFIRMATIVE_PATTERN.match(latest):
        return True

    lowered = latest.lower()
    return lowered.startswith(("yes ", "yeah ", "sure ", "ok ", "go ahead ")) and len(latest) < 80
