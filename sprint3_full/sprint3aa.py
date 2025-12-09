#fjdfiubufuewiodsfkjsfdhkksdf
"""fsm"""
import asyncio
import paho.mqtt.client as mqtt
import time
import serial
import random

class Sprint3aa:
    def __init__(self):
        #MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        self.msg = "idle"
        self.lastMsg = "idle"

    def loop(self):
        """
        if normal, run normal eyes and sound on randoms/in loop idk
        if hungry, run hungry eyes and sound on randoms/in loop idk
        if eating, run a set eating sequence then publish done message
        """

    def on_message(client, userdata, msg, self):
        text = msg.payload.decode()    # convert bytes → string
        if text == "idle":
                self.msg = "idle"
        elif text == "hungry":
                self.msg = "hungry"
        elif text == "eating":
                self.msg = "eating"
        print("Received text:", text)

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe("state/text")
        print("Connected and subscribed.")

        
        

if __name__ == "__main__":
    aa = Sprint3aa()
    aa.start()

    #50hz loop
    while True:
        aa.loop()
        time.sleep(0.02)