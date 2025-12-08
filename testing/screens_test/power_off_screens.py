import lgpio
import time

h = lgpio.gpiochip_open(0)

# screen pinout
screens = [
    {"cs": 5, "dc": 12, "rst": 16, "vccen": 17, "pmoden": 27},
    {"cs": 6, "dc": 13, "rst": 20, "vccen": 4,  "pmoden": 22}
]

# claim pins
for s in screens:
    lgpio.gpio_claim_output(h, s["cs"], 1)
    lgpio.gpio_claim_output(h, s["dc"], 1)
    lgpio.gpio_claim_output(h, s["rst"], 1)
    lgpio.gpio_claim_output(h, s["vccen"], 1)   # assume on
    lgpio.gpio_claim_output(h, s["pmoden"], 1)  # logic power

# send command helper
def send_cmd(s, cmd):
    lgpio.gpio_write(h, s["dc"], 0)
    lgpio.gpio_write(h, s["cs"], 0)
    time.sleep(0.000005)
    lgpio.gpio_write(h, s["cs"], 1)

# proper power-off sequence from datasheet
def shutdown_display(s):
    print(f"Shutting down screen with CS={s['cs']}")

    # 1. Send Display Off
    send_cmd(s, 0xAE)

    # 2. Turn off VCCEN 
    lgpio.gpio_write(h, s["vccen"], 0)

    # 3. Delay 100ms
    time.sleep(0.1)

    # 4. Turn off VCC 
    lgpio.gpio_write(h, s["pmoden"], 0)

# run shutdown on both displays
for scr in screens:
    shutdown_display(scr)

# cleanup
lgpio.gpiochip_close(h)

print("Displays powered off safely")
