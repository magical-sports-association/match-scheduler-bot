"""
    :module_name: cli
    :module_summary: a CLI for msadiscordapp
    :module_author: CountTails
"""

import click
import os.path
import asyncio

# from msadiscordapp.bot import startup
# from msadiscordapp.exceptions import BotConfigurationError
# from msadiscordapp import setup_config


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
        the asychronous runtime the the service runs on top of

        Parameters:
            bot_config [click.Path]: path of the bot's configuration file
            log_config [click.Path]: path of the logging configuration file

        Returns:
            None

        Raises:

    '''
    # asyncio.run(startup(bot_config, log_config))
    print('Starting service')


@main.command()
@click.option(
    '--bot-config',
    type=click.Path(exists=True),
    default=f'{os.path.expanduser("~/.config/msa/bot.json")}'
)
def check(bot_config):
    """Check if the given config file is valid
    try:
        setup_config(bot_config)
        click.echo('Configuration is valid')
    except BotConfigurationError as err:
        click.echo(
            err.__cause__.errors()
        )
    """
    print('Checking config file')
