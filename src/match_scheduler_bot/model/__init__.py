'''
    :module_name: model
    :module_summary: data model for the discord bot
    :module_author: CountTails
'''

from pathlib import Path
from typing import List, Dict, Annotated, Optional, Union
from .filecache import FileCacheProvider
from .pool import AsyncConnectionPool
from .rows import (
    MatchToCancel,
    MatchToSchedule,
    ScheduledMatch
)
from .runners import MatchlistQueryRunner


import pydantic


class OutputChannel(pydantic.BaseModel):
    channel_id: Annotated[int, pydantic.Field(gt=0)]
    interested_parties: List[int]


class BotOutput(pydantic.BaseModel):
    public: OutputChannel
    audit: OutputChannel


class BotAuthInfo(pydantic.BaseModel):
    token: pydantic.SecretStr
    intents: Dict[str, pydantic.StrictBool]
    server: Annotated[int, pydantic.Field(gt=0)]
    logs: BotOutput


class CommandSpec(pydantic.BaseModel):
    invoke_with: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    description: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    parameters: Annotated[Dict[str, str], pydantic.Field(default={})]
    renames: Annotated[Dict[str, str], pydantic.Field(default={})]
    allowlist: Optional[List[int | str]]


class GroupSpec(pydantic.BaseModel):
    group_module: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    group_name: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    group_description: Annotated[
        pydantic.StrictStr, pydantic.Field(min_length=1)
    ]
    group_commands: Dict[str, CommandSpec]


class DataSources(pydantic.BaseModel):
    database: str | Path
    messages: str | Path
    # timezones: Set[str]


class BotConfig(pydantic.BaseModel):
    auth: BotAuthInfo
    commands: Dict[str, Union[GroupSpec, CommandSpec]]
    data: DataSources
