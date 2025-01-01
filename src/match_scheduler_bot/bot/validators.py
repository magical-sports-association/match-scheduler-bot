'''
    :module_name: validators
    :module_summary: callbacks for validating command parameters beyond simple checks
    :module_author: CountTails
'''

import logging
import datetime
import zoneinfo

from ..exceptions import (
    InvalidTimezoneSpecified,
    InvalidStartTimeGiven
)


__LOGGER__ = logging.getLogger(__name__)


def date_parts(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    tzkey: str
) -> datetime.datetime:
    __LOGGER__.info('Validating given parts as an actual datetime')
    try:
        return datetime.datetime(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            tzinfo=zoneinfo.ZoneInfo(tzkey)
        )
    except zoneinfo.ZoneInfoNotFoundError as err:
        __LOGGER__.error('`%s` is not a known time zone', tzkey)
        raise InvalidTimezoneSpecified(
            f'{tzkey} is not a known timezone'
        ) from err
    except ValueError as err:
        __LOGGER__.error('Invalid date data: `%s`', str(err))
        raise InvalidStartTimeGiven(
            f'Invalid date: {str(err).removeprefix('ValueError: ')}'
        )
