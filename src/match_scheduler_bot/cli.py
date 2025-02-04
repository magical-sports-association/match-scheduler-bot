"""
    :module_name: cli
    :module_summary: a CLI for match_scheduler_bot
    :module_author: CountTails
"""

import click
import os.path
import asyncio

from match_scheduler_bot.bot import startup


@click.command()
@click.option(
    '--bot-config',
    type=click.Path(exists=True),
    default=f'{os.path.expanduser("~/.config/msa/bot.json")}'
)
@click.option(
    '--log-config',
    type=click.Path(exists=True),
    default=f'{os.path.expanduser("~/.config/msa/logging.json")}'
)
def main(bot_config, log_config):
    """Entry point to matchschedulerbot"""
    asyncio.run(startup(bot_config, log_config))
