"""do for every script"""

import asyncio
import signal
import serial

SERIAL_PORT = "/dev/ttyUSB0"
BAUD = 115200

stop_event = asyncio.Event()

def handle_shutdown():
    print("Shutdown signal received")
    stop_event.set()

async def serial_task(ser: serial.Serial):
    try:
        while not stop_event.is_set():
            if ser.in_waiting:
                data = ser.readline().decode(errors="ignore").strip()
                print(data)
            await asyncio.sleep(0.01)  # IMPORTANT: yield to event loop
    except asyncio.CancelledError:
        pass
    finally:
        print("Serial task exiting")

async def main():
    ser = serial.Serial(
        SERIAL_PORT,
        BAUD,
        timeout=0.1   # 🚨 REQUIRED: never block forever
    )

    try:
        task = asyncio.create_task(serial_task(ser))
        await stop_event.wait()   # wait for SIGINT/SIGTERM
    finally:
        print("Cleaning up...")
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        ser.close()
        print("Serial closed")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Handle Ctrl-C and kill
    loop.add_signal_handler(signal.SIGINT, handle_shutdown)
    loop.add_signal_handler(signal.SIGTERM, handle_shutdown)

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
        print("Loop closed")
