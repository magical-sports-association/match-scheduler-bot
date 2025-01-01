"""
    :module_name: config
    :module_summary: A set of dataclasses defining the config structure used
    :module_author: CountTails
"""

import pydantic
from typing import List, Dict
from typing_extensions import Annotated
import pathlib


class BotAuthInfo(pydantic.BaseModel):
    token: pydantic.SecretStr
    intents: Dict[str, bool]


class PersistentStorage(pydantic.BaseModel):
    database: str | pathlib.Path
    logs: str | int


class BotConfig(pydantic.BaseModel):
    auth: BotAuthInfo
    storage: PersistentStorage
