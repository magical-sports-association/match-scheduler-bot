"""
    :module_name: cli
    :module_summary: a CLI for msadiscordapp
    :module_author: CountTails
"""

import click
import os.path
import asyncio

from msadiscordapp.bot import startup
from msadiscordapp import setup_config


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
    '''
        Entry point to the `serve` subcommand of this application.
        Serves as the initialization point for the module's service and
        the asychronous runtime that the service runs on top of

        Parameters:
            bot_config [click.Path]: path of the bot's configuration file
            log_config [click.Path]: path of the logging configuration file

        Returns:
            None

        Raises:
            BaseMSADiscordAppException: if the service fails to start
            discord.errors.*: if the service bot could not be initialized
    '''
    asyncio.run(startup(bot_config, log_config))


@main.command()
@click.option(
    '--bot-config',
    type=click.Path(exists=True),
    default=f'{os.path.expanduser("~/.config/msa/bot.json")}'
)
def check(bot_config):
    '''
        Entry point to the `check` subcommand of this application
        Serves as a helpful resource for validating the input
        configuration for be used as the value for the `--bot-config`
        option in the `serve` subcommand.

        Parameters:
            bot_config [click.Path]: the config file to validate

        Returns:
            None

        Raises:
            pydantic.ValidationError: if the file does not conform
    '''
    setup_config(bot_config)
