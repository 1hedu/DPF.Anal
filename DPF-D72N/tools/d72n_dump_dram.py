#!/usr/bin/env python3
"""
D72N DRAM Memory Dump
=====================

Dump shared DRAM memory via SERDB.

DRAM Memory Map (traced from D72N AEON analysis):
  0x000000-0x0BFFFF  System/Reserved (AEON code, stack)
  0x0C0000-0x0FFFFF  Secondary buffer (~256KB, 673 refs)
  0x100000-0x17FFFF  Main decode buffer (~512KB, 888 refs)
  0x150000-0x1AFFFF  Output buffer (~256KB, 384 refs)

Key Sub-regions (traced):
  0x100030  +0x030  Header/metadata (74 refs)
  0x100100  +0x100  Image data start (152 refs)
  0x100400  +0x400  Parameter block (121 refs)
  0x100600  +0x600  Secondary data (126 refs)

Usage:
    python3 d72n_dump_dram.py /dev/i2c-1 --range 0x100000 0x1000 -o buffer.bin
    python3 d72n_dump_dram.py /dev/i2c-1 --buffer main -o main_buffer.bin
    python3 d72n_dump_dram.py /dev/i2c-1 --search-pattern DEADBEEF
"""

import argparse
import sys
import time
from d72n_serdb import D72N_SERDB

# DRAM buffer regions (traced from D72N docs)
DRAM_BUFFERS = {
    'secondary': (0x0C0000, 0x40000, 'Secondary buffer (673 refs)'),
    'main':      (0x100000, 0x80000, 'Main decode buffer (888 refs)'),
    'output':    (0x150000, 0x60000, 'Output buffer (384 refs)'),
}

# Key sub-regions within main buffer
MAIN_BUFFER_REGIONS = {
    'header':     (0x100030, 0x100, 'Header/metadata'),
    'image_start': (0x100100, 0x100, 'Image data start'),
    'params':     (0x100400, 0x100, 'Parameter block'),
    'secondary':  (0x100600, 0x100, 'Secondary data'),
    'extended':   (0x100700, 0x200, 'Extended data'),
}


def dump_dram_region(serdb, start, length, output_file=None, show_hex=True,
                     progress=True):
    """Dump a region of DRAM

    Args:
        serdb: D72N_SERDB instance
        start: Start address (24-bit)
        length: Bytes to read
        output_file: Optional file to save to
        show_hex: Display hexdump
        progress: Show progress bar

    Returns:
        bytes object with data
    """
    print(f"[*] Reading DRAM 0x{start:06X} - 0x{start+length-1:06X} ({length} bytes)")

    data = bytearray(length)
    start_time = time.time()

    for i in range(length):
        data[i] = serdb.read_dram(start + i)
        if progress and (i + 1) % 256 == 0:
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

    if show_hex and length <= 0x400:  # Only show hex for small dumps
        print("\n" + serdb.hexdump(data, start))

    return bytes(data)


def dump_buffer(serdb, buffer_name, output_file=None, limit=None):
    """Dump a named buffer

    Args:
        serdb: D72N_SERDB instance
        buffer_name: Name from DRAM_BUFFERS
        output_file: Optional file to save to
        limit: Limit bytes to read
    """
    if buffer_name not in DRAM_BUFFERS:
        print(f"[-] Unknown buffer: {buffer_name}")
        print(f"    Available: {', '.join(DRAM_BUFFERS.keys())}")
        return None

    start, length, desc = DRAM_BUFFERS[buffer_name]
    if limit:
        length = min(length, limit)

    print(f"\n{'='*60}")
    print(f"Buffer: {buffer_name} - {desc}")
    print(f"{'='*60}")

    return dump_dram_region(serdb, start, length, output_file,
                           show_hex=(length <= 0x400))


def search_pattern(serdb, pattern_hex, start=0x0C0000, end=0x180000,
                   chunk_size=0x1000):
    """Search for a hex pattern in DRAM

    Args:
        serdb: D72N_SERDB instance
        pattern_hex: Hex string to search (e.g., "DEADBEEF")
        start: Start address
        end: End address
        chunk_size: Read chunk size
    """
    pattern = bytes.fromhex(pattern_hex)
    print(f"[*] Searching for pattern {pattern_hex} in DRAM "
          f"0x{start:06X}-0x{end:06X}")

    matches = []
    addr = start

    while addr < end:
        chunk_len = min(chunk_size, end - addr)
        data = serdb.read_dram_range(addr, chunk_len)

        # Search for pattern in chunk
        pos = 0
        while True:
            idx = data.find(pattern, pos)
            if idx == -1:
                break
            match_addr = addr + idx
            matches.append(match_addr)
            print(f"[+] Found at 0x{match_addr:06X}")
            pos = idx + 1

        addr += chunk_len
        pct = ((addr - start) * 100) // (end - start)
        print(f"\r[*] Searching: {pct}%", end='', flush=True)

    print(f"\n[+] Found {len(matches)} matches")
    return matches


