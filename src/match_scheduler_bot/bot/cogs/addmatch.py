'''
    :module_name: addmatch
    :module_summary: cog definition for the slash command to add a match
    :module_author: CountTails
'''

from __future__ import annotations
import logging
import datetime

from ...model.matchlist import MatchListRepository
from ...model.rows import MatchToSchedule, ScheduledMatch
from ...exceptions import (
    MatchSchedulingException
)
from ... import get_config
from ..autocomplete import autocomplete_timezone
from ..validators import (
    date_in_near_future,
    date_parts
)
from ..responses.feedback import (
    AcknowledgeCommandUsage,
    CommandSucceeded,
    CommandFailed
)
from ..responses.announcements import (
    PublicLog,
)

import discord
from discord.ext import commands


__LOGGER__ = logging.getLogger(__name__)
__SPEC__ = get_config().cmds["create_match"]


class AddMatchCommand(commands.Cog):

    def __init__(self, matchdb: str):
        self.matchlist = MatchListRepository(matchdb)

    @discord.app_commands.command(
        name=__SPEC__.invoke_with,
        description=__SPEC__.description
    )
    @discord.app_commands.describe(
        **__SPEC__.parameters
    )
    @discord.app_commands.rename(
        **__SPEC__.renames
    )
    @discord.app_commands.autocomplete(
        timezone=autocomplete_timezone
    )
    @discord.app_commands.checks.has_any_role(
        *__SPEC__.allowlist
    )
    async def do_it(
        self,
        interaction: discord.Interaction,
        team_1: discord.Role,
        team_2: discord.Role,
        year: discord.app_commands.Range[int, datetime.MINYEAR, datetime.MAXYEAR],
        month: discord.app_commands.Range[int, 1, 12],
        day: discord.app_commands.Range[int, 1, 31],
        hour: discord.app_commands.Range[int, 0, 23],
        minute: discord.app_commands.Range[int, 0, 59],
        timezone: str
    ):
        try:
            await interaction.response.send_message(
                content=AcknowledgeCommandUsage.create_match_used(
                    used_by=interaction.user,
                    friend=team_1,
                    foe=team_2
                ),
                ephemeral=True,
                delete_after=1
            )
            __LOGGER__.info(
                '/%s invoked by user %s',
                interaction.command.name,
                interaction.user.display_name
            )
            __LOGGER__.debug('Validating date/time input')
            as_dt = date_in_near_future(date_parts(
                year,
                month,
                day,
                hour,
                minute,
                timezone
            ))
            __LOGGER__.debug('Provided date/time is valid')
            with self.matchlist as db:
                __LOGGER__.debug('Inserting proposed match into matchlist')
                scheduled = db.insert_match(
                    MatchToSchedule.with_determistic_team_ordering(
                        round(as_dt.timestamp()),
                        team_1.id,
                        team_2.id
                    )
                )
            __LOGGER__.info('Match successfully added')
            await interaction.followup.send(
                embed=CommandSucceeded.created_match(
                    interaction,
                    scheduled
                ),
                ephemeral=True
            )
            announcement = PublicLog.match_scheduled(
                interaction,
                scheduled
            )
            __LOGGER__.info('Publishing schuduled match to public bulletin')
            await interaction.guild.get_channel(
                __SPEC__.respond.public.channel_id
            ).send(
                embed=announcement
            )
            __LOGGER__.info('Alerting staff of new scheduled match')
            await interaction.guild.get_channel(
                __SPEC__.respond.audit.channel_id
            ).send(
                content=interaction.guild.get_role(
                    __SPEC__.respond.audit.mention[0]
                ).mention,
                embed=announcement
            )
        except MatchSchedulingException as err:
            __LOGGER__.error('Match scheduling prevented: %s', err.what)
            await interaction.followup.send(
                embed=CommandFailed.managed_failure(err),
                ephemeral=True
            )

    @do_it.error
    async def cannot_do_it(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ):
        if isinstance(error, discord.app_commands.MissingAnyRole):
            __LOGGER__.info(
                '%s does not have a required role to use /%s',
                interaction.user.display_name,
                interaction.command.name
            )
            await interaction.response.send_message(
                content=CommandFailed.forbidden(
                    interaction,
                    [
                        interaction.guild.get_role(r)
                        for r in __SPEC__.allowlist
                        if interaction.guild.get_role(r) is not None
                    ]
                ),
                ephemeral=True
            )
        else:
            __LOGGER__.exception('Unexpected error\n', error)
            await interaction.response.send_message(
                content=CommandFailed.unexpected_failure(),
                ephemeral=True
            )
