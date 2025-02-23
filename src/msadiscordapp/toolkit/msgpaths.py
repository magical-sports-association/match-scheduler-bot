'''
    :module_name: msgpaths
    :module_summary: enumeration of paths used to construct messages
    :module_author: CountTails
'''

from pathlib import Path
from enum import Enum


class CoreContentPaths(Enum):
    '''
        Paths for core parts of the responses made by this command group
    '''
    ACK_CMD_USE = Path('core/acknowledge.content.md')
    CMD_ISSUE = Path('core/issue.embedtitle.md')
    CMD_ERROR = Path('core/error.embedtitle.md')
    CMD_ERROR_MSG = Path('core/error.embedfieldname.md')
    TEAMS_MATCHUP = Path('core/teams.embedfieldvalue.md')
    MATCHUP_DATE = Path('core/date.embedfieldvalue.md')
    INSUFFICIENT_PERMISSIONS = Path('core/forbidden.embedfieldname.md')
    ALLOWED_ROLES = Path('core/forbidden.embedfieldvalue.md')
    SUPPORT_LINK = Path('core/supportlink.embedfieldvalue.md')


class SchedulingConfirmationPaths(Enum):
    '''
        Paths for the scheduling confirmation
        responses made by this command group
    '''
    MATCH_SCHEDULED_TITLE = Path('scheduling/confirm/created.embedtitle.md')
    MATCH_CANCELLED_TITLE = Path('scheduling/confirm/deleted.embedtitle.md')
    MATCH_CALENDAR_TITLE = Path('scheduling/confirm/read.embedtitle.md')
    MATCH_CALENDAR_SUBTITLE = Path('scheduling/confirm/read.embedsubtitle.md')
    MATCH_CALENDAR_SOME = Path(
        'scheduling/confirm/read.somematch.embedfieldvalue.md'
    )
    MATCH_CALENDAR_NONE = Path(
        'scheduling/confirm/read.nomatch.embedfieldvalue.md'
    )


class SchedulingAnnouncementPaths(Enum):
    '''
        Paths for the scheduling announcment responses
        made by this command group
    '''
    MATCH_SCHEDULED_TITLE = Path('scheduling/announce/created.embedtitle.md')
    MATCH_CANCELLED_TITLE = Path('scheduling/announce/deleted.embedtitle.md')
    INCOMING_MATCH_TITLE = Path('scheduling/announce/incoming.embedtitle.md')
    INCOMING_MATCH_INFO_HEAD = Path(
        'scheduling/announce/matchinfo.embedfieldname.md'
    )
    INCOMING_MATCH_INFO_BODY = Path(
        'scheduling/announce/matchinfo.embedfieldvalue.md'
    )
    INCOMING_STREAM_INFO_HEAD = Path(
        'scheduling/announce/watchinfo.embedfieldname.md'
    )
    INCOMING_STREAM_INFO_BODY = Path(
        'scheduling/announce/watchinfo.embedfieldvalue.md'
    )
    INCOMING_TEAM_INFO_HEAD = Path(
        'scheduling/announce/playersinfo.embedfieldname.md'
    )
    INCOMING_TEAM_INFO_BODY = Path(
        'scheduling/announce/playersinfo.embedfieldvalue.md'
    )
