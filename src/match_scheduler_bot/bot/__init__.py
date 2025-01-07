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
from ..model.config import CommandSpec
from ..exceptions import MatchSchedulingException
from .autocomplete import autocomplete_timezone
from .validators import date_parts


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
    addmatch_options: CommandSpec = config.commands.get('create_match')
    delmatch_options: CommandSpec = config.commands.get('delete_match')
    showmatches_options: CommandSpec = config.commands.get('list_matches')
    helpcommand_options: CommandSpec = config.commands.get('command_help')

    @bot.event
    async def on_ready():
        await bot.tree.sync()

    @bot.tree.command(
        name=addmatch_options.invoke_with,
        description=addmatch_options.description
    )
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
        team_1: discord.Role,
        team_2: discord.Role,
        year: discord.app_commands.Range[int, datetime.MINYEAR, datetime.MAXYEAR],
        month: discord.app_commands.Range[int, 1, 12],
        day: discord.app_commands.Range[int, 1, 31],
        hour: discord.app_commands.Range[int, 0, 23],
        minute: discord.app_commands.Range[int, 0, 59],
        timezone: str
    ):
        pass

    @bot.tree.command(
        name=delmatch_options.invoke_with,
        description=delmatch_options.description
    )
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
            team_1: discord.Role,
            team_2: discord.Role
    ):
        pass

    @bot.tree.command(
        name=showmatches_options.invoke_with,
        description=showmatches_options.description
    )
    async def show_matches(interaction: discord.Interaction):
        pass

    return bot