def compare_buffers(serdb, addr1, addr2, length):
    """Compare two memory regions

    Args:
        serdb: D72N_SERDB instance
        addr1: First address
        addr2: Second address
        length: Length to compare
    """
    print(f"[*] Comparing 0x{addr1:06X} and 0x{addr2:06X} ({length} bytes)")

    differences = []
    for i in range(length):
        val1 = serdb.read_dram(addr1 + i)
        val2 = serdb.read_dram(addr2 + i)
        if val1 != val2:
            differences.append((i, val1, val2))

        if (i + 1) % 256 == 0:
            pct = ((i + 1) * 100) // length
            print(f"\r[*] Comparing: {pct}%", end='', flush=True)

    print(f"\n[+] Found {len(differences)} differences")

    if differences:
        print(f"\n{'Offset':<10} {'Addr1':<15} {'Addr2':<15}")
        print("-" * 45)
        for offset, v1, v2 in differences[:50]:
            print(f"0x{offset:04X}     0x{v1:02X} @ 0x{addr1+offset:06X}    "
                  f"0x{v2:02X} @ 0x{addr2+offset:06X}")
        if len(differences) > 50:
            print(f"... and {len(differences) - 50} more")

    return differences


def main():
    parser = argparse.ArgumentParser(
        description='D72N DRAM Memory Dump',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dump main decode buffer (limited to 4KB)
    python3 d72n_dump_dram.py /dev/i2c-1 --buffer main --limit 0x1000

    # Dump specific range
    python3 d72n_dump_dram.py /dev/i2c-1 --range 0x100000 0x1000 -o dump.bin

    # Search for pattern
    python3 d72n_dump_dram.py /dev/i2c-1 --search DEADBEEF

    # Compare two regions
    python3 d72n_dump_dram.py /dev/i2c-1 --compare 0x100000 0x0C0000 0x100
        """
    )

    parser.add_argument('bus', help='I2C bus (e.g., /dev/i2c-1)')
    parser.add_argument('--range', nargs=2, metavar=('START', 'LENGTH'),
                        help='Dump specific range')
    parser.add_argument('--buffer', choices=list(DRAM_BUFFERS.keys()),
                        help='Dump named buffer')
    parser.add_argument('--limit', type=lambda x: int(x, 0),
                        help='Limit bytes to read')
    parser.add_argument('--search', metavar='PATTERN',
                        help='Search for hex pattern (e.g., DEADBEEF)')
    parser.add_argument('--compare', nargs=3, metavar=('ADDR1', 'ADDR2', 'LEN'),
                        help='Compare two regions')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('--no-hex', action='store_true',
                        help='Suppress hex dump display')
    parser.add_argument('--list-buffers', action='store_true',
                        help='List known buffers')

    args = parser.parse_args()

    if args.list_buffers:
        print("Known DRAM Buffers (traced from D72N docs):")
        print("-" * 60)
        for name, (start, length, desc) in DRAM_BUFFERS.items():
            print(f"  {name:<12} 0x{start:06X}  {length/1024:>6.0f}KB  {desc}")
        print("\nMain buffer sub-regions:")
        for name, (start, length, desc) in MAIN_BUFFER_REGIONS.items():
            print(f"  {name:<12} 0x{start:06X}  {length:>6}B   {desc}")
        return 0

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

            if args.search:
                search_pattern(serdb, args.search)

            elif args.compare:
                addr1 = int(args.compare[0], 0)
                addr2 = int(args.compare[1], 0)
                length = int(args.compare[2], 0)
                compare_buffers(serdb, addr1, addr2, length)

            elif args.buffer:
                dump_buffer(serdb, args.buffer, args.output, args.limit)

            elif args.range:
                start = int(args.range[0], 0)
                length = int(args.range[1], 0)
                dump_dram_region(serdb, start, length, args.output,
                                show_hex=not args.no_hex)

            else:
                # Default: list buffers
                print("Known DRAM Buffers (traced from D72N docs):")
                print("-" * 60)
                for name, (start, length, desc) in DRAM_BUFFERS.items():
                    print(f"  {name:<12} 0x{start:06X}  {length/1024:>6.0f}KB  {desc}")
                print("\nUse --buffer <name> to dump a buffer")

    except OSError as e:
        print(f"[-] I2C error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
