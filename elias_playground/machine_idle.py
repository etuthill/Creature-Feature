"""Node for machine idle behavior state."""

import paho.mqtt.client as mqtt
from hunger import Hunger
from boredom import Boredom
import asyncio

class MachineIdle:
    def __init__(self):
        # MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        # Needs
        self.hunger = Hunger(self.client, topic="anim/hunger")
        self.boredom = Boredom(self.client, topic="anim/boredom")

        self.machineIdle = True

        self.currentState = None

        self.idleStates = {
            "idle": False,
            "hungry": False,
            "bored": False,
            "hangry": False
            }
        
    def reset(self):
        self.hunger.reset()
        self.boredom.reset()
        self.currentState = None
        self.machineIdle = True
        print("MachineIdle reset done")
            
    def decide_state(self):
        if self.hunger.is_hungry and self.boredom.is_bored:
            return "hangry"

        if self.hunger.is_hungry:
            return "hungry"

        if self.boredom.is_bored:
            return "bored"

        return "idle"


    def start(self):
        self.hunger.start()
        self.boredom.start()

    def loop(self):
        if not self.machineIdle:
            return

        next_state = self.decide_state()

        if next_state != self.currentState:
            self.currentState = next_state
            print(f"Idle state → {next_state}")
            self.client.publish("anim/text", next_state)

    def setAllFalseExcept(self, stateName):
        for state in self.idleStates:
            if state == stateName:
                self.idleStates[state] = True
            else:
                self.idleStates[state] = False

    def on_message(self, client, userdata, msg):
        text = msg.payload.decode()
        if text == "machineIdle":
            self.machineIdle = True
        elif text in ("sensing", "reacting"):
            self.machineIdle = False
        elif text == "RESET":
            print("Received RESET")
            self.reset()


    def on_connect(self, client, userdata, flags, rc):
        client.subscribe("state/text")
        print("Connected and subscribed.")

async def main():
        idle = MachineIdle()
        idle.start()

        while True:
            idle.loop()
            await asyncio.sleep(0.1)

asyncio.run(main())