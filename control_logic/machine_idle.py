"""Node for machine idle behavior state."""
import asyncio
import random
import serial
import paho.mqtt.client as mqtt
import time

#ALL OF THIS NEEDS TO BE RESET SOMEHOW!!!!!!!!!

class MachineIdle:
    def __init__(self):

        #MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        #Serial
        self.ser = serial.Serial('/dev/ttyACM0', baudrate=9600, timeout=0.1)

        "Behavioral attributes"
        #healthbars
        self.hunger = 17 #will subtract 1 on random time interval. Max 25
        self.boredom = 17 #will subtract 1 on random time interval. Max 25
        self.hungryThreshold = 8
        self.boredThreshold = 8

        #is this the active state?
        self.machineIdle = True
        
        self.idleStates = {
        "idle": True,
        "hungry": False,
        "bored": False,
        }

        "Control attributes"
        self.machineIdle = True #no sensing or reacting - normal state
        

        "Timing attributes"
        #section for likely timers and intervals
        self.hungerInterval = random.randint(1, 5) #seconds
        self.boredomInterval = random.randint(1, 5) #seconds

    def start(self):
        "use as setup function"
        asyncio.create_task(self.hungerTimer())
        asyncio.create_task(self.boredomTimer())
    
    def loop(self):
        "control system"
        message = None
        if self.machineIdle:
            
            if self.hunger <= self.hungryThreshold and not self.idleStates["bored"]:
                #if hungry and not bored
                if not self.idleStates["hungry"]:
                    #if not already in hungry state
                    self.setAllFalseExcept("hungry")
                    print("Switching to hungry state")
                    message = "hungry"
            elif self.boredom <= self.boredThreshold and not self.idleStates["hungry"]:
                #if bored and not hungry
                if not self.idleStates["bored"]:
                    #if not already in bored state
                    self.setAllFalseExcept("bored")
                    print("Switching to bored state")
                    message = "bored"
            else:
                if not self.idleStates["idle"]:
                    #if not already in idle state
                    self.setAllFalseExcept("idle")
                    print("Switching to idle state")
                    message = "idle"
        self.client.publish("anim/text", message)
    
    async def hungerTimer(self):
        while True:
            await asyncio.sleep(self.hungerInterval)
            if self.idleStates["idle"]:
                if self.hunger > 0:
                    self.hunger -= 1
                    print(f"Hunger decreased to {self.hunger}")
                    self.ser.write(b'D: hunger\n')

    async def boredomTimer(self):
        while True:
            await asyncio.sleep(self.boredomInterval)
            if self.idleStates["idle"]:
                if self.boredom > 0:
                    self.boredom -= 1
                    print(f"Boredom decreased to {self.boredom}")
                    self.ser.write(b'D: force\n')

    def setAllFalseExcept(self, stateName):
        for state in self.idleStates:
            if state == stateName:
                self.states[state] = True
            else:
                self.idleStates[state] = False

    def on_message(client, userdata, msg, self):
        text = msg.payload.decode()    # convert bytes → string
        if text == "machineIdle":
                self.machineIdle = True
        elif text != None:
                self.machineIdle = False
        print("Received text:", text)

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe("state/text")
        print("Connected and subscribed.")

if __name__ == "__main__":
    idle = MachineIdle()
    idle.start()
    #50hz loop#50hz loop
    while True:
        idle.loop()
        time.sleep(0.02)