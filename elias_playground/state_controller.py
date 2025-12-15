"""State controller - handles serial communication with Arduino and MQTT messaging for state changes."""
import serial
import paho.mqtt.client as mqtt

class StateController:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.connect("localhost")
        self.client.loop_start()

        self.ser = serial.Serial('/dev/ttyACM0', baudrate=9600, timeout=0.1)

        self.lastState = None
        self.currentState = "machineIdle"

    def loop(self):

        line = self.ser.readline().decode(errors="ignore").strip()

        message = None

        if line in ("hi", "fi"):
            message = "machineIdle"

        elif line in ("ih", "if", "he"):
            message = "sensing"

        elif line in ("ef", "pp"):
            message = "reacting"

        elif line in ("ed", "pd"):
            message = "machineIdle"

        if message and message != self.lastState:
            self.client.publish("state/text", message)
            print(f"FSM → {message}")
            self.lastState = message
    
    def reset_machine(self):
        print("FSM -> RESET")
        self.client.publish("state/text", "RESET") 
        try:
            self.ser.write(b"RESET\n") 
        except Exception as e:
            print("Failed to send RESET to Arduino:", e)
