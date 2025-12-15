"""Node for machine idle behavior state"""

import paho.mqtt.client as mqtt
from hunger import Hunger
from boredom import Boredom
import asyncio


class MachineIdle:
    """
    Handles the machine's idle behavior state.

    Tracks hunger and boredom needs, decides the current idle substate
    (idle, hungry, bored, hangry), and publishes state updates over MQTT.

    Attributes:
        client (mqtt.Client): MQTT client for subscribing and publishing state.
        hunger (Hunger): Hunger need system.
        boredom (Boredom): Boredom need system.
        machineIdle (bool): True if the machine is in idle mode, else False.
        currentState (str | None): Currently active idle state.
        idleStates (dict[str, bool]): Substate flags for idle, hungry, bored, hangry.
    """

    def __init__(self) -> None:
        """Initialize the MachineIdle node.

        Sets up MQTT client, subscribes to FSM topic, initializes
        hunger and boredom systems, and idle state tracking.
        """
        # mqtt client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        # need systems
        self.hunger = Hunger(self.client, topic="anim/hunger")
        self.boredom = Boredom(self.client, topic="anim/boredom")

        # machine idle/state tracking
        self.machineIdle = True 
        self.currentState = None 

        # tracking
        self.idleStates = {
            "idle": False,
            "hungry": False,
            "bored": False,
            "hangry": False
        }

    def reset(self) -> None:
        """Reset internal need systems and return machine to idle mode."""
        # reset internal need systems
        self.hunger.reset()
        self.boredom.reset()

        self.currentState = None # clear current idle state

        # return machine to idle mode
        self.machineIdle = True
        print("MachineIdle reset done")

    def decide_state(self) -> str:
        """Determine which idle substate should be active.

        Returns:
            str: One of 'idle', 'hungry', 'bored', or 'hangry'.
        """
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

    def start(self) -> None:
        """Start the hunger and boredom decay timers."""
        # start need decay timers
        self.hunger.start()
        self.boredom.start()

    def loop(self) -> None:
        """Main idle update loop.

        Checks current needs, decides state, and publishes changes
        if the machine is in idle mode.
        """
        # do nothing if machine is not in idle mode
        if not self.machineIdle:
            return

        next_state = self.decide_state() # determine which idle state should be active

        # publish only if state changed
        if next_state != self.currentState:
            self.currentState = next_state
            print(f"Idle state to {next_state}")
            self.client.publish("anim/text", next_state)

    def setAllFalseExcept(self, stateName: str) -> None:
        """Mark one idle substate as active and all others as False.

        Args:
            stateName (str): The state to activate.
        """
        # helper to mark one idle substate as active
        for state in self.idleStates:
            if state == stateName:
                self.idleStates[state] = True
            else:
                self.idleStates[state] = False

    def on_message(self, client, userdata, msg):
        text = msg.payload.decode()
        
        # Machine idle
        if text == "machineIdle":
            self.machineIdle = True
            print("MachineIdle to idle")

        # Sensing
        elif text in ("sensingH", "sensingF", "sensing"):
            self.machineIdle = False
            print(f"MachineIdle to sensing ({text})")

        # Reacting
        elif text == "reactingF":  # eat to fed
            self.machineIdle = False
            print("MachineIdle to reacting (eat)")
            self.hunger.reset()  # reset hunger
            print("Hunger reset!")

        elif text == "reactingP":  # play to played
            self.machineIdle = False
            print("MachineIdle to reacting (play)")
            self.boredom.reset()  # reset boredom
            print("Boredom reset!")

        # Reset FSM completely
        elif text == "RESET":
            print("Received RESET")
            self.reset()

    def on_connect(self, client: mqtt.Client, userdata, flags, rc: int) -> None:
        """Subscribe to FSM topic when MQTT connects.

        Args:
            client (mqtt.Client): The MQTT client instance.
            userdata: User-defined data (unused).
            flags: Response flags from the broker.
            rc (int): Connection result code.
        """
        # subscribe to global fsm state topic
        client.subscribe("state/text")
        print("Connected and subscribed.")


async def main() -> None:
        # create and start idle node
        idle = MachineIdle()
        idle.start()

        # main idle update loop
        while True:
            idle.loop()
            await asyncio.sleep(0.1)


asyncio.run(main())
