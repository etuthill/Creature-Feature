"""
state controller handles serial communication with arduino
and mqtt messaging for state changes
"""

import serial
import paho.mqtt.client as mqtt


class StateController:
    def __init__(self):
        self.client = mqtt.Client() # MQTT client used to publish fsm state updates
        self.client.on_connect = self.on_connect # callback when mqtt connects
        self.client.connect("localhost") # connect to local 
        self.client.loop_start() # start mqtt loop in background thread
        self.client.on_message = self.on_message # start message reading

        # serial connection to arduino non blocking read
        self.ser = serial.Serial('/dev/ttyACM0', baudrate=9600, timeout=0.1)

        # previous published state used to avoid duplicates
        self.lastState = None

        # starting fsm state
        self.currentState = "machineIdle"

    def loop(self):
        # read a line from arduino over serial
        line = self.ser.readline().decode(errors="ignore").strip()

        # holds the state message to publish
        message = None

        # sensors to idle
        if line in ("hi", "fi"):
            message = "machineIdle"

        # idle to sensing + sensing to reacting
        elif line in ("ih", "if", "he", "fp"):
            message = "sensing"

        # eat to fed and play to played
        elif line in ("ef", "pp"):
            message = "reacting"

        # eat to done and play to done
        elif line in ("ed", "pd"):
            message = "machineIdle"

        # publish state only if it changed
        if message and message != self.lastState:
            self.client.publish("state/text", message)
            print(f"fsm -> {message}")
            self.lastState = message

    def handle_reset(self):
        # clear FSM state
        self.lastState = None
        self.currentState = "machineIdle"

        # optionally notify arduino
        try:
            self.ser.write(b"RESET\n")
        except Exception as e:
            print("failed to send reset to arduino", e)

        print("FSM reset complete")

    def reset_machine(self):
        print("fsm -> reset")
        self.client.publish("state/text", "RESET")
        self.handle_reset()
        
    def on_connect(self, client, userdata, flags, rc):
        print("FSM connected to MQTT")
        client.subscribe("state/text")

    def on_message(self, client, userdata, msg):
        text = msg.payload.decode()

        if text == "RESET":
            print("FSM received RESET")
            self.handle_reset()


if __name__ == "__main__":
    fsm = StateController()

    try:
        while True:
            fsm.loop()
    except KeyboardInterrupt:
        print("FSM stopped")

