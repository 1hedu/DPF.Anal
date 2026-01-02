#!/usr/bin/env python3
"""
D72N System State Dump
======================

Comprehensive system state dump for DPF-D72N via SERDB.
All addresses traced from D72N 8051 overlay blocks.

Shows:
  - AEON processor status
  - Watchdog state
  - Mailbox protocol state
  - Primary state variables
  - GWin display state

Usage:
    python3 d72n_state.py /dev/i2c-1
    python3 d72n_state.py /dev/i2c-1 --watch  # Continuous monitoring
    python3 d72n_state.py /dev/i2c-1 --json   # JSON output
"""

import argparse
import json
import sys
import time
from d72n_serdb import D72N_SERDB, D72N_ADDR


def read_state(serdb):
    """Read complete D72N system state

    Returns:
        Dictionary with all state values
    """
    state = {
        'timestamp': time.time(),
        'aeon': {},
        'watchdog': {},
        'mailbox': {},
        'state': {},
        'gwin': {},
    }

    # AEON Control (traced from block 01: 0x3CDF, 0x3D25, 0xD96C)
    aeon_ctrl = serdb.read_xdata(D72N_ADDR.AEON_CTRL)
    state['aeon'] = {
        'register': aeon_ctrl,
        'running': bool(aeon_ctrl & 0x01),
        'enabled': bool(aeon_ctrl & 0x02),
        'reset_n': bool(aeon_ctrl & 0x04),
    }

    # Watchdog (traced from blocks 15, 16)
    wdt_state = serdb.read_xdata(D72N_ADDR.WDT_STATE)
    wdt_lo = serdb.read_xdata(D72N_ADDR.WDT_COUNTER_LO)
    wdt_hi = serdb.read_xdata(D72N_ADDR.WDT_COUNTER_HI)
    state['watchdog'] = {
        'state': wdt_state,
        'enabled': bool(wdt_state & 0x01),
        'counter': (wdt_hi << 8) | wdt_lo,
    }

    # Mailbox (traced from block 02: 0x2830-0x2845)
    state['mailbox'] = {
        'command': serdb.read_xdata(D72N_ADDR.MAILBOX_CMD),
        'param0': serdb.read_xdata(D72N_ADDR.MAILBOX_PARAM),
        'sync': serdb.read_xdata(D72N_ADDR.MAILBOX_SYNC),
        'status': serdb.read_xdata(D72N_ADDR.MAILBOX_STATUS),
        'response': [
            serdb.read_xdata(D72N_ADDR.MAILBOX_RESP + i)
            for i in range(4)
        ],
    }

    # Primary State Variables (high ref count)
    state['state'] = {
        'primary_0': serdb.read_xdata(D72N_ADDR.STATE_PRIMARY),
        'primary_1': serdb.read_xdata(D72N_ADDR.STATE_PRIMARY + 1),
        'secondary': serdb.read_xdata(D72N_ADDR.STATE_SECONDARY),
        'decode': serdb.read_xdata(D72N_ADDR.STATE_DECODE),
        'storage': serdb.read_xdata(D72N_ADDR.STATE_STORAGE),
    }

    # GWin Display (traced from multiple blocks)
    state['gwin'] = {
        'primary': serdb.read_xdata(D72N_ADDR.GWIN_PRIMARY),
        'secondary': serdb.read_xdata(D72N_ADDR.GWIN_SECONDARY),
        'enable': serdb.read_xdata(D72N_ADDR.GWIN_ENABLE),
    }

    return state


