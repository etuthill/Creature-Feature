"""fsm"""
import asyncio
import paho.mqtt.client as mqtt
import time
import serial

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

        #Serial
        self.ser = serial.Serial('/dev/ttyACM0')

        #could be machineIdle, sensing, reacting
        self.lastState = "machineIdle"
        self.currentState = "machineIdle"
        

    def start(self):
        "use as setup function"
        asyncio.create_task(self.sensor())
    
    def loop(self):
        message = None

        "control system"
        #check buttons and sensors to set machine mode
        #update state to sensing, reacting, or machineIdle
        self.currentState = self.getCurrentState()

        #state transition
        if self.lastState != self.currentState:
            if self.currentState == "machineIdle":
                self.lastState = "machineIdle"
                self.ser.write(b'B: idle/n')
                message = "machineIdle"

            elif self.currentState == "sensing":
                self.lastState = "machineIdle"
                if self.hungry_loop:
                    self.ser.write(b'S: hall/n')
                elif self.bored_loop:
                    self.ser.write(b'S: force/n')
                message = "sensing"
                
            elif self.currentState == "reacting":
                self.lastState = "reacting"
                self.ser.write(b'S: reacting/n')
                message = "reacting"

        self.client.publish("state/text", message)


    def getCurrentState(self):
        self.lastState = self.currentState
        #determine current state
        return self.currentState


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