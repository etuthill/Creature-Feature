# Data sheet instructions:
# Power-On Sequence:
#   1. Apply power to VCC
#   2. Send Display Off command
#   3. Initialize display to +
# default settings
#   4. Clear Screen
#   5. Apply power to VCCEN
#   6. Delay 100ms
#   7. Send Display On command
# Power-Off Sequence:
#   1. Send Display Off command
#   2. Power off VCCEN
#   3. Delay 100ms
#   4. Power off VCC

import spidev
import lgpio
import time
import os

# open GPIO chip (lgpio replacement for GPIO.setmode)
h = lgpio.gpiochip_open(0)

# screen pinout
screens = [
    {"cs": 5, "dc": 12, "rst": 16, "vccen": 17, "pmoden": 27},
    {"cs": 6, "dc": 13, "rst": 20, "vccen": 4, "pmoden": 22}
]

# setup GPIO pins
for s in screens:
    lgpio.gpio_claim_output(h, s["cs"], 1)  # CS idle high
    lgpio.gpio_claim_output(h, s["dc"], 0) # DC default low
    lgpio.gpio_claim_output(h, s["rst"], 1)  # Reset idle high
    lgpio.gpio_claim_output(h, s["vccen"], 0)  # VCCEN off
    lgpio.gpio_claim_output(h, s["pmoden"], 1)  # PMODEN on

# SPI setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000   # safe debug speed
spi.mode = 0

def send_cmd(s, cmd):
    lgpio.gpio_write(h, s["dc"], 0)
    lgpio.gpio_write(h, s["cs"], 0)
    spi.writebytes([cmd])
    lgpio.gpio_write(h, s["cs"], 1)

def send_data(s, data):
    lgpio.gpio_write(h, s["dc"], 1)
    lgpio.gpio_write(h, s["cs"], 0)

    CHUNK = 4096
    for i in range(0, len(data), CHUNK):
        spi.writebytes(list(data[i:i+CHUNK]))

    lgpio.gpio_write(h, s["cs"], 1)

# power-on sequence
def power_on_displays(s):

    # hardware reset
    lgpio.gpio_write(h, s["rst"], 0)
    time.sleep(0.05)
    lgpio.gpio_write(h, s["rst"], 1)
    time.sleep(0.05)

    # display OFF
    send_cmd(s, 0xAE)

    # command lock
    send_cmd(s, 0xFD)
    send_cmd(s, 0x12)

    # clock div
    send_cmd(s, 0xB3)
    send_cmd(s, 0xF1)

    # 64 rows
    send_cmd(s, 0xA8)
    send_cmd(s, 0x3F)

    # display offset = 0
    send_cmd(s, 0xA2)
    send_cmd(s, 0x00)

    # display start line = 0
    send_cmd(s, 0xA1)
    send_cmd(s, 0x00)

    # RGB565 color mode
    send_cmd(s, 0xA0)
    send_cmd(s, 0x74)

    # set column address range 0–95
    send_cmd(s, 0x15)
    send_cmd(s, 0x00)
    send_cmd(s, 0x5F)

    # set row address range 0–63
    send_cmd(s, 0x75)
    send_cmd(s, 0x00)
    send_cmd(s, 0x3F)

    # clear screen (send black)
    send_cmd(s, 0x5C)
    send_data(s, bytes(96 * 64 * 2))

    # enable power to panel
    lgpio.gpio_write(h, s["vccen"], 1)
    time.sleep(0.1)

    # display ON
    send_cmd(s, 0xAF)

def draw_rgb565_file(s, filename, bgr=False):
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
    send_cmd(s, 0x15)  # column
    send_cmd(s, 0)
    send_cmd(s, 95)
    send_cmd(s, 0x75)  # row
    send_cmd(s, 0)
    send_cmd(s, 63)
    send_cmd(s, 0x5C)  # write RAM

    fixed = bytearray(len(raw_pixels))

    for i in range(0, len(raw_pixels), 2):
        lo = raw_pixels[i]
        hi = raw_pixels[i + 1]
        fixed[i]     = hi  # send high byte first
        fixed[i + 1] = lo  # send low byte second

    send_data(s, fixed)



def shutdown_displays(s):
    send_cmd(s, 0xAE)
    lgpio.gpio_write(h, s["vccen"], 0)
    time.sleep(0.1)
    lgpio.gpio_write(h, s["pmoden"], 0)

# run
for scr in screens:
    power_on_displays(scr)

draw_rgb565_file(screens[0], "../eyes/eye_test_rgb565/left/blue.rgb565")
draw_rgb565_file(screens[1], "../eyes/eye_test_rgb565/right/normal_blink_full_right.rgb565")

time.sleep(10)

for scr in screens:
    shutdown_displays(scr)

lgpio.gpiochip_close(h)
