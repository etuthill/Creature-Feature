import spidev
import lgpio
import pygame
import random
import threading
import time
import os
import paho.mqtt.client as mqtt

class AudioScreenDrivers:
    """
    Handles screen drawing, eye animations, and audio playback for the machine.

    Attributes:
        client (mqtt.Client): MQTT client for receiving FSM state messages.
        msg (str): Current state message (initially "idle").
        lastMsg (str | None): Last processed state message to prevent repeats.
        h (int): GPIO chip handle from lgpio.
        screens (list[dict]): List of screen pinouts with keys cs, dc, rst, vccen, pmoden.
        stop_eyes_event (threading.Event): Event to stop eye animation threads.
        eye_thread (threading.Thread | None): Thread currently running eye animation.
        stop_interval_audio (bool): Flag to stop interval-based audio playback.
        spi_lock (threading.Lock): Lock to protect SPI bus access.
        draw_lock (threading.Lock): Lock to protect full-frame screen drawing.
    """

    def __init__(self):
        """
        Init SPI, GPIO, MQTT, and audio systems for screens and speakers.
        Sets up locks and threading control (aaaa screens corruption).
        """
        # MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost")
        self.client.loop_start()

        self.msg = "idle"
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
        self.spi_lock = threading.Lock()  # protects SPI bus
        self.draw_lock = threading.Lock()  # protects full frame draws

        # setup GPIO pins
        for s in self.screens:
            lgpio.gpio_claim_output(self.h, s["cs"], 1)  # CS idle high
            lgpio.gpio_claim_output(self.h, s["dc"], 0)  # DC default low
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

        for s in self.screens:
            self.power_on_displays(s)
            print("Screens powered on")

    # SCREEN FUNCTIONS
    def send_cmd(self, s: dict, cmd: int):
        """
        Send a command byte to a screen.

        Args:
            s (dict): Screen pin dictionary with keys cs and dc.
            cmd (int): Command byte to send.
        """
        with self.spi_lock:
            lgpio.gpio_write(self.h, s["dc"], 0)
            lgpio.gpio_write(self.h, s["cs"], 0)
            self.spi.writebytes([cmd])
            lgpio.gpio_write(self.h, s["cs"], 1)

    def send_data(self, s: dict, data: bytes):
        """
        Send a data buffer to a screen.

        Args:
            s (dict): Screen pin dictionary with keys cs and dc.
            data (bytes): Byte array of pixel data to send.
        """
        with self.spi_lock:
            lgpio.gpio_write(self.h, s["dc"], 1)
            lgpio.gpio_write(self.h, s["cs"], 0)

            CHUNK = 4096
            for i in range(0, len(data), CHUNK):
                self.spi.writebytes(data[i:i+CHUNK])

            lgpio.gpio_write(self.h, s["cs"], 1)

    def power_on_displays(self, s: dict):
        """
        Power on a screen with reset sequence, set address ranges, and enable RGB565 mode.
        Basically drivers aaaaa.

        Args:
            s (dict): Screen pin dictionary with keys cs, dc, rst, vccen, pmoden.
        """
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

    def draw_rgb565_file(self, s: dict, filename: str, bgr: bool = False):
        """
        Draw RGB565 image file to one screen.

        Args:
            s (dict): Screen pin dictionary with keys cs and dc.
            filename (str): Path to .rgb565 file.
            bgr (bool): Whether to swap R/B channels (default False).
        """
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

    def shutdown_all_displays(self):
        """
        Safely power off all displays and GPIO pins based on datasheet.
        """
        print("Shutting down displays safely")

        for s in self.screens:
            try:
                # display OFF
                self.send_cmd(s, 0xAE)

                # panel power off
                lgpio.gpio_write(self.h, s["vccen"], 0)
                time.sleep(0.1)

                # logic power off
                lgpio.gpio_write(self.h, s["pmoden"], 0)

            except Exception as e:
                print("Shutdown error:", e)

        try:
            lgpio.gpiochip_close(self.h)
        except:
            pass

    def draw_both_screens(self, left_file: str, right_file: str):
        """
        Draw two screens with thread-safe locking (prevent corruption).

        Args:
            left_file (str): Left screen RGB565 file.
            right_file (str): Right screen RGB565 file.
        """
        with self.draw_lock:
            self.draw_rgb565_file(self.screens[0], left_file)
            time.sleep(0.05)
            self.draw_rgb565_file(self.screens[1], right_file)

        #EYE ANIMATION

    def narrowing_food_eyes(self):
        """
        Animate the eyes narrowing to indicate hunger.
        """
        left_dir = "../eyes/eye_outputs/narrowing_food/left"
        right_dir = "../eyes/eye_outputs/narrowing_food/right"

        # run intro sequence once
        intro_steps = [
            ("eyes_big_open_color_left.rgb565", "eyes_big_open_color_right.rgb565", 0.5),
            ("eyes_half_narrow_left.rgb565", "eyes_half_narrow_right.rgb565", 0.6),
            ("eyes_full_narrow_left.rgb565", "eyes_full_narrow_right.rgb565", 0.8),
        ]

        # hungry stare loop
        loop_steps = [
            ("eyes_full_narrow_left.rgb565", "eyes_full_narrow_right.rgb565", 5),
            ("normal_blink_closed_left.rgb565", "normal_blink_closed_right.rgb565", 0.5),
        ]

        for lf_name, rf_name, duration in intro_steps:
            if self.stop_eyes_event.is_set():
                return
            self.draw_both_screens(os.path.join(left_dir, lf_name),
                                   os.path.join(right_dir, rf_name))
            if not self.sleep_or_stop(duration):
                return

        while not self.stop_eyes_event.is_set():
            for lf_name, rf_name, duration in loop_steps:
                if self.stop_eyes_event.is_set():
                    return
                self.draw_both_screens(os.path.join(left_dir, lf_name),
                                       os.path.join(right_dir, rf_name))
                if not self.sleep_or_stop(duration):
                    return

    def normal_blink_eyes(self):
        """
        Animate normal blinking eyes for idle state.
        """
        left_dir = "../eyes/eye_outputs/normal_blink/left"
        right_dir = "../eyes/eye_outputs/normal_blink/right"

        steps = [
            ("normal_blink_full_left.rgb565", "normal_blink_full_right.rgb565", 5),
            ("normal_blink_half_left.rgb565", "normal_blink_half_right.rgb565", 0.75),
            ("normal_blink_closed_left.rgb565", "normal_blink_closed_right.rgb565", 0.75),
            ("normal_blink_half_left.rgb565", "normal_blink_half_right.rgb565", 0.75),
        ]

        while not self.stop_eyes_event.is_set():
            for lf_name, rf_name, duration in steps:
                if self.stop_eyes_event.is_set():
                    return
                self.draw_both_screens(os.path.join(left_dir, lf_name),
                                       os.path.join(right_dir, rf_name))
                if not self.sleep_or_stop(duration):
                    return

    def starry_eyes(self):
        """
        Animate starry eyes for eating or playful states.
        """
        left_dir = "../eyes/eye_outputs/starry/left"
        right_dir = "../eyes/eye_outputs/starry/right"

        # intro frame
        self.draw_both_screens(os.path.join(right_dir, "eyes_half_color_small_star_right.rgb565"),
                               os.path.join(left_dir, "eyes_half_color_small_star_left.rgb565"))
        if not self.sleep_or_stop(2):
            return

        steps = [
            ("eyes_half_color_small_star_left.rgb565", "eyes_half_color_small_star_right.rgb565", 1.5),
            ("eyes_half_color_large_star_stars_left.rgb565", "eyes_half_color_large_star_stars_right.rgb565", 1.5),
            ("eyes_half_color_small_circle_stars_left.rgb565", "eyes_half_color_small_circle_stars_right.rgb565", 1.5),
        ]

        while not self.stop_eyes_event.is_set():
            for lf_name, rf_name, duration in steps:
                if self.stop_eyes_event.is_set():
                    return
                # swap left and right because aaah it's backward for unknown reason
                self.draw_both_screens(os.path.join(right_dir, rf_name),
                                       os.path.join(left_dir, lf_name))
                if not self.sleep_or_stop(duration):
                    return

    def side_to_side_eyes(self):
        """
        Animate eyes looking side-to-side for boredom state.
        """
        left_dir = "../eyes/eye_outputs/side_to_side/left"
        right_dir = "../eyes/eye_outputs/side_to_side/right"

        steps = [
            ("normal_blink_full_left.rgb565", "normal_blink_full_right.rgb565", 3),
            ("eyes_half_sideways_left.rgb565", "eyes_half_sideways_right.rgb565", 2),
            ("eyes_full_sideways_left.rgb565", "eyes_full_sideways_right.rgb565", 2),
            ("eyes_half_sideways_left.rgb565", "eyes_half_sideways_right.rgb565", 2),
            ("normal_blink_full_left.rgb565", "normal_blink_full_right.rgb565", 2),
            ("eyes_half_sideways_left_2.rgb565", "eyes_half_sideways_right_2.rgb565", 2),
            ("eyes_full_sideways_left_2.rgb565", "eyes_full_sideways_right_2.rgb565", 2),
            ("eyes_half_sideways_left_2.rgb565", "eyes_half_sideways_right_2.rgb565", 2),
        ]

        while not self.stop_eyes_event.is_set():
            for lf_name, rf_name, duration in steps:
                if self.stop_eyes_event.is_set():
                    return
                self.draw_both_screens(os.path.join(left_dir, lf_name),
                                       os.path.join(right_dir, rf_name))
                if not self.sleep_or_stop(duration):
                    return

    # SLEEP

    def sleep_or_stop(self, duration: float, check_interval: float = 0.05) -> bool:
        """
        Sleep for duration seconds, but wake early if stop_eyes_event is set.

        Args:
            duration (float): Total seconds to sleep.
            check_interval (float): Interval to check stop condition.

        Returns:
            bool: True if full duration elapsed, False if stopped early.
        """
        start = time.time()
        while time.time() - start < duration:
            if self.stop_eyes_event.is_set():
                return False
            time.sleep(check_interval)
        return True

    # AUDIO

    def start_looping_sound(self, filename: str):
        """
        Play a sound in an infinite loop.

        Args:
            filename (str): Name of audio file.
        """
        filepath = os.path.join("../audio", filename)
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play(-1)

    def stop_sound(self):
        """Stop any currently playing sound."""
        pygame.mixer.music.stop()

    def interval_audio(self, filenames: list[str], min_interval: float, max_interval: float):
        """
        Play random sounds from a list at random intervals.

        Args:
            filenames (list[str]): List of filenames in '../audio/'.
            min_interval (float): Minimum wait time between sounds.
            max_interval (float): Maximum wait time between sounds.
        """
        while not self.stop_interval_audio:
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

    def start_interval_audio(self, filenames: list[str], min_interval: float, max_interval: float):
        """
        Start a background thread to play interval audio.

        Args:
            filenames (list[str]): List of audio filenames.
            min_interval (float): Minimum interval.
            max_interval (float): Maximum interval.
        """
        self.stop_interval_audio = False
        threading.Thread(
            target=self.interval_audio,
            args=(filenames, min_interval, max_interval),
            daemon=True
        ).start()

    # MQTT

    def on_message(self, client, userdata, msg):
        fsm_state = msg.payload.decode()

        # FSM to behavior mapping
        if fsm_state == "machineIdle":
            self.set_state("idle")

        elif fsm_state in ("sensingH",):
            self.set_state("hungry")

        elif fsm_state in ("sensingF",):
            self.set_state("boredom")

        elif fsm_state == "sensing":
            self.set_state("idle")

        elif fsm_state == "reactingF":
            self.set_state("eating")

        elif fsm_state == "reactingP":
            self.set_state("playing")

        elif fsm_state == "RESET":
            self.set_state("RESET")

    def on_connect(self, client, userdata, flags, rc):
        """
        MQTT callback when client connects.

        Subscribes to 'state/text'.
        """
        client.subscribe("state/text")
        print("Connected and subscribed.")

    def set_state(self, state: str):
        """
        Change the system state and update eye animations and audio.

        Args:
            state (str): State string (idle, hungry, eating, boredom, etc.)
        """
        if state == self.lastMsg:
            return

        # stop current animations and audio
        self.stop_eyes_event.set()
        self.stop_interval_audio = True
        self.stop_sound()

        # wait for ongoing draw to finish
        with self.draw_lock:
            pass

        # wait for eye thread to exit
        if self.eye_thread and self.eye_thread.is_alive():
            self.eye_thread.join(timeout=1.0)

        self.stop_eyes_event.clear()
        time.sleep(0.05)

        #s new animation and audio based on state
        if state == "idle":
            self.eye_thread = threading.Thread(target=self.normal_blink_eyes, daemon=True)
            self.eye_thread.start()
            self.start_interval_audio(["idle_hehehehe.wav", "idle_hmhmhm.wav", "idle_jaunty_song.wav",
                "idle_lalala_lalala.wav", "idle_lala_lalala_laLA.wav",
                "idle_mountain_king.wav", "idle_oraawrr.wav", "idle_second_jaunty_song.wav",
                "idle_slightly_maniacle.wav", "hehehewav.wav"], 3, 6)

        elif state == "hungry":
            self.eye_thread = threading.Thread(target=self.narrowing_food_eyes, daemon=True)
            self.eye_thread.start()
            self.start_interval_audio(["hungry_dsitraught.wav"], 5, 10)

        elif state == "eating":
            self.start_looping_sound("eating_omnomnom.wav")
            self.eye_thread = threading.Thread(target=self.starry_eyes, daemon=True)
            self.eye_thread.start()

        elif state == "boredom":
            self.eye_thread = threading.Thread(target=self.side_to_side_eyes, daemon=True)
            self.eye_thread.start()
            self.start_interval_audio(["bored_mm_mm.wav", "bored_nnnnnaa.wav"], 3, 6)

        elif state == "boredom_hungry":
            self.eye_thread = threading.Thread(target=self.narrowing_food_eyes, daemon=True)
            self.eye_thread.start()
            self.start_interval_audio(["bored_mm_mm.wav", "bored_nnnnnaa.wav", "hungry_dsitraught.wav"], 3, 6)

        elif state == "playing":
            self.eye_thread = threading.Thread(target=self.starry_eyes, daemon=True)
            self.eye_thread.start()
            self.start_interval_audio(["waAaAa.wav", "wah_wah_wah.wav", "waowaowaoooo.wav", "waow.wav", "wOoOoOw.wav"], 2, 5)

        elif state == "RESET":
            self.eye_thread = threading.Thread(target=self.normal_blink_eyes, daemon=True)
            self.eye_thread.start()
            self.start_interval_audio(["idle_hehehehe.wav", "idle_hmhmhm.wav", "idle_jaunty_song.wav",
                "idle_lalala_lalala.wav", "idle_lala_lalala_laLA.wav",
                "idle_mountain_king.wav", "idle_oraawrr.wav", "idle_second_jaunty_song.wav",
                "idle_slightly_maniacle.wav", "hehehewav.wav"], 3, 6)

        self.lastMsg = state
