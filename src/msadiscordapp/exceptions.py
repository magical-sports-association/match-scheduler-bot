'''
    :module_name: exceptions
    :module_summary: custom exception classes for this package
    :module_author: CountTails
'''

from __future__ import annotations
from pathlib import Path


class BaseMSADiscordAppException(Exception):
    '''Base exception class for this package'''

    def __init__(self, msg: str):
        '''
            Initializes the exception with the given message.
            Also accepts any additional data for the parent constructor.
            Since this is the builtin Exception class, this is typically none.

            Parameters:
                msg [str]: the error message for this exception

            Returns:
                None
        '''
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


class MessageCacheFailure(MSADiscordAppResourceAccessError):
    '''Exception for general issues regarding the disk cache'''


class MessageContentNotReadable(MessageCacheFailure):
    '''Exception describing an issue obtaining contents from the disk cache'''

    def __init__(self, msg: str, path: Path) -> None:
        '''
            Initializes the exception with the given path and message

            Parameters:
                msg [str]: the error message
                path [Path]: problematic path causing error


            Returns:
                None
        '''
        super().__init__(msg)
        self._path = path

    @property
    def reason(self) -> str:
        '''
            Property accessor for the error message of this exception

            Returns:
                str -> the error message
        '''
        return f'Error reading {self._path}: {self._reason}'
