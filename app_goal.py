# app_start.py
# Represents the start of the time measurement
import time
import logging

from light_barrier import LightBarrier


def app_goal():
    logging.info("App Goal")
    light_barrier = LightBarrier()
    while True:
        if light_barrier.is_activated():
            logging.info("Light barrier Activated")
        else:
            logging.info("Light barrier Deactivated")
        time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.info('PyCharm')
    app_goal()
