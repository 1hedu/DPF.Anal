#!/usr/bin/env python3
"""
D72N SERDB Core Library
=======================

Cross-platform SERDB I2C interface for DPF-D72N digital picture frame.
Protocol based on linux-chenxing.org documentation.

SERDB I2C Address: 0x59

Supported I2C Backends:
  - Linux: smbus/smbus2 (native /dev/i2c-*)
  - Windows/macOS/Linux: pyftdi (FT232H, FT2232H USB adapters)
  - Any platform: Simulation mode for testing

Commands:
  0x10: Bus access (4-byte address, big endian)
  0x34: Disable bus access
  0x35: Enable bus access
  0x36: Resume MCU
  0x37: Stop MCU
  0x45: Exit SERDB (NAKed)
  0x51: Sent before stopping MCU
  0x53: Sent when not stopping MCU
  0x71: I2C reshape
  0x7F: Unknown (part of init)

Channels:
  0: 8051 XDATA
  3: PM RIU
  4: Non-PM RIU

Usage:
    # Linux with native I2C
    serdb = D72N_SERDB('/dev/i2c-1')

    # Windows/Mac with FTDI adapter
    serdb = D72N_SERDB('ftdi://ftdi:232h/1')

    # Simulation mode (no hardware)
    serdb = D72N_SERDB('sim://')
"""

import sys
import time

# =============================================================================
# I2C Backend Detection
# =============================================================================

# Try smbus (Linux native)
_smbus = None
try:
    import smbus2 as _smbus
except ImportError:
    try:
        import smbus as _smbus
    except ImportError:
        pass

# Try pyftdi (cross-platform USB)
_pyftdi = None
try:
    from pyftdi.i2c import I2cController
    _pyftdi = I2cController
except ImportError:
    pass

# Check what's available
def get_available_backends():
    """Return list of available I2C backends"""
    backends = ['sim']  # Simulation always available
    if _smbus:
        backends.append('smbus')
    if _pyftdi:
        backends.append('pyftdi')
    return backends


# =============================================================================
# SERDB Constants
# =============================================================================

SERDB_I2C_ADDR = 0x59

# Commands
CMD_BUS_ACCESS = 0x10       # Bus access with 4-byte address
CMD_DISABLE_ACCESS = 0x34   # Disable bus access
CMD_ENABLE_ACCESS = 0x35    # Enable bus access
CMD_RESUME_MCU = 0x36       # Resume MCU
CMD_STOP_MCU = 0x37         # Stop MCU
CMD_EXIT = 0x45             # Exit SERDB (NAKed)
CMD_BEFORE_STOP = 0x51      # Sent before stopping MCU
CMD_NOT_STOPPING = 0x53     # Sent when not stopping MCU
CMD_I2C_RESHAPE = 0x71      # I2C reshape
CMD_UNKNOWN_7F = 0x7F       # Unknown (part of init sequence)

# Channel bit commands
CMD_CH_BIT0_CLR = 0x80
CMD_CH_BIT0_SET = 0x81
CMD_CH_BIT1_CLR = 0x82
CMD_CH_BIT1_SET = 0x83
CMD_CH_BIT2_CLR = 0x84
CMD_CH_BIT2_SET = 0x85

# Channel numbers
CHANNEL_XDATA = 0       # 8051 XDATA
CHANNEL_PM_RIU = 3      # PM RIU
CHANNEL_NONPM_RIU = 4   # Non-PM RIU

# Initialization magic
SERDB_MAGIC = b'SERDB'


# =============================================================================
# I2C Backend Abstraction
# =============================================================================

class I2CBackend:
    """Abstract I2C backend interface"""

    def write_byte(self, addr, byte):
        raise NotImplementedError

    def write_bytes(self, addr, data):
        raise NotImplementedError

    def read_byte(self, addr):
        raise NotImplementedError

    def close(self):
        pass


