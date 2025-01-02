"""
    :module_name: match_scheduler_bot
    :module_summary: A discord bot for scheduling msa matches
    :module_author: CountTails
"""

import logging
import logging.config
import logging.handlers
import json
import atexit

from .model import use_config

LOGGER = logging.getLogger(__name__)


def setup_logging(config: str) -> None:
    with open(config) as f_in:
        logconfig = json.load(f_in)
        print(json.dumps(logconfig, indent=4))
    logging.config.dictConfig(logconfig)
    qhandler = logging.getHandlerByName("queue_handler")
    if qhandler:
        qhandler.listener.start()
        atexit.register(qhandler.listener.stop)


def setup_config(config: str) -> None:
    use_config(config)
