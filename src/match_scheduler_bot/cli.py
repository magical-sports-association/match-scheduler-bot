"""
    :module_name: cli
    :module_summary: a CLI for match_scheduler_bot
    :module_author: CountTails
"""

import click
import os.path
import time

from . import LOGGER, setup_logging


def slow_task():
    for x in range(1, 11):
        time.sleep(5)
        LOGGER.debug("Step %d of some slow task completed", x)


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
    click.echo(f"Grabbing bot config from: {bot_config}")
    click.echo(f"Grabbing logging config from: {log_config}")
    setup_logging(log_config)
    LOGGER.info("Application successfully initialized. Starting slow task")
    time.sleep(3)
    slow_task()
    time.sleep(3)
    LOGGER.info("Slow task completed. Exiting...")
