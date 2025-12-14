"""fsm"""
import asyncio
import paho.mqtt.client as mqtt
import time
import serial

#ALL OF THIS NEEDS TO BE RESET SOMEHOW!!!!!!!!!

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

        "control system"
        #check buttons and sensors to set machine mode
        #update state to sensing, reacting, or machineIdle
        serial_output = self.ser.readline().decode(errors="ignore").strip()
        if serial_output == "hi":
            #hall->idle
            self.currentState = "machineIdle"
            message = "machineIdle"
            self.ser.write(b'B: idle\n')
        elif serial_output == "fi":
            #force->idle
            self.currentState = "idle"
            message = "machineIdle"
            self.ser.write(b'B: idle\n')
        elif serial_output == "ih":
            #//idle->hall
            self.currentState = "sensing"
            message = "sensing"
            self.ser.write(b'S: hall\n')
        elif serial_output == "if":
            #idle->force
            self.currentState = "sensing"
            message = "sensing"
            self.ser.write(b'S: force\n')
        elif serial_output == "he":
            #hall->eating
            self.currentState = "sensing"
            message = "sensing"
        elif serial_output == "ef":
            #eating->food react
            self.currentState = "reacting"
            message = "reacting"
        elif serial_output == "fp":
            #force->playing
            self.currentState = "reacting"
            message = "sensing"
        elif serial_output == "pp":
            #playing->play react
            self.currentState = "reacting"
            message = "reacting"
        elif serial_output == "ed":
            #eat react->done
            self.currentState = "idle"
            message = "idle"
        elif serial_output == "pd":
            #eat react->done
            self.currentState = "idle"
            message = "idle"
        #switch from reacting to idle 
        if message != None:
            self.client.publish("state/text", message)

if __name__ == "__main__":
    creature = StateController()
    creature.start()

    #50hz loop
    while True:
        creature.loop()
        time.sleep(0.02)