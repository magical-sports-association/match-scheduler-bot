"""
    :module_name: config
    :module_summary: A set of dataclasses defining the config structure used
    :module_author: CountTails
"""

from typing import List, Dict, Literal
from typing_extensions import Annotated
import pathlib

import pydantic


class BotAuthInfo(pydantic.BaseModel):
    token: pydantic.SecretStr
    intents: Dict[str, bool]


class PersistentStorage(pydantic.BaseModel):
    database: str | pathlib.Path
    # timezones: Set[str]


class CommandParameterInfo(pydantic.BaseModel):
    uiname: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    helptext: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]


class CommandSpec(pydantic.BaseModel):
    invoke_with: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    description: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    parameters: Dict[str, CommandParameterInfo]
    allowed_roles: List[int | str]


class BotConfig(pydantic.BaseModel):
    auth: BotAuthInfo
    commands: Dict[
        Literal[
            'create_match',
            'delete_match',
            'list_matches',
            'command_help'
        ],
        CommandSpec
    ]
    storage: PersistentStorage
