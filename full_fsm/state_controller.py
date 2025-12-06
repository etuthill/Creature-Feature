"""fsm"""
import asyncio
import paho.mqtt.client as mqtt
import time

class StateController:
    def __init__(self):
        """REMINDER TO 'sudo usermod -a -G dialout $USER' TO ACCESS SERIAL PORTS
"""

        #MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        #could be machineIdle, sensing, reacting
        self.lastState = "machineIdle"
        self.currentState = "machineIdle"

        "Control attributes"
        #button/dial pin decs
        

    def start(self):
        "use as setup function"
        asyncio.create_task(self.sensor())
    
    def loop(self):
        message = None

        "control system"
        #check buttons and sensors to set machine mode
        #update state to sensing, reacting, or machineIdle
        self.currentState = self.getCurrentState()

        if self.lastState != self.currentState:
            #transition behaviors like resetting hunger 
            if self.currentState == "machineIdle":
                self.lastState = "machineIdle"
                #turn off sensors
                self.sensorsOff()
                #turn on healthbar and indicators
                self.allLightsOn()
                message = "machineIdle"

            elif self.currentState == "sensing":
                self.lastState = "machineIdle"
                #tell arduino to turn on sensors

                #turn off healthbar and indicators
                self.lightsOff()
                message = "sensing"
                
            elif self.currentState == "reacting":
                self.lastState = "reacting"
                #turn off sensors and buttons
                self.sensorsOff()
                self.controlOff()
                #turn off back button
                #start relevant animation
                message = "reacting"
        self.client.publish("state/text", message)


    def getCurrentState(self):
        self.lastState = self.currentState
        #determine current state
        return self.currentState
    
    def sensorsOff(self):
        #turns off sensors somehow lol
        pass
    

    def lightsOff(self):
        #turns off lights except back button somehow lol
        pass
    
    def allLightsOn(self):
        #turns on all lights somehow lol
        pass

    def contolOn(self):
        #enables control inputs somehow lol
        pass
    
    def controlOff(self):
        #disables control inputs somehow lol
        pass

    async def sensorRead(self):
        while True:
            if self.currentState == "sensing":
                #read arduino
                pass


if __name__ == "__main__":
    creature = StateController()
    creature.start()

    #50hz loop
    while True:
        creature.loop()
        time.sleep(0.02)