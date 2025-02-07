'''
    :module_name: scheduling
    :module_summary: command group for scheduling MSA league matches
    :module_author: CountTails
'''

from __future__ import annotations
import logging
import datetime

from ...model.filecache import FileCacheProvider
from ...model.rows import MatchToSchedule, ScheduledMatch, MatchToCancel
from ...model import CommandSpec, GroupSpec
from ...exceptions import (
    MatchSchedulingException,
    MatchCancellationException,
    MatchScheduleNotObtained
)
from ... import get_config
from ..autocomplete import autocomplete_timezone
from ..validators import (
    date_in_near_future,
    date_parts
)

import discord


__LOGGER__ = logging.getLogger(__name__)
__SPEC__: GroupSpec = get_config().commands["scheduling"]


@discord.app_commands.guilds(get_config().auth.server)
class MatchSchedulingCommandGroup(discord.app_commands.Group):
    '''
        Command group implementing the slash commands to schedule MSA matches
    '''
    __CREATE__: CommandSpec = __SPEC__.group_commands["create_match"]
    __READ__: CommandSpec = __SPEC__.group_commands["get_match"]
    __DELETE__: CommandSpec = __SPEC__.group_commands["delete_match"]

    def __init__(self):
        self._message_provider = FileCacheProvider(
            get_config().data.messages,
            3600
        )
        super().__init__(
            name=__SPEC__.group_name,
            description=__SPEC__.group_description,
            guild_only=True
        )

    @discord.app_commands.command(
        name=__CREATE__.invoke_with,
        description=__CREATE__.description
    )
    @discord.app_commands.describe(
        **__CREATE__.parameters
    )
    @discord.app_commands.rename(
        **__CREATE__.renames
    )
    @discord.app_commands.autocomplete(
        timezone=autocomplete_timezone
    )
    @discord.app_commands.checks.has_any_role(
        *__CREATE__.allowlist
    )
    async def add_match(
        self,
        interaction: discord.Interaction,
        team_1: discord.Role,
        team_2: discord.Role,
        year: discord.app_commands.Range[int, 1970, datetime.MAXYEAR],
        month: discord.app_commands.Range[int, 1, 12],
        day: discord.app_commands.Range[int, 1, 31],
        hour: discord.app_commands.Range[int, 0, 23],
        minute: discord.app_commands.Range[int, 0, 59],
        timezone: str
    ):
        pass

    @add_match.error
    async def cannot_add_match(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ):
        pass

    @discord.app_commands.command(
        name=__DELETE__.invoke_with,
        description=__DELETE__.description
    )
    @discord.app_commands.describe(
        **__DELETE__.parameters
    )
    @discord.app_commands.rename(
        **__DELETE__.renames
    )
    @discord.app_commands.checks.has_any_role(
        *__DELETE__.allowlist
    )
    async def delete_match(
        self,
        interaction: discord.Interaction,
        team_1: discord.Role,
        team_2: discord.Role
    ):
        pass

    @delete_match.error
    async def cannot_cancel_match(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ):
        pass

    @discord.app_commands.command(
        name=__READ__.invoke_with,
        description=__READ__.description
    )
    async def show_matches(self, interaction: discord.Interaction):
        pass

    @show_matches.error
    async def cannot_show_matches(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ):
        pass


async def setup(bot: discord.ext.commands.Bot) -> None:
    '''
        Adds the functionality in this module to the provided bot

        Parameters:
            bot [discord.ext.commands.Bot] the bot set up

        Returns:
            None
    '''
    bot.tree.add_command(MatchSchedulingCommandGroup())
