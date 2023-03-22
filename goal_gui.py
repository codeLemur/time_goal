import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, NumericProperty, ListProperty
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.clock import mainthread

import time
from threading import Thread

import globals
from light_barrier import LightBarrier
from request_socket import RequestSocket

NS_PER_MS = int(1e6)
STATUS_POLL_PERIOD_S = 2.5

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
    current_time = NumericProperty(0)
    duration_time = NumericProperty(0)

    def set_ready(self):
        logging.info('set_ready')
        request_socket.send_event(globals.Events.SET_READY)

    def confirm_time(self):
        logging.info('confirm_time')
        request_socket.send_event(globals.Events.STOP)

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
        self.system_status = request_socket.get_current_state()
        logging.info(f'Current status: {self.system_status}')
        goal_screen = sm.get_screen('goal')
        goal_screen.set_system_state(self.system_status.name, COLOR_LOOKUP[self.system_status])
        if self.system_status == globals.States.RUNNING:
            goal_screen.confirm_button.disabled = False
            goal_screen.ready_button.disabled = True
        elif self.system_status in [globals.States.IDLE, globals.States.STOPPED]:
            goal_screen.ready_button.disabled = False
            goal_screen.confirm_button.disabled = True
        else:
            goal_screen.confirm_button.disabled = True
            goal_screen.ready_button.disabled = True

def observe_lightbarrier():
    while True:
        if light_barrier.is_activated():
            if GoalApp.system_status == globals.States.RUNNING:
                request_socket.post_timestamp(int(time.time_ns() / NS_PER_MS))
        else:
            logging.info("Light barrier Deactivated")
        time.sleep(0.01)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info('Goal Module of Time Measurement')
    request_socket = RequestSocket(globals.ROLE_GOAL)
    light_barrier = LightBarrier()
    GoalApp().run()