def print_state(state, colorize=True):
    """Pretty print system state

    Args:
        state: State dictionary from read_state()
        colorize: Use ANSI colors
    """
    def color(text, code):
        if colorize:
            return f"\033[{code}m{text}\033[0m"
        return text

    def status_color(enabled):
        return color("ON", "32") if enabled else color("OFF", "31")

    print("=" * 70)
    print(color("D72N System State", "1;36"))
    print("=" * 70)

    # AEON Status
    aeon = state['aeon']
    print(f"\n{color('AEON Processor', '1;33')} (0x0FE6 = 0x{aeon['register']:02X})")
    print(f"  RUN:      {status_color(aeon['running'])}")
    print(f"  ENABLE:   {status_color(aeon['enabled'])}")
    print(f"  RESET_N:  {status_color(aeon['reset_n'])}")

    # Watchdog Status
    wdt = state['watchdog']
    print(f"\n{color('Watchdog', '1;33')} (0x44CE = 0x{wdt['state']:02X})")
    print(f"  Enabled:  {status_color(wdt['enabled'])}")
    print(f"  Counter:  0x{wdt['counter']:04X} ({wdt['counter']})")

    # Mailbox Status
    mb = state['mailbox']
    status_names = {0x00: 'Processing', 0xFE: 'Ready', 0x01: 'Complete'}
    status_str = status_names.get(mb['status'], f"Unknown (0x{mb['status']:02X})")
    print(f"\n{color('Mailbox', '1;33')}")
    print(f"  Command:  0x{mb['command']:02X}")
    print(f"  Param[0]: 0x{mb['param0']:02X}")
    print(f"  Sync:     0x{mb['sync']:02X}")
    print(f"  Status:   {status_str}")
    print(f"  Response: [{', '.join(f'0x{r:02X}' for r in mb['response'])}]")

    # State Variables
    st = state['state']
    print(f"\n{color('State Variables', '1;33')}")
    print(f"  Primary:   0x{st['primary_0']:02X}{st['primary_1']:02X}")
    print(f"  Secondary: 0x{st['secondary']:02X}")
    print(f"  Decode:    0x{st['decode']:02X}")
    print(f"  Storage:   0x{st['storage']:02X}")

    # GWin Display
    gwin = state['gwin']
    print(f"\n{color('GWin Display', '1;33')}")
    print(f"  Primary:   0x{gwin['primary']:02X}")
    print(f"  Secondary: 0x{gwin['secondary']:02X}")
    print(f"  Enable:    0x{gwin['enable']:02X}")

    print()


def watch_state(serdb, interval=1.0):
    """Continuously monitor state changes

    Args:
        serdb: D72N_SERDB instance
        interval: Update interval in seconds
    """
    print("Watching D72N state (Ctrl+C to stop)...")
    print()

    last_state = None

    try:
        while True:
            state = read_state(serdb)

            # Clear screen and print
            print("\033[2J\033[H", end='')  # Clear screen
            print_state(state)

            # Show changes
            if last_state:
                changes = []
                for section in ['aeon', 'watchdog', 'mailbox', 'state', 'gwin']:
                    for key, val in state[section].items():
                        if state[section][key] != last_state[section].get(key):
                            changes.append(f"{section}.{key}: {last_state[section].get(key)} -> {val}")

                if changes:
                    print("\033[1;35mChanges:\033[0m")
                    for change in changes:
                        print(f"  {change}")

            last_state = state
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nStopped.")


def main():
    parser = argparse.ArgumentParser(
        description='D72N System State Dump',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Show current state
    python3 d72n_state.py /dev/i2c-1

    # Watch for changes
    python3 d72n_state.py /dev/i2c-1 --watch

    # JSON output (for scripting)
    python3 d72n_state.py /dev/i2c-1 --json

    # No colors (for piping)
    python3 d72n_state.py /dev/i2c-1 --no-color
        """
    )

    parser.add_argument('bus', help='I2C bus (e.g., /dev/i2c-1)')
    parser.add_argument('--watch', '-w', action='store_true',
                        help='Continuously monitor state')
    parser.add_argument('--interval', '-i', type=float, default=1.0,
                        help='Watch interval in seconds (default: 1.0)')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output as JSON')
    parser.add_argument('--no-color', action='store_true',
                        help='Disable colored output')

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

            if args.watch:
                watch_state(serdb, args.interval)
            else:
                state = read_state(serdb)

                if args.json:
                    print(json.dumps(state, indent=2))
                else:
                    print_state(state, colorize=not args.no_color)

    except OSError as e:
        print(f"[-] I2C error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
