'''
    :module_name: bot
    :module_summary: a discord bot built using the commands framework
    :module_author: CountTails
'''

import logging
import asyncio
from pathlib import Path
from enum import Enum, StrEnum
from typing import Optional, List

import discord
from discord.ext import commands
from pydantic import SecretStr

from .. import BotConfig
from ..model import (
    AsyncConnectionPool,
    FileCacheProvider
)
from ..model.rows import SchedulingEvent
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
        self._scheduling_events = asyncio.Queue()
        super().__init__(
            command_prefix=commands.when_mentioned_or('/'),
            intents=self.intentions
        )

    async def publish_scheduling_event(
        self,
        event: SchedulingEvent
    ) -> None:
        '''
            Coroutine to add the given event to event queue

            Parameters:
                event [SchedulingEvent] event to add to queue

            Returns:
                None
        '''
        await self._scheduling_events.put(event)

    def get_next_scheduling_event(self) -> Optional[SchedulingEvent]:
        '''
            Returns the next scheduling event in the queue (if any)
            Returns `None` if no events are in the queue

            Returns:
                Optional[SchedulingEvent]: next event in queue (if any)
        '''
        try:
            __LOGGER__.debug('Attempting to get next event in queue')
            return self._scheduling_events.get_nowait()
        except asyncio.QueueEmpty:
            __LOGGER__.error(
                'No events to pull from the queue (queue is empty)'
            )
            return None

    async def setup_hook(self):

        __LOGGER__.info(
            'Loading extension: `match_scheduler_bot.bot.extensions.scheduling`'
        )
        await self.load_extension(
            name='match_scheduler_bot.bot.extensions.scheduling'
        )
        __LOGGER__.info(
            'Loading extension: `match_scheduler_bot.bot.extensions.calendar`'
        )
        await self.load_extension(
            name='match_scheduler_bot.bot.extensions.calendar'
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
            self._config.auth.logs.public.channel_id
        )

    @property
    def audit_log_channel(self) -> discord.Object:
        return discord.Object(
            self._config.auth.logs.audit.channel_id
        )

    @property
    def public_log_pings(self) -> List[discord.Object]:
        return [
            discord.Object(roleid)
            for roleid in self._config.auth.logs.public.interested_parties
        ]

    @property
    def audit_log_pings(self) -> List[discord.Object]:
        return [
            discord.Object(roleid)
            for roleid in self._config.auth.logs.audit.interested_parties
        ]


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
