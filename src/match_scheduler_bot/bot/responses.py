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
from ..model.config import DiscordBotEmbedResponse


__LOGGER__ = logging.getLogger(__name__)


def make_scheduling_success_message(
    interaction: discord.Interaction,
    match: ScheduledMatch,
    format: DiscordBotEmbedResponse
) -> discord.Embed:
    msg = discord.Embed(
        title=format.title,
        color=discord.Color.from_str(format.color)
    )
    msg.add_field(
        name=format.field_format.name,
        value=format.field_format.value,
        inline=format.field_format.inline
    )
    msg.set_footer(
        text=format.footer_format.text
    )
    return msg


def make_scheduling_failure_message(
    interaction: discord.Interaction,
    error: MatchSchedulingException,
    format: DiscordBotEmbedResponse
) -> discord.Embed:
    msg = discord.Embed(
        title=format.title,
        description=format.description,
        color=discord.Color.from_str(format.color)
    )
    msg.add_field(
        name=format.field_format.name,
        value=format.field_format.value.format(
            str(error).removeprefix(f'{error.__class__.__name__}')
        ),
        inline=format.field_format.inline
    )
    msg.set_footer(
        text=format.footer_format.text
    )
    return msg


def make_cancellation_success_message(
    interaction: discord.Interaction,
    home: discord.Role,
    away: discord.Role,
    format: DiscordBotEmbedResponse
) -> discord.Embed:
    msg = discord.Embed(
        title=format.title,
        color=discord.Color.from_str(format.color)
    )
    msg.add_field(
        name=format.field_format.name,
        value=format.field_format.value.format(
            away.name,
            home.name
        )
    )
    msg.set_footer(
        text=format.footer_format.text
    )
    return msg


def make_cancellation_failure_message(
    interaction: discord.Interaction,
    home: discord.Role,
    away: discord.Role,
    format: DiscordBotEmbedResponse
) -> discord.Embed:
    msg = discord.Embed(
        title=format.title,
        description=format.description,
        color=discord.Color.from_str(format.color)
    )
    msg.add_field(
        name=format.field_format.name,
        value=format.field_format.value.format(
            away.name,
            home.name
        )
    )
    msg.set_footer(
        text=format.footer_format.text
    )
    return msg


def make_match_calendar_message(
    interaction: discord.Interaction,
    matches: sqlite3.Cursor,
    format: DiscordBotEmbedResponse
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
            name=format.field_format.name,
            value=format.field_format.value.format(
                interaction.guild.get_role(match.away_team).name,
                interaction.guild.get_role(match.home_team).name,
                f'<t:{match.scheduled_timestamp}:f>'
            ),
            inline=format.field_format.inline
        )
        has_matches = True
    else:
        if not has_matches:
            msg.set_footer(
                text=format.footer_format.text
            )

    return msg
