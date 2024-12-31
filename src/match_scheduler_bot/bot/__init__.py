'''
    :module_name: bot
    :module_summary: a discord bot built using the commands framework
    :module_author: CountTails
'''

import logging
import datetime
import sqlite3

import discord
from discord.ext import commands

from ..model import ActiveConfig
from ..model.matchlist import MatchListRepository, ScheduledMatch
from ..exceptions import MatchSchedulingException
from .utils import (
    fuzzytzkeys,
    validate_start_time
)


LOGGER = logging.getLogger(__name__)


def setup_bot():
    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or('!'),
        intents=discord.Intents(
            **ActiveConfig.instance_or_err().intents_mapping
        )
    )
    matchlist = MatchListRepository(ActiveConfig.instance_or_err().dbpath)

    @bot.event
    async def on_ready():
        await bot.tree.sync()

    @bot.tree.command(name='addmatch')
    @discord.app_commands.describe(
        home_team='The home team participant in the match to be scheduled',
        away_team='The away team participant in the match to be scheduled',
        year='The year the scheduled match is to take place',
        month='The month the scheduled match is to take place',
        day='The day of month the scheduled match is to take place',
        hour='The hour of the day the match is to take place',
        minute='The minute of the hour the match is to take place',
        timezone='The timezone identifier used to localize the provide date/time info'
    )
    @discord.app_commands.autocomplete(
        timezone=fuzzytzkeys
    )
    async def add_match(
        interaction: discord.Interaction,
        home_team: discord.Role,
        away_team: discord.Role,
        year: discord.app_commands.Range[int, datetime.MINYEAR, datetime.MAXYEAR],
        month: discord.app_commands.Range[int, 1, 12],
        day: discord.app_commands.Range[int, 1, 31],
        hour: discord.app_commands.Range[int, 0, 23],
        minute: discord.app_commands.Range[int, 0, 59],
        timezone: str
    ):
        try:
            LOGGER.debug('Validating start time parameters')
            match_start: datetime.datetime = validate_start_time(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                tzkey=timezone
            )
            LOGGER.debug(
                'Start time parameters successfully validated and converted into aware datetime'
            )
            match_to_schedule = ScheduledMatch(
                scheduled_timestamp=int(match_start.timestamp()),
                home_team=home_team.id,
                away_team=away_team.id,
                scheduled_at=int(datetime.datetime.now(
                    tz=datetime.timezone.utc
                ).timestamp()),
                scheduled_by=interaction.user.id
            )
            with matchlist as db:
                db.schedule_match(match_to_schedule)

            LOGGER.info('Match scheduled successfully')

        except sqlite3.OperationalError as err:
            LOGGER.error(
                'Match could not be scheduled: %s',
                str(err)
            )
            await _issue_scheduling_failure_message(interaction)
        except sqlite3.IntegrityError as err:
            LOGGER.error(
                'Match already in match list: %s',
                str(err)
            )
            await _issue_scheduling_failure_message(interaction)
        except MatchSchedulingException as err:
            LOGGER.error(
                'Match could not be scheduled: %s',
                str(err)
            )
            await _issue_scheduling_failure_message(interaction)
        else:
            await _issue_scheduling_confirmation_message(interaction)

    async def _issue_scheduling_failure_message(interaction: discord.Interaction):
        await interaction.response.send_message('Scheduling failed', ephemeral=True)

    async def _issue_scheduling_confirmation_message(interaction: discord.Interaction):
        await interaction.response.send_message('Scheduling successful', ephemeral=True)

    @bot.tree.command(name='delmatch')
    async def del_match(interaction: discord.Interaction, home: str, away: str):
        await interaction.response.send_message(
            f'Canceling the match between {away} vs {home}'
        )

    @bot.tree.command(name='showmatches')
    async def show_matches(interaction: discord.Interaction, team: discord.Role):
        await interaction.response.send_message(
            f'Showing the upcoming matches with {team.mention}'
        )

    '''
    @bot.tree.command(name='domath')
    async def do_math(interaction: discord.Interaction, a: int, op: str, b: int):
        LOGGER.info('/domath command invoked')
        match op:
            case '+':
                LOGGER.debug('+ operator detected! computing sum...')
                await interaction.response.send_message(
                    f'{a} + {b} = {a + b}'
                )
            case '-':
                LOGGER.debug('- operator detected! computing difference...')
                await interaction.response.send_message(
                    f'{a} - {b} = {a - b}'
                )
            case '*':
                LOGGER.debug('* operator detected! computing product...')
                await interaction.response.send_message(
                    f'{a} * {b} = {a * b}'
                )

            case '/':
                LOGGER.debug('/ operator detected! computing quotient...')
                await interaction.response.send_message(
                    f'{a} / {b} = {a / b}'
                )
            case _:
                LOGGER.error('Unknown operator detected! raising exception')
                raise ValueError(f'Unknown operator: {op}')

    @do_math.error
    async def math_errors(interaction: discord.Interaction, error: Exception):
        LOGGER.error('An error occured: %s', str(error))

        await interaction.response.send_message(
            'The command failed!'
        )

    @bot.tree.command(name='asciifor')
    async def ascii_for(interaction: discord.Interaction, character: AsciiTransformer):
        await interaction.response.send_message(character)
    '''

    return bot
