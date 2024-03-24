import time

import board
import digitalio

button = digitalio.DigitalInOut(board.C0)
button.direction = digitalio.Direction.INPUT
# button.pull = digitalio.Pull.UP

while True:
    start = time.time()
    print(button.value)
    print(f"delta: {time.time() - start}")
    time.sleep(0.5)
