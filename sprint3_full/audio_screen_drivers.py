import spidev
import lgpio
import pygame
import time
import os
import paho.mqtt.client as mqtt

class AudioScreenDrivers:
    def __init__(self):
        #MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        self.msg = "idle"
        self.lastMsg = "idle"
        
        # SCREENS
        # open GPIO chip
        self.h = lgpio.gpiochip_open(0)

        # screen pinout
        self.screens = [
            {"cs": 5, "dc": 12, "rst": 16, "vccen": 17, "pmoden": 27},
            {"cs": 6, "dc": 13, "rst": 20, "vccen": 4, "pmoden": 22}
        ]

        # setup GPIO pins
        for s in self.screens:
            lgpio.gpio_claim_output(self.h, s["cs"], 1)  # CS idle high
            lgpio.gpio_claim_output(self.h, s["dc"], 0) # DC default low
            lgpio.gpio_claim_output(self.h, s["rst"], 1)  # Reset idle high
            lgpio.gpio_claim_output(self.h, s["vccen"], 0)  # VCCEN off
            lgpio.gpio_claim_output(self.h, s["pmoden"], 1)  # PMODEN on

        # SPI setup
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 3000000   
        self.spi.mode = 0

        # SPEAKERS
        pygame.mixer.init()

    # SCREEN FUNCTIONS 
    def send_cmd(self, s, cmd):
        lgpio.gpio_write(self.h, s["dc"], 0)
        lgpio.gpio_write(self.h, s["cs"], 0)
        self.spi.writebytes([cmd])
        lgpio.gpio_write(self.h, s["cs"], 1)

    def send_data(self, s, data):
        lgpio.gpio_write(self.h, s["dc"], 1)
        lgpio.gpio_write(self.h, s["cs"], 0)

        CHUNK = 4096
        for i in range(0, len(data), CHUNK):
            self.spi.writebytes(list(data[i:i+CHUNK]))

        lgpio.gpio_write(self.h, s["cs"], 1)

    # power-on sequence
    def power_on_displays(self, s):

        # hardware reset
        lgpio.gpio_write(self.h, s["rst"], 0)
        time.sleep(0.05)
        lgpio.gpio_write(self.h, s["rst"], 1)
        time.sleep(0.05)

        # display OFF
        self.send_cmd(s, 0xAE)

        # command lock
        self.send_cmd(s, 0xFD)
        self.send_cmd(s, 0x12)

        # clock div
        self.send_cmd(s, 0xB3)
        self.send_cmd(s, 0xF1)

        # 64 rows
        self.send_cmd(s, 0xA8)
        self.send_cmd(s, 0x3F)

        # display offset = 0
        self.send_cmd(s, 0xA2)
        self.send_cmd(s, 0x00)

        # display start line = 0
        self.send_cmd(s, 0xA1)
        self.send_cmd(s, 0x00)

        # RGB565 color mode
        self.send_cmd(s, 0xA0)
        self.send_cmd(s, 0x76)

        # set column address range 0–95
        self.send_cmd(s, 0x15)
        self.send_cmd(s, 0x00)
        self.send_cmd(s, 0x5F)

        # set row address range 0–63
        self.send_cmd(s, 0x75)
        self.send_cmd(s, 0x00)
        self.send_cmd(s, 0x3F)

        # clear screen (send black)
        self.send_cmd(s, 0x5C)
        self.send_data(s, bytes(96 * 64 * 2))

        # enable power to panel
        lgpio.gpio_write(self.h, s["vccen"], 1)
        time.sleep(0.1)

        # display ON
        self.send_cmd(s, 0xAF)

    def draw_rgb565_file(self, s, filename, bgr=False):
        if not os.path.exists(filename):
            print("File not found:", filename)
            return

        with open(filename, "rb") as f:
            raw = f.read()

        if len(raw) != 4 + 96 * 64 * 2:
            print("File is wrong size:", len(raw))
            return

        raw_pixels = raw[4:]  # skip 4-byte header

        # set column and row ranges
        self.send_cmd(s, 0x15)  # column
        self.send_cmd(s, 0)
        self.send_cmd(s, 95)
        self.send_cmd(s, 0x75)  # row
        self.send_cmd(s, 0)
        self.send_cmd(s, 63)
        self.send_cmd(s, 0x5C)  # write RAM

        fixed = bytearray(len(raw_pixels))

        for i in range(0, len(raw_pixels), 2):
            lo = raw_pixels[i]
            hi = raw_pixels[i + 1]

            # combine to 16-bit pixel
            pixel = (hi << 8) | lo

            # extract RGB565 components
            r = (pixel >> 11) & 0x1F
            g = (pixel >> 5) & 0x3F
            b = pixel & 0x1F

            # swap R and B
            new_pixel = (b << 11) | (g << 5) | r

            # write as big-endian to display
            fixed[i] = (new_pixel >> 8) & 0xFF
            fixed[i + 1] = new_pixel & 0xFF

        self.send_data(s, fixed)

    def shutdown_displays(self, s):
        self.send_cmd(s, 0xAE)
        lgpio.gpio_write(self.h, s["vccen"], 0)
        time.sleep(0.1)
        lgpio.gpio_write(self.h, s["pmoden"], 0)

    def draw_both_screens(self, left_file, right_file):
        self.draw_rgb565_file(self.screens[0], left_file)
        self.draw_rgb565_file(self.screens[1], right_file)

    def narrowing_food_eyes(self):
        left_dir = "../eyes/eye_outputs/left/narrowing_food"
        right_dir = "../eyes/eye_outputs/right/narrowing_food"

        steps = [
            ("eyes_big_open_color_left.png", "eyes_big_open_color_right.png", 3),
            ("eyes_half_narrow_left.png", "eyes_half_narrow_right.png", 0.15),
            ("eyes_full_narrow_left.png", "eyes_full_narrow_right.png", 0.15),
            ("eyes_half_narrow_left.png", "eyes_half_narrow_right.png", 0.15),
            ("normal_blink_full_left.png", "normal_blink_full_right.png", 2),
        ]

        while True:
            for lf_name, rf_name, duration in steps:
                lf = os.path.join(left_dir, lf_name)
                rf = os.path.join(right_dir, rf_name)

                self.draw_both_screens(lf, rf)
                time.sleep(duration)

    def normal_blink_eyes(self):
        left_dir = "../eyes/eye_outputs/left/normal_blink"
        right_dir = "../eyes/eye_outputs/right/normal_blink"

        steps = [
            ("normal_blink_full_left.png", "normal_blink_full_right.png", 5),
            ("normal_blink_half_left.png", "normal_blink_half_right.png", 0.15),
            ("normal_blink_closed_left.png", "normal_blink_closed_right.png", 0.15),
            ("normal_blink_half_left.png", "normal_blink_half_right.png", 0.15),
        ]

        while True:
            for lf_name, rf_name, duration in steps:
                lf = os.path.join(left_dir, lf_name)
                rf = os.path.join(right_dir, rf_name)

                self.draw_both_screens(lf, rf)
                time.sleep(duration)


    def starry_eyes(self):
        left_dir = "../eyes/eye_outputs/left/starry"
        right_dir = "../eyes/eye_outputs/right/starry"

        left_file = os.path.join(left_dir, "normal_blink_full_left.png")
        right_file = os.path.join(right_dir, "normal_blink_full_right.png")
        self.draw_both_screens(left_file, right_file)
        time.sleep(2)

        steps = [
            ("eyes_half_color_small_star_right.png", "eyes_half_color_small_star_left.png", 0.15),
            ("eyes_half_color_large_star_stars_left.png", "eyes_half_color_large_star_stars_right.png", 0.15),
            ("eues_half_color_small_circle_star_left.png", "eues_half_color_small_circle_star_right.png", 0.15),
            ("eyes_half_color_large_star_stars_left.png", "eyes_half_color_large_star_stars_right.png", 0.15)
        ]

        while True:
            for lf_name, rf_name, duration in steps:
                lf = os.path.join(left_dir, lf_name)
                rf = os.path.join(right_dir, rf_name)

                self.draw_both_screens(lf, rf)
                time.sleep(duration)

    def side_to_side_eyes(self):
        left_dir = "../eyes/eye_outputs/left/side_to_side"
        right_dir = "../eyes/eye_outputs/right/side_to_side"

        steps = [
            ("normal_blink_full_left.png", "normal_blink_full_right.png", 3),
            ("eyes_half_sideways_left.png", "eyes_half_sideways_right.png", 0.2),
            ("eyes_full_sideways_left.png", "eyes_full_sideways_right.png", 0.2),
            ("eyes_half_sideways_left.png", "eyes_half_sideways_right.png", 0.2),
            ("normal_blink_full_left.png", "normal_blink_full_right.png", 0.2),
            ("eyes_half_sideways_left2.png", "eyes_half_sideways_right2.png", 0.2),
            ("eyes_full_sideways_left2.png", "eyes_full_sideways_right2.png", 0.2),
            ("eyes_half_sideways_left2.png", "eyes_half_sideways_right2.png", 0.2),
        ]

        while True:
            for lf_name, rf_name, duration in steps:
                lf = os.path.join(left_dir, lf_name)
                rf = os.path.join(right_dir, rf_name)

                self.draw_both_screens(lf, rf)
                time.sleep(duration)


    # SPEAKER FUNCTIONs
    def play_sound(self, filename):
        filepath = os.path.join("../audio", filename)
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():  # wait for sound to finish
            time.sleep(0.1)

    # MQTT FUNCTIONS

    def on_message(self, client, userdata, msg):
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

