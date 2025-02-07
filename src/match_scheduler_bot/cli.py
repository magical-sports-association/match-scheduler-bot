"""
    :module_name: cli
    :module_summary: a CLI for match_scheduler_bot
    :module_author: CountTails
"""

import click
import os.path
import asyncio

from match_scheduler_bot.bot import startup
from match_scheduler_bot.exceptions import BotConfigurationError
from match_scheduler_bot import setup_config


@click.group
def main():
    pass


@main.command()
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
def serve(bot_config, log_config):
    """Entry point to matchschedulerbot"""
    asyncio.run(startup(bot_config, log_config))


@main.command()
@click.option(
    '--bot-config',
    type=click.Path(exists=True),
    default=f'{os.path.expanduser("~/.config/msa/bot.json")}'
)
def check(bot_config):
    """Check if the given config file is valid"""
    try:
        setup_config(bot_config)
        click.echo('Configuration is valid')
    except BotConfigurationError as err:
        click.echo(
            err.__cause__.errors()
        )
