import requests
import logging
import globals


class ShareTime:
    URL = 'http://192.168.1.82'
    ROLE_KEY = 'role'  # Possible roles: start, goal, server
    TIMESTAMP_KEY = 'time'
    START_NUMBER_KEY = 'start_number'

    def __init__(self):
        pass

    def post_timestamp(self, role: str, start_number: int, timestamp_ms: int):
        logging.info(timestamp_ms)
        logging.info(start_number)
        data = {
            globals.ROLE_KEY: role,
            globals.START_NUMBER_KEY: start_number,
            globals.TIMESTAMP_KEY: timestamp_ms,
        }
        # TODO Dump the timestamps in a file so that we can still measure the time without internet connection
        try:
            response = requests.post(self.URL, json=data, timeout=1)
            # TODO handle response.status_code
            if response.status_code == 200:
                logging.info(response.text)
            elif response.status_code == 400:
                logging.error("Request failed")
            else:
                logging.warning(f'status_code {response.status_code}')
        except requests.exceptions.ConnectTimeout:
            logging.error(f"Connection timeout could not reach: {self.URL}")


if __name__ == '__main__':
    import time

    logging.basicConfig(level=logging.DEBUG)
    NS_PER_MS = int(1e6)
    logging.info(NS_PER_MS)
    st = ShareTime()
    st.post_timestamp(globals.ROLE_GOAL, 456, int(time.time_ns() / NS_PER_MS))


