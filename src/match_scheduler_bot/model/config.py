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


class RolesList(pydantic.BaseModel):
    staff: str
    captain: str
    subscriber: str


class UsageGrants(pydantic.BaseModel):
    addmatch: List[str]
    cancelmatch: List[str]
    showmatches: List[str]


class AddMatchBehavior(pydantic.BaseModel):
    earliest: Annotated[int, pydantic.Field(gt=0)]
    latest: Annotated[int, pydantic.Field(gt=0)]


class CancleMatchBehavior(pydantic.BaseModel):
    latest: Annotated[int, pydantic.Field(gt=0)]


class ShowMatchesBehavior(pydantic.BaseModel):
    limit: Annotated[int, pydantic.Field(gt=0)]


class CommandBehaviors(pydantic.BaseModel):
    addmatch: AddMatchBehavior
    cancelmatch: CancleMatchBehavior
    showmatches: ShowMatchesBehavior


class PersistentStorage(pydantic.BaseModel):
    database: str | pathlib.Path


class BotConfig(pydantic.BaseModel):
    auth: BotAuthInfo
    roles: RolesList
    permissions: UsageGrants
    commands: CommandBehaviors
    storage: PersistentStorage
