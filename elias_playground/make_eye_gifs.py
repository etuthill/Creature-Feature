import os
import sys
from PIL import Image
import numpy as np


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EYES_DIR = os.path.join(BASE_DIR, "..", "eyes", "eye_outputs")

GIF_DIR = os.path.join(BASE_DIR, "..", "gifs")
os.makedirs(GIF_DIR, exist_ok=True)

WIDTH = 64
HEIGHT = 96

def rgb565_file_to_image(path):
    with open(path, "rb") as f:
        raw = f.read()

    if len(raw) != 4 + WIDTH * HEIGHT * 2:
        raise ValueError(f"Bad RGB565 size: {path}")

    raw = raw[4:]  # skip header

    data = np.frombuffer(raw, dtype=np.uint16)
    data = data.reshape((WIDTH, HEIGHT)).T  

    r = (data >> 11) & 0x1F
    g = (data >> 5) & 0x3F
    b = data & 0x1F

    r <<= 3
    g <<= 2
    b <<= 3

    img = np.dstack((r, g, b)).astype(np.uint8)
    img = Image.fromarray(img, "RGB")

    # flip and mirror guh
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img = img.transpose(Image.FLIP_LEFT_RIGHT)

    return img





def make_eye_gif(steps, left_dir, right_dir, out_name):
    frames = []
    durations = []

    for lf, rf, duration in steps:
        left = rgb565_file_to_image(os.path.join(left_dir, lf))
        right = rgb565_file_to_image(os.path.join(right_dir, rf))

        combined = Image.new("RGB", (WIDTH * 2, HEIGHT))
        combined.paste(left, (0, 0))
        combined.paste(right, (WIDTH, 0))

        frames.append(combined)
        durations.append(int(duration * 1000))

    out_path = os.path.join(GIF_DIR, out_name)
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0
    )

    print("Wrote:", out_path)



def gif_narrowing_food():
    left = os.path.join(EYES_DIR, "narrowing_food", "left")
    right = os.path.join(EYES_DIR, "narrowing_food", "right")

    intro = [
        ("eyes_big_open_color_left.rgb565", "eyes_big_open_color_right.rgb565", 0.5),
        ("eyes_half_narrow_left.rgb565", "eyes_half_narrow_right.rgb565", 0.6),
        ("eyes_full_narrow_left.rgb565", "eyes_full_narrow_right.rgb565", 0.8),
    ]

    loop = [
        ("eyes_full_narrow_left.rgb565", "eyes_full_narrow_right.rgb565", 5),
        ("normal_blink_closed_left.rgb565", "normal_blink_closed_right.rgb565", 0.5),
    ]

    make_eye_gif(intro + loop * 2, left, right, "narrowing_food.gif")


def gif_normal_blink():
    left = os.path.join(EYES_DIR, "normal_blink", "left")
    right = os.path.join(EYES_DIR, "normal_blink", "right")

    steps = [
        ("normal_blink_full_left.rgb565", "normal_blink_full_right.rgb565", 5),
        ("normal_blink_half_left.rgb565", "normal_blink_half_right.rgb565", 0.75),
        ("normal_blink_closed_left.rgb565", "normal_blink_closed_right.rgb565", 0.75),
        ("normal_blink_half_left.rgb565", "normal_blink_half_right.rgb565", 0.75),
    ]

    make_eye_gif(steps * 2, left, right, "normal_blink.gif")


def gif_starry():
    left_dir = os.path.join(EYES_DIR, "starry", "left")
    right_dir = os.path.join(EYES_DIR, "starry", "right")

    steps = [
        ("eyes_half_color_small_star_right.rgb565",
         "eyes_half_color_small_star_left.rgb565", 1.5),

        ("eyes_half_color_large_star_stars_right.rgb565",
         "eyes_half_color_large_star_stars_left.rgb565", 1.5),

        ("eyes_half_color_small_circle_stars_right.rgb565",
         "eyes_half_color_small_circle_stars_left.rgb565", 1.5),
    ]

    make_eye_gif(steps * 2, right_dir, left_dir, "starry.gif")



if __name__ == "__main__":
    gif_narrowing_food()
    gif_normal_blink()
    gif_starry()
