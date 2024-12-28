'''
    :module_name: bot
    :module_summary: a discord bot built using the commands framework
    :module_author: CountTails
'''

import logging

import discord
from discord.ext import commands

from ..model import ActiveConfig


LOGGER = logging.getLogger(__name__)


def setup_bot():
    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or('!'),
        intents=discord.Intents(
            **ActiveConfig.instance_or_err().intents_mapping
        )
    )

    @bot.event
    async def on_ready():
        await bot.tree.sync()

    @bot.tree.command()
    async def hello(interaction: discord.Interaction, arg: str = 'world'):
        await interaction.response.send_message(f'Hello {arg}')

    return bot
