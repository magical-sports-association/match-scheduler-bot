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

import discord
from discord.ext import commands


__LOGGER__ = logging.getLogger(__name__)
__SPEC__ = get_config().cmds["create_match"]


class AddMatchCommand(commands.Cog):
    SUCCESS = discord.Color.from_str('#2ECC71')
    ERROR = discord.Color.from_str('#E74C3C')
    INFO = discord.Color.from_str('#ffc01c')

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
                content=self.ack_cmd_msg.format(team_1.name, team_2.name),
                ephemeral=True
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
            announcement = self.cmd_ok_msg(interaction, scheduled)
            await interaction.followup.send(
                embed=announcement,
                ephemeral=True
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
                embed=self.cmd_err_msg(err),
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
                content=self.cmd_forbidden.format(error.missing_roles),
                ephemeral=True
            )
        else:
            __LOGGER__.exception('Unexpected error\n', error)
            await interaction.response.send_message(
                content=self.cmd_exc_msg,
                ephemeral=True
            )

    @property
    def ack_cmd_msg(self) -> str:
        return 'Attempting to schedule a match between __{}__ and __{}__ ...'

    @property
    def cmd_forbidden(self) -> str:
        return '**Sorry**\n' + \
            'You do __NOT__ have permission to use this command.\n' + \
            'You must have at least one of these roles: {}.\n'

    @property
    def cmd_exc_msg(self) -> str:
        return 'Something has gone terribly wrong!\n' + \
            'Calm yourself. You didn\'t break anything.\n' + \
            'My programming did not account for what just happened.\n' + \
            'Please alert staff if this continues.'

    def cmd_err_msg(self, error: MatchSchedulingException) -> discord.Embed:
        return discord.Embed(
            title='Error',
            color=self.ERROR
        ).add_field(
            name='What went wrong',
            value=f'- {error.what}',
            inline=False
        )

    def cmd_ok_msg(
        self,
        interaction: discord.Interaction,
        match: ScheduledMatch
    ) -> discord.Embed:
        return discord.Embed(
            title='Match Scheduled',
            color=self.SUCCESS
        ).add_field(
            name='',
            value='- **Teams:** __{}__ vs. __{}__'.format(
                interaction.guild.get_role(match.team_1_id).name,
                interaction.guild.get_role(match.team_2_id).name
            ),
            inline=False
        ).add_field(
            name='',
            value='- **Date:** <t:{}:f>'.format(match.start_time),
            inline=False
        )
