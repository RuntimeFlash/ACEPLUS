import os
from dataclasses import dataclass
from typing import Tuple


def _parse_origins() -> Tuple[str, ...]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    values = [value.strip() for value in raw.split(",")]
    return tuple(value for value in values if value)


@dataclass(frozen=True)
class AppSettings:
    app_name: str = "AcePlus Backend v2"
    app_version: str = "2.0.0"
    cors_origins: Tuple[str, ...] = _parse_origins()
    allow_credentials: bool = True


settings = AppSettings()

