'''
    :module_name: bot
    :module_summary: a discord bot built using the commands framework
    :module_author: CountTails
'''

import logging

import discord
from discord.ext import commands

from .. import get_config
from .cogs import (
    AddMatchCommand,
    DeleteMatchCommand,
    GetMatchCommand
)


__LOGGER__ = logging.getLogger(__name__)
__BOT__ = None

print(get_config())


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
            await __BOT__.add_cog(GetMatchCommand(
                get_config().data.database,
                __BOT__
            ))
            __LOGGER__.info('Added extension: %s', GetMatchCommand.__name__)
            __LOGGER__.debug('Synchronizing command tree with discord')
            await __BOT__.tree.sync()
            __LOGGER__.debug('Command tree synchronized')

    __LOGGER__.info('Returning the singleton bot instance')
    return __BOT__
