'''
    :module_name: exceptions
    :module_summary: custom exception classes for this package
    :module_author: CountTails
'''

from __future__ import annotations
from pathlib import Path

import discord


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


class MatchlistOperationFailure(MSADiscordAppResourceAccessError):
    '''Exception for when manipulating/accessing the matchlist fails'''

    def __init__(
        self,
        msg: str,
        team1: discord.Role.id,
        team2: discord.Role.id
    ) -> None:
        '''
            Initializes the exception with the given error message, and teams

            Parameters:
                msg [str]: the error message
                team1 [discord.Role]: first team in this invalid matchup
                team2 [discord.Role]: second time in this invalid matchup

            Returns:
                None
        '''
        super().__init__(msg)
        self._team1 = team1
        self._team2 = team2

        @property
        def team1_mention(self) -> str:
            '''
                Property accessor for the mention string for team1

                Returns:
                    str -> the mention string
            '''
            return f'<@&{self._team1}>'

        @property
        def team2_mention(self) -> str:
            '''
                Property accessor for the mention string for team2

                Returns:
                    str -> the mention string
            '''
            return f'<@&{self._team2}>'


class MatchToScheduleAlreadyExists(MatchlistOperationFailure):
    '''Exception for when scheduling a match that already exists'''

    @property
    def reason(self) -> str:
        '''
            Property accessor for the error message of this exception

            Returns:
                str -> the error message
        '''
        team1 = self.team1_mention
        team2 = self.team2_mention
        return f'Match between {team1} and {team2} is already scheduled!' + \
            'Cancel the existing match before rescheduling.'


class MatchToCancelDoesNotExist(MatchlistOperationFailure):
    '''Exception when cancelling a match that does not exist'''

    @property
    def reason(self) -> str:
        '''
            Property accessor for the error message of this exception

            Returns:
                str -> the error message
        '''
        team1 = self.team1_mention
        team2 = self.team2_mention
        return f'No match between {team1} and {team2} could be found.'


class InvalidParameterValueGiven(MSADiscordAppCommandError):
    '''Exception for validation issues with app command parameters'''
