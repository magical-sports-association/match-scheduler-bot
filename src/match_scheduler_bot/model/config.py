"""
    :module_name: config
    :module_summary: A set of dataclasses defining the config structure used
    :module_author: CountTails
"""

from typing import List, Dict, Set, Optional, Any
from typing_extensions import Annotated
import pathlib
import re

import pydantic

from ..exceptions import MissingConfigurationError


class BotAuthInfo(pydantic.BaseModel):
    token: pydantic.SecretStr
    intents: Dict[str, bool]


class DiscordBotChannel(pydantic.BaseModel):
    log_to_text_channel: pydantic.StrictBool
    text_channel_id: Annotated[pydantic.StrictInt, pydantic.Field(gt=0)]


class EmbedResponseField(pydantic.BaseModel):
    name: Annotated[pydantic.StrictStr, pydantic.Field(max_length=256)]
    value: Annotated[pydantic.StrictStr, pydantic.Field(max_length=1024)]
    inline: pydantic.StrictBool


class EmbedResponseFooter(pydantic.BaseModel):
    text: Annotated[pydantic.StrictStr, pydantic.Field(max_length=2048)]


class DiscordBotEmbedResponse(pydantic.BaseModel):
    title: Annotated[pydantic.StrictStr, pydantic.Field(max_length=256)]
    description: Annotated[pydantic.StrictStr, pydantic.Field(max_length=4096)]
    color: Annotated[
        pydantic.StrictStr,
        pydantic.Field(
            min_length=7,
            max_length=7,
            pattern=re.compile(r'^#[0-9A-Fa-f]{6}$')
        )
    ]
    field_format: EmbedResponseField
    footer_format: EmbedResponseFooter


class PersistentStorage(pydantic.BaseModel):
    database: str | pathlib.Path
    usage_records: DiscordBotChannel
    task_records: DiscordBotChannel
    # timezones: Set[str]


class BotCommand(pydantic.BaseModel):
    command_name: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    parameters: Dict[str, str]
    direct_response_ok: Optional[DiscordBotEmbedResponse]
    direct_response_not_ok: Optional[DiscordBotEmbedResponse]
    task_completed_message: Optional[DiscordBotEmbedResponse]

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BotCommand):
            return self.command_name == other.command_name
        if isinstance(other, str):
            return self.command_name == other
        return False


class BotConfig(pydantic.BaseModel):
    auth: BotAuthInfo
    commands: List[BotCommand]
    storage: PersistentStorage

    def get_command_info(self, cmd: str) -> BotCommand:
        for cmdinfo in self.commands:
            if cmdinfo == cmd:
                return cmdinfo
        else:
            raise MissingConfigurationError(
                f'No such command configured: {cmd}'
            )
