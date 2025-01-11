'''
    :module_name: model
    :module_summary: data model for the discord bot
    :module_author: CountTails
'''

from pathlib import Path
from typing import List, Dict, Annotated, Optional


import pydantic


class BotAuthInfo(pydantic.BaseModel):
    token: pydantic.SecretStr
    intents: Dict[str, bool]
    server: Annotated[int, pydantic.Field(gt=0)]


class CommandOutput(pydantic.BaseModel):
    channel_id: Annotated[int, pydantic.Field(gt=0)]
    mention: List[int]


class CommandOutputDestination(pydantic.BaseModel):
    public: Optional[CommandOutput]
    audit: Optional[CommandOutput]


class CommandSpec(pydantic.BaseModel):
    invoke_with: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    description: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    parameters: Annotated[Dict[str, str], pydantic.Field(default={})]
    renames: Annotated[Dict[str, str], pydantic.Field(default={})]
    allowlist: Optional[List[int | str]]
    respond: CommandOutputDestination


class DataSources(pydantic.BaseModel):
    database: str | Path
    # timezones: Set[str]


class BotConfig(pydantic.BaseModel):
    auth: BotAuthInfo
    cmds: Dict[str, CommandSpec]
    data: DataSources
