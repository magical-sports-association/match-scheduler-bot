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
from ... import get_config

import discord
from discord.ext import commands
from discord.ext import tasks


__LOGGER__ = logging.getLogger(__name__)
__SPEC__ = get_config().cmds["get_match"]


class GetMatchCommand(commands.Cog):
    SUCCESS = discord.Color.from_str('#2ECC71')
    ERROR = discord.Color.from_str('#E74C3C')
    INFO = discord.Color.from_str('#ffc01c')

    def __init__(self, matchdb: str, bot: commands.Bot):
        self.matchlist = MatchListRepository(matchdb)
        self.bot = bot
        self.announce_match_start.start()

    @discord.app_commands.command(
        name=__SPEC__.invoke_with,
        description=__SPEC__.description
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
                value='- {} vs. {} | <t:{}:f>'.format(
                    interaction.guild.get_role(m.team_1_id).mention,
                    interaction.guild.get_role(m.team_2_id).mention,
                    m.start_time
                ),
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

    def match_starts_soon(self, guild: discord.Guild, match: ScheduledMatch) -> discord.Embed:
        return discord.Embed(
            title='Match Starting Soon',
            color=self.INFO
        ).add_field(
            name=f'Match starts in <t:{match.start_time}:R>',
            value='__{}__ vs. __{}__'.format(
                guild.get_role(match.team_1_id).mention,
                guild.get_role(match.team_2_id).mention
            ),
            inline=False
        ).add_field(
            name='How to watch',
            value='' +
            '- Do this\n' +
            '- Do that\n',
            inline=False
        ).add_field(
            name='Team instructions',
            value='' +
            '- Do this\n' +
            '- Do that\n',
            inline=False
        )

    def _starts_in(self, **kwargs):
        announce_time_start = datetime.timedelta(**kwargs)
        announce_time_end = announce_time_start + \
            datetime.timedelta(seconds=60)
        now = round(
            datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
        )

        def is_soon(m: ScheduledMatch) -> bool:
            time_diff = m.start_time - now
            before = announce_time_start.total_seconds()
            after = announce_time_end.total_seconds()
            return before <= time_diff <= after

        return is_soon

    @tasks.loop(seconds=60)
    async def announce_match_start(self):
        __LOGGER__.info('Task start: announcing matches starting soon')

        with self.matchlist as db:
            upcoming = db.find_upcoming_matches(
                not_before=round(
                    datetime.datetime.now(
                        tz=datetime.timezone.utc
                    ).timestamp()
                )
            )

        if server := self.bot.get_guild(get_config().auth.server):
            embeds = [
                self.match_starts_soon(server, m)
                for m in filter(self._starts_in(minutes=30), upcoming)
            ]
            if embeds:
                await server.get_channel(
                    __SPEC__.respond.public.channel_id
                ).send(
                    content=server.get_role(
                        __SPEC__.respond.public.mention[0]
                    ).mention,
                    embeds=embeds
                )

        __LOGGER__.info(
            'Task end: announced %d matches starting soon',
            len(embeds)
        )
