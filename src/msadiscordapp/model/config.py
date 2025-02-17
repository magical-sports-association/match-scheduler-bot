'''
    :module_name: config
    :module_summary: definition of pydantic model for validating input config
    :module_author: CountTails
'''

from pathlib import Path
from typing import List, Dict, Annotated, Optional, Union

import pydantic


class OutputChannel(pydantic.BaseModel):
    '''
        Describes the channel the bot will send its output to

        Attributes:
            channel_id [int]: Id of the channel in the server to send output to
            interested_parties [List[int]]: List of role Id to ping with output
    '''
    channel_id: Annotated[int, pydantic.Field(gt=0)]
    interested_parties: List[int]


class BotOutput(pydantic.BaseModel):
    '''
        Describes the output channels the bot relies on to function

        Attributes:
            public: [OutputChannel]: publicly visible output
            audit: [OutputChannel]: audit message output
    '''
    public: OutputChannel
    audit: OutputChannel


class BotAuthInfo(pydantic.BaseModel):
    '''
        Describes the authentication info used to log the bot into discord

        Attributes:
            token [pydantic.SecretStr]: secret token (bot's password)
            intents [Dict[str, pydantic.StrictBool]]: bot's privilege request
            server [int]: server id bot is expected to be installed on
            logs [BotOutput]: output specification for the bot
    '''
    token: pydantic.SecretStr
    intents: Dict[str, pydantic.StrictBool]
    server: Annotated[int, pydantic.Field(gt=0)]
    logs: BotOutput


class CommandSpec(pydantic.BaseModel):
    '''
        Describes the command the discord.py library will create from callback

        Attributes:
            invoke_with [pydantic.StrictStr]: token to invoke this command
            description [pydantic.StrictStr]: short help text to display in UI
            parameters [Dict[str, str]]: short help text to display on options
            renames [Dict[str, str]]: option names to display on UI (if given)
            allowlist [Optional[List[int]]]: role ids allowed to use this cmd
    '''
    invoke_with: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    description: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    parameters: Annotated[Dict[str, str], pydantic.Field(default={})]
    renames: Annotated[Dict[str, str], pydantic.Field(default={})]
    allowlist: Optional[List[int | str]]


class GroupSpec(pydantic.BaseModel):
    '''
        Describes a group of commands the discord.py will create from callbacks

        Attributes:
            group_module [pydantic.StrictStr]: python module group created in
            group_name [pydantic.StrictStr]: token to invoke this group
            group_description [pydantic.StrictStr]: help text to display in UI
            group_commands [Dict[str, CommandSpec]]: commands in this group
    '''
    group_module: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    group_name: Annotated[pydantic.StrictStr, pydantic.Field(min_length=1)]
    group_description: Annotated[
        pydantic.StrictStr, pydantic.Field(min_length=1)
    ]
    group_commands: Dict[str, CommandSpec]


class DataSources(pydantic.BaseModel):
    '''
        Describes the data sources available to this bot

        Attributes:
            database [str | Path]: database file the bot will use
            messages [str | Path]: message directory the bot will use
    '''
    database: str | Path
    messages: str | Path
    # timezones: Set[str]


class BotConfig(pydantic.BaseModel):
    '''
        Describes the top-level format of the bot's configuration file

        Attributes:
            auth [BotAuthInfo]: information for bot authentication
            commands [Dict[str, Union[GroupSpec, CommandSpec]]]: bot's commands
            data [DataSources]: external resources available to the bot
    '''
    auth: BotAuthInfo
    commands: Dict[str, Union[GroupSpec, CommandSpec]]
    data: DataSources