class SMBusBackend(I2CBackend):
    """Linux smbus backend"""

    def __init__(self, bus_path):
        if _smbus is None:
            raise ImportError("smbus/smbus2 not available. Install: pip install smbus2")

        if isinstance(bus_path, str):
            if bus_path.startswith('/dev/i2c-'):
                bus_num = int(bus_path.split('-')[-1])
            elif bus_path.isdigit():
                bus_num = int(bus_path)
            else:
                raise ValueError(f"Invalid bus path: {bus_path}")
        else:
            bus_num = bus_path

        self.bus = _smbus.SMBus(bus_num)

    def write_byte(self, addr, byte):
        self.bus.write_byte(addr, byte)

    def write_bytes(self, addr, data):
        if len(data) == 1:
            self.bus.write_byte(addr, data[0])
        else:
            self.bus.write_i2c_block_data(addr, data[0], list(data[1:]))

    def read_byte(self, addr):
        return self.bus.read_byte(addr)

    def close(self):
        self.bus.close()


class PyFTDIBackend(I2CBackend):
    """Cross-platform FTDI USB-I2C backend

    Works on Windows, macOS, Linux with FT232H or FT2232H adapters.

    URLs:
      ftdi://ftdi:232h/1    - FT232H
      ftdi://ftdi:2232h/1   - FT2232H channel A
      ftdi://ftdi:2232h/2   - FT2232H channel B
    """

    def __init__(self, url):
        if _pyftdi is None:
            raise ImportError("pyftdi not available. Install: pip install pyftdi")

        self.ctrl = I2cController()
        self.ctrl.configure(url)
        self._port = None

    def _get_port(self, addr):
        if self._port is None or self._port.address != addr:
            self._port = self.ctrl.get_port(addr)
        return self._port

    def write_byte(self, addr, byte):
        port = self._get_port(addr)
        port.write([byte])

    def write_bytes(self, addr, data):
        port = self._get_port(addr)
        port.write(list(data))

    def read_byte(self, addr):
        port = self._get_port(addr)
        result = port.read(1)
        return result[0] if result else 0

    def close(self):
        self.ctrl.terminate()


class SimulationBackend(I2CBackend):
    """Simulation backend for testing without hardware

    Maintains a simulated memory space for XDATA and DRAM.
    """

    def __init__(self):
        self.xdata = bytearray(65536)  # 64KB XDATA
        self.dram = bytearray(0x200000)  # 2MB DRAM
        self._dram_high_byte = 0
        self._last_addr = 0
        print("[SIM] Simulation mode - no hardware connected")

    def write_byte(self, addr, byte):
        # Just track commands
        pass

    def write_bytes(self, addr, data):
        if len(data) >= 5 and data[0] == CMD_BUS_ACCESS:
            # Bus access command
            full_addr = (data[1] << 24) | (data[2] << 16) | (data[3] << 8) | data[4]
            self._last_addr = full_addr

            if len(data) > 5:
                # Write operation
                if full_addr == 0x0000:
                    self._dram_high_byte = data[5]
                elif full_addr < 0x10000:
                    self.xdata[full_addr] = data[5]

    def read_byte(self, addr):
        # Return from last accessed address
        if self._last_addr < 0x10000:
            return self.xdata[self._last_addr]
        return 0

    def close(self):
        pass


def create_backend(bus_spec):
    """Create appropriate I2C backend based on bus specification

    Args:
        bus_spec: One of:
            - '/dev/i2c-1' or '1' - Linux smbus
            - 'ftdi://...' - FTDI USB adapter
            - 'sim://' - Simulation mode

    Returns:
        I2CBackend instance
    """
    if isinstance(bus_spec, int):
        return SMBusBackend(bus_spec)

    if bus_spec.startswith('sim://') or bus_spec == 'sim':
        return SimulationBackend()

    if bus_spec.startswith('ftdi://'):
        return PyFTDIBackend(bus_spec)

    if bus_spec.startswith('/dev/i2c-') or bus_spec.isdigit():
        return SMBusBackend(bus_spec)

    raise ValueError(f"Unknown bus specification: {bus_spec}\n"
                     f"Available backends: {get_available_backends()}")


# =============================================================================
# Main SERDB Class
# =============================================================================

