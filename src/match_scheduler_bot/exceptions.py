'''
    :module_name: exceptions
    :module_summary: exception classes for the discord bot
    :module_author: CountTails
'''


class MatchSchedulerBotException(Exception):
    '''Base exception for the bot package'''


class BotConfigurationError(MatchSchedulerBotException):
    '''Exception for specifying issues with bot configuration'''


class MissingConfigurationError(BotConfigurationError):
    '''Exception for indicating the bot configuration is missing when needed'''


class BadConfigurationError(BotConfigurationError):
    '''Exception to indicate an issue with reading the bot configuration'''