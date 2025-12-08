"""Node for sensing behavior state."""
import asyncio
import paho.mqtt.client as mqtt

class Sensing:
    def __init__(self):

        #MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        #MQTT Client
        client = mqtt.Client()
        client.connect("localhost")

        #is it active 
        self.sensing = True

        #Behaviors
        self.foodSensing = False,
        self.playSensing = False

        "Sensor attributes"
        #sensor pin decs
        

    def start(self):
        "use as setup function"
         
    
    def loop(self):
        "control system"
        #check buttons and sensors to set machine mode
        #update state to sensing, reacting, or machineIdle

        if sensing:
            if self.foodSensing:
                #check for food sensor
                #if triggered send message
                pass
            elif self.playSensing:
                #check for play sensor
                #if triggered send message
                pass

    def on_message(client, userdata, msg, self):
        text = msg.payload.decode()    # convert bytes → string
        if text == "sensing":
                self.machineIdle = True
        elif text == "machineIdle" or text == "reacting":
                self.machineIdle = False
        print("Received text:", text)

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe("state/text")
        print("Connected and subscribed.")
                


if __name__ == "__main__":
    sensing = Sensing()
    sensing.start()