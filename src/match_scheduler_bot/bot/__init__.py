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
from .announcements import make_match_callendar_modified_announcement


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
    addmatch_options: BotCommand = config.get_command_info('schedule-match')
    delmatch_options: BotCommand = config.get_command_info('cancel-match')
    showmatches_options: BotCommand = config.get_command_info(
        'scheduled-matches')

    @bot.event
    async def on_ready():
        await bot.tree.sync()

    @bot.tree.command(name=addmatch_options.command_name)
    @discord.app_commands.describe(
        **{
            param: info.helptext
            for param, info in addmatch_options.parameters.items()
        }
    )
    @discord.app_commands.autocomplete(
        timezone=autocomplete_timezone
    )
    @discord.app_commands.rename(
        **{
            param: info.uiname
            for param, info in addmatch_options.parameters.items()
        }
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
            await make_match_callendar_modified_announcement(
                addmatch_options.task_completed_message,
                interaction.guild.get_channel(
                    config.storage.task_records.text_channel_id
                ),
                home_team,
                away_team,
                int(match_start.timestamp())
            )

    @bot.tree.command(name=delmatch_options.command_name)
    @discord.app_commands.describe(
        **{
            param: info.helptext
            for param, info in delmatch_options.parameters.items()
        }
    )
    @discord.app_commands.rename(
        **{
            param: info.uiname
            for param, info in delmatch_options.parameters.items()
        }

    )
    async def del_match(
            interaction: discord.Interaction,
            home: discord.Role,
            away: discord.Role
    ):
        LOGGER.info('Canceling the match: %s vs %s', away.name, home.name)
        with matchlist as db:
            cancelled_match = db.cancel_match(home.id, away.id).fetchone()
            print(f'{cancelled_match=}')
            if cancelled_match is not None:
                await interaction.response.send_message(
                    embed=make_cancellation_success_message(
                        interaction,
                        home,
                        away,
                        delmatch_options.direct_response_ok
                    ),
                    ephemeral=True
                )
                await make_match_callendar_modified_announcement(
                    delmatch_options.task_completed_message,
                    interaction.guild.get_channel(
                        config.storage.task_records.text_channel_id
                    ),
                    home,
                    away,
                    int(cancelled_match[0])
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
