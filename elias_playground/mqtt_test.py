import asyncio
import paho.mqtt.client as mqtt
from queue import Queue
from threading import Thread
import time

# import your classes
from state_controller import StateController
from machine_idle import MachineIdle

# queue to simulate Arduino serial input
serial_queue = Queue()

class TestStateController(StateController):
    """Override the serial read to use a queue instead of real Arduino."""
    def loop(self):
        try:
            # get a simulated serial line
            line = serial_queue.get_nowait()
        except:
            line = ""
        message = None

        # FSM logic
        if line in ("hi", "fi"):
            message = "machineIdle"
        elif line in ("ih", "if", "he", "fp"):
            message = "sensing"
        elif line in ("ef", "pp"):
            message = "reacting"
        elif line in ("ed", "pd"):
            message = "machineIdle"

        if message and message != self.lastState:
            self.client.publish("state/text", message)
            print(f"fsm -> {message}")
            self.lastState = message

async def main():
    # start MachineIdle node
    idle_node = MachineIdle()
    idle_node.start()

    # start TestStateController
    fsm_node = TestStateController()

    async def fsm_loop():
        while True:
            fsm_node.loop()
            await asyncio.sleep(0.1)

    def simulate_sequence():
        sequence = ["ih", "ef", "ed"]  # sensing to eating/fed to done
        for cmd in sequence:
            serial_queue.put(cmd)
            print(f"Test -> simulated Arduino command: {cmd}")
            time.sleep(5)  # small delay between commands

    # run simulation in separate thread
    Thread(target=simulate_sequence, daemon=True).start()

    # run FSM loop
    await fsm_loop()

if __name__ == "__main__":
    asyncio.run(main())
