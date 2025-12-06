"""Node for machine idle behavior state."""
import asyncio
import random
import paho.mqtt.client as mqtt

class MachineIdle:
    def __init__(self):

        #MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        "Behavioral attributes"
        #healthbars
        self.hunger = random.randint(20, 25) #will subtract 1 on random time interval. Max 25
        self.boredom = random.randint(20, 25) #will subtract 1 on random time interval. Max 25
        self.hungryThreshold = 9
        self.boredThreshold = 9

        #is this the active state?
        self.machineIdle = True
        
        self.idleStates = {
        "idle": True,
        "hungry": False,
        "bored": False,
        }

        self.animations = {
        "idle": True,
        "hungry": False,
        "bored": False,
        }

        "Control attributes"
        self.modeSelect = 0 #0 = empty, 1 = eat, 2 = play. Controls indicator lights
        self.sensing = False #turn on sensors, turn off buttons
        self.reacting = False #turn off sensing and buttons - like a cutscene
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
        #check buttons and sensors to set machine mode
        #update state to sensing, reacting, or machineIdle
        if self.machineIdle:
            
            if self.hunger <= self.hungryThreshold and not self.idleStates["bored"]:
                #if hungry and not bored
                if not self.idleStates["hungry"]:
                    #if not already in hungry state
                    self.setAllFalseExcept("hungry")
                    print("Switching to hungry state")
            elif self.boredom <= self.boredThreshold and not self.idleStates["hungry"]:
                #if bored and not hungry
                if not self.idleStates["bored"]:
                    #if not already in bored state
                    self.setAllFalseExcept("bored")
                    print("Switching to bored state")
            else:
                if not self.idleStates["idle"]:
                    #if not already in idle state
                    self.setAllFalseExcept("idle")
                    print("Switching to idle state")
            
            self.setHealthLights()

    def setHealthLights(self):
        "set color of health lights based on hunger and boredom levels"
        pass
    
    async def hungerTimer(self):
        while True:
            await asyncio.sleep(self.hungerInterval)
            if not self.sensing and not self.reacting:
                if self.hunger > 0:
                    self.hunger -= 1
                    print(f"Hunger decreased to {self.hunger}")

    async def boredomTimer(self):
        while True:
            await asyncio.sleep(self.boredomInterval)
            if not self.sensing and not self.reacting:
                if self.boredom > 0:
                    self.boredom -= 1
                    print(f"Boredom decreased to {self.boredom}")

    def setAllFalseExcept(self, stateName):
        currentState = stateName
        for state in self.idleStates:
            if state == stateName:
                self.states[state] = True
            else:
                self.idleStates[state] = False

    def on_message(client, userdata, msg, self):
        text = msg.payload.decode()    # convert bytes → string
        if text == "machineIdle":
                self.machineIdle = True
        elif text == "sensing" or text == "reacting":
                self.machineIdle = False
        print("Received text:", text)

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe("state/text")
        print("Connected and subscribed.")

if __name__ == "__main__":
    idle = MachineIdle()
    idle.start()