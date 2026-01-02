#!/usr/bin/env python3
"""
D72N Mailbox Protocol
======================

8051 <-> AEON mailbox IPC interface via SERDB.

Mailbox Memory Map (XDATA):
  0x4401: Command byte
  0x4402: Param bytes (up to 21)
  0x4417: Sync flag
  0x40FB: Status register
  0x40FC-0x40FF: Response bytes

Commands (traced from 8051 blocks):
  0x01: MB_JPD_CMD_INIT (block 02: 0x22F7)
  0x02: MB_JPD_CMD_MJPG_START_DEC (block 02: 0x22F2)
  0x03: MB_JPD_CMD_ABORT
  0x04: MB_JPD_CMD_PAUSE
  0x05: MB_JPD_CMD_RESUME
  0x10: MB_BMP_CMD_DECODE_MEM_OUT (block 02: 0xAC80)
  0x20: MB_TIFF_CMD_GET_HEAD_INF
  0x21: MB_TIFF_CMD_START_DEC
  0x22: MB_TIFF_CMD_DECODE_MEM_OUT

Usage:
    python3 d72n_mailbox.py /dev/i2c-1 status
    python3 d72n_mailbox.py /dev/i2c-1 send 0x01
    python3 d72n_mailbox.py /dev/i2c-1 send 0x10 --params 00 00 10 00
"""

import argparse
import sys
import time
from d72n_serdb import D72N_SERDB, D72N_ADDR


# Mailbox commands (traced from D72N docs)
MAILBOX_COMMANDS = {
    0x01: 'MB_JPD_CMD_INIT',
    0x02: 'MB_JPD_CMD_MJPG_START_DEC',
    0x03: 'MB_JPD_CMD_ABORT',
    0x04: 'MB_JPD_CMD_PAUSE',
    0x05: 'MB_JPD_CMD_RESUME',
    0x06: 'MB_JPD_CMD_IMAGE_DROP',
    0x10: 'MB_BMP_CMD_DECODE_MEM_OUT',
    0x20: 'MB_TIFF_CMD_GET_HEAD_INF',
    0x21: 'MB_TIFF_CMD_START_DEC',
    0x22: 'MB_TIFF_CMD_DECODE_MEM_OUT',
}

# Status codes
STATUS_PROCESSING = 0x00
STATUS_READY = 0xFE
STATUS_COMPLETE = 0x01


class D72N_Mailbox:
    """Mailbox IPC controller

    Traced from D72N 8051 block 02:
    - Send function: 0x2830-0x2845
    - Command dispatch: 0x22E2-0x2301
    - Sync trigger: 0x24AA-0x24B5
    - Status read: block 01: 0x4E32
    - Response read: block 03: 0x3300+
    """

    # Mailbox addresses (traced)
    ADDR_CMD = 0x4401       # Command byte
    ADDR_PARAM = 0x4402     # First param byte
    ADDR_SYNC = 0x4417      # Sync flag
    ADDR_STATUS = 0x40FB    # Status register
    ADDR_RESP = 0x40FC      # Response[0]

    MAX_PARAMS = 21         # Maximum param bytes

    def __init__(self, serdb):
        self.serdb = serdb

    def read_status(self):
        """Read mailbox status register"""
        return self.serdb.read_xdata(self.ADDR_STATUS)

    def read_command(self):
        """Read current command byte"""
        return self.serdb.read_xdata(self.ADDR_CMD)

    def read_params(self, count=8):
        """Read parameter bytes

        Args:
            count: Number of params to read

        Returns:
            List of param values
        """
        return [self.serdb.read_xdata(self.ADDR_PARAM + i) for i in range(count)]

    def read_response(self, count=4):
        """Read response bytes

        Traced from block 03 offset 0x3300+

        Args:
            count: Number of response bytes

        Returns:
            List of response values
        """
        return [self.serdb.read_xdata(self.ADDR_RESP + i) for i in range(count)]

    def read_sync(self):
        """Read sync flag"""
        return self.serdb.read_xdata(self.ADDR_SYNC)

    def is_ready(self):
        """Check if mailbox is ready for command"""
        return self.read_status() == STATUS_READY

    def wait_ready(self, timeout=1.0):
        """Wait for mailbox ready

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if ready, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            if self.is_ready():
                return True
            time.sleep(0.01)
        return False

    def send_command(self, cmd, params=None, wait=True, timeout=1.0):
        """Send mailbox command

        Traced from block 02 offset 0x2830-0x2845

        Args:
            cmd: Command byte
            params: Optional list of param bytes
            wait: Wait for completion
            timeout: Wait timeout

        Returns:
            Response bytes if wait=True, else None
        """
        # Write command (traced: 0x2835-0x2839)
        self.serdb.write_xdata(self.ADDR_CMD, cmd)

        # Write params (traced: 0x283A-0x283C)
        if params:
            for i, p in enumerate(params[:self.MAX_PARAMS]):
                self.serdb.write_xdata(self.ADDR_PARAM + i, p)

        # Trigger sync (traced: 0x24AA-0x24B5)
        for i in range(4):
            self.serdb.write_xdata(self.ADDR_SYNC + i, 0xFF)

        if wait:
            if not self.wait_ready(timeout):
                return None
            return self.read_response()

        return None

    def status(self):
        """Get detailed mailbox status

        Returns:
            Dictionary with status info
        """
        status_val = self.read_status()
        cmd = self.read_command()
        sync = self.read_sync()
        response = self.read_response()
        params = self.read_params(8)

        status_name = {
            STATUS_PROCESSING: 'Processing',
            STATUS_READY: 'Ready',
            STATUS_COMPLETE: 'Complete',
        }.get(status_val, f'Unknown (0x{status_val:02X})')

        cmd_name = MAILBOX_COMMANDS.get(cmd, f'Unknown (0x{cmd:02X})')

        return {
            'status': status_val,
            'status_name': status_name,
            'command': cmd,
            'command_name': cmd_name,
            'sync': sync,
            'params': params,
            'response': response,
        }

    def print_status(self):
        """Print formatted mailbox status"""
        status = self.status()

        print("=" * 60)
        print("Mailbox Status")
        print("=" * 60)
        print(f"Status:   0x{status['status']:02X} ({status['status_name']})")
        print(f"Command:  0x{status['command']:02X} ({status['command_name']})")
        print(f"Sync:     0x{status['sync']:02X}")
        print(f"Params:   [{', '.join(f'0x{p:02X}' for p in status['params'])}]")
        print(f"Response: [{', '.join(f'0x{r:02X}' for r in status['response'])}]")
        print()

        # Show available commands
        print("Known Commands:")
        for cmd, name in sorted(MAILBOX_COMMANDS.items()):
            marker = " <-- current" if cmd == status['command'] else ""
            print(f"  0x{cmd:02X}: {name}{marker}")


def main():
    parser = argparse.ArgumentParser(
        description='D72N Mailbox Protocol',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
    status  - Show mailbox status
    send    - Send mailbox command
    watch   - Monitor mailbox activity

Examples:
    # Show current status
    python3 d72n_mailbox.py /dev/i2c-1 status

    # Send JPEG init command
    python3 d72n_mailbox.py /dev/i2c-1 send 0x01

    # Send BMP decode with address params
    python3 d72n_mailbox.py /dev/i2c-1 send 0x10 --params 00 00 10 00

    # Monitor mailbox activity
    python3 d72n_mailbox.py /dev/i2c-1 watch

Known Commands (traced from D72N blocks):
    0x01: MB_JPD_CMD_INIT
    0x02: MB_JPD_CMD_MJPG_START_DEC
    0x10: MB_BMP_CMD_DECODE_MEM_OUT
    0x20: MB_TIFF_CMD_GET_HEAD_INF
        """
    )

    parser.add_argument('bus', help='I2C bus (e.g., /dev/i2c-1)')
    parser.add_argument('command', nargs='?', default='status',
                        choices=['status', 'send', 'watch'],
                        help='Command to execute (default: status)')
    parser.add_argument('cmd_byte', nargs='?', type=lambda x: int(x, 0),
                        help='Command byte to send (for "send" command)')
    parser.add_argument('--params', '-p', nargs='+',
                        help='Parameter bytes (hex, space-separated)')
    parser.add_argument('--no-wait', action='store_true',
                        help='Do not wait for response')
    parser.add_argument('--timeout', '-t', type=float, default=1.0,
                        help='Wait timeout in seconds (default: 1.0)')
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

            mb = D72N_Mailbox(serdb)

            if args.command == 'status':
                mb.print_status()

            elif args.command == 'send':
                if args.cmd_byte is None:
                    print("[-] Command byte required for 'send'")
                    return 1

                # Parse params
                params = None
                if args.params:
                    params = [int(p, 16) for p in args.params]

                cmd_name = MAILBOX_COMMANDS.get(args.cmd_byte, 'Unknown')
                print(f"[*] Sending command 0x{args.cmd_byte:02X} ({cmd_name})")

                if params:
                    print(f"[*] Params: [{', '.join(f'0x{p:02X}' for p in params)}]")

                response = mb.send_command(
                    args.cmd_byte,
                    params,
                    wait=not args.no_wait,
                    timeout=args.timeout
                )

                if response is not None:
                    print(f"[+] Response: [{', '.join(f'0x{r:02X}' for r in response)}]")
                elif args.no_wait:
                    print("[*] Command sent (no wait)")
                else:
                    print("[-] Timeout waiting for response")

            elif args.command == 'watch':
                print("Watching mailbox activity (Ctrl+C to stop)...")
                print()

                last_status = None
                last_cmd = None

                try:
                    while True:
                        status = mb.status()

                        # Detect changes
                        changed = (status['status'] != last_status or
                                   status['command'] != last_cmd)

                        if changed:
                            print(f"[{time.strftime('%H:%M:%S')}] "
                                  f"Status: {status['status_name']:<12} "
                                  f"Cmd: 0x{status['command']:02X} ({status['command_name']})")

                        last_status = status['status']
                        last_cmd = status['command']

                        time.sleep(args.interval)

                except KeyboardInterrupt:
                    print("\nStopped.")

    except OSError as e:
        print(f"[-] I2C error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
