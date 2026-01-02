#!/usr/bin/env python3
"""
D72N Display Test - VISIBLE OUTPUT
===================================

Write directly to the D72N display buffer via SERDB.
This produces IMMEDIATE VISIBLE OUTPUT on the LCD panel.

Traced from firmware:
  - Display output buffer: 0x150000 (384 refs in AEON)
  - Screen: 480x234 pixels
  - Format: RGB565 (16-bit, 2 bytes per pixel)

The 0x150000 buffer is the FINAL output stage that feeds the panel.
Writing here bypasses all decode/scaling and shows immediately.

Attack demonstration:
  1. Connect via SERDB (I2C 0x59)
  2. Write pattern to 0x150000
  3. Pattern appears on screen IMMEDIATELY

Usage:
    # Linux
    python d72n_display_test.py /dev/i2c-1 --red-screen
    python d72n_display_test.py /dev/i2c-1 --stripe
    python d72n_display_test.py /dev/i2c-1 --marker "PWNED"

    # Windows (FTDI)
    python d72n_display_test.py ftdi://ftdi:232h/1 --red-screen

    # Simulation
    python d72n_display_test.py sim:// --red-screen
"""

import argparse
import sys
import time

# Import from our SERDB library
try:
    from d72n_serdb import D72N_SERDB, D72N_ADDR
except ImportError:
    # If run standalone, provide minimal implementation
    print("Note: Run from DPF-D72N/tools/ directory for full functionality")
    sys.exit(1)


# Display parameters (traced from firmware)
DISPLAY_WIDTH = 480
DISPLAY_HEIGHT = 234
DISPLAY_BPP = 16  # RGB565
DISPLAY_BUFFER = 0x150000  # Output buffer (384 refs in AEON)

# RGB565 colors
RGB565_RED = 0xF800
RGB565_GREEN = 0x07E0
RGB565_BLUE = 0x001F
RGB565_WHITE = 0xFFFF
RGB565_BLACK = 0x0000
RGB565_YELLOW = 0xFFE0
RGB565_CYAN = 0x07FF
RGB565_MAGENTA = 0xF81F


def rgb_to_565(r, g, b):
    """Convert 8-bit RGB to RGB565"""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def write_pixel(serdb, x, y, color):
    """Write a single RGB565 pixel to display buffer"""
    if x < 0 or x >= DISPLAY_WIDTH or y < 0 or y >= DISPLAY_HEIGHT:
        return

    offset = (y * DISPLAY_WIDTH + x) * 2  # 2 bytes per pixel
    addr = DISPLAY_BUFFER + offset

    # Write low byte first, then high byte (little-endian)
    serdb.write_dram(addr, color & 0xFF)
    serdb.write_dram(addr + 1, (color >> 8) & 0xFF)


def fill_rect(serdb, x, y, width, height, color, progress=False):
    """Fill a rectangle with solid color"""
    total = width * height
    count = 0

    for py in range(y, y + height):
        for px in range(x, x + width):
            write_pixel(serdb, px, py, color)
            count += 1
            if progress and count % 1000 == 0:
                pct = (count * 100) // total
                print(f"\rWriting: {pct}%", end='', flush=True)

    if progress:
        print("\rWriting: 100%")


def draw_text_5x7(serdb, x, y, text, color, bg_color=None):
    """Draw text using simple 5x7 font

    Only supports uppercase A-Z and some symbols.
    Each character is 6 pixels wide (5 + 1 space).
    """
    # Simple 5x7 font data (uppercase only)
    font = {
        'A': [0x7C, 0x12, 0x11, 0x12, 0x7C],
        'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
        'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
        'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
        'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
        'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
        'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
        'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
        'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
        'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
        'N': [0x7F, 0x02, 0x0C, 0x10, 0x7F],
        'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
        'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
        'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
        'S': [0x46, 0x49, 0x49, 0x49, 0x31],
        'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
        'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
        'W': [0x3F, 0x40, 0x38, 0x40, 0x3F],
        'X': [0x63, 0x14, 0x08, 0x14, 0x63],
        'Y': [0x07, 0x08, 0x70, 0x08, 0x07],
        '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
        ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
        '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
        '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
        '2': [0x42, 0x61, 0x51, 0x49, 0x46],
        '7': [0x01, 0x71, 0x09, 0x05, 0x03],
        'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
    }

    cx = x
    for char in text.upper():
        if char in font:
            cols = font[char]
            for col_idx, col in enumerate(cols):
                for row in range(7):
                    if col & (1 << row):
                        write_pixel(serdb, cx + col_idx, y + row, color)
                    elif bg_color is not None:
                        write_pixel(serdb, cx + col_idx, y + row, bg_color)
            cx += 6  # 5 pixels + 1 space
        else:
            cx += 6  # Unknown char = space


def red_screen(serdb):
    """Fill entire screen with red - most visible test"""
    print("[*] Filling screen with RED...")
    print(f"    Buffer: 0x{DISPLAY_BUFFER:06X}")
    print(f"    Size: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")

    # Write RED (0xF800) to every pixel
    # For speed, write in chunks
    bytes_per_row = DISPLAY_WIDTH * 2
    total_bytes = bytes_per_row * DISPLAY_HEIGHT

    print(f"    Total: {total_bytes} bytes ({total_bytes//1024}KB)")
    print()

    # Red in RGB565 = 0xF800 = bytes [0x00, 0xF8]
    for row in range(DISPLAY_HEIGHT):
        for col in range(DISPLAY_WIDTH):
            offset = (row * DISPLAY_WIDTH + col) * 2
            addr = DISPLAY_BUFFER + offset
            serdb.write_dram(addr, 0x00)      # Low byte
            serdb.write_dram(addr + 1, 0xF8)  # High byte (red)

        pct = ((row + 1) * 100) // DISPLAY_HEIGHT
        print(f"\rProgress: {pct}% (row {row+1}/{DISPLAY_HEIGHT})", end='', flush=True)

    print("\n[+] Screen should now be RED")


