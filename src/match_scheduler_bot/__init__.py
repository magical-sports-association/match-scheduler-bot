"""
    :module_name: match_scheduler_bot
    :module_summary: A discord bot for scheduling msa matches
    :module_author: CountTails
"""

import logging
import logging.config
import logging.handlers
import json
import atexit
from typing import Optional
from pathlib import Path

from .exceptions import MissingConfigurationError, BadConfigurationError
from .model import BotConfig

import pydantic

__LOGGER__ = logging.getLogger(__name__)
__CONFIG__: Optional[BotConfig] = None
__VERSION__ = (0, 1, 1)


def setup_logging(config: str) -> None:
    with open(config) as f_in:
        logconfig = json.load(f_in)
        print(json.dumps(logconfig, indent=4))
    logging.config.dictConfig(logconfig)
    qhandler = logging.getHandlerByName("queue_handler")
    if qhandler:
        qhandler.listener.start()
        atexit.register(qhandler.listener.stop)


def setup_config(config: str | Path) -> None:
    global __CONFIG__
    try:
        __LOGGER__.debug('Opening config file: %s', config)
        with open(config) as f_in:
            __LOGGER__.debug(
                'Validating JSON structure conforms to config'
            )
            config = BotConfig.model_validate_json(
                f_in.read(),
                strict=True
            )
            __LOGGER__.debug('JSON structure is conforming')
            __CONFIG__ = config
    except FileNotFoundError as err:
        __LOGGER__.error('Config file `%s` does not exist', config)
        raise MissingConfigurationError(
            f'No such configuration file: {config}'
        ) from err
    except pydantic.ValidationError as err:
        __LOGGER__.error(
            'Config file does not conform to config structure'
        )
        raise BadConfigurationError(
            f'Bad configuration read: {err.error_count()} issues'
        ) from err


def get_config() -> BotConfig:
    global __CONFIG__
    if __CONFIG__ is None:
        __LOGGER__.error(
            'Attempted to read configuration object when not present'
        )
        raise MissingConfigurationError('No configuration loaded')
    return __CONFIG__
