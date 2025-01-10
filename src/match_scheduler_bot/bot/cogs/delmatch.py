'''
    :module_name: delmatch
    :module_summary: cog definition for slash command used to delete a match
    :module_author: CountTails
'''

from __future__ import annotations
import logging
import datetime

from ...model.matchlist import MatchListRepository
from ...model.rows import ScheduledMatch, MatchToCancel
from ...exceptions import MatchCancellationException

import discord
from discord.ext import commands
from discord.ext import tasks


__LOGGER__ = logging.getLogger(__name__)


class DelMatchOptions:
    def __init__(self):
        raise TypeError(
            f'{self.__class__.__name__} cannot be instantiated'
        )

    @staticmethod
    def command_info() -> dict:
        __LOGGER__.debug('Retrieving command information')
        return {
            'name': 'cancel-match',
            'description': 'Cancel a match between two opposing teams'
        }

    @staticmethod
    def parameter_descriptions() -> dict:
        __LOGGER__.debug('Retrieving parameter descriptions')
        return {
            'team_1': 'Affiliated team',
            'team_2': 'Opposing team',
        }

    @staticmethod
    def paremeter_renames() -> dict:
        __LOGGER__.debug('Retrieving parameter renames')
        return {
            'team_1': 'team¹',
            'team_2': 'team²'
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


class DeleteMatchCommand(commands.Cog):
    SUCCESS = discord.Color.from_str('#2ECC71')
    ERROR = discord.Color.from_str('#E74C3C')
    INFO = discord.Color.from_str('#ffc01c')

    def __init__(self, matchdb: str):
        self.matchlist = MatchListRepository(matchdb)
        self.remove_past_matches.start()

    @discord.app_commands.command(
        **DelMatchOptions.command_info()
    )
    @discord.app_commands.describe(
        **DelMatchOptions.parameter_descriptions()
    )
    @discord.app_commands.rename(
        **DelMatchOptions.paremeter_renames()
    )
    @discord.app_commands.checks.has_any_role(*DelMatchOptions.allowlist())
    async def do_it(
        self,
        interaction: discord.Interaction,
        team_1: discord.Role,
        team_2: discord.Role
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
            with self.matchlist as db:
                __LOGGER__.debug('Removing requested match from match list')
                cancelled = db.delete_match(
                    MatchToCancel.with_determistic_team_ordering(
                        team_1.id,
                        team_2.id
                    )
                )
            __LOGGER__.info('Match successfully cancelled')
            announcement = self.cmd_ok_msg(interaction, cancelled)
            await interaction.followup.send(
                embed=announcement,
                ephemeral=True
            )
            __LOGGER__.info('Publishing match cancellation to public bulletin')
            await interaction.guild.get_channel(
                DelMatchOptions.bulletin_board_channel_id()
            ).send(
                embed=announcement
            )
            __LOGGER__.info('Alerting staff of cancelled match')
            await interaction.guild.get_channel(
                DelMatchOptions.staff_alert_channel_id()
            ).send(
                content=interaction.guild.get_role(
                    DelMatchOptions.staff_role_id()
                ).mention,
                embed=announcement
            )
        except MatchCancellationException as err:
            __LOGGER__.error('Match cancellation prevented: %s', err.what)
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
        return 'Attempting to cancel the match between __{}__ and __{}__ ...'

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

    def cmd_err_msg(self, error: MatchCancellationException) -> discord.Embed:
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
            title='Match Cancelled',
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

    @tasks.loop(seconds=60)
    async def remove_past_matches(self):
        __LOGGER__.info('Task start: remove past matches from match list')

        with self.matchlist as db:
            purged = db.purge_expired(
                round(
                    datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
                )
            )

        __LOGGER__.info(
            'Task end: removed %d matches from match list',
            len(purged)
        )