def color_stripes(serdb):
    """Draw color stripes - tests full color range"""
    print("[*] Drawing color stripes...")

    colors = [
        ("Red", RGB565_RED),
        ("Green", RGB565_GREEN),
        ("Blue", RGB565_BLUE),
        ("Yellow", RGB565_YELLOW),
        ("Cyan", RGB565_CYAN),
        ("Magenta", RGB565_MAGENTA),
        ("White", RGB565_WHITE),
        ("Black", RGB565_BLACK),
    ]

    stripe_height = DISPLAY_HEIGHT // len(colors)

    for i, (name, color) in enumerate(colors):
        y = i * stripe_height
        height = stripe_height if i < len(colors) - 1 else DISPLAY_HEIGHT - y
        print(f"    {name}: y={y}, height={height}")
        fill_rect(serdb, 0, y, DISPLAY_WIDTH, height, color)

    print("[+] Stripes should be visible")


def draw_marker(serdb, text="D72N"):
    """Draw text marker in center of screen"""
    print(f"[*] Drawing marker: {text}")

    # Calculate center position
    text_width = len(text) * 6  # 6 pixels per char
    text_height = 7
    x = (DISPLAY_WIDTH - text_width) // 2
    y = (DISPLAY_HEIGHT - text_height) // 2

    # Draw background box
    pad = 10
    fill_rect(serdb, x - pad, y - pad, text_width + 2*pad, text_height + 2*pad, RGB565_BLACK)

    # Draw text
    draw_text_5x7(serdb, x, y, text, RGB565_RED)

    print(f"[+] Marker drawn at ({x}, {y})")


def quick_test(serdb):
    """Quick test - write small pattern to top-left corner"""
    print("[*] Quick test - writing 10x10 red square to top-left...")

    for y in range(10):
        for x in range(10):
            write_pixel(serdb, x, y, RGB565_RED)

    print("[+] Red square should appear at top-left corner")


def verify_buffer(serdb, count=32):
    """Read back display buffer to verify writes"""
    print(f"[*] Reading {count} bytes from display buffer...")

    data = []
    for i in range(count):
        data.append(serdb.read_dram(DISPLAY_BUFFER + i))

    print(f"    Address: 0x{DISPLAY_BUFFER:06X}")
    print("    Data: " + ' '.join(f'{b:02X}' for b in data))

    return bytes(data)


def main():
    parser = argparse.ArgumentParser(
        description='D72N Display Test - Write directly to screen',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script writes directly to the D72N display buffer at 0x150000.
Changes appear IMMEDIATELY on the LCD panel.

Examples:
    # Fill screen with red (most visible test)
    python d72n_display_test.py /dev/i2c-1 --red-screen

    # Draw color stripes
    python d72n_display_test.py /dev/i2c-1 --stripe

    # Draw text marker
    python d72n_display_test.py /dev/i2c-1 --marker "PWNED"

    # Quick 10x10 test square
    python d72n_display_test.py /dev/i2c-1 --quick

    # Windows with FTDI adapter
    python d72n_display_test.py ftdi://ftdi:232h/1 --red-screen

Display Buffer:
    Address: 0x150000 (traced, 384 refs in AEON)
    Size: 480 x 234 pixels
    Format: RGB565 (16-bit, little-endian)

This is the FINAL output buffer that feeds the LCD panel.
        """
    )

    parser.add_argument('bus', help='I2C bus (/dev/i2c-1, ftdi://..., sim://)')

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--red-screen', '-r', action='store_true',
                      help='Fill entire screen with red')
    mode.add_argument('--stripe', '-s', action='store_true',
                      help='Draw color stripes')
    mode.add_argument('--marker', '-m', metavar='TEXT',
                      help='Draw text marker on screen')
    mode.add_argument('--quick', '-q', action='store_true',
                      help='Quick 10x10 test square')
    mode.add_argument('--verify', '-v', action='store_true',
                      help='Read and display buffer contents')

    args = parser.parse_args()

    try:
        print("=" * 60)
        print("D72N Display Test")
        print("=" * 60)
        print(f"Bus: {args.bus}")
        print(f"Display buffer: 0x{DISPLAY_BUFFER:06X}")
        print(f"Resolution: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
        print()

        with D72N_SERDB(args.bus) as serdb:
            if not serdb.probe():
                print("[-] SERDB not responding")
                return 1

            print("[+] SERDB connected")
            print()

            if args.red_screen:
                red_screen(serdb)
            elif args.stripe:
                color_stripes(serdb)
            elif args.marker:
                draw_marker(serdb, args.marker)
            elif args.quick:
                quick_test(serdb)
            elif args.verify:
                verify_buffer(serdb)

        return 0

    except ImportError as e:
        print(f"[-] Missing dependency: {e}")
        return 1
    except OSError as e:
        print(f"[-] I2C error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
