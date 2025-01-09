'''
    :module_name: getmatch
    :module_summary: cog definition for slash commands and tasks to display the matchlist
    :module_author: CountTails
'''

from __future__ import annotations
import logging
import datetime
from typing import List

from ...model.matchlist import MatchListRepository
from ...model.rows import ScheduledMatch
from ...exceptions import MatchScheduleNotObtained

import discord
from discord.ext import commands


__LOGGER__ = logging.getLogger(__name__)


class GetMatchOptions:
    def __init__(self):
        raise TypeError(
            f'{self.__class__.__name__} cannot be instantiated'
        )

    @staticmethod
    def command_info() -> dict:
        __LOGGER__.debug('Retrieving command information')
        return {
            'name': 'match-calendar',
            'description': 'Display a list of upcoming matches'
        }


class GetMatchCommand(commands.Cog):
    SUCCESS = discord.Color.from_str('#2ECC71')
    ERROR = discord.Color.from_str('#E74C3C')
    INFO = discord.Color.from_str('#ffc01c')

    def __init__(self, matchdb: str):
        self.matchlist = MatchListRepository(matchdb)

    @discord.app_commands.command(
        **GetMatchOptions.command_info()
    )
    async def do_it(self, interaction: discord.Interaction):
        try:
            __LOGGER__.info('Retrieving upcoming scheduled matches')
            with self.matchlist as db:
                upcoming = db.find_upcoming_matches(
                    not_before=round(
                        datetime.datetime.now(
                            tz=datetime.timezone.utc
                        ).timestamp()
                    )
                )
            __LOGGER__.info('Displaying match list as response')
            await interaction.response.send_message(
                embed=self.cmd_ok_msg(interaction, upcoming),
                ephemeral=True
            )
        except MatchScheduleNotObtained as err:
            __LOGGER__.error('Schedule acquisition prevented: %s', err.what)
            await interaction.response.send_message(
                embed=self.cmd_err_msg(err),
                ephemeral=True
            )

    @do_it.error
    async def cannot_do_it(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ):
        __LOGGER__.exception('Unexpected error\n', error)
        await interaction.response.send_message(
            content=self.cmd_exc_msg,
            ephemeral=True
        )

    @property
    def cmd_exc_msg(self) -> str:
        return 'Something has gone terribly wrong!\n' + \
            'Calm yourself. You didn\'t break anything.\n' + \
            'My programming did not account for what just happened.\n' + \
            'Please alert staff if this continues.'

    def cmd_err_msg(self, error: MatchScheduleNotObtained) -> discord.Embed:
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
        matches: List[ScheduledMatch]
    ) -> discord.Embed:
        msg = discord.Embed(
            title='Upcoming MSA Matches',
            color=self.INFO
        )
        has_matches = False
        for m in matches:
            msg.add_field(
                name='',
                value='- **Teams** | {} vs. {}'.format(
                    interaction.guild.get_role(m.team_1_id).mention,
                    interaction.guild.get_role(m.team_2_id).mention
                ),
                inline=False
            )
            msg.add_field(
                name='',
                value='- **Date** | <t:{}:f>'.format(m.start_time),
                inline=False
            )
            has_matches = True
        else:
            if not has_matches:
                msg.add_field(
                    name='',
                    value='-# There are no matches scheduled at this time'
                )
        return msg
