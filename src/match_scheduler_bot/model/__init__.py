'''
    :module_name: model
    :module_summary: data model for the discord bot
    :module_author: CountTails
'''

from pathlib import Path
from typing import Optional
import logging

from ..exceptions import (
    BadConfigurationError,
    MissingConfigurationError
)
from .config import (
    BotConfig
)

import pydantic

LOGGER = logging.getLogger(__name__)
__CONFIG__: Optional[BotConfig] = None


def use_config(config: str | Path) -> None:
    global __CONFIG__
    try:
        LOGGER.debug('Opening config file: %s', config)
        with open(config) as f_in:
            LOGGER.debug(
                'Validating JSON structure conforms to config'
            )
            config = BotConfig.model_validate_json(
                f_in.read(),
                strict=True
            )
            LOGGER.debug('JSON structure is conforming')
            __CONFIG__ = config
    except FileNotFoundError as err:
        LOGGER.error('Config file `%s` does not exist', config)
        raise MissingConfigurationError(
            f'No such configuration file: {config}'
        ) from err
    except pydantic.ValidationError as err:
        LOGGER.error(
            'Config file does not conform to config structure'
        )
        raise BadConfigurationError(
            f'Bad configuration read: {err.error_count()} issues'
        ) from err


def get_config() -> BotConfig:
    global __CONFIG__
    if __CONFIG__ is None:
        LOGGER.error(
            'Attempted to read configuration object when not present'
        )
        raise MissingConfigurationError('No configuration loaded')
    return __CONFIG__
