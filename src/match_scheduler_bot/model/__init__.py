'''
    :module_name: model
    :module_summary: data model for the discord bot
    :module_author: CountTails
'''

from pathlib import Path
from typing import Optional, Dict
import logging

from ..exceptions import BotConfigurationError
from .config import (
    BotConfig
)

import pydantic

LOGGER = logging.getLogger(__name__)


class ActiveConfig:
    _instance = None

    def __new__(cls, config: str | Path):
        if cls._instance is None:
            cls._instance = super(ActiveConfig, cls).__new__(cls)
            cls._instance.config = cls.from_file(config)
        return cls._instance

    @staticmethod
    def from_file(config_file: str | Path):
        try:
            LOGGER.debug('Opening config file: %s', config_file)
            with open(config_file) as f_in:
                LOGGER.debug(
                    'Validating JSON structure conforms to config'
                )
                config = BotConfig.model_validate_json(
                    f_in.read(),
                    strict=True
                )
                LOGGER.debug('JSON structure is conforming')
                return config
        except FileNotFoundError as err:
            LOGGER.error('Config file `%s` does not exist', config_file)
            raise BotConfigurationError(
                f'No such configuration file: {config_file}'
            ) from err
        except pydantic.ValidationError as err:
            LOGGER.error(
                'Config file does not conform to config structure'
            )
            raise BotConfigurationError(
                f'Bad configuration read: {err.error_count()} issues'
            ) from err

    @classmethod
    def instance_or_err(cls):
        if cls._instance is None:
            LOGGER.error('No active configuration available')
            raise BotConfigurationError(
                'No active configuration available'
            )
        LOGGER.info('Returning available configuration for bot')
        return cls._instance

    @property
    def access_token(self) -> pydantic.SecretStr:
        return self.config.auth.token

    @property
    def intents_mapping(self) -> Dict[str, bool]:
        return self.config.auth.intents
