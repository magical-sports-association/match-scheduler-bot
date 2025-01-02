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


__LOGGER__ = logging.getLogger(__name__)


def make_scheduling_success_message(
    interaction: discord.Interaction,
    match: ScheduledMatch
) -> discord.Embed:
    msg = discord.Embed(
        title='Match scheduled successfully!',
        color=discord.Color.green()
    )
    msg.add_field(
        name='',
        value='You have successfully scheduled a match'
    )
    msg.set_footer(
        text='Please check #bot-logs for the official confirmation or use `/showmatches` to set the updated match calendar'
    )
    return msg


def make_scheduling_failure_message(
    interaction: discord.Interaction,
    error: MatchSchedulingException
) -> discord.Embed:
    msg = discord.Embed(
        title='Match unabled to be scheduled',
        description='There was a problem scheduling the match',
        color=discord.Color.red()
    )
    msg.add_field(
        name='',
        value=f'Error: {error}'.removeprefix(f'{error.__class__.__name__}:'),
        inline=False
    )
    msg.add_field(
        name='',
        value='To schedule a match between these two teams, delete the existing one first.',
        inline=False
    )
    msg.set_footer(
        text='If you continue to experience issues scheduling a match, please alert staff'
    )
    return msg


def make_cancellation_success_message(
    interaction: discord.Interaction,
    home: discord.Role,
    away: discord.Role
) -> discord.Embed:
    msg = discord.Embed(
        title='Match cancelled successfully',
        color=discord.Color.green()
    )
    msg.add_field(
        name='',
        value='You have successfully cancelled the match between {} and {}'.format(
            away.name,
            home.name
        )
    )
    msg.set_footer(
        text='Please check #bot-logs for the official confirmation or use `/showmatches` to set the updated match calendar'
    )
    return msg


def make_cancellation_failure_message(
    interaction: discord.Interaction,
    home: discord.Role,
    away: discord.Role
) -> discord.Embed:
    msg = discord.Embed(
        title='Match unabled to be cancelled',
        description='There was a problem cancelling the match',
        color=discord.Color.red()
    )
    msg.add_field(
        name='',
        value='Error: It is likely the match you are attempting to cancel ({} vs {}) does not exist'.format(
            away.name,
            home.name
        )
    )
    msg.set_footer(
        text='If you continue to experience issues cancelling a match, please alert staff'
    )
    return msg


def make_match_calendar_message(
    interaction: discord.Interaction,
    matches: sqlite3.Cursor
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
        title='Scheduled matches',
        description='Here\'s a schedule of upcoming matches',
        color=discord.Color.blue()
    )
    has_matches = False
    for match in map(row_to_match, matches.fetchall()):
        msg.add_field(
            name='',
            value='- __{}__ vs __{}__ @ {}'.format(
                interaction.guild.get_role(match.away_team).name,
                interaction.guild.get_role(match.home_team).name,
                f'<t:{match.scheduled_timestamp}:f>'
            ),
            inline=False
        )
        has_matches = True
    else:
        if not has_matches:
            msg.set_footer(
                text='There are no matches scheduled. Add one using `/addmatch`!'
            )

    return msg
