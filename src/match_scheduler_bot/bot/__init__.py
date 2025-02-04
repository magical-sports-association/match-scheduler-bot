'''
    :module_name: bot
    :module_summary: a discord bot built using the commands framework
    :module_author: CountTails
'''

import logging
from pathlib import Path
from typing import Dict, List

import discord
from discord.ext import commands
from pydantic import SecretStr

from .. import BotConfig
from ..model import (
    AsyncConnectionPool
)
from .. import setup_config, setup_logging, get_config


__LOGGER__ = logging.getLogger(__name__)
__BOT__ = None


'''
def make_bot() -> commands.Bot:
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
'''


class MagicalSportsApplicationBot(commands.Bot):
    '''
        Subclass of the discord.py's command.Bot client for the MSA bot
    '''

    def __init__(
        self,
        botconf: BotConfig,
        pool: AsyncConnectionPool
    ):
        self._config = botconf
        self._pool = pool
        super().__init__(
            command_prefix=commands.when_mentioned_or('/'),
            intents=discord.Intents(**self.intentions)
        )

    @property
    def token(self) -> SecretStr:
        return self._config.auth.token

    @property
    def intentions(self) -> Dict[str, bool]:
        return self._config.auth.intents

    @property
    def dbpath(self) -> str:
        return self._config.data.database

    @property
    def msgpath(self) -> str:
        return self._config.data.messages

    @property
    def guild(self) -> discord.Guild:
        return self.get_guild(
            self._config.auth.server
        )


async def startup(
    botconfig: Path,
    logconfig: Path
):
    setup_config(botconfig)
    setup_logging(logconfig)

    async with AsyncConnectionPool(get_config().data.database, 3) as pool:
        async with MagicalSportsApplicationBot(get_config(), pool) as bot:
            await bot.start(bot.token.get_secret_value())