class D72N_SERDB:
    """D72N SERDB I2C interface using proper protocol

    Provides access to:
    - XDATA: 8051 memory space (channel 0)
    - PM RIU: Power management registers (channel 3)
    - Non-PM RIU: Peripheral registers (channel 4)

    Works on:
    - Linux: native I2C via smbus
    - Windows/macOS: FTDI USB adapters via pyftdi
    - Any platform: simulation mode for testing
    """

    def __init__(self, i2c_bus, addr=SERDB_I2C_ADDR, auto_init=True):
        """Initialize SERDB interface

        Args:
            i2c_bus: Bus specification:
                - '/dev/i2c-1' or '1' for Linux
                - 'ftdi://ftdi:232h/1' for FTDI adapter
                - 'sim://' for simulation
            addr: SERDB I2C address (default 0x59)
            auto_init: Automatically initialize SERDB on creation
        """
        self.backend = create_backend(i2c_bus)
        self.addr = addr
        self._delay = 0.001  # 1ms between operations
        self._current_channel = None
        self._initialized = False

        if auto_init:
            self.init()

    def close(self):
        """Close SERDB session and I2C bus"""
        if self._initialized:
            self._exit_serdb()
        self.backend.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ==========================================================================
    # Low-level I2C operations
    # ==========================================================================

    def _write_byte(self, byte):
        """Write a single command byte"""
        self.backend.write_byte(self.addr, byte)
        time.sleep(self._delay)

    def _write_bytes(self, data):
        """Write multiple bytes"""
        if isinstance(data, int):
            data = bytes([data])
        self.backend.write_bytes(self.addr, data)
        time.sleep(self._delay)

    def _read_byte(self):
        """Read a single byte"""
        time.sleep(self._delay)
        return self.backend.read_byte(self.addr)

    # ==========================================================================
    # SERDB Protocol
    # ==========================================================================

    def _write_magic(self):
        """Write SERDB initialization magic string"""
        self._write_bytes(SERDB_MAGIC)

    def _set_channel(self, channel):
        """Set bus channel using bit commands"""
        if self._current_channel == channel:
            return

        # Set bit 0
        self._write_byte(CMD_CH_BIT0_SET if channel & 0x01 else CMD_CH_BIT0_CLR)
        # Set bit 1
        self._write_byte(CMD_CH_BIT1_SET if channel & 0x02 else CMD_CH_BIT1_CLR)
        # Set bit 2
        self._write_byte(CMD_CH_BIT2_SET if channel & 0x04 else CMD_CH_BIT2_CLR)

        self._current_channel = channel

    def _init_sequence(self):
        """Send initialization sequence: 0x53, 0x7F, 0x35, 0x71"""
        self._write_byte(CMD_NOT_STOPPING)   # 0x53
        self._write_byte(CMD_UNKNOWN_7F)     # 0x7F
        self._write_byte(CMD_ENABLE_ACCESS)  # 0x35
        self._write_byte(CMD_I2C_RESHAPE)    # 0x71

    def _bus_access(self, addr, read=True, write_data=None):
        """Perform bus access with 4-byte big-endian address"""
        cmd = bytes([
            CMD_BUS_ACCESS,
            (addr >> 24) & 0xFF,
            (addr >> 16) & 0xFF,
            (addr >> 8) & 0xFF,
            addr & 0xFF
        ])

        if write_data is not None:
            cmd = cmd + bytes([write_data])

        self._write_bytes(cmd)

        if read:
            return self._read_byte()
        return None

    def _exit_serdb(self):
        """Send exit sequence: 0x34 then 0x45"""
        try:
            self._write_byte(CMD_DISABLE_ACCESS)
            self._write_byte(CMD_EXIT)
        except OSError:
            pass  # Expected NAK on 0x45
        self._initialized = False

    def init(self):
        """Initialize SERDB session"""
        self._write_magic()
        self._set_channel(CHANNEL_XDATA)
        self._init_sequence()
        self._initialized = True
        self._current_channel = CHANNEL_XDATA

    def reinit(self):
        """Re-initialize after errors"""
        self._current_channel = None
        self._initialized = False
        self.init()

    # ==========================================================================
    # XDATA Access (Channel 0)
    # ==========================================================================

    def read_xdata(self, addr):
        """Read byte from XDATA (16-bit address space)"""
        self._set_channel(CHANNEL_XDATA)
        return self._bus_access(addr & 0xFFFF, read=True)

    def write_xdata(self, addr, value):
        """Write byte to XDATA"""
        self._set_channel(CHANNEL_XDATA)
        self._bus_access(addr & 0xFFFF, read=False, write_data=value & 0xFF)

    def read_xdata_range(self, start, length):
        """Read range of bytes from XDATA"""
        self._set_channel(CHANNEL_XDATA)
        return bytes(self.read_xdata(start + i) for i in range(length))

    # ==========================================================================
    # DRAM Access via XDMIU
    # ==========================================================================

    def read_dram(self, addr):
        """Read byte from DRAM (24-bit address via XDMIU)"""
        self._set_channel(CHANNEL_XDATA)
        # Set high address byte at 0x0000
        self._bus_access(0x0000, read=False, write_data=(addr >> 16) & 0xFF)
        # Access low 16 bits
        return self._bus_access(addr & 0xFFFF, read=True)

    def write_dram(self, addr, value):
        """Write byte to DRAM"""
        self._set_channel(CHANNEL_XDATA)
        self._bus_access(0x0000, read=False, write_data=(addr >> 16) & 0xFF)
        self._bus_access(addr & 0xFFFF, read=False, write_data=value & 0xFF)

    def read_dram_range(self, start, length, progress=False):
        """Read range of bytes from DRAM"""
        data = bytearray(length)
        for i in range(length):
            data[i] = self.read_dram(start + i)
            if progress and (i % 1024 == 0):
                pct = (i * 100) // length
                print(f"\rReading: {pct}%", end='', flush=True)
        if progress:
            print("\rReading: 100%")
        return bytes(data)

    # ==========================================================================
    # RIU Access
    # ==========================================================================

    def read_riu(self, bank, offset, pm=False):
        """Read 16-bit RIU register"""
        self._set_channel(CHANNEL_PM_RIU if pm else CHANNEL_NONPM_RIU)
        addr = (bank << 8) | (offset & 0xFF)
        low = self._bus_access(addr, read=True)
        high = self._bus_access(addr + 1, read=True)
        return (high << 8) | low

    def write_riu(self, bank, offset, value, pm=False):
        """Write 16-bit RIU register"""
        self._set_channel(CHANNEL_PM_RIU if pm else CHANNEL_NONPM_RIU)
        addr = (bank << 8) | (offset & 0xFF)
        self._bus_access(addr, read=False, write_data=value & 0xFF)
        self._bus_access(addr + 1, read=False, write_data=(value >> 8) & 0xFF)

    # ==========================================================================
    # MCU Control
    # ==========================================================================

    def stop_mcu(self):
        """Stop the MCU (8051)"""
        self._write_byte(CMD_BEFORE_STOP)
        self._write_byte(CMD_STOP_MCU)

    def resume_mcu(self):
        """Resume the MCU (8051)"""
        self._write_byte(CMD_RESUME_MCU)

    # ==========================================================================
    # Utility
    # ==========================================================================

    def probe(self):
        """Probe SERDB connection"""
        try:
            if not self._initialized:
                self.init()
            self.read_xdata(0x0000)
            return True
        except OSError:
            return False

    def hexdump(self, data, start_addr=0, width=16):
        """Format data as hex dump"""
        lines = []
        for i in range(0, len(data), width):
            chunk = data[i:i+width]
            hex_part = ' '.join(f'{b:02X}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            lines.append(f"{start_addr + i:06X}  {hex_part:<{width*3}}  {ascii_part}")
        return '\n'.join(lines)


# =============================================================================
# D72N Addresses
# =============================================================================

class D72N_ADDR:
    """D72N traced addresses from documentation"""

    # Mailbox
    MAILBOX_CMD = 0x4401
    MAILBOX_PARAM = 0x4402
    MAILBOX_SYNC = 0x4417
    MAILBOX_STATUS = 0x40FB

    # AEON Control
    AEON_CTRL = 0x0FE6

    # Watchdog
    WDT_STATE = 0x44CE
    WDT_COUNTER_LO = 0x44D3
    WDT_COUNTER_HI = 0x44D4

    # DRAM Buffers
    DRAM_MAIN_BUFFER = 0x100000
    DRAM_SECONDARY = 0x0C0000
    DRAM_OUTPUT = 0x150000


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='D72N SERDB Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Linux with native I2C
    python d72n_serdb.py /dev/i2c-1 --probe

    # Windows/macOS with FTDI FT232H adapter
    python d72n_serdb.py ftdi://ftdi:232h/1 --probe

    # Simulation mode (no hardware)
    python d72n_serdb.py sim:// --probe

    # Read XDATA
    python d72n_serdb.py /dev/i2c-1 --read-xdata 0x4401

    # Read DRAM
    python d72n_serdb.py /dev/i2c-1 --read-dram 0x100000

Available backends: """ + ', '.join(get_available_backends())
    )

    parser.add_argument('bus', help='I2C bus (see examples above)')
    parser.add_argument('--probe', action='store_true', help='Probe connection')
    parser.add_argument('--read-xdata', type=lambda x: int(x, 0), metavar='ADDR')
    parser.add_argument('--read-dram', type=lambda x: int(x, 0), metavar='ADDR')
    parser.add_argument('--write-xdata', nargs=2, metavar=('ADDR', 'VAL'))
    parser.add_argument('--write-dram', nargs=2, metavar=('ADDR', 'VAL'))
    parser.add_argument('--dump-xdata', nargs=2, type=lambda x: int(x, 0),
                        metavar=('START', 'LEN'), help='Dump XDATA range')
    parser.add_argument('--dump-dram', nargs=2, type=lambda x: int(x, 0),
                        metavar=('START', 'LEN'), help='Dump DRAM range')
    parser.add_argument('--stop-mcu', action='store_true')
    parser.add_argument('--resume-mcu', action='store_true')

    args = parser.parse_args()

    try:
        with D72N_SERDB(args.bus) as serdb:
            if args.probe:
                if serdb.probe():
                    print("[+] SERDB responding at 0x59")
                else:
                    print("[-] SERDB not responding")
                    return 1

            if args.stop_mcu:
                serdb.stop_mcu()
                print("[+] MCU stopped")

            if args.resume_mcu:
                serdb.resume_mcu()
                print("[+] MCU resumed")

            if args.read_xdata is not None:
                val = serdb.read_xdata(args.read_xdata)
                print(f"XDATA[0x{args.read_xdata:04X}] = 0x{val:02X}")

            if args.read_dram is not None:
                val = serdb.read_dram(args.read_dram)
                print(f"DRAM[0x{args.read_dram:06X}] = 0x{val:02X}")

            if args.dump_xdata:
                start, length = args.dump_xdata
                data = serdb.read_xdata_range(start, length)
                print(serdb.hexdump(data, start))

            if args.dump_dram:
                start, length = args.dump_dram
                data = serdb.read_dram_range(start, length, progress=True)
                print(serdb.hexdump(data, start))

            if args.write_xdata:
                addr, val = int(args.write_xdata[0], 0), int(args.write_xdata[1], 0)
                serdb.write_xdata(addr, val)
                print(f"Wrote 0x{val:02X} to XDATA[0x{addr:04X}]")

            if args.write_dram:
                addr, val = int(args.write_dram[0], 0), int(args.write_dram[1], 0)
                serdb.write_dram(addr, val)
                print(f"Wrote 0x{val:02X} to DRAM[0x{addr:06X}]")

    except ImportError as e:
        print(f"[-] Missing dependency: {e}")
        print(f"    Available backends: {get_available_backends()}")
        return 1
    except OSError as e:
        print(f"[-] I2C error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
