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
from discord.ext import tasks


__LOGGER__ = logging.getLogger(__name__)
__SPEC__ = get_config().cmds["get_match"]


class GetMatchCommand(commands.Cog):

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
            await interaction.response.send_message(
                content=AcknowledgeCommandUsage.get_match_used(
                    interaction.user
                ),
                ephemeral=True,
                delete_after=1
            )
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
            await interaction.followup.send(
                embed=CommandSucceeded.got_match(interaction, upcoming),
                ephemeral=True
            )
        except MatchScheduleNotObtained as err:
            __LOGGER__.error('Schedule acquisition prevented: %s', err.what)
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
        __LOGGER__.exception('Unexpected error\n', error)
        await interaction.followup.send(
            embed=CommandFailed.unexpected_failure(),
            ephemeral=True
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
                PublicLog.match_starting_soon(server, m)
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
