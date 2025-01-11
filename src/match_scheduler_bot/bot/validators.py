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


def date_in_near_future(dt: datetime.datetime) -> datetime.datetime:
    __LOGGER__.debug(
        'Checking if given date is in the future by at most 1 year'
    )
    now = datetime.datetime.now(dt.tzinfo)
    one_year_from_now = now + datetime.timedelta(days=365)

    if dt <= now:
        __LOGGER__.error('Given date %s is not in the future', dt.isoformat())
        raise InvalidStartTimeGiven(
            'Invalid date: must be in the future'
        )

    if dt > one_year_from_now:
        __LOGGER__.error(
            'Given date %s exceeds one year into the future',
            dt.isoformat()
        )
        raise InvalidStartTimeGiven(
            'Invalid date: must be at most 1 year into the future'
        )

    return dt
