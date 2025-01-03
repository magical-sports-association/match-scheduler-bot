'''
    :module_name: bot
    :module_summary: a discord bot built using the commands framework
    :module_author: CountTails
'''

import logging
import datetime

import discord
from discord.ext import commands

from ..model import get_config
from ..model.matchlist import MatchListRepository, ScheduledMatch
from ..model.config import BotCommand
from ..exceptions import MatchSchedulingException
from .autocomplete import autocomplete_timezone
from .validators import date_parts
from .responses import (
    make_scheduling_success_message,
    make_scheduling_failure_message,
    make_cancellation_success_message,
    make_cancellation_failure_message,
    make_match_calendar_message
)


LOGGER = logging.getLogger(__name__)


def setup_bot():
    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or('!'),
        intents=discord.Intents(
            **get_config().auth.intents
        )
    )
    config = get_config()
    matchlist = MatchListRepository(config.storage.database)
    addmatch_options: BotCommand = config.get_command_info('addmatch')
    delmatch_options: BotCommand = config.get_command_info('delmatch')
    showmatches_options: BotCommand = config.get_command_info('showmatches')

    @bot.event
    async def on_ready():
        await bot.tree.sync()

    @bot.tree.command(name=addmatch_options.command_name)
    @discord.app_commands.describe(
        **addmatch_options.parameters
    )
    @discord.app_commands.autocomplete(
        timezone=autocomplete_timezone
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
            match_start: datetime.datetime = date_parts(
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

        except MatchSchedulingException as err:
            LOGGER.error(
                'Match could not be scheduled: %s',
                str(err)
            )
            await interaction.response.send_message(
                embed=make_scheduling_failure_message(
                    interaction,
                    err,
                    addmatch_options.direct_response_not_ok
                ),
                ephemeral=True
            )
        else:
            LOGGER.info('Match scheduled successfully')
            await interaction.response.send_message(
                embed=make_scheduling_success_message(
                    interaction,
                    match_to_schedule,
                    addmatch_options.direct_response_ok
                ),
                ephemeral=True
            )

    @bot.tree.command(name=delmatch_options.command_name)
    @discord.app_commands.describe(
        **delmatch_options.parameters
    )
    async def del_match(
            interaction: discord.Interaction,
            home: discord.Role,
            away: discord.Role
    ):
        LOGGER.info('Canceling the match: %s vs %s', away.name, home.name)
        with matchlist as db:
            if db.cancel_match(home.id, away.id).rowcount > 0:
                await interaction.response.send_message(
                    embed=make_cancellation_success_message(
                        interaction,
                        home,
                        away,
                        delmatch_options.direct_response_ok
                    ),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    embed=make_cancellation_failure_message(
                        interaction,
                        home,
                        away,
                        delmatch_options.direct_response_not_ok
                    ),
                    ephemeral=True
                )

    @bot.tree.command(name=showmatches_options.command_name)
    async def show_matches(interaction: discord.Interaction):
        with matchlist as db:
            matches = db.find_matches()
            await interaction.response.send_message(
                embed=make_match_calendar_message(
                    interaction,
                    matches,
                    showmatches_options.direct_response_ok
                ),
                ephemeral=True
            )

    return bot
