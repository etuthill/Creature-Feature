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
        self.ser = serial.Serial('/dev/ttyACM0', baudrate=9600, timeout=0.1)

        #could be machineIdle, sensing, reacting
        self.lastState = "machineIdle"
        self.currentState = "machineIdle"
        

    def start(self):
        "use as setup function"
        pass
    
    def loop(self):
        message = None
        anim_message = None

        "control system"
        #check buttons and sensors to set machine mode
        #update state to sensing, reacting, or machineIdle
        serial_output = self.ser.readline().decode(errors="ignore").strip()
        if serial_output == "hi":
            #hall->idle
            self.currentState = "machineIdle"
            message = "machineIdle"
            anim_message = "hi"
            self.ser.write(b'B: idle\n')
        elif serial_output == "hf":
            #//hall->food react
            self.currentState = "reacting"
            message = "reacting"
            anim_message = "hf"
            self.ser.write(b'S: reacting\n')
        elif serial_output == "fi":
            #force->idle
            self.currentState = "idle"
            message = "machineIdle"
            anim_message = "fi"
            self.ser.write(b'B: idle\n')
        elif serial_output == "fp":
            #force->play react
            self.currentState = "reacting"
            message = "reacting"
            anim_message = "fp"
            self.ser.write(b'S: reacting\n')
        elif serial_output == "ih":
            #//idle->hall
            self.currentState = "sensing"
            message = "sensing"
            anim_message = "ih"
            self.ser.write(b'S: hall\n')
        elif serial_output == "if":
            #idle->force
            self.currentState = "sensing"
            message = "sensing"
            anim_message = "if"
            self.ser.write(b'S: force\n')
        #switch from reacting to idle 
        if message != None:
            self.client.publish("state/text", message)
            #pause before sending anim message to ensure state message is received first
        if anim_message != None:
            self.client.publish("anim/text", anim_message)

if __name__ == "__main__":
    creature = StateController()
    creature.start()

    #50hz loop
    while True:
        creature.loop()
        time.sleep(0.02)