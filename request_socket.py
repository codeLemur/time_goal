
import csv
import globals
import logging
import os
from datetime import datetime
import time
from enum import Enum
import asyncio
import requests_async as requests
REQUEST_TIMEOUT=0.8


class HttpStatus(Enum):
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class RequestSocket:
    URL = 'http://codelemur.pythonanywhere.com/'
    DATA_PATH = 'data'
    GOAL_TIME_FILENAME = os.path.join(DATA_PATH, 'goal_time.csv')

    def __init__(self, role: str):
        self._role = role
        self._current_shadow_state = globals.States.IDLE
        self.goal_time_fieldnames = [globals.TIMESTAMP_KEY, globals.LOG_TIME_KEY]

        if not os.path.exists(self.DATA_PATH):
            os.makedirs(self.DATA_PATH)
        if not os.path.exists(self.GOAL_TIME_FILENAME):
            with open(self.GOAL_TIME_FILENAME, 'w', newline='') as goal_time_file:
                writer = csv.DictWriter(goal_time_file, fieldnames=self.goal_time_fieldnames)
                writer.writeheader()

    async def post_timestamp(self, timestamp_ms: int):
        logging.info(timestamp_ms)
        data = {
            globals.ROLE_KEY: self._role,
            globals.COMMAND_TYPE_KEY: globals.CMD_REPORT_TIME,
            globals.TIMESTAMP_KEY: timestamp_ms,
        }
        with open(self.GOAL_TIME_FILENAME, 'a', newline='') as goal_time_file:
            writer = csv.DictWriter(goal_time_file, fieldnames=self.goal_time_fieldnames)
            writer.writerow({globals.TIMESTAMP_KEY: timestamp_ms,
                             globals.LOG_TIME_KEY: datetime.fromtimestamp(time.time())})
        await self._post(data)

    async def send_event(self, event: globals.Events):
        logging.info(f'Sending event: {event.name}')
        data = {
            globals.ROLE_KEY: self._role,
            globals.COMMAND_TYPE_KEY: globals.CMD_STATE_CHANGE,
            globals.EVENT_KEY: event.name
        }
        await self._post(data)

    async def request_current_state(self):
        try:
            async with requests.Session() as session:
                response = await session.get(self.URL, timeout=REQUEST_TIMEOUT)
            if response.status_code == HttpStatus.OK.value:
                logging.info(f'Current state: {response.text}')
                self._current_shadow_state = globals.States[response.text]
            else:
                logging.error(f"GET received invalid status code: {HttpStatus(response.status_code).name}")
                self._current_shadow_state = globals.States.ERROR
        except requests.exceptions.ConnectTimeout:
            logging.error(f"Connection timeout could not reach: {self.URL}")
            self._current_shadow_state = globals.States.ERROR
        except Exception as exp:
            logging.error(f"GET received exception: {exp}")
            self._current_shadow_state = globals.States.ERROR

    async def request_start_number(self) -> int:
        data = {
            globals.ROLE_KEY: self._role,
            globals.COMMAND_TYPE_KEY: globals.CMD_REQUEST_START_NUMBER,
        }
        response = await self._post(data)
        try:
            start_number = int(response.text)
        except ValueError:
            logging.error(f'Invalid start number response: {response.text}')
            start_number = 0  # the default value
        except AttributeError:
            logging.error(f'Invalid start number response: {response}')
            start_number = 0  # the default value
        return start_number

    def get_current_state(self):
        return self._current_shadow_state

    async def _post(self, data: dict):
        response = 0
        try:
            async with requests.Session() as session:
                response = await session.post(self.URL, json=data, timeout=REQUEST_TIMEOUT)
            if response.status_code == HttpStatus.OK.value:
                logging.info(f'Server response: {response.text}')
            else:
                logging.warning(f'POST received invalid status code {HttpStatus(response.status_code).name}')
                self._current_shadow_state = globals.States.ERROR
        except requests.exceptions.ConnectTimeout:
            logging.error(f"Connection timeout could not reach: {self.URL}")
            self._current_shadow_state = globals.States.ERROR
        except Exception as exp:
            logging.error(f"POST received exception: {exp}")
            self._current_shadow_state = globals.States.ERROR
        return response


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
