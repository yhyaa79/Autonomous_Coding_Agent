import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "projects",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Agent ---
def _env_str(name: str, default: str = "") -> str:
    value = os.getenv(name, default).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1].strip()
    return value


# گپ‌جی‌پی‌تی — API سازگار با OpenAI (https://gapgpt.app/)
GAPGPT_API_KEY = _env_str("GAPGPT_API_KEY") or _env_str("OPENAI_API_KEY")
GAPGPT_BASE_URL = (
    _env_str("GAPGPT_BASE_URL", "https://api.gapgpt.app/v1").rstrip("/")
)
GAPGPT_MODEL = _env_str("GAPGPT_MODEL") or _env_str("OPENAI_MODEL", "gpt-4o-mini")
_workspace = os.getenv("AGENT_WORKSPACE", "")
AGENT_WORKSPACE = Path(_workspace).resolve() if _workspace else (BASE_DIR / "workspace").resolve()
AGENT_MAX_TOOL_ROUNDS = int(os.getenv("AGENT_MAX_TOOL_ROUNDS", "30"))
AGENT_COMMAND_TIMEOUT = int(os.getenv("AGENT_COMMAND_TIMEOUT", "120"))
AGENT_MAX_HISTORY_TURNS = int(os.getenv("AGENT_MAX_HISTORY_TURNS", "24"))
AGENT_MAX_TOOL_RESULT_CHARS = int(os.getenv("AGENT_MAX_TOOL_RESULT_CHARS", "8000"))
AGENT_MAX_HISTORY_MESSAGE_CHARS = int(os.getenv("AGENT_MAX_HISTORY_MESSAGE_CHARS", "6000"))
AGENT_MAX_TOOL_ARG_FIELD_CHARS = int(os.getenv("AGENT_MAX_TOOL_ARG_FIELD_CHARS", "600"))
AGENT_MAX_CHAT_PAYLOAD_CHARS = int(os.getenv("AGENT_MAX_CHAT_PAYLOAD_CHARS", "0"))
AGENT_LIST_DIR_MAX_ENTRIES = int(os.getenv("AGENT_LIST_DIR_MAX_ENTRIES", "500"))
AGENT_SEARCH_MAX_MATCHES = int(os.getenv("AGENT_SEARCH_MAX_MATCHES", "80"))
AGENT_GLOB_MAX_MATCHES = int(os.getenv("AGENT_GLOB_MAX_MATCHES", "120"))
AGENT_MAX_READ_BYTES = int(os.getenv("AGENT_MAX_READ_BYTES", "2000000"))
AGENT_GREP_USE_RG = _env_str("AGENT_GREP_USE_RG", "true").lower() in ("1", "true", "yes")
AGENT_IGNORE_DIRS = _env_str("AGENT_IGNORE_DIRS")
AGENT_MEMORY_SNIPPET_CHARS = int(os.getenv("AGENT_MEMORY_SNIPPET_CHARS", "2500"))
AGENT_WEB_FETCH_MAX_BYTES = int(os.getenv("AGENT_WEB_FETCH_MAX_BYTES", "500000"))
AGENT_WEB_FETCH_TIMEOUT = int(os.getenv("AGENT_WEB_FETCH_TIMEOUT", "25"))
GAPGPT_THINKING_MODEL = _env_str("GAPGPT_THINKING_MODEL")

_allow = _env_str("AGENT_PROJECT_PATH_ALLOWLIST")
AGENT_PROJECT_PATH_ALLOWLIST = [p.strip() for p in _allow.split(",") if p.strip()]
AGENT_API_TOKEN = _env_str("AGENT_API_TOKEN")
# فقط بک‌آپ‌های قدیمی. بک‌آپ جدید داخل <پروژه>/.aca/backups ذخیره می‌شود.
_backup_dir = _env_str("AGENT_MESSAGE_BACKUP_DIR")
AGENT_MESSAGE_BACKUP_DIR = (
    Path(_backup_dir).expanduser().resolve()
    if _backup_dir
    else (BASE_DIR / "var" / "message_backups").resolve()
)
AGENT_DEBUG_RETRY_THRESHOLD = int(os.getenv("AGENT_DEBUG_RETRY_THRESHOLD", "3"))
AGENT_DEBUG_HINT_THRESHOLD = int(os.getenv("AGENT_DEBUG_HINT_THRESHOLD", "2"))
AGENT_DEBUG_MAX_RECOVERIES = int(os.getenv("AGENT_DEBUG_MAX_RECOVERIES", "2"))
AGENT_MAX_CREATE_PROJECT_TOOL_ATTEMPTS = int(
    os.getenv("AGENT_MAX_CREATE_PROJECT_TOOL_ATTEMPTS", "3")
)
AGENT_LLM_TIMEOUT = float(os.getenv("AGENT_LLM_TIMEOUT", "300"))
AGENT_USER_INPUT_TIMEOUT = float(os.getenv("AGENT_USER_INPUT_TIMEOUT", "1800"))
AGENT_PERMISSION_TIMEOUT = float(os.getenv("AGENT_PERMISSION_TIMEOUT", "600"))

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "chat" / "static"]
