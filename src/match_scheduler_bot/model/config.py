"""
    :module_name: config
    :module_summary: A set of dataclasses defining the config structure used
    :module_author: CountTails
"""

from typing import Dict
import pathlib

import pydantic


class BotAuthInfo(pydantic.BaseModel):
    token: pydantic.SecretStr
    intents: Dict[str, bool]


class DataSources(pydantic.BaseModel):
    database: str | pathlib.Path
    # timezones: Set[str]


class BotConfig(pydantic.BaseModel):
    auth: BotAuthInfo
    data: DataSources
