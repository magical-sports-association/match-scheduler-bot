'''
    :module_name: responses:
    :module_summary: factories for generating bot responses
    :module_author: CountTails
'''

from enum import Enum, StrEnum

import discord


class AccentColor(Enum):
    SUCCESS = discord.Color.from_str('#2ECC71')
    ERROR = discord.Color.from_str('#E74C3C')
    INFO = discord.Color.from_str('#55acee')
    WARN = discord.Color.from_str('#ffcc4d')


class Emoji(StrEnum):
    SEPARATOR = u"\uFF5C"
    STADIUM = ':stadium:'
    CALENDAR = ':calendar_spiral:'
    STOP = ':octagonal_sign:'
    CHECK = ':white_check_mark:'
    WARN = ':warning:'
