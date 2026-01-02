#!/usr/bin/env python3
"""
D72N Watchdog Control
=====================

Control the software watchdog timer via SERDB.

Watchdog Registers (XDATA):
  0x44CE: Watchdog state (bit 0 = enable)
  0x44D3: Counter low byte
  0x44D4: Counter high byte

Traced from D72N 8051 blocks:
  Block 15 offset 0x2450: State read
  Block 15 offset 0x6A02: Counter write
  Block 15 offset 0x6AC1: Counter check
  Block 16 offset 0x1775: Disable (ANL A,#0xFE)

Usage:
    python3 d72n_watchdog.py /dev/i2c-1 status
    python3 d72n_watchdog.py /dev/i2c-1 disable
    python3 d72n_watchdog.py /dev/i2c-1 enable
    python3 d72n_watchdog.py /dev/i2c-1 feed
"""

import argparse
import sys
import time
from d72n_serdb import D72N_SERDB, D72N_ADDR


class D72N_Watchdog:
    """Watchdog timer control

    Traced from D72N 8051 blocks 15, 16:
    - State register: 0x44CE
    - Counter: 0x44D3-0x44D4 (16-bit)
    - Disable: ANL A,#0xFE (block 16: 0x1775)
    """

    # Watchdog registers
    WDT_STATE = 0x44CE
    WDT_COUNTER_LO = 0x44D3
    WDT_COUNTER_HI = 0x44D4

    # Control bits
    BIT_ENABLE = 0x01  # Traced: ANL A,#0xFE clears this

    def __init__(self, serdb):
        self.serdb = serdb

    def read_state(self):
        """Read watchdog state register"""
        return self.serdb.read_xdata(self.WDT_STATE)

    def write_state(self, value):
        """Write watchdog state register"""
        self.serdb.write_xdata(self.WDT_STATE, value)

    def read_counter(self):
        """Read 16-bit watchdog counter

        Traced from block 15 offset 0x6AD4-0x6ADB
        """
        low = self.serdb.read_xdata(self.WDT_COUNTER_LO)
        high = self.serdb.read_xdata(self.WDT_COUNTER_HI)
        return (high << 8) | low

    def write_counter(self, value):
        """Write 16-bit watchdog counter

        Traced from block 15 offset 0x6A02-0x6A08
        """
        self.serdb.write_xdata(self.WDT_COUNTER_LO, value & 0xFF)
        self.serdb.write_xdata(self.WDT_COUNTER_HI, (value >> 8) & 0xFF)

    def is_enabled(self):
        """Check if watchdog is enabled (bit 0)"""
        return (self.read_state() & self.BIT_ENABLE) != 0

    def disable(self):
        """Disable watchdog timer

        Traced from block 16 offset 0x1775:
        ANL A,#0xFE clears bit 0
        """
        state = self.read_state()
        new_state = state & ~self.BIT_ENABLE
        self.write_state(new_state)
        self.write_counter(0x0000)  # Reset counter
        return not self.is_enabled()

    def enable(self):
        """Enable watchdog timer"""
        state = self.read_state()
        new_state = state | self.BIT_ENABLE
        self.write_state(new_state)
        return self.is_enabled()

    def feed(self, value=0x0000):
        """Feed (reset) the watchdog counter

        Args:
            value: Counter value to set (default 0)
        """
        self.write_counter(value)

    def status(self):
        """Get detailed status

        Returns:
            Dictionary with status info
        """
        state = self.read_state()
        counter = self.read_counter()
        return {
            'state': state,
            'enabled': bool(state & self.BIT_ENABLE),
            'counter': counter,
        }

    def print_status(self):
        """Print formatted status"""
        status = self.status()

        print("=" * 50)
        print("Watchdog Status")
        print("=" * 50)
        print(f"State Register: 0x{status['state']:02X} (XDATA 0x{self.WDT_STATE:04X})")
        print(f"Counter:        0x{status['counter']:04X} ({status['counter']}) "
              f"(XDATA 0x{self.WDT_COUNTER_LO:04X}-0x{self.WDT_COUNTER_HI:04X})")
        print()
        print(f"Enabled: {'YES - Watchdog active' if status['enabled'] else 'NO - Watchdog disabled'}")

        if status['enabled']:
            # Threshold from traced code: 0xEA00 (block 15: 0x6AC0)
            threshold = 0xEA00
            if status['counter'] > threshold:
                print(f"WARNING: Counter above threshold (0x{threshold:04X}) - may reset soon!")


def main():
    parser = argparse.ArgumentParser(
        description='D72N Watchdog Control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
    status  - Show watchdog status
    disable - Disable watchdog timer
    enable  - Enable watchdog timer
    feed    - Reset watchdog counter
    watch   - Monitor counter continuously

Examples:
    python3 d72n_watchdog.py /dev/i2c-1 status
    python3 d72n_watchdog.py /dev/i2c-1 disable
    python3 d72n_watchdog.py /dev/i2c-1 feed

IMPORTANT:
    Disable the watchdog before long operations that might
    trigger a timeout (like memory dumps or code injection).
        """
    )

    parser.add_argument('bus', help='I2C bus (e.g., /dev/i2c-1)')
    parser.add_argument('command', nargs='?', default='status',
                        choices=['status', 'disable', 'enable', 'feed', 'watch'],
                        help='Command to execute (default: status)')
    parser.add_argument('--interval', '-i', type=float, default=0.5,
                        help='Watch interval in seconds (default: 0.5)')

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

            wdt = D72N_Watchdog(serdb)

            if args.command == 'status':
                wdt.print_status()

            elif args.command == 'disable':
                before_state = wdt.read_state()
                before_counter = wdt.read_counter()
                success = wdt.disable()
                after_state = wdt.read_state()

                print(f"[*] State: 0x{before_state:02X} -> 0x{after_state:02X}")
                print(f"[*] Counter: 0x{before_counter:04X} -> 0x0000")

                if success:
                    print("[+] Watchdog disabled")
                else:
                    print("[-] Watchdog disable failed")

            elif args.command == 'enable':
                before = wdt.read_state()
                success = wdt.enable()
                after = wdt.read_state()

                print(f"[*] State: 0x{before:02X} -> 0x{after:02X}")

                if success:
                    print("[+] Watchdog enabled")
                else:
                    print("[-] Watchdog enable failed")

            elif args.command == 'feed':
                before = wdt.read_counter()
                wdt.feed()
                after = wdt.read_counter()
                print(f"[+] Counter reset: 0x{before:04X} -> 0x{after:04X}")

            elif args.command == 'watch':
                print("Watching watchdog counter (Ctrl+C to stop)...")
                print()

                try:
                    while True:
                        status = wdt.status()
                        enabled = "ON" if status['enabled'] else "OFF"
                        print(f"\rEnabled: {enabled}  Counter: 0x{status['counter']:04X} "
                              f"({status['counter']:5d})", end='', flush=True)
                        time.sleep(args.interval)
                except KeyboardInterrupt:
                    print("\nStopped.")

    except OSError as e:
        print(f"[-] I2C error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
