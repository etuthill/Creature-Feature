"""Node for machine idle behavior state."""
import asyncio
import random
import paho.mqtt.client as mqtt

class MachineIdle:
    def __init__(self):

        #MQTT Client
        client = mqtt.Client()
        client.connect("localhost")

        "Behavioral attributes"
        #healthbars
        int hunger = random.randint(20, 25) #will subtract 1 on random time interval. Max 25
        int boredom = random.randint(20, 25) #will subtract 1 on random time interval. Max 25
        int hungryThreshold = 9
        int boredThreshold = 9

        #is this the active state?
        bool machineIdle = True
        
        dict idleStates = {
        "idle": True,
        "hungry": False,
        "bored": False,
        }

        dict animations = {
        "idle": True,
        "hungry": False,
        "bored": False,
        }

        "Control attributes"
        int modeSelect = 0 #0 = empty, 1 = eat, 2 = play. Controls indicator lights
        bool sensing = False #turn on sensors, turn off buttons
        bool reacting = False #turn off sensing and buttons - like a cutscene
        bool machineIdle = True #no sensing or reacting - normal state
        

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
        if machineIdle:
            
            if self.hunger <= self.hungryThreshold and not idleStates["bored"]:
                #if hungry and not bored
                if not idleStates["hungry"]:
                    #if not already in hungry state
                    self.setAllFalseExcept("hungry")
                    print("Switching to hungry state")
            else if self.boredom <= self.boredThreshold and not idleStates["hungry"]:
                #if bored and not hungry
                if not idleStates["bored"]:
                    #if not already in bored state
                    self.setAllFalseExcept("bored")
                    print("Switching to bored state")
            else:
                if not idleStates["idle"]:
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
            if not sensing and not reacting:
                if self.hunger > 0:
                    self.hunger -= 1
                    print(f"Hunger decreased to {self.hunger}")

    async def boredomTimer(self):
        while True:
            await asyncio.sleep(self.boredomInterval)
            if not sensing and not reacting:
                if self.boredom > 0:
                    self.boredom -= 1
                    print(f"Boredom decreased to {self.boredom}")

    def setAllFalseExcept(self, str stateName):
        currentState = stateName
        for state in self.idleStates:
            if state == stateName:
                self.states[state] = True
            else:
            self.states[state] = False

if __name__ == "__main__":
    idle = MachineIdle()
    idle.start()