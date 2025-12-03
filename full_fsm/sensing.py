"""Node for sensing behavior state."""
import asyncio
import paho.mqtt.client as mqtt

class Sensing:
    def __init__(self):

        #MQTT Client
        client = mqtt.Client()
        client.connect("localhost")

        #is it active 
        bool sensing = True

        #Behaviors
        bool foodSensing = False,
        bool playSensing = False

        "Sensor attributes"
        #sensor pin decs
        

    def start(self):
        "use as setup function"
         
    
    def loop(self):
        "control system"
        #check buttons and sensors to set machine mode
        #update state to sensing, reacting, or machineIdle

        if sensing:
            if foodSensing:
                #check for food sensor
                #if triggered send message
                
            else if playSensing:
                #check for play sensor
                #if triggered send message
                


if __name__ == "__main__":
    sensing = Sensing()
    sensing.start()