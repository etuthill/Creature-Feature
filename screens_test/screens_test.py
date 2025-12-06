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
    {"cs": 6, "dc": 13, "rst": 20, "vccen": 4,"pmoden": 22}
]

# setup GPIO pins
for s in screens:
    lgpio.gpio_claim_output(h, s["cs"], 1)  
    lgpio.gpio_claim_output(h, s["dc"], 1)
    lgpio.gpio_claim_output(h, s["rst"], 1)
    lgpio.gpio_claim_output(h, s["vccen"], 0)
    lgpio.gpio_claim_output(h, s["pmoden"], 0)

# SPI setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 7000000
spi.mode = 0

def send_cmd(s, cmd):
    lgpio.gpio_write(h, s["dc"], 0)   # GPIO.output(s["dc"], GPIO.LOW)
    lgpio.gpio_write(h, s["cs"], 0)
    spi.writebytes([cmd])
    lgpio.gpio_write(h, s["cs"], 1)

def send_data(s, data):
    lgpio.gpio_write(h, s["dc"], 1)   # GPIO.output(s["dc"], GPIO.HIGH)
    lgpio.gpio_write(h, s["cs"], 0)

    CHUNK = 4096
    if isinstance(data, bytes):
        for i in range(0, len(data), CHUNK):
            spi.writebytes(list(data[i:i+CHUNK]))
    else:
        for i in range(0, len(data), CHUNK):
            spi.writebytes(data[i:i+CHUNK])

    lgpio.gpio_write(h, s["cs"], 1)

# power-on sequence
def power_on_displays(s):

    # 1. Apply power to VCC
    lgpio.gpio_write(h, s["pmoden"], 1)   # logic power only
    time.sleep(0.05)

    # hardware reset
    lgpio.gpio_write(h, s["rst"], 0)
    time.sleep(0.05)
    lgpio.gpio_write(h, s["rst"], 1)
    time.sleep(0.05)

    # 2. Send Display Off Command
    send_cmd(s, 0xAE)

    # 3. Initialize display default settings
    send_cmd(s, 0xFD)
    send_cmd(s, 0x12)

    send_cmd(s, 0xB3)
    send_cmd(s, 0xF0)

    send_cmd(s, 0xA8)
    send_cmd(s, 0x3F)

    send_cmd(s, 0xA2)
    send_cmd(s, 0x00)

    send_cmd(s, 0xA1)
    send_cmd(s, 0x00)

    send_cmd(s, 0xA0)
    send_cmd(s, 0x72)

    # set window before clearing ram
    send_cmd(s, 0x75)
    send_cmd(s, 0x00)
    send_cmd(s, 0x3F)

    send_cmd(s, 0x15)
    send_cmd(s, 0x00)
    send_cmd(s, 0x5F)

    send_cmd(s, 0xAD)
    send_cmd(s, 0x8E)

    send_cmd(s, 0xB1)
    send_cmd(s, 0x31)

    # 4. Clear Screen 
    send_cmd(s, 0x25)   # clear / fill rectangle
    send_cmd(s, 0)      # x0
    send_cmd(s, 0)      # y0
    send_cmd(s, 95)     # x1
    send_cmd(s, 63)     # y1
    send_cmd(s, 0)      # outline R
    send_cmd(s, 0)      # outline G
    send_cmd(s, 0)      # outline B
    send_cmd(s, 0)      # fill R
    send_cmd(s, 0)      # fill G
    send_cmd(s, 0)      # fill B

    # 5. Apply power to VCCEN
    lgpio.gpio_write(h, s["vccen"], 1)

    # 6. Delay 100ms
    time.sleep(0.1)

    # 7. Display ON
    send_cmd(s, 0xAF)

def draw_rgb565_file(s, filename):
    if not os.path.exists(filename):
        print("File not found:", filename)
        return

    with open(filename, "rb") as f:
        raw = f.read()

    if len(raw) != 4 + 96 * 64 * 2:
        print("File is wrong size:", len(raw))
        return

    # skip 4-byte header
    raw_pixels = raw[4:]

    send_cmd(s, 0x15)
    send_cmd(s, 0)
    send_cmd(s, 95)

    send_cmd(s, 0x75)
    send_cmd(s, 0)
    send_cmd(s, 63)

    send_cmd(s, 0x5C)

    out = bytearray()
    append = out.extend
    for i in range(0, len(raw_pixels), 2):
        hi = raw_pixels[i] # high byte of RGB565 pixel
        lo = raw_pixels[i+1] # low byte of RGB565 pixel
        pixel = (hi << 8) | lo # combine into a 16-bit integer

        # 5-bit red, 6-bit green, 5-bit blue components from RGB565
        r5 = (pixel >> 11) & 0x1F
        g6 = (pixel >> 5)  & 0x3F
        b5 =  pixel        & 0x1F

        # convert RGB565 to full-range 8-bit RGB
        r8 = (r5 * 527 + 23) >> 6
        g8 = (g6 * 259 + 33) >> 6
        b8 = (b5 * 527 + 23) >> 6

        # append resulting RGB888 pixel to output buffer
        append(bytes((r8, g8, b8)))

    send_data(s, out)

# Power-Off Sequence:
def shutdown_displays(s):
    #   1. Send Display Off command
    send_cmd(s, 0xAE)
    #   2. Power off VCCEN
    lgpio.gpio_write(h, s["vccen"], 0)
    #   3. Delay 100ms
    time.sleep(0.1)
    #   4. Power off VCC
    lgpio.gpio_write(h, s["pmoden"], 0)

# run init
for scr in screens:
    power_on_displays(scr)

# show images on both screens
draw_rgb565_file(screens[0], "eye_test_rgb565/left/normal_blink_closed_left.rgb565")
draw_rgb565_file(screens[1], "eye_test_rgb565/right/normal_blink_closed_right.rgb565")

time.sleep(10)  # display for 10 seconds

# shutdown both screens
for scr in screens:
    shutdown_displays(scr)

# lgpio cleanup 
lgpio.gpiochip_close(h)
