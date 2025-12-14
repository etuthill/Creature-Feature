import spidev
import lgpio
import pygame
import random
import threading
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

        self.lastMsg = None
        
        # SCREENS
        # open GPIO chip
        self.h = lgpio.gpiochip_open(0)

        # screen pinout
        self.screens = [
            {"cs": 5, "dc": 12, "rst": 16, "vccen": 17, "pmoden": 27},
            {"cs": 6, "dc": 13, "rst": 20, "vccen": 4, "pmoden": 22}
        ]

        self.stop_eyes_event = threading.Event()
        self.eye_thread = None
        self.stop_interval_audio = True
        self.spi_lock = threading.Lock()     # protects SPI bus
        self.draw_lock = threading.Lock()    # protects full frame draws

        self.set_state("idle")


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
        self.spi.max_speed_hz = 2000000   
        self.spi.mode = 0

        # SPEAKERS
        pygame.mixer.init()

    # SCREEN FUNCTIONS 
    def send_cmd(self, s, cmd):
        with self.spi_lock:
            lgpio.gpio_write(self.h, s["dc"], 0)
            lgpio.gpio_write(self.h, s["cs"], 0)
            self.spi.writebytes([cmd])
            lgpio.gpio_write(self.h, s["cs"], 1)

    def send_data(self, s, data):
        with self.spi_lock:
            lgpio.gpio_write(self.h, s["dc"], 1)
            lgpio.gpio_write(self.h, s["cs"], 0)

            CHUNK = 4096
            for i in range(0, len(data), CHUNK):
                self.spi.writebytes(data[i:i+CHUNK])

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
        with self.draw_lock:
            self.draw_rgb565_file(self.screens[0], left_file)
            time.sleep(0.05)
            self.draw_rgb565_file(self.screens[1], right_file)

    def narrowing_food_eyes(self):
        left_dir = "../eyes/eye_outputs/narrowing_food/left"
        right_dir = "../eyes/eye_outputs/narrowing_food/right"

        steps = [
            ("eyes_big_open_color_left.rgb565", "eyes_big_open_color_right.rgb565", 3),
            ("eyes_half_narrow_left.rgb565", "eyes_half_narrow_right.rgb565", 1.5),
            ("eyes_full_narrow_left.rgb565", "eyes_full_narrow_right.rgb565", 1.5),
            ("eyes_half_narrow_left.rgb565", "eyes_half_narrow_right.rgb565", 1.5),
            ("normal_blink_full_right.rgb565", "normal_blink_full_left.rgb565", 2),
        ]

        while not self.stop_eyes_event.is_set():
            for lf_name, rf_name, duration in steps:
                lf = os.path.join(left_dir, lf_name)
                rf = os.path.join(right_dir, rf_name)

                self.draw_both_screens(lf, rf)
                time.sleep(duration)

    def normal_blink_eyes(self):
        left_dir = "../eyes/eye_outputs/normal_blink/left"
        right_dir = "../eyes/eye_outputs/normal_blink/right"

        steps = [
            ("normal_blink_full_left.rgb565", "normal_blink_full_right.rgb565", 5),
            ("normal_blink_half_left.rgb565", "normal_blink_half_right.rgb565", 1.5),
            ("normal_blink_closed_left.rgb565", "normal_blink_closed_right.rgb565", 1.5),
            ("normal_blink_half_left.rgb565", "normal_blink_half_right.rgb565", 1.5),
        ]

        while not self.stop_eyes_event.is_set():
            for lf_name, rf_name, duration in steps:
                lf = os.path.join(left_dir, lf_name)
                rf = os.path.join(right_dir, rf_name)

                self.draw_both_screens(lf, rf)
                time.sleep(duration)


    def starry_eyes(self):
        left_dir = "../eyes/eye_outputs/starry/left"
        right_dir = "../eyes/eye_outputs/starry/right"

        left_file = os.path.join(left_dir, "normal_blink_full_left.rgb565")
        right_file = os.path.join(right_dir, "normal_blink_full_right.rgb565")
        self.draw_both_screens(left_file, right_file)
        time.sleep(2)

        steps = [
            ("eyes_half_color_small_star_left.rgb565", "eyes_half_color_small_star_right.rgb565", 1.5),
            ("eyes_half_color_large_star_stars_left.rgb565", "eyes_half_color_large_star_stars_right.rgb565", 1.5),
            ("eyes_half_color_small_circle_stars_left.rgb565", "eyes_half_color_small_circle_stars_right.rgb565", 1.5),
            ("normal_blink_full_right.rgb565", "normal_blink_full_left.rgb565", 1.5),
        ]


        while not self.stop_eyes_event.is_set():
            
            for lf_name, rf_name, duration in steps:
                lf = os.path.join(left_dir, lf_name)
                rf = os.path.join(right_dir, rf_name)

                self.draw_both_screens(lf, rf)
                time.sleep(duration)

    def side_to_side_eyes(self):
        left_dir = "../eyes/eye_outputs/side_to_side/left"
        right_dir = "../eyes/eye_outputs/side_to_side/right"

        steps = [
            ("normal_blink_full_left.rgb565", "normal_blink_full_right.rgb565", 3),
            ("eyes_half_sideways_left.rgb565", "eyes_half_sideways_right.rgb565", 2),
            ("eyes_full_sideways_left.rgb565", "eyes_full_sideways_right.rgb565", 2),
            ("eyes_half_sideways_left.rgb565", "eyes_half_sideways_right.rgb565", 2),
            ("normal_blink_full_left.rgb565", "normal_blink_full_right.rgb565", 2),
            ("eyes_half_sideways_left2.rgb565", "eyes_half_sideways_right2.rgb565", 2),
            ("eyes_full_sideways_left2.rgb565", "eyes_full_sideways_right2.rgb565", 2),
            ("eyes_half_sideways_left2.rgb565", "eyes_half_sideways_right2.rgb565", 2),
        ]

        while not self.stop_eyes_event.is_set():
            for lf_name, rf_name, duration in steps:
                lf = os.path.join(left_dir, lf_name)
                rf = os.path.join(right_dir, rf_name)

                self.draw_both_screens(lf, rf)
                time.sleep(duration)


    # SPEAKER FUNCTIONs
    def start_looping_sound(self, filename):
        filepath = os.path.join("../audio", filename)
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play(-1)  # loop forever

    def stop_sound(self):
        pygame.mixer.music.stop()

    def interval_audio(self, filenames, min_interval, max_interval):
        while not self.stop_interval_audio:
            # wait random or fixed interval
            wait_time = random.uniform(min_interval, max_interval)
            start = time.time()

            while time.time() - start < wait_time:
                if self.stop_interval_audio:
                    return
                time.sleep(0.05)

            if self.stop_interval_audio:
                return

            filename = random.choice(filenames)
            filepath = os.path.join("../audio", filename)

            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if self.stop_interval_audio:
                    pygame.mixer.music.stop()
                    return
                time.sleep(0.05)
    def start_interval_audio(self, filenames, min_interval, max_interval):
        self.stop_interval_audio = False
        threading.Thread(
            target=self.interval_audio,
            args=(filenames, min_interval, max_interval),
            daemon=True
        ).start()
        
    # MQTT FUNCTIONS

    def on_message(self, client, userdata, msg):
        text = msg.payload.decode() # convert bytes → string
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

    def set_state(self, state):
        if state == self.lastMsg:
            return

        # stop eyes + audio
        self.stop_eyes_event.set()
        self.stop_interval_audio = True
        self.stop_sound()

        # wait for draw in progress
        with self.draw_lock:
            pass

        # wait for eye thread to exit
        if self.eye_thread and self.eye_thread.is_alive():
            self.eye_thread.join(timeout=1.0)

        self.stop_eyes_event.clear()
        time.sleep(0.05)

        if state == "idle":
            self.eye_thread = threading.Thread(
                target=self.normal_blink_eyes,
                daemon=True
            )
            self.eye_thread.start()

            self.start_interval_audio(["idle_hehehehe.wav", 
                "idle_hmhmhm.wav", "idle_jaunty_song.wav", "idle_lalala_lalala.wav", 
                "idle_lala_lalala_laLA.wav", "idle_mountain_king.wav", "idle_oraawwrr.wav", 
                "idle_second_jaunty_song.wav", "idle_slightly_maniacle.wav"], 3,6)

        elif state == "hungry":
            self.eye_thread = threading.Thread(
                target=self.narrowing_food_eyes,
                daemon=True
            )
            self.eye_thread.start()

            self.start_interval_audio(["hungry_dsitraught.wav"], 5, 10)

        elif state == "eating":
            self.start_looping_sound("eating_omnomnom.wav")
            self.eye_thread = threading.Thread(
                target=self.starry_eyes,
                daemon=True
            )
            self.eye_thread.start()

        self.lastMsg = state
