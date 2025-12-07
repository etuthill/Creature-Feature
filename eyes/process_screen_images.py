import os
from PIL import Image

TARGET_WIDTH = 96
TARGET_HEIGHT = 64

INPUT_RIGHT = "animations/normal_blink/right_side"
INPUT_LEFT = "animations/normal_blink/left_side"

OUTPUT_BASE = "eye_test_rgb565"
OUTPUT_RIGHT = os.path.join(OUTPUT_BASE, "right")
OUTPUT_LEFT = os.path.join(OUTPUT_BASE, "left")


def rgb888_to_rgb565(r, g, b):
    """Convert 8-bit RGB to 16-bit RGB565."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def process_image(path, out_path):
    img = Image.open(path).convert("RGB")

    # resize to target dimensions
    img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.NEAREST)

    width, height = img.size
    pixels = img.load()

    with open(out_path, "wb") as f:
        # 4-byte header: width, height 
        f.write(width.to_bytes(2, "little"))
        f.write(height.to_bytes(2, "little"))

        # row-major pixel order
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                rgb565 = rgb888_to_rgb565(r, g, b)
                f.write(rgb565.to_bytes(2, "little"))


def process_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
            in_path = os.path.join(input_folder, filename)
            out_path = os.path.join(
                output_folder, os.path.splitext(filename)[0] + ".rgb565"
            )
            print(f"Processing {filename} → {out_path}")
            process_image(in_path, out_path)


def main():
    if not os.path.exists(OUTPUT_BASE):
        os.makedirs(OUTPUT_BASE)

    process_folder(INPUT_RIGHT, OUTPUT_RIGHT)
    process_folder(INPUT_LEFT, OUTPUT_LEFT)


if __name__ == "__main__":
    main()