'''
    :module_name: addmatch
    :module_summary: cog definition for the slash command to add a match
    :module_author: CountTails
'''

import logging


import discord
from discord.ext import commands


__LOGGER__ = logging.getLogger(__name__)


class AddMatchCog(commands.Cog):

    @discord.app_commands.command(
        name='test-cog-cmd',
        description='Slash command defined with a cog'
    )
    async def test_slash_cmd_in_cog(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            content='Command executed in cog',
            ephemeral=True
        )
