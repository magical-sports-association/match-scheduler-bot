"""
    :module_name: cli
    :module_summary: a CLI for match_scheduler_bot
    :module_author: CountTails
"""

import click
import os.path

from . import (
    setup_logging,
    setup_config,
)
from .model import get_config
from .bot import setup_bot


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
def matchschedulerbot(bot_config, log_config):
    """Entry point to matchschedulerbot"""
    setup_logging(log_config)
    setup_config(bot_config)
    setup_bot().run(
        token=get_config().auth.token.get_secret_value(),
        log_handler=None
    )
