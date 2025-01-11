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
__SPEC__ = get_config().cmds["delete_match"]


class DeleteMatchCommand(commands.Cog):

    def __init__(self, matchdb: str):
        self.matchlist = MatchListRepository(matchdb)
        self.remove_past_matches.start()

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
    @discord.app_commands.checks.has_any_role(
        *__SPEC__.allowlist
    )
    async def do_it(
        self,
        interaction: discord.Interaction,
        team_1: discord.Role,
        team_2: discord.Role
    ):
        try:
            await interaction.response.send_message(
                content=AcknowledgeCommandUsage.delete_match_used(
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
            with self.matchlist as db:
                __LOGGER__.debug('Removing requested match from match list')
                cancelled = db.delete_match(
                    MatchToCancel.with_determistic_team_ordering(
                        team_1.id,
                        team_2.id
                    )
                )
            __LOGGER__.info('Match successfully cancelled')
            await interaction.followup.send(
                embed=CommandSucceeded.deleted_match(
                    interaction,
                    cancelled
                ),
                ephemeral=True
            )
            announcement = PublicLog.match_cancelled(
                interaction,
                cancelled
            )
            __LOGGER__.info('Publishing match cancellation to public bulletin')
            await interaction.guild.get_channel(
                __SPEC__.respond.public.channel_id
            ).send(
                embed=announcement
            )
            __LOGGER__.info('Alerting staff of cancelled match')
            await interaction.guild.get_channel(
                __SPEC__.respond.audit.channel_id
            ).send(
                content=interaction.guild.get_role(
                    __SPEC__.respond.audit.mention[0]
                ).mention,
                embed=announcement
            )
        except MatchCancellationException as err:
            __LOGGER__.error('Match cancellation prevented: %s', err.what)
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
                embed=CommandFailed.forbidden(
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
                embed=CommandFailed.unexpected_failure(),
                ephemeral=True
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
