import asyncio
import paho.mqtt.client as mqtt
from queue import Queue

from machine_idle import MachineIdle
from state_controller import StateController

# queue to simulate Arduino serial input
serial_queue = Queue()

# helper to await MQTT connection
class AsyncMQTTClient(mqtt.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connected_event = asyncio.Event()
    
    def on_connect(self, client, userdata, flags, rc):
        print("MQTT connected")
        client.subscribe("state/text")
        self.connected_event.set()


class TestStateController(StateController):
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()
        self.lastState = None
        self._last_line = ""

    def loop(self):
        try:
            self._last_line = serial_queue.get_nowait()
            print(f"[FSM] got serial: {self._last_line}")
        except:
            pass

        line = self._last_line
        message = None

        if line in ("hi", "fi"):
            message = "machineIdle"
        elif line == "ih":
            message = "sensingH"
        elif line == "if":
            message = "sensingF"
        elif line == "ef":
            message = "reactingF"
        elif line == "pp":
            message = "reactingP"
        elif line in ("ed", "pd"):
            message = "machineIdle"

        if message and message != self.lastState:
            self.client.publish("state/text", message)
            print(f"fsm -> {message}")
            self.lastState = message


async def fsm_loop(fsm_node):
    while True:
        try:
            fsm_node.loop()
        except Exception as e:
            print("FSM loop error:", e)
            raise
        await asyncio.sleep(0.1)

async def simulate_sequence():
    # wait for a moment to let subscription settle
    await asyncio.sleep(5)

    sequence = ["ih", "ef", "ed"]
    for cmd in sequence:
        serial_queue.put(cmd)
        print(f"Test -> simulated Arduino command: {cmd}")
        await asyncio.sleep(3)  # small delay between commands


async def main():
    # create MachineIdle node
    idle_node = MachineIdle()
    idle_node.start()

    # create FSM node
    fsm_node = TestStateController()

    # give MachineIdle time to connect and subscribe
    await asyncio.sleep(1)

    # start FSM loop
    asyncio.create_task(fsm_loop(fsm_node))

    # run the test sequence
    await simulate_sequence()


if __name__ == "__main__":
    asyncio.run(main())
