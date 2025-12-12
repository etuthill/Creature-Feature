"""Has the functions for each anim of the creature. Must be async from main loop."""
import asyncio
import paho.mqtt.client as mqtt
import time
import serial

class StateController:
    def __init__(self):
        """REMINDER TO 'sudo usermod -a -G dialout $USER' TO ACCESS SERIAL PORTS"""
        #MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        #Serial
        self.ser = serial.Serial('/dev/ttyACM0', baudrate=9600, timeout=0.1)

        self.hf = False
        self.fp = False

    def start(self):
        "use as setup function"
        pass

    def loop(self):
        message = None
        if self.fp:
            #wait 3 seconds
            time.sleep(3)
            self.reacting = False
            message = "pd"
            if message != None:
                self.client.publish("state/text", message)
        if self.hf:
            #wait 3 seconds
            time.sleep(3)
            self.reacting = False
            message = "fd"
            if message != None:
                self.client.publish("state/text", message)


    def on_message(client, userdata, msg, self):
        text = msg.payload.decode()    # convert bytes → string
        if text == "fp":
                self.fp = True
        elif text == "hf":
                self.hf = True

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe("anim/text")
        print("Connected and subscribed.")

if __name__ == "__main__":
    creature = StateController()
    creature.start()

    #50hz loop
    while True:
        creature.loop()
        time.sleep(0.02)