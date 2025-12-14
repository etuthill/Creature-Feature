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
        serial_output = self.ser.readline().decode(errors="ignore").strip()
        if serial_output == "hi":
            #hall->idle
            pass
            
        elif serial_output == "fi":
            #force->idle
            pass
            
        elif serial_output == "ih":
            #//idle->hall
            pass
            
        elif serial_output == "if":
            #idle->force
            pass
            
        elif serial_output == "he":
            #hall->eating
            pass
            
        elif serial_output == "ef":
            #eating->food react
            pass
            
        elif serial_output == "fp":
            #force->playing
            pass
            
        elif serial_output == "pp":
            #playing->play react
            pass
            
        elif serial_output == "ed":
            #playing->play react
            pass
            
        elif serial_output == "pd":
            #playing->play react
            pass
            
        


    def on_message(client, userdata, msg, self):
        text = msg.payload.decode()    # convert bytes → string
        if text == "machineIdle":
                pass
        elif text == "sensing":
                pass
        elif text == "reacting":
                pass
        elif text == "idle":
                pass
        elif text == "bored":
                pass
        elif text == "hungry":
                pass
        print("Received text:", text)

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