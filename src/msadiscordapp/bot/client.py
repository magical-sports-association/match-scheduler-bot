'''
    :module_name: client
    :module_summary: custom bot client for the magical sports application
    :module_author: CountTails
'''

import logging
import asyncio
from enum import Enum
from typing import Optional, List

from ..model.config import BotConfig
from ..model.processing import AsyncConnectionPool, DiskCache
from ..model.adts import SchedulingEvent


import discord
from discord.ext import commands
from pydantic import SecretStr


__LOGGER__ = logging.getLogger(__name__)


class MagicalSportsApplicationBot(commands.Bot):
    '''
        Subclass of the discord.py's commands.Bot client for the MSA bot

        Attributes:
            AccentColor [Enum]: enumeration of colors used for bot's embeds

        Methods:
            async publish_scheduling_event(): publishes a scheduling event
            async get_next_scheduling_event(): consumes a scheduling event
    '''

    class AccentColor(Enum):
        '''
            Enumeration of typical colors for embeds used by the bot

            Variants:
                Success [discord.Color]: color for success embeds
                Error [discord.Color]: color for error embeds
                INFO [discord.Color]: color for info embeds
                WARN [discord.Color]: color for warning embeds
        '''
        SUCCESS = discord.Color.from_str('#2ECC71')
        ERROR = discord.Color.from_str('#E74C3C')
        INFO = discord.Color.from_str('#55acee')
        WARN = discord.Color.from_str('#ffcc4d')

    def __init__(
        self,
        botconf: BotConfig,
        pool: AsyncConnectionPool,
        cache: DiskCache
    ) -> None:
        '''
            Initializes the bot with the given config and resource managers

            Parameters:
                botconf [BotConfig]: configuration for this bot instance
                pool [AsyncConnectionPool]: db connection resource manager
                cache [DiskCache]: disk files resource manager

            Returns:
                None
        '''
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

    async def setup_hook(self) -> None:
        '''
            Runs during the setup of self

            Parameters:
                None

            Returns:
                None
        '''

        __LOGGER__.info(
            'Loading extension: `msadiscordapp.toolkit.scheduling`'
        )
        await self.load_extension(
            name='msadiscordapp.toolkit.scheduling'
        )
        __LOGGER__.info(
            'Loading extension: `msadiscordapp.toolkit.calendar`'
        )
        await self.load_extension(
            name='msadiscordapp.toolkit.calendar'
        )

        __LOGGER__.info('Syncing command tree')
        await self.tree.sync(guild=self.guild)

    @property
    def token(self) -> SecretStr:
        '''
            Property accessor for the login token to use with self

            Returns:
                SecretStr -> wrapped login token
        '''
        return self._config.auth.token

    @property
    def intentions(self) -> discord.Intents:
        '''
            Property accessor for the intents used during bot login

            Returns:
                discord.Intents -> intentions of self when logging in
        '''
        return discord.Intents(
            **self._config.auth.intents
        )

    @property
    def dbpool(self) -> AsyncConnectionPool:
        '''
            Property accessor for the resource manager of database connection

            Returns:
                AsyncConnectionPool -> db connnection resource manager
        '''
        return self._pool

    @property
    def messages(self) -> DiskCache:
        '''
            Property accessor for the resource manager of disk activity

            Returns:
                DiskCache -> disk activity manager
        '''
        return self._message_cache

    @property
    def guild(self) -> discord.Object:
        '''
            Property accessor for the guild id this bot connects to

            Returns:
                discord.Object -> wrapped guild ID
        '''
        return discord.Object(
            self._config.auth.server
        )

    @property
    def public_log_channel(self) -> discord.Object:
        '''
            Property accessor for the public log channel for this bot

            Returns:
                discord.Object -> wrapped channel ID
        '''
        return discord.Object(
            self._config.auth.logs.public.channel_id
        )

    @property
    def audit_log_channel(self) -> discord.Object:
        '''
            Property accessor for the audit log channel for this bot

            Returns:
                discord.Object -> wrapped channel id
        '''
        return discord.Object(
            self._config.auth.logs.audit.channel_id
        )

    @property
    def public_log_pings(self) -> List[discord.Object]:
        '''
            Property accessor for the public log pings for this bot

            Returns:
                List[discord.Object] -> list of wrapped role ids
        '''
        return [
            discord.Object(roleid)
            for roleid in self._config.auth.logs.public.interested_parties
        ]

    @property
    def audit_log_pings(self) -> List[discord.Object]:
        '''
            Property accessor for the audit log pings for this bot

            Returns:
                List[discord.Object] -> list of wrapped role ids
        '''
        return [
            discord.Object(roleid)
            for roleid in self._config.auth.logs.audit.interested_parties
        ]
