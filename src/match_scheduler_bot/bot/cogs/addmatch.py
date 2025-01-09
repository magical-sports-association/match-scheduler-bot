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
    InvalidStartTimeGiven,
    InvalidTimezoneSpecified,
    DuplicatedMatchDetected,
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
            __LOGGER__.debug('Validating date input')
            as_dt = date_in_near_future(date_parts(
                year,
                month,
                day,
                hour,
                minute,
                timezone
            ))
            __LOGGER__.debug('Provided date is valid')
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
                embed=self.cmd_ok_msg(interaction, scheduled),
                ephemeral=True
            )
        except InvalidTimezoneSpecified as err:
            __LOGGER__.error('Provided timezone is not known')
        except InvalidStartTimeGiven as err:
            __LOGGER__.error('Provided datetime is invalid')
        except DuplicatedMatchDetected as err:
            __LOGGER__.error('Provided matchup already exists')
        except MatchSchedulingException as err:
            __LOGGER__.error('Match scheduling prevented')

    @do_it.error
    async def cannot_do_it(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ):
        pass

    @property
    def ack_cmd_msg(self) -> str:
        return 'Attempting to schedule a match between __{}__ and __{}__ ...'

    def cmd_err_msg(self, error: MatchSchedulingException) -> discord.Embed:
        return "Error: {}"

    def cmd_ok_msg(
        self,
        interaction: discord.Interaction,
        match: ScheduledMatch
    ) -> discord.Embed:
        return discord.Embed(
            title='Success',
            color=self.SUCCESS
        ).add_field(
            name='Teams',
            value='- __{}__ and __{}__'.format(
                interaction.guild.get_role(match.team_1_id).name,
                interaction.guild.get_role(match.team_2_id).name
            ),
            inline=False
        ).add_field(
            name='Kickoff',
            value='- <t:{}:f>'.format(match.start_time),
            inline=False
        )
