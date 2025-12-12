#fjdfiubufuewiodsfkjsfdhkksdf
"""fsm"""
import asyncio
import paho.mqtt.client as mqtt
import time
import serial
import random
import lgpio
import spidev
from audio_screen_drivers import (
    power_on_displays,
    shutdown_displays,
    draw_both_screens,
    animate_screens,
    play_sound)

class Sprint3aa:
    def __init__(self):
        #MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        self.msg = "idle"
        self.lastMsg = "idle"
        
class Sprint3aa:
    def __init__(self):
        # MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        self.msg = "idle"
        self.lastMsg = "idle"
        
        # screens setup
        # open GPIO chip
        self.h = lgpio.gpiochip_open(0)

        # screen pinout
        self.screens = [
            {"cs": 5, "dc": 12, "rst": 16, "vccen": 17, "pmoden": 27},
            {"cs": 6, "dc": 13, "rst": 20, "vccen": 4, "pmoden": 22}
        ]

        # setup GPIO pins
        for s in self.screens:
            lgpio.gpio_claim_output(self.h, s["cs"], 1) # CS idle high
            lgpio.gpio_claim_output(self.h, s["dc"], 0) # DC default low
            lgpio.gpio_claim_output(self.h, s["rst"], 1) # Reset idle high
            lgpio.gpio_claim_output(self.h, s["vccen"], 0) # VCCEN off
            lgpio.gpio_claim_output(self.h, s["pmoden"], 1) # PMODEN on

        # SPI setup
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 3000000
        self.spi.mode = 0

    def start_screens(self):
        power_on_displays(self.screens)

    def shutdown_screens(self):
        shutdown_displays(self.screens)

    def loop(self):
        """
        if normal, run normal eyes and sound on randoms/in loop idk
        if hungry, run hungry eyes and sound on randoms/in loop idk
        if eating, run a set eating sequence then publish done message
        """

    def on_message(client, userdata, msg, self):
        text = msg.payload.decode()    # convert bytes → string
        if text == "idle":
                self.msg = "idle"
        elif text == "hungry":
                self.msg = "hungry"
        elif text == "eating":
                self.msg = "eating"
        print("Received text:", text)

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe("state/text")
        print("Connected and subscribed.")

        
        

if __name__ == "__main__":
    aa = Sprint3aa()
    aa.start()

    #50hz loop
    while True:
        aa.loop()
        time.sleep(0.02)