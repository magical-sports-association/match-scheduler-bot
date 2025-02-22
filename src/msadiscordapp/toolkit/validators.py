'''
    :module_name: validators
    :module_summary: callbacks for validating command parameters
    :module_author: CountTails
'''

import logging
import datetime
import zoneinfo

from ..exceptions import InvalidParameterValueGiven


__LOGGER__ = logging.getLogger(__name__)


def date_parts(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    tzkey: str
) -> datetime.datetime:
    '''
        Validates the given date/time info is an actual calendar date

        Parameters:
            year [int]: year to validate, between 0 and 9999
            month [int]: month to validate, between 0 and 12
            day [int]: day to validate, varies but typically between 0 and 31
            hour [int]: hour to validate, between 0 and 23
            minute [int]: minute to validate between 0 and 59
            tzkey [str]: name of timezone for datetime localization

        Returns:
            datetime.datetime -> valid calendar date

        Raises:
            InvalidParameterValueGiven -> (
                - if the given tzkey is not known
                - if the parts of the date do not exist on the calendar
            )
    '''
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
        raise InvalidParameterValueGiven(
            f'{tzkey} is not a known timezone'
        ) from err
    except ValueError as err:
        __LOGGER__.error('Invalid date data: `%s`', str(err))
        raise InvalidParameterValueGiven(
            f'Invalid date: {str(err).removeprefix('ValueError: ')}'
        )


def date_in_near_future(dt: datetime.datetime) -> datetime.datetime:
    '''
        Validates the given date is within 1 year in the future

        Parameters:
            dt [datetime.datetime]: date/time to validate is in the near future

        Returns:
            datetime.datetime -> validated date/time info

        Raises:
            InvalidParameterValueGiven -> (
                - The given datetime is in the past
                - The given datetime is far in the future (more than 1 year)
            )
    '''
    __LOGGER__.debug(
        'Checking if given date is in the future by at most 1 year'
    )
    now = datetime.datetime.now(dt.tzinfo)
    one_year_from_now = now + datetime.timedelta(days=365)

    if dt <= now:
        __LOGGER__.error('Given date %s is not in the future', dt.isoformat())
        raise InvalidParameterValueGiven(
            'Invalid date: must be in the future'
        )

    if dt > one_year_from_now:
        __LOGGER__.error(
            'Given date %s exceeds one year into the future',
            dt.isoformat()
        )
        raise InvalidParameterValueGiven(
            'Invalid date: must be at most 1 year into the future'
        )

    return dt
