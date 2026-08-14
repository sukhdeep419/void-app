import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_cors = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
CORS_ORIGINS = [origin.strip() for origin in _cors.split(",") if origin.strip()]

PENDING_ACTION_TTL_SECONDS = int(os.getenv("PENDING_ACTION_TTL_SECONDS", "300"))
APP_CACHE_TTL_SECONDS = int(os.getenv("APP_CACHE_TTL_SECONDS", "300"))
TERMINAL_COMMAND_TIMEOUT = int(os.getenv("TERMINAL_COMMAND_TIMEOUT", "60"))
TERMINAL_LONG_COMMAND_TIMEOUT = int(os.getenv("TERMINAL_LONG_COMMAND_TIMEOUT", "600"))
