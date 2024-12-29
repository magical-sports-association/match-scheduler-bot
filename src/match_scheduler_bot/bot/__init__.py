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

    @bot.tree.command(name='addmatch')
    async def add_match(interaction: discord.Interaction, home: str, away: str):
        await interaction.response.send_message(
            f'Scheduling a match: {away} vs {home}'
        )

    @bot.tree.command(name='delmatch')
    async def del_match(interaction: discord.Interaction, home: str, away: str):
        await interaction.response.send_message(
            f'Canceling the match between {away} vs {home}'
        )

    @bot.tree.command(name='showmatches')
    async def show_matches(interaction: discord.Intents):
        await interaction.response.send_message(
            'Showing the upcoming matches'
        )

    return bot
