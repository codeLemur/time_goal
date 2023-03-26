import os
import time

if os.name != 'nt':
    import RPi.GPIO as GPIO


class LightBarrier:
    INPUT_PIN = 17  # Broadcom pin 17 (P1 pin 11)

    def __init__(self, is_active_high: bool = True) -> None:
        self.current_state = False
        if os.name != 'nt':
            GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
            GPIO.setup(self.INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def is_activated(self) -> bool:
        if os.name == 'nt':
            return (int(time.time()) % 2) == 0
        else:
            return GPIO.input(self.INPUT_PIN)
