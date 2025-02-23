'''
    :module_name: bot
    :module_summary: a discord bot built using the commands framework
    :module_author: CountTails
'''

from pathlib import Path

from .client import MagicalSportsApplicationBot

from ..model.processing import (
    DiskCache,
    AsyncConnectionPool
)

from .. import setup_config, setup_logging, get_config


async def startup(
    botconfig: Path,
    logconfig: Path
) -> None:
    '''
        Coroutine to initialize a MSA bot service with the given configurations

        Parameters:
            botconfig [Path]: path to the bot's configuration file to use
            logconfig [Path]: path to the logging configuration file to use

        Returns:
            None

        Raises:
            discord.errors.* -> the bot service could not be initialized
            ValueError -> the logconfig is not valid
            MSADiscordAppConfigurationError -> the botconfig is not valid
    '''
    setup_config(botconfig)
    setup_logging(logconfig)

    async with AsyncConnectionPool(get_config().data.database, 3) as pool:
        cache = DiskCache(get_config().data.messages, 3600)
        async with MagicalSportsApplicationBot(
            get_config(),
            pool,
            cache
        ) as bot:
            await bot.start(bot.token.get_secret_value())
