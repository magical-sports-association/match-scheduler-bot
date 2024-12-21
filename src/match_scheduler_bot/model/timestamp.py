"""
    :module_name: timestamp
    :module_summary: a wrapper class for dealing with unix timestamps
    :module_author: CountTails
"""


class Timestamp:
    def __init__(self, seconds: int):
        self._since_epoch = seconds
