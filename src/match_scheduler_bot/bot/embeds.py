'''
    :module_name: embeds
    :module_summary: factory functions for embedded responses used by this bot
    :module_author: CountTails
'''

from enum import Enum

import discord


class EmbedAccentColor(Enum):
    SUCCESS = discord.Color.from_str('#2ECC71')
    ERROR = discord.Color.from_str('#E74C3C')
    INFO = discord.Color.from_str('#ffc01c')


def match_scheduled_successfully(

) -> discord.Embed:
    pass


def match_scheduled_unsuccessfully(

) -> discord.Embed:
    pass


def match_cancelled_successfully(

) -> discord.Embed:
    pass


def match_cancelled_unsuccessfully(

) -> discord.Embed:
    pass


def match_calendar(

) -> discord.Embed:
    pass
