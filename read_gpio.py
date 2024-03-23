import sys
import time
from pylibftdi import BitBangDevice


def read_gpio(pin_number):
    try:
        with BitBangDevice() as bb:
            bb.direction = (1 << pin_number)  # Set pin as input
            return bb.port & (1 << pin_number) != 0  # Read pin state
    except Exception as e:
        print("Error:", e)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python read_gpio.py [pin_number]")
        sys.exit(1)

    pin_number = int(sys.argv[1])

    while True:
        try:
            pin_state = read_gpio(pin_number)
            print(f"GPIO pin {pin_number} state:", pin_state)
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)
