import RPi.GPIO as GPIO


class LightBarrier:
    INPUT_PIN = 17  # Broadcom pin 17 (P1 pin 11)

    def __init__(self, is_active_high: bool = True) -> None:
        GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
        GPIO.setup(self.INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # TODO PUP required?

    def is_activated(self) -> bool:
        return GPIO.input(self.INPUT_PIN)