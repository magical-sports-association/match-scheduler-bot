'''
    :module_name: utils
    :module_summary: utilities for the discord bot
    :module_author: CountTails
'''

import logging
import datetime
import zoneinfo
from typing import List, Set

import discord

from ..exceptions import (
    InvalidStartTimeGiven,
    InvalidTimezoneSpecified
)


timezones: Set[str] = zoneinfo.available_timezones()
LOGGER = logging.getLogger(__name__)


async def fuzzytzkeys(
    interaction: discord.Interaction,
    current: str,
) -> List[discord.app_commands.Choice[str]]:
    LOGGER.debug('Finding timezones starting with `%s`', current)
    return [
        discord.app_commands.Choice(name=tz, value=tz)
        for tz in timezones if tz.lower().startswith(current.lower())
    ][:25]


def validate_start_time(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    tzkey: str
) -> datetime.datetime:
    try:
        LOGGER.debug('Attempting to validate start time information')
        return datetime.datetime(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            tzinfo=zoneinfo.ZoneInfo(tzkey)
        )
    except zoneinfo.ZoneInfoNotFoundError as err:
        LOGGER.error('`%s` is not a known time zone', tzkey)
        raise InvalidTimezoneSpecified(
            f'{tzkey} is not a known timezone'
        ) from err
    except ValueError as err:
        LOGGER.error('Invalid date data: `%s`', str(err))
        raise InvalidStartTimeGiven(
            f'Invalid date: {str(err).removeprefix('ValueError: ')}'
        )
