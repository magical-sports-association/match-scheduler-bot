'''
    :module_name: responses
    :module_summary: definitions for response messages of the bot
    :module_author: CountTails
'''

import logging
import sqlite3

import discord

from ..exceptions import MatchSchedulingException
from ..model.matchlist import ScheduledMatch
from ..model.config import DiscordBotEmbedResponseTemplate


__LOGGER__ = logging.getLogger(__name__)


def make_scheduling_success_message(
    interaction: discord.Interaction,
    match: ScheduledMatch,
    format: DiscordBotEmbedResponseTemplate
) -> discord.Embed:
    return discord.Embed(
        title=format.title,
        description=format.description,
        color=discord.Color.from_str(format.color)
    ).add_field(
        name=format.get_field("match_participants").name,
        value=format.get_field("match_participants").value.format(
            interaction.guild.get_role(match.away_team).name,
            interaction.guild.get_role(match.home_team).name
        ),
        inline=format.get_field("match_participants").inline
    ).add_field(
        name=format.get_field("confirm_scheduling").name,
        value=format.get_field("confirm_scheduling").value.format(
            '#bot-log'
        ),
        inline=format.get_field("confirm_scheduling").inline
    )


def make_scheduling_failure_message(
    interaction: discord.Interaction,
    error: MatchSchedulingException,
    format: DiscordBotEmbedResponseTemplate
) -> discord.Embed:
    return discord.Embed(
        title=format.title,
        description=format.description,
        color=discord.Color.from_str(format.color)
    ).add_field(
        name=format.get_field("match_scheduling_error").name,
        value=format.get_field("match_scheduling_error").value.format(
            str(error).removeprefix(f'{error.__class__.__name__}')
        ),
        inline=format.get_field("match_scheduling_error").inline
    )


def make_cancellation_success_message(
    interaction: discord.Interaction,
    home: discord.Role,
    away: discord.Role,
    format: DiscordBotEmbedResponseTemplate
) -> discord.Embed:
    return discord.Embed(
        title=format.title,
        description=format.description,
        color=discord.Color.from_str(format.color)
    ).add_field(
        name=format.get_field("match_participants").name,
        value=format.get_field("match_participants").value.format(
            away.name,
            home.name
        ),
        inline=format.get_field("match_participants").inline
    )


def make_cancellation_failure_message(
    interaction: discord.Interaction,
    home: discord.Role,
    away: discord.Role,
    format: DiscordBotEmbedResponseTemplate
) -> discord.Embed:
    return discord.Embed(
        title=format.title,
        description=format.description,
        color=discord.Color.from_str(format.color)
    ).add_field(
        name=format.get_field("no_such_match").name,
        value=format.get_field("no_such_match").value.format(
            away.name,
            home.name
        ),
        inline=format.get_field("no_such_match").inline
    )


def make_match_calendar_message(
    interaction: discord.Interaction,
    matches: sqlite3.Cursor,
    format: DiscordBotEmbedResponseTemplate
) -> discord.Embed:
    # FIXME: find a way to move this to db repo
    def row_to_match(r) -> ScheduledMatch:
        return ScheduledMatch(
            scheduled_timestamp=r[0],
            away_team=r[1],
            home_team=r[2],
            scheduled_at=r[3],
            scheduled_by=r[4]
        )

    msg = discord.Embed(
        title=format.title,
        description=format.description,
        color=discord.Color.from_str(format.color)
    )
    has_matches = False
    for match in map(row_to_match, matches.fetchall()):
        msg.add_field(
            name=format.get_field("match_item").name,
            value=format.get_field("match_item").value.format(
                interaction.guild.get_role(match.away_team).name,
                interaction.guild.get_role(match.home_team).name,
                f'<t:{match.scheduled_timestamp}:f>'
            ),
            inline=format.get_field("match_item").inline
        )
        has_matches = True
    else:
        if not has_matches:
            msg.add_field(
                name=format.get_field("match_list_empty").name,
                value=format.get_field("match_list_empty").value,
                inline=format.get_field("match_list_empty").inline
            )

    return msg
