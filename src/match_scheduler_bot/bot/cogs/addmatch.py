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
from ..autocomplete import autocomplete_timezone
from ..validators import (
    date_in_near_future,
    date_parts
)

import discord
from discord.ext import commands


__LOGGER__ = logging.getLogger(__name__)


class AddMatchOptions:
    def __init__(self):
        raise TypeError(
            f'{self.__class__.__name__} cannot be instantiated'
        )

    @staticmethod
    def command_info() -> dict:
        __LOGGER__.debug('Retrieving command information')
        return {
            'name': 'schedule-match',
            'description': 'Schedule a match between two opposing teams'
        }

    @staticmethod
    def parameter_descriptions() -> dict:
        __LOGGER__.debug('Retrieving parameter descriptions')
        return {
            'team_1': 'Affiliated team',
            'team_2': 'Opposing team',
            'year': 'The year this match will take place',
            'month': 'The month this match will take place',
            'day': 'The day of the month this match will take place',
            'hour': 'The hour of day (in military time) this match will take place',
            'minute': 'The minute of the hour this match will take place',
            'timezone': 'The timezone identifier used to localize the provided date/time info'
        }

    @staticmethod
    def parameter_renames() -> dict:
        __LOGGER__.debug('Retrieving parameter renames')
        return {
            'team_1': 'team¹',
            'team_2': 'team²'
        }

    @staticmethod
    def autocomplete_callbacks() -> dict:
        __LOGGER__.debug('Retrieving autocomplete callbacks')
        return {
            'timezone': autocomplete_timezone
        }

    @staticmethod
    def allowlist() -> list:
        __LOGGER__.debug('Retrieving allowlist')
        return [
            'team captain',
            'staff'
        ]

    @staticmethod
    def bulletin_board_channel_id() -> int:
        return 1327047213234524252

    @staticmethod
    def staff_alert_channel_id() -> int:
        return 1327047313482317918

    @staticmethod
    def staff_role_id() -> int:
        return 1320147480482021416


class AddMatchCommand(commands.Cog):
    SUCCESS = discord.Color.from_str('#2ECC71')
    ERROR = discord.Color.from_str('#E74C3C')
    INFO = discord.Color.from_str('#ffc01c')

    def __init__(self, matchdb: str):
        self.matchlist = MatchListRepository(matchdb)

    @discord.app_commands.command(
        **AddMatchOptions.command_info()
    )
    @discord.app_commands.describe(
        **AddMatchOptions.parameter_descriptions()
    )
    @discord.app_commands.rename(
        **AddMatchOptions.parameter_renames()
    )
    @discord.app_commands.autocomplete(
        **AddMatchOptions.autocomplete_callbacks()
    )
    @discord.app_commands.checks.has_any_role(*AddMatchOptions.allowlist())
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
                AddMatchOptions.bulletin_board_channel_id()
            ).send(
                embed=announcement
            )
            __LOGGER__.info('Alerting staff of new scheduled match')
            await interaction.guild.get_channel(
                AddMatchOptions.staff_alert_channel_id()
            ).send(
                content=interaction.guild.get_role(
                    AddMatchOptions.staff_role_id()
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
