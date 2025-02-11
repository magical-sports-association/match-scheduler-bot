'''
    :module_name: bot
    :module_summary: a discord bot built using the commands framework
    :module_author: CountTails
'''

import logging
from pathlib import Path
from enum import Enum, StrEnum

import discord
from discord.ext import commands
from pydantic import SecretStr

from .. import BotConfig
from ..model import (
    AsyncConnectionPool,
    FileCacheProvider
)
from .. import setup_config, setup_logging, get_config


__LOGGER__ = logging.getLogger(__name__)


class MagicalSportsApplicationBot(commands.Bot):
    '''
        Subclass of the discord.py's command.Bot client for the MSA bot
    '''

    class AccentColor(Enum):
        SUCCESS = discord.Color.from_str('#2ECC71')
        ERROR = discord.Color.from_str('#E74C3C')
        INFO = discord.Color.from_str('#55acee')
        WARN = discord.Color.from_str('#ffcc4d')

    class Emoji(StrEnum):
        SEPARATOR = u"\uFF5C"
        STADIUM = ':stadium:'
        CALENDAR = ':calendar_spiral:'
        STOP = ':octagonal_sign:'
        CHECK = ':white_check_mark:'
        WARN = ':warning:'

    def __init__(
        self,
        botconf: BotConfig,
        pool: AsyncConnectionPool,
        cache: FileCacheProvider
    ):
        self._config = botconf
        self._pool = pool
        self._message_cache = cache
        super().__init__(
            command_prefix=commands.when_mentioned_or('/'),
            intents=self.intentions
        )

    async def setup_hook(self):

        __LOGGER__.info(
            'Loading extension: `match_scheduler_bot.bot.extensions.scheduling`'
        )
        await self.load_extension(
            name='match_scheduler_bot.bot.extensions.scheduling'
        )

        __LOGGER__.info('Syncing command tree')
        await self.tree.sync(guild=self.guild)

    @property
    def token(self) -> SecretStr:
        return self._config.auth.token

    @property
    def intentions(self) -> discord.Intents:
        return discord.Intents(
            **self._config.auth.intents
        )

    @property
    def dbpool(self) -> AsyncConnectionPool:
        return self._pool

    @property
    def msgcache(self) -> FileCacheProvider:
        return self._message_cache

    @property
    def guild(self) -> discord.Object:
        return discord.Object(
            self._config.auth.server
        )

    @property
    def public_log_channel(self) -> discord.Object:
        return discord.Object(
            self._config.auth.logs.public_log
        )

    @property
    def audit_log_channel(self) -> discord.Object:
        return discord.Object(
            self._config.auth.logs.audit_log
        )


async def startup(
    botconfig: Path,
    logconfig: Path
):
    setup_config(botconfig)
    setup_logging(logconfig)

    async with AsyncConnectionPool(get_config().data.database, 3) as pool:
        cache = FileCacheProvider(get_config().data.messages, 3600)
        async with MagicalSportsApplicationBot(
            get_config(),
            pool,
            cache
        ) as bot:
            await bot.start(bot.token.get_secret_value())
