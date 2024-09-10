import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic.networks import MySQLDsn


__all__ = [
    "settings",
]

project_root = os.path.abspath(os.path.dirname(__file__))

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        #extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    INIT_SCRIPT:str = os.path.join(project_root, "crawler/js/stealth.min.js")
    UA: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    CONTEXT_CACHE: str = "./data/context_cache.json"

settings = Settings()
