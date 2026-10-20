"""Environment configuration with early validation."""
from dataclasses import dataclass
import os
import re
from dotenv import load_dotenv


TOKEN_PATTERN = re.compile(r"^\d{5,}:[A-Za-z0-9_-]{20,}$")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    restaurant_name: str
    database_path: str
    currency: str


def get_settings(environ: dict[str, str] | None = None) -> Settings:
    """Read and validate settings. Passing a mapping makes this easy to test."""
    if environ is None:
        load_dotenv()
        environ = os.environ
    token = environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is missing. Copy .env.example to .env and set your BotFather token.")
    if not TOKEN_PATTERN.fullmatch(token):
        raise ValueError("BOT_TOKEN has an invalid format. Check the token from @BotFather.")
    admin_ids: set[int] = set()
    raw_admins = environ.get("ADMIN_IDS", "").strip()
    if raw_admins:
        try:
            admin_ids = {int(part.strip()) for part in raw_admins.split(",") if part.strip()}
        except ValueError as exc:
            raise ValueError("ADMIN_IDS must be comma-separated numeric Telegram user IDs.") from exc
        if any(user_id <= 0 for user_id in admin_ids):
            raise ValueError("ADMIN_IDS must contain positive numeric Telegram user IDs.")
    return Settings(
        bot_token=token,
        admin_ids=frozenset(admin_ids),
        restaurant_name=environ.get("RESTAURANT_NAME", "Restaurant").strip() or "Restaurant",
        database_path=environ.get("DATABASE_PATH", "restaurant.db").strip() or "restaurant.db",
        currency=environ.get("CURRENCY", "сомони").strip() or "сомони",
    )
