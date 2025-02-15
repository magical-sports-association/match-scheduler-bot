'''
    :module_name: exceptions
    :module_summary: custom exception classes for this package
    :module_author: CountTails
'''

from __future__ import annotations
from typing import Tuple, Any


class BaseMSADiscordAppException(Exception):
    '''Base exception class for this package'''

    def __init__(self, msg: str, *args: Tuple[Any]):
        '''
            Initializes the exception with the given message.
            Also accepts any additional data for the parent constructor.
            Since this is the builtin Exception class, this is typically none.

            Parameters:
                msg [str]: the error message for this exception
                *args [Tuple[Any]]: additional data for parent constructor

            Returns:
                None
        '''
        super().__init__(*args)
        self._reason = msg

    @property
    def reason(self) -> str:
        '''
            Property accessor for the error message of this exception

            Returns:
                str -> the error message
        '''
        return self._reason


class MSADicsordAppConfigurationError(BaseMSADiscordAppException):
    '''Base exception for configuration related issues within this package'''


class MSADiscordAppCommandError(BaseMSADiscordAppException):
    '''Base exception for slash command related issues within this package'''


class MSADiscordAppResourceAccessError(BaseMSADiscordAppException):
    '''Base exception for issues related to resource access in this package'''
