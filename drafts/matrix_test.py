import time
import serial
import struct

import numpy as np


def write(arr):
    ser.write(
        struct.pack(
            f"<{'x' * 4}B{len(arr)}sB{'x' * 4}", 0x7E, arr.tobytes(), 0x7D
        ),
    )
    ser.flush()


def main(ser):
    while True:
        for i in range(7):
            a = np.zeros(48, dtype=np.uint8)
            a[i * 6] = 255
            write(a)
            time.sleep(0.2)
        for i in reversed(range(1, 6)):
            a = np.zeros(48, dtype=np.uint8)
            a[i * 6] = 255
            write(a)
            time.sleep(0.2)


if __name__ == "__main__":
    # sudo chmod a+rw /dev/ttyACM0
    PORT = "/dev/ttyACM0"
    BAUD = 115200

    with serial.Serial(PORT, BAUD) as ser:
        main(ser)