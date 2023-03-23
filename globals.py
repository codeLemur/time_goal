from enum import Enum

# Database Keys
ROLE_KEY = 'role'  # Required
COMMAND_TYPE_KEY = 'cmd'  # Required
TIMESTAMP_KEY = 'time'
START_NUMBER_KEY = 'start_number'
EVENT_KEY = 'event'
DURATION_KEY = 'duration_ms'
LOG_TIME_KEY = 'log_time'

# Roles
ROLE_START = 'start'
ROLE_GOAL = 'goal'
ROLE_SERVER = 'server'

# Command Types
CMD_STATE_CHANGE = 'state_change'
CMD_REPORT_TIME = 'report_time'
CMD_REQUEST_START_NUMBER = 'request_start_number'


class States(Enum):
    IDLE = 0
    READY = 1
    RUNNING = 2
    STOPPED = 3
    ERROR = 4


class Events(Enum):
    SET_READY = 0
    START = 1
    STOP = 2
    ENTER_ERROR = 3
    QUIT_ERROR = 4
