import logging

from kivy.core.window import Window
Window.size = (800, 520)
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.clock import mainthread

import time
from datetime import datetime
from threading import Thread

import globals
from light_barrier import LightBarrier
from request_socket import RequestSocket

NS_PER_MS = int(1e6)
STATUS_POLL_PERIOD_S = 0.1

RED = (1, 0, 0)
GREEN = (0, 0.4, 0)
LIGHT_GREEN = (0.4, 1, 0.4)
ORANGE = (1, 0.6, 0.2)
YELLOW = (1, 1, 0)
COLOR_LOOKUP = {
    globals.States.IDLE: YELLOW,
    globals.States.READY: GREEN,
    globals.States.RUNNING: LIGHT_GREEN,
    globals.States.STOPPED: ORANGE,
    globals.States.ERROR: RED,
}


class GoalScreen(Screen):
    start_number = NumericProperty(0)
    current_time = StringProperty("00:00")
    duration_time = StringProperty("00:00")

    def set_ready(self):
        logging.info('set_ready')
        request_socket.send_event(globals.Events.SET_READY)
        self.set_start_number(0)
        self.set_duration_time('00:00')
        self.set_current_time('00:00')

    def confirm_time(self):
        logging.info('confirm_time')
        request_socket.send_event(globals.Events.STOP)
        self.current_time = self.duration_time

    def set_start_number(self, start_number):
        logging.info("set_start_number")
        self.start_number = start_number

    def set_current_time(self, current_time):
        logging.info(f'Changed current time to: {current_time}')
        self.current_time = current_time

    def set_duration_time(self, duration_time):
        logging.info(f'Changed duration time to: {duration_time}')
        self.duration_time = duration_time

    @mainthread
    def set_system_state(self, state: str, color: tuple):
        self.system_status.text = state
        self._set_background_color(self.system_status, color)

    @staticmethod
    def _set_background_color(widget, color):
        with widget.canvas.before:
            Color(color[0], color[1], color[2])
            Rectangle(size=widget.size, pos=widget.pos)


class WindowManager(ScreenManager):
    pass


kv = Builder.load_file("goal_gui.kv")

sm = WindowManager()
Window.clearcolor = (0.0, 0.0, 0.1, 0.2)
screens = [GoalScreen(name="goal")]
for screen in screens:
    sm.add_widget(screen)

sm.current = "goal"


class GoalApp(App):
    system_status = globals.States.IDLE
    start_time = 0

    def build(self):
        Thread(target=observe_lightbarrier).start()
        Clock.schedule_interval(self.start_status_request, STATUS_POLL_PERIOD_S)
        return sm

    def start_status_request(self, *args):
        logging.info(time.time())
        Thread(target=self.poll_system_status).start()

    def poll_system_status(self):
        request_socket.request_current_state()
        logging.info(f'Time2: {time.time()}')
        previous_state = self.system_status
        self.system_status = request_socket.get_current_state()
        logging.info(f'Current status: {self.system_status}')
        goal_screen = sm.get_screen('goal')
        goal_screen.set_system_state(self.system_status.name, COLOR_LOOKUP[self.system_status])
        if self.system_status == globals.States.RUNNING and previous_state == globals.States.READY:
            self.start_time = time.time()
            start_number = request_socket.request_start_number()
            goal_screen.set_start_number(start_number)
        if self.system_status == globals.States.RUNNING:
            goal_screen.confirm_button.disabled = False
            goal_screen.ready_button.disabled = True
            # Update current time
            goal_screen.set_current_time(f'{datetime.fromtimestamp(time.time() - app.start_time).strftime("%M:%S.%f")[:-5]}')
        elif self.system_status in [globals.States.IDLE, globals.States.STOPPED]:
            goal_screen.ready_button.disabled = False
            goal_screen.confirm_button.disabled = True
        else:
            goal_screen.confirm_button.disabled = True


def observe_lightbarrier():
    while True:
        if light_barrier.is_activated():
            if app.system_status == globals.States.RUNNING:
                timestamp_ms = int(time.time_ns() / NS_PER_MS)
                request_socket.post_timestamp(timestamp_ms)
                sm.get_screen('goal').set_duration_time(f'{datetime.fromtimestamp(time.time() - app.start_time).strftime("%M:%S.%f")[:-5]}')
                time.sleep(1)  # TODO remove me
        else:
            pass
            # logging.info("Light barrier Deactivated")
        time.sleep(0.01)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info('Goal Module of Time Measurement')
    request_socket = RequestSocket(globals.ROLE_GOAL)
    light_barrier = LightBarrier()
    app = GoalApp()
    app.run()
