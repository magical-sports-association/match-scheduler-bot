"""
    :module_name: snowflake
    :module_summary: a wrapper class for dealing with snowflake IDs
    :module_author: CountTails
"""

from __future__ import annotations


class Snowflake:
    def __init__(self, snowflake_id: int):
        self._id = snowflake_id

    def __str__(self):
        return str(self._id)

    @classmethod
    def from_string(cls, s: str) -> Snowflake:
        as_integer = int(s)
        return cls(as_integer)
