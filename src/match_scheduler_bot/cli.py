"""
    :module_name: cli
    :module_summary: a CLI for match_scheduler_bot
    :module_author: CountTails
"""

import click

@click.command()
def matchschedulerbot():
    """Entry point to matchschedulerbot"""
    click.echo('Hello World!')
