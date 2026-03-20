from dataclasses import dataclass
from pathlib import Path

import toml_rs
from adaptix import Retort

retort = Retort()


@dataclass(slots=True, kw_only=True)
class BotConfig:
    token: str


@dataclass(slots=True, kw_only=True)
class GoogleConfig:
    api_key: str


@dataclass(slots=True, kw_only=True)
class Config:
    telegram_bot: BotConfig
    google: GoogleConfig


def load_config(path: str) -> Config:
    return retort.load(toml_rs.loads(Path(path).read_text(), toml_version="1.1.0"), Config)
