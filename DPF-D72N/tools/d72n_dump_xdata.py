#!/usr/bin/env python3
"""
D72N XDATA Memory Dump
======================

Dump 8051 XDATA memory regions via SERDB.

XDATA Memory Map (traced from D72N 8051 blocks):
  0x0000-0x00FF  SFR mirror
  0x0100-0x0FFF  System area
  0x1000-0x1FFF  RIU access window
  0x4000-0x4FFF  Mailbox/State (primary)
  0x5000-0x5FFF  Extended state
  0x6000-0x6FFF  GWin/Display control
  0x7000-0xFFFF  Buffers/Stack

Usage:
    python3 d72n_dump_xdata.py /dev/i2c-1 --range 0x4000 0x1000 -o mailbox.bin
    python3 d72n_dump_xdata.py /dev/i2c-1 --full -o xdata_full.bin
    python3 d72n_dump_xdata.py /dev/i2c-1 --regions
"""

import argparse
import sys
import time
from d72n_serdb import D72N_SERDB

# Key XDATA regions (traced from D72N docs)
XDATA_REGIONS = {
    'system':   (0x0100, 0x0F00, 'System area'),
    'riu':      (0x1000, 0x1000, 'RIU access window'),
    'mailbox':  (0x4000, 0x0500, 'Mailbox/state variables'),
    'state':    (0x4800, 0x0300, 'Primary state machine'),
    'gwin':     (0x6E00, 0x0200, 'GWin display control'),
    'extended': (0x5000, 0x1000, 'Extended state'),
}


def dump_region(serdb, start, length, output_file=None, show_hex=True):
    """Dump a region of XDATA

    Args:
        serdb: D72N_SERDB instance
        start: Start address
        length: Bytes to read
        output_file: Optional file to save to
        show_hex: Display hexdump
    """
    print(f"[*] Reading XDATA 0x{start:04X} - 0x{start+length-1:04X} ({length} bytes)")

    data = bytearray(length)
    start_time = time.time()

    for i in range(length):
        data[i] = serdb.read_xdata(start + i)
        if (i + 1) % 256 == 0:
            pct = ((i + 1) * 100) // length
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (length - i - 1) / rate if rate > 0 else 0
            print(f"\r[*] Progress: {pct}% ({i+1}/{length}) - "
                  f"{rate:.1f} B/s, ETA: {remaining:.0f}s", end='', flush=True)

    elapsed = time.time() - start_time
    print(f"\n[+] Read {length} bytes in {elapsed:.1f}s ({length/elapsed:.1f} B/s)")

    if output_file:
        with open(output_file, 'wb') as f:
            f.write(data)
        print(f"[+] Saved to {output_file}")

    if show_hex:
        print("\n" + serdb.hexdump(data, start))

    return bytes(data)


def dump_all_regions(serdb, output_dir=None):
    """Dump all known XDATA regions

    Args:
        serdb: D72N_SERDB instance
        output_dir: Directory to save dumps
    """
    import os

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    for name, (start, length, desc) in XDATA_REGIONS.items():
        print(f"\n{'='*60}")
        print(f"Region: {name} - {desc}")
        print(f"{'='*60}")

        output_file = None
        if output_dir:
            output_file = os.path.join(output_dir, f"xdata_{name}_{start:04X}.bin")

        dump_region(serdb, start, length, output_file, show_hex=True)


def dump_key_variables(serdb):
    """Dump key state variables

    Addresses traced from D72N documentation
    """
    print("=" * 60)
    print("D72N Key State Variables")
    print("=" * 60)

    variables = [
        # Mailbox (traced from block 02)
        (0x4401, 'Mailbox Command'),
        (0x4402, 'Mailbox Param[0]'),
        (0x4417, 'Mailbox Sync'),
        (0x40FB, 'Mailbox Status'),
        (0x40FC, 'Mailbox Response[0]'),
        (0x40FD, 'Mailbox Response[1]'),
        (0x40FE, 'Mailbox Response[2]'),
        (0x40FF, 'Mailbox Response[3]'),

        # AEON Control (traced from block 01)
        (0x0FE6, 'AEON Control'),

        # Watchdog (traced from blocks 15, 16)
        (0x44CE, 'Watchdog State'),
        (0x44D3, 'Watchdog Counter Lo'),
        (0x44D4, 'Watchdog Counter Hi'),

        # Primary State (high ref count)
        (0x4800, 'Primary State[0]'),
        (0x4801, 'Primary State[1]'),
        (0x4185, 'Secondary State'),
        (0x4A9D, 'Decode State'),
        (0x4100, 'Storage State'),

        # GWin (traced from multiple blocks)
        (0x6EA8, 'GWin Primary'),
        (0x6FA8, 'GWin Secondary'),
        (0x6EE0, 'GWin Enable'),
    ]

    print(f"{'Address':<10} {'Name':<25} {'Value':<10} {'Binary':<10}")
    print("-" * 60)

    for addr, name in variables:
        val = serdb.read_xdata(addr)
        print(f"0x{addr:04X}     {name:<25} 0x{val:02X}       {val:08b}")


def main():
    parser = argparse.ArgumentParser(
        description='D72N XDATA Memory Dump',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dump mailbox region
    python3 d72n_dump_xdata.py /dev/i2c-1 --range 0x4000 0x500

    # Dump all known regions
    python3 d72n_dump_xdata.py /dev/i2c-1 --regions --output-dir ./xdata_dumps/

    # Dump full 64KB XDATA (slow!)
    python3 d72n_dump_xdata.py /dev/i2c-1 --full -o xdata_full.bin

    # Show key variables only
    python3 d72n_dump_xdata.py /dev/i2c-1 --variables
        """
    )

    parser.add_argument('bus', help='I2C bus (e.g., /dev/i2c-1)')
    parser.add_argument('--range', nargs=2, metavar=('START', 'LENGTH'),
                        help='Dump specific range')
    parser.add_argument('--full', action='store_true',
                        help='Dump full 64KB XDATA')
    parser.add_argument('--regions', action='store_true',
                        help='Dump all known regions')
    parser.add_argument('--variables', action='store_true',
                        help='Show key variables')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('--output-dir', help='Output directory for regions')
    parser.add_argument('--no-hex', action='store_true',
                        help='Suppress hex dump display')

    args = parser.parse_args()

    # Parse bus argument
    if args.bus.isdigit():
        bus = int(args.bus)
    else:
        bus = args.bus

    try:
        with D72N_SERDB(bus) as serdb:
            if not serdb.probe():
                print("[-] SERDB not responding at 0x59")
                return 1

            print("[+] SERDB connection established")

            if args.variables:
                dump_key_variables(serdb)

            elif args.regions:
                dump_all_regions(serdb, args.output_dir)

            elif args.full:
                dump_region(serdb, 0x0000, 0x10000, args.output,
                           show_hex=not args.no_hex)

            elif args.range:
                start = int(args.range[0], 0)
                length = int(args.range[1], 0)
                dump_region(serdb, start, length, args.output,
                           show_hex=not args.no_hex)

            else:
                # Default: show variables
                dump_key_variables(serdb)

    except OSError as e:
        print(f"[-] I2C error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
