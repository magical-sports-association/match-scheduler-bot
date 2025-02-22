'''
    :module_name: autocomplete
    :module_summary: coroutines for command parameter completion suggestions
    :module_author: CountTails
'''

import logging
import zoneinfo
from typing import Set, List

import discord
from discord import app_commands


__LOGGER__ = logging.getLogger(__name__)
timezones: Set[str] = zoneinfo.available_timezones()


async def autocomplete_timezone(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    '''
        Coroutines that filters for similar timezones to what is in input field

        Parameters:
            interaction [discord.Interaction]: field requesting autocomplete
            current [str]: the current input value to base autocomplete options

        Returns:
            List[app_commands.Choice[str]] -> autocomplete options
    '''
    __LOGGER__.debug(
        'Finding timezones similar to `%s`',
        current
    )
    return [
        discord.app_commands.Choice(name=tz, value=tz)
        for tz in timezones if current.lower() in tz.lower()
    ][:25]
