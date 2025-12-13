#fjdfiubufuewiodsfkjsfdhkksdf
"""fsm"""
import asyncio
import paho.mqtt.client as mqtt
import time
import serial
import random
from audio_screen_drivers import AudioScreenDrivers
import threading

class Sprint3:
    def __init__(self):
        #MQTT Client
        # self.client = mqtt.Client()
        # self.client.on_connect = self.on_connect
        # self.client.on_message = self.on_message
        # self.client.connect("localhost")
        # self.client.loop_start()

        #Serial
        self.ser = serial.Serial('/dev/ttyACM0', timeout=0.1)

        "Behavioral attributes"
        #healthbars
        self.hunger = 17 #will subtract 1 on random time interval. Max 25
        self.hungryThreshold = 8

        #states - idle, hungry, eating
        self.currentState = "idle"
        self.lastState = "idle"
        self.eat = False
        self.ate = False

        self.drivers = AudioScreenDrivers()
        self.eye_task = None

    def start(self):
        "use as setup function"
        asyncio.create_task(self.hungerTimer())
        asyncio.create_task(self.readSerial())
        for s in self.drivers.screens:
            self.drivers.power_on_displays(s)

    def loop(self):
        "control system"

        # ate event
        if self.ate:
            #self.client.publish("state/text", "ate")
            print("ate event")
            self.ate = False

        #determine state
        if self.eat:
            self.currentState = "eating"
        elif self.hunger <= self.hungryThreshold:
            self.currentState = "hungry"
        else:
            self.currentState = "idle"

        #state transition
        if self.lastState != self.currentState:
            self.drivers.set_state(self.currentState) 
            if self.currentState == "idle":
                self.lastState = "idle"
                self.eat = False
                #self.client.publish("state/text", "idle")
                print("idle")

            elif self.currentState == "hungry":
                self.lastState = "hungry"
                #self.client.publish("state/text", "hungry")
                print("hungry")

            elif self.currentState == "eating":
                self.lastState = "eating"
                #self.client.publish("state/text", "eating")
                print("eating")
                
    async def hungerTimer(self):
        while True:
            await asyncio.sleep(random.randint(1, 3))
            if self.currentState == "idle" or self.currentState == "hungry":
                if self.hunger > 0:
                    self.hunger -= 1
                    print(f"Hunger decreased to {self.hunger}")
                    self.ser.write(b"L:hunger\n")

    async def readSerial(self):
        while True:
            line = self.ser.readline().decode(errors="ignore").strip() 
            if not line: 
                await asyncio.sleep(0)
                continue
            if line == "eat":
                print("eat")
                self.eat = True
            elif line == "ate":
                print("ate")
                self.eat = False
                self.ate = True
                self.hunger = 17

            await asyncio.sleep(0) 


if __name__ == "__main__":
    creature = Sprint3()

    async def main_loop():
        creature.start()
        while True:
            creature.loop()
            await asyncio.sleep(0.02)

    asyncio.run(main_loop())
