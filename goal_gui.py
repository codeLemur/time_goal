import logging
import os
import asyncio
import queue

from kivy.core.window import Window
if os.name != 'nt':
  Window.fullscreen = 'auto'
  Window.show_cursor = False
else:
    Window.size = (800, 420)
    Window.top = 0

os.environ['KIVY_WINDOW'] = 'egl_rpi'


from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.graphics import Color, Rectangle
from kivy.clock import mainthread

import time
from datetime import datetime

import globals
from light_barrier import LightBarrier
from request_socket import RequestSocket

NS_PER_MS = int(1e6)
STATUS_POLL_PERIOD_S = 1

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
        event_queue.put_nowait(globals.Events.SET_READY)
        self.set_start_number(0)
        self.set_duration_time('00:00')
        self.set_current_time('00:00')

    def confirm_time(self):
        logging.info('confirm_time')
        event_queue.put_nowait(globals.Events.STOP)
        self.current_time = self.duration_time

    def set_start_number(self, start_number):
        logging.info("set_start_number")
        self.start_number = start_number

    def set_current_time(self, current_time):
        self.current_time = current_time

    def set_duration_time(self, duration_time):
        logging.info(f'Changed duration time to: {duration_time}')
        self.duration_time = duration_time

    def set_system_state(self, state: str, color: tuple):
        self.system_status.text = state
        self._set_background_color(self.system_status, color)

    def set_light_barrier(self, state: str, color: tuple):
        self.light_barrier.text = state
        self._set_background_color(self.light_barrier, color)

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
    light_barrier_task = None
    request_task = None
    update_time_task = None

    def build(self):
        return sm

    def app_func(self):
        self.light_barrier_task = asyncio.ensure_future(self.observe_lightbarrier())
        self.request_task = asyncio.ensure_future(self.poll_system_status())
        self.update_time_task = asyncio.ensure_future(self.update_displayed_time())

        async def run_wrapper():
            await self.async_run(async_lib='asyncio')
            print('App done')
            self.light_barrier_task.cancel()
            self.request_task.cancel()
            self.update_time_task.cancel()

        return asyncio.gather(run_wrapper(), self.light_barrier_task, self.request_task, self.update_time_task)

    async def update_displayed_time(self):
        while True:
            goal_screen = sm.get_screen('goal')
            if self.system_status == globals.States.RUNNING:
                goal_screen.set_current_time(f'{datetime.fromtimestamp(time.time() - self.start_time).strftime("%M:%S.%f")[:-5]}')
            await asyncio.sleep(0.49)

    async def poll_system_status(self):
        while True:
            while not event_queue.empty():
                await request_socket.send_event(event_queue.get_nowait())
            await request_socket.request_current_state()
            previous_state = self.system_status
            self.system_status = request_socket.get_current_state()
            logging.info(f'Current status: {self.system_status}')
            goal_screen = sm.get_screen('goal')
            goal_screen.set_system_state(self.system_status.name, COLOR_LOOKUP[self.system_status])
            if self.system_status == globals.States.RUNNING and previous_state == globals.States.READY:
                self.start_time = time.time()
                start_number = await request_socket.request_start_number()
                goal_screen.set_start_number(start_number)
            if self.system_status == globals.States.RUNNING:
                # goal_screen.confirm_button.disabled = False
                goal_screen.ready_button.disabled = True
                # Update current time
            elif self.system_status in [globals.States.IDLE, globals.States.STOPPED]:
                goal_screen.ready_button.disabled = False
                goal_screen.confirm_button.disabled = True
            else:
                goal_screen.confirm_button.disabled = True
            await asyncio.sleep(STATUS_POLL_PERIOD_S)

    async def observe_lightbarrier(self):
        SENSOR_HYSTERESE_S = 1
        time_last_activated_s = 0
        while True:
            if light_barrier.is_activated():
                if not light_barrier.current_state:
                    logging.info("Light barrier Activated")
                    sm.get_screen("goal").set_light_barrier("Activated", ORANGE)
                    light_barrier.current_state = True
                if self.system_status == globals.States.RUNNING:
                    if (time.time() - time_last_activated_s) > SENSOR_HYSTERESE_S:
                        timestamp_ms = int(time.time_ns() / NS_PER_MS)
                        await request_socket.post_timestamp(timestamp_ms)
                        sm.get_screen('goal').set_duration_time(f'{datetime.fromtimestamp(time.time() - self.start_time).strftime("%M:%S.%f")[:-5]}')
                        sm.get_screen('goal').confirm_button.disabled = False
                        time_last_activated_s = time.time()
            elif light_barrier.current_state:
                logging.info("Light barrier Deactivated")
                light_barrier.current_state = False
                sm.get_screen("goal").set_light_barrier("Deactivated", LIGHT_GREEN)
            await asyncio.sleep(0.01)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info('Goal Module of Time Measurement')
    request_socket = RequestSocket(globals.ROLE_GOAL)
    light_barrier = LightBarrier()
    event_queue = queue.Queue()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(GoalApp().app_func())
    loop.close()
