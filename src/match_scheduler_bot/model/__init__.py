'''
    :module_name: model
    :module_summary: data model for the discord bot
    :module_author: CountTails
'''

from pathlib import Path
from typing import Optional, Dict


import pydantic


class BotAuthInfo(pydantic.BaseModel):
    token: pydantic.SecretStr
    intents: Dict[str, bool]


class DataSources(pydantic.BaseModel):
    database: str | Path
    # timezones: Set[str]


class BotConfig(pydantic.BaseModel):
    auth: BotAuthInfo
    data: DataSources
