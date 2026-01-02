#!/usr/bin/env python3
"""
D72N AEON Processor Control
============================

Control the AEON R2 coprocessor via SERDB.

AEON Control Register: XDATA 0x0FE6
  Bit 0: RUN     - 1=running, 0=halted
  Bit 1: ENABLE  - Processor enable
  Bit 2: RESET_N - Reset release

Traced from D72N 8051 blocks:
  Block 01 offset 0x3CDF: Resume (ORL #0x01)
  Block 01 offset 0x3D25: Halt (ANL #0xFE)
  Block 01 offset 0xD96C: Enable (ORL #0x02)
  Block 16 offset 0x66DF: Resume in watchdog recovery

Usage:
    python3 d72n_aeon_control.py /dev/i2c-1 status
    python3 d72n_aeon_control.py /dev/i2c-1 halt
    python3 d72n_aeon_control.py /dev/i2c-1 resume
    python3 d72n_aeon_control.py /dev/i2c-1 reset
"""

import argparse
import sys
import time
from d72n_serdb import D72N_SERDB, D72N_ADDR


class D72N_AEON:
    """AEON R2 processor control

    Traced from D72N 8051 block 01:
    - Resume: offset 0x3CDF (ORL A,#0x01)
    - Halt: offset 0x3D25 (ANL A,#0xFE)
    - Enable: offset 0xD96C (ORL A,#0x02)
    """

    # Control register
    AEON_CTRL = 0x0FE6

    # Control bits (traced from ORL/ANL operations)
    BIT_RUN = 0x01      # Traced: ORL A,#0x01 at 0x3CE3
    BIT_ENABLE = 0x02   # Traced: ORL A,#0x02 at 0xD970
    BIT_RESET_N = 0x04  # Combined with ENABLE

    def __init__(self, serdb):
        self.serdb = serdb

    def read_ctrl(self):
        """Read AEON control register"""
        return self.serdb.read_xdata(self.AEON_CTRL)

    def write_ctrl(self, value):
        """Write AEON control register"""
        self.serdb.write_xdata(self.AEON_CTRL, value)

    def is_running(self):
        """Check if AEON is running (bit 0)"""
        return (self.read_ctrl() & self.BIT_RUN) != 0

    def is_enabled(self):
        """Check if AEON is enabled (bit 1)"""
        return (self.read_ctrl() & self.BIT_ENABLE) != 0

    def halt(self):
        """Halt AEON processor

        Traced from block 01 offset 0x3D25-0x3D2B:
        ANL A,#0xFE clears bit 0 (RUN)
        """
        current = self.read_ctrl()
        new_value = current & ~self.BIT_RUN
        self.write_ctrl(new_value)
        return not self.is_running()

    def resume(self):
        """Resume AEON processor

        Traced from block 01 offset 0x3CDF-0x3CE5:
        ORL A,#0x01 sets bit 0 (RUN)
        """
        current = self.read_ctrl()
        new_value = current | self.BIT_RUN
        self.write_ctrl(new_value)
        return self.is_running()

    def enable(self):
        """Enable AEON (without running)

        Traced from block 01 offset 0xD96C-0xD972:
        ORL A,#0x02 sets bit 1 (ENABLE)
        """
        self.write_ctrl(self.BIT_ENABLE | self.BIT_RESET_N)

    def disable(self):
        """Fully disable AEON (hold in reset)"""
        self.write_ctrl(0x00)

    def reset(self, delay=0.1):
        """Full reset cycle

        Sequence:
        1. Halt (clear RUN)
        2. Disable (hold in reset)
        3. Enable (release reset)
        4. Resume (set RUN)
        """
        print("[*] Halting AEON...")
        self.halt()
        time.sleep(delay)

        print("[*] Disabling AEON...")
        self.disable()
        time.sleep(delay)

        print("[*] Enabling AEON...")
        self.enable()
        time.sleep(delay)

        print("[*] Resuming AEON...")
        success = self.resume()

        if success:
            print("[+] AEON reset complete - running")
        else:
            print("[-] AEON reset failed - not running")

        return success

    def status(self):
        """Get detailed status

        Returns:
            Dictionary with status info
        """
        val = self.read_ctrl()
        return {
            'register': val,
            'running': bool(val & self.BIT_RUN),
            'enabled': bool(val & self.BIT_ENABLE),
            'reset_n': bool(val & self.BIT_RESET_N),
        }

    def print_status(self):
        """Print formatted status"""
        status = self.status()

        print("=" * 50)
        print("AEON Processor Status")
        print("=" * 50)
        print(f"Control Register: 0x{status['register']:02X} (XDATA 0x{self.AEON_CTRL:04X})")
        print()
        print(f"  Bit 0 (RUN):     {'SET - Running' if status['running'] else 'CLEAR - Halted'}")
        print(f"  Bit 1 (ENABLE):  {'SET - Enabled' if status['enabled'] else 'CLEAR - Disabled'}")
        print(f"  Bit 2 (RESET_N): {'SET - Released' if status['reset_n'] else 'CLEAR - In Reset'}")
        print()

        if status['running'] and status['enabled'] and status['reset_n']:
            print("Status: RUNNING (fully operational)")
        elif status['enabled'] and status['reset_n']:
            print("Status: ENABLED but HALTED")
        elif status['enabled']:
            print("Status: IN RESET")
        else:
            print("Status: DISABLED")


def main():
    parser = argparse.ArgumentParser(
        description='D72N AEON Processor Control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
    status  - Show AEON status
    halt    - Halt AEON processor
    resume  - Resume AEON processor
    reset   - Full reset cycle
    enable  - Enable without running
    disable - Fully disable

Examples:
    python3 d72n_aeon_control.py /dev/i2c-1 status
    python3 d72n_aeon_control.py /dev/i2c-1 halt
    python3 d72n_aeon_control.py /dev/i2c-1 resume

Use Cases:
    - Halt to freeze display for screenshot
    - Halt to safely inspect DRAM buffers
    - Halt to modify AEON code/data
    - Reset to recover from crash
        """
    )

    parser.add_argument('bus', help='I2C bus (e.g., /dev/i2c-1)')
    parser.add_argument('command', nargs='?', default='status',
                        choices=['status', 'halt', 'resume', 'reset', 'enable', 'disable'],
                        help='Command to execute (default: status)')
    parser.add_argument('--delay', type=float, default=0.1,
                        help='Reset sequence delay (default: 0.1s)')

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

            aeon = D72N_AEON(serdb)

            if args.command == 'status':
                aeon.print_status()

            elif args.command == 'halt':
                before = aeon.read_ctrl()
                success = aeon.halt()
                after = aeon.read_ctrl()
                print(f"[*] Control: 0x{before:02X} -> 0x{after:02X}")
                if success:
                    print("[+] AEON halted")
                else:
                    print("[-] AEON halt failed")

            elif args.command == 'resume':
                before = aeon.read_ctrl()
                success = aeon.resume()
                after = aeon.read_ctrl()
                print(f"[*] Control: 0x{before:02X} -> 0x{after:02X}")
                if success:
                    print("[+] AEON resumed")
                else:
                    print("[-] AEON resume failed")

            elif args.command == 'reset':
                aeon.reset(delay=args.delay)

            elif args.command == 'enable':
                aeon.enable()
                print("[+] AEON enabled (but not running)")
                aeon.print_status()

            elif args.command == 'disable':
                aeon.disable()
                print("[+] AEON disabled")
                aeon.print_status()

    except OSError as e:
        print(f"[-] I2C error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
