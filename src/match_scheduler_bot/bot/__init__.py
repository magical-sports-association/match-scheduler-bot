'''
    :module_name: bot
    :module_summary: a discord bot built using the commands framework
    :module_author: CountTails
'''

import logging

import discord
from discord.ext import commands

from ..model import get_config
from .cogs import (
    AddMatchCommand,
    DeleteMatchCommand
)


__LOGGER__ = logging.getLogger(__name__)
__BOT__ = None


def use_bot() -> commands.Bot:
    global __BOT__
    if __BOT__ is None:
        __LOGGER__.info('First request for bot instance, initializing...')
        __BOT__ = commands.Bot(
            command_prefix=commands.when_mentioned_or('!'),
            intents=discord.Intents(
                **get_config().auth.intents
            )
        )

        @__BOT__.event
        async def on_ready():
            __LOGGER__.info('Responding to event `on_ready`')
            await __BOT__.add_cog(AddMatchCommand(get_config().data.database))
            __LOGGER__.info('Added extension: %s', AddMatchCommand.__name__)
            await __BOT__.add_cog(DeleteMatchCommand(get_config().data.database))
            __LOGGER__.info('Added extension: %s', DeleteMatchCommand.__name__)
            __LOGGER__.debug('Synchronizing command tree with discord')
            await __BOT__.tree.sync()
            __LOGGER__.debug('Command tree synchronized')

    __LOGGER__.info('Returning the singleton bot instance')
    return __BOT__


'''
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
        try:
            await interaction.response.send_message(
                content='Attempting to schedule a match between __{}__ and __{}__ ...'.format(
                    team_1.name,
                    team_2.name
                ),
                ephemeral=True
            )
            as_dt = date_in_near_future(date_parts(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                tzkey=timezone
            ))
            with matchlist as db:
                scheduled = db.insert_match(
                    MatchToSchedule.with_determistic_team_ordering(
                        round(as_dt.timestamp()),
                        team_1.id,
                        team_2.id
                    )
                )
            await interaction.followup.send(
                embed=None,
                ephemeral=True
            )

        except InvalidTimezoneSpecified as err:
            pass
        except InvalidStartTimeGiven as err:
            pass
        except DuplicatedMatchDetected as err:
            pass
        except MatchSchedulingException as err:
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
        try:
            with matchlist as db:
                db.delete_match(
                    MatchToCancel.with_determistic_team_ordering(
                        team_1.id,
                        team_2.id
                    )
                )
        except CancellingNonexistantMatch as err:
            pass
        except MatchCancellationException as err:
            pass

    @bot.tree.command(
        name=showmatches_options.invoke_with,
        description=showmatches_options.description
    )
    async def show_matches(interaction: discord.Interaction):
        try:
            with matchlist as db:
                pass
        except MatchScheduleNotObtained as err:
            pass

    return bot
'''
