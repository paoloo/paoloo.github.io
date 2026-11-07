"""Build a quiet, near-black CRT recording loop for the 1999 page.

Run with Python and Pillow. No downloaded textures or footage are used.
"""

from pathlib import Path
import random

from PIL import Image


DESTINATION = Path(__file__).resolve().parents[1] / "assets" / "1999"
WIDTH, HEIGHT = 640, 360
randomizer = random.Random(1999)
palette = [channel for value in range(256) for channel in (value, min(255, value + 1), value)]


def quiet_frame():
    pixels = bytearray(WIDTH * HEIGHT)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            # Dark phosphor and sparse grain; no repeating star/dot pattern.
            value = 7 if y % 3 == 0 else 8
            if randomizer.random() < 0.07:
                value += randomizer.choice((-1, 1, 2))
            pixels[y * WIDTH + x] = value
    return pixels


def tracking_frame(position, strength):
    pixels = quiet_frame()
    for y in range(position, min(HEIGHT, position + 32)):
        roll = 1 - abs(y - position - 16) / 17
        for x in range(WIDTH):
            pixels[y * WIDTH + x] += int(roll * strength * randomizer.uniform(0.1, 0.6))
    # Short, broken horizontal tears rather than a screen-wide flash.
    for offset in (3, 10, 23):
        y = min(HEIGHT - 1, position + offset)
        x_start = randomizer.randrange(10, WIDTH // 2)
        x_end = randomizer.randrange(WIDTH // 2, WIDTH - 10)
        for x in range(x_start, x_end):
            if randomizer.random() > 0.19:
                pixels[y * WIDTH + x] = randomizer.randrange(12, 12 + strength)
    return pixels


def frame(pixels):
    result = Image.frombytes("P", (WIDTH, HEIGHT), bytes(pixels))
    result.putpalette(palette)
    return result


def main():
    DESTINATION.mkdir(parents=True, exist_ok=True)
    still = frame(quiet_frame())
    frames = [
        still,
        frame(tracking_frame(76, 32)),
        frame(tracking_frame(91, 52)),
        frame(tracking_frame(107, 20)),
        frame(quiet_frame()),
        frame(tracking_frame(244, 44)),
        frame(tracking_frame(258, 26)),
        frame(quiet_frame()),
    ]
    durations = [4200, 100, 180, 180, 2800, 140, 180, 4800]
    still.save(DESTINATION / "crt-still.png", optimize=True)
    frames[0].save(
        DESTINATION / "crt-static.gif",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=1,
        optimize=True,
    )
    print(f"Created CRT loop: {sum(durations) / 1000:.2f}s, {len(frames)} frames")


if __name__ == "__main__":
    main()
