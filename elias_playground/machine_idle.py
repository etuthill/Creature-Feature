"""node for machine idle behavior state"""

import paho.mqtt.client as mqtt
from hunger import Hunger
from boredom import Boredom
import asyncio


class MachineIdle:
    def __init__(self):
        # mqtt client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        # need systems
        self.hunger = Hunger(self.client, topic="anim/hunger")
        self.boredom = Boredom(self.client, topic="anim/boredom")

        # machine idle/state
        self.machineIdle = True 
        self.currentState = None 

        # tracking
        self.idleStates = {
            "idle": False,
            "hungry": False,
            "bored": False,
            "hangry": False
        }

    def reset(self):
        # reset internal need systems
        self.hunger.reset()
        self.boredom.reset()

        self.currentState = None # clear current idle state

        # return machine to idle mode
        self.machineIdle = True
        print("MachineIdle reset done")

    def decide_state(self):
        # highest priority when both needs are critical
        if self.hunger.is_hungry and self.boredom.is_bored:
            return "hangry"
        
        # hungly only
        if self.hunger.is_hungry and not self.boredom.is_bored:
            return "hungry"
        
        # boredom only
        if self.boredom.is_bored and not self.hunger.is_hungry:
            return "bored"

        return "idle" # idle otherwise

    def start(self):
        # start need decay timers
        self.hunger.start()
        self.boredom.start()

    def loop(self):
        # do nothing if machine is not in idle mode
        if not self.machineIdle:
            return

        next_state = self.decide_state() # determine which idle state should be active

        # publish only if state changed
        if next_state != self.currentState:
            self.currentState = next_state
            print(f"Idle state → {next_state}")
            self.client.publish("anim/text", next_state)

    def setAllFalseExcept(self, stateName):
        # helper to mark one idle substate as active
        for state in self.idleStates:
            if state == stateName:
                self.idleStates[state] = True
            else:
                self.idleStates[state] = False

    def on_message(self, client, userdata, msg):
        text = msg.payload.decode() # handle incoming fsm state messages

        # machine entered idle state
        if text == "machineIdle":
            self.machineIdle = True

        # machine left idle state
        elif text in ("sensing", "reacting"):
            self.machineIdle = False

        # reset all idle logic
        elif text == "RESET":
            print("Received RESET")
            self.reset()

    def on_connect(self, client, userdata, flags, rc):
        # subscribe to global fsm state topic
        client.subscribe("state/text")
        print("Connected and subscribed.")


async def main():
        # create and start idle node
        idle = MachineIdle()
        idle.start()

        # main idle update loop
        while True:
            idle.loop()
            await asyncio.sleep(0.1)


asyncio.run(main())
