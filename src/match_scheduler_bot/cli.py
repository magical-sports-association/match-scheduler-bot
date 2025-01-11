"""
    :module_name: cli
    :module_summary: a CLI for match_scheduler_bot
    :module_author: CountTails
"""

import click
import os.path
import importlib

from match_scheduler_bot import setup_config, setup_logging, get_config


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
    setup_logging(log_config)
    setup_config(bot_config)
    bot = importlib.import_module('match_scheduler_bot.bot')
    bot.use_bot().run(
        token=get_config().auth.token.get_secret_value(),
        log_handler=None
    )
