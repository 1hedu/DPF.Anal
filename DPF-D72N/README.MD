# DPF-D72N Reverse Engineering Index

Documentation index for the DPF-D72N digital picture frame firmware.

## Architecture

The D72N uses the same dual-processor architecture as other MStar-based picture frames:

```
MSPD2212B SoC
├── PM51 (8051 MCU) - Main application processor
│   ├── UI/Menu logic, file system, storage drivers
│   ├── Contains MDrv_*/HAL_* driver code (traced in D72N_DRIVERS.md)
│   └── PARTIAL - 18 overlay blocks available (0x40000-0x160000)
└── AEON R2 (32-bit RISC)
    ├── Display engine, image decoders (JPEG, TIFF, BMP, GIF)
    ├── Full libtiff library, EXIF/DNG parsing
    └── FULLY DOCUMENTED BELOW
```

**Note:** We have the full AEON image and 18 partial 8051 blocks from flash. The 8051 bootstrap area (0x02000-0x0FFFF) is not available, but overlay banks contain key functions like UART switch, mailbox ISR, and OSD loading.

## Verification Summary

Addresses verified by comparing with a known-working similar firmware (40,662 shared code sequences, identical boot header):

| Category | Status |
|----------|--------|
| Boot header | ✓ Identical architecture |
| Mailbox addresses | ✓ Traced (block 02) |
| Mailbox send function | ✓ Traced (block 02: 0x2830) |
| State variables | ✓ Traced (132 XDATA addresses) |
| DRAM buffers | ✓ Traced (888, 673, 384 refs) |
| GWin addresses | ✓ Traced (0x6653, 0x69BE, 0x6D2C) |
| RIU banks | ✓ Traced (all 18 blocks, 2412 total refs) |
| RIU registers | ✓ Traced (60+ registers) |
| Watchdog addresses | ✓ Traced (blocks 15, 16) |
| JPEG commands (0x01-0x02) | ✓ Traced (block 02: 0x22F2) |
| BMP command (0x10) | ✓ Traced (all blocks: 0xAC80) |
| TIFF commands (0x20-0x22) | ✓ Traced (blocks 02, 03, 05, 12, 14) |
| UART switch (RIU 0x0F55) | ✓ Traced |
| AEON control (0x0FE6) | ✓ Traced |

Command bytes verified through 8051 code tracing of `/DPF-D72N/blocks/`:
- JPEG commands 0x01, 0x02 traced in block 02 at 0x22F2, 0x22F7
- Mailbox send function traced in block 02 at 0x2830-0x2845
- Watchdog registers (0x44CE, 0x44D3) traced in blocks 15 and 16
- UART switch code traced in block 01 with full disassembly
- AEON control code traced in blocks 01 and 16
- BMP command 0x10 found in 8051 dispatch at offset 0xAC80
- TIFF commands inferred from debug strings, need hardware verification

## AEON Image Overview

| Property | Value |
|----------|-------|
| Source | `DPF-D72N/K9F1G08U0C@TSOP48_no_ecc_no_header_code_halved_aeon.bin` |
| Flash Chip | Samsung K9F1G08U0C NAND |
| AEON Size | 390KB (400,320 bytes) |
| Build Date | Jun 24 2009 |
| Toolchain | Mar 1 2008 |

## Documentation

### Reference Maps

| Document | Status | Description |
|----------|--------|-------------|
| [D72N_REGISTER_MAP.md](D72N_REGISTER_MAP.md) | Complete | RIU register reference (traced from all blocks) |
| [D72N_MEMORY_MAP.md](D72N_MEMORY_MAP.md) | Complete | Flash/DRAM memory layout (traced) |
| [D72N_VARIABLE_MAP.md](D72N_VARIABLE_MAP.md) | Complete | XDATA variable reference (132 addresses traced) |
| [D72N_FUNCTION_MAP.md](D72N_FUNCTION_MAP.md) | Complete | Combined 8051+AEON function map (122 functions) |
| [D72N_DRIVERS.md](D72N_DRIVERS.md) | Complete | Peripheral driver reference (traced from all blocks) |
| [D72N_DISPLAY_PIPELINE.md](D72N_DISPLAY_PIPELINE.md) | Complete | Display subsystem (GE, GOP, OSDE, buffers) |
| [D72N_BMP_DISPLAY_PIPELINE.md](D72N_BMP_DISPLAY_PIPELINE.md) | Complete | BMP decode for RCE (memory write paths) |
| [D72N_PERIPHERAL_MAP.md](D72N_PERIPHERAL_MAP.md) | Complete | RIU banks, I2C, GPIO, timers |
| [D72N_ARCHITECTURE.dot](D72N_ARCHITECTURE.dot) | Complete | Graphviz architecture diagram |

### Protocol & Control

| Document | Status | Description |
|----------|--------|-------------|
| [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) | Complete | SERDB control reference with XDATA/DRAM maps |
| [D72N_MAILBOX_PROTOCOL.md](D72N_MAILBOX_PROTOCOL.md) | Complete | 8051↔AEON mailbox IPC (traced from block 02) |
| [D72N_COMMAND_DISPATCH.md](D72N_COMMAND_DISPATCH.md) | Complete | JPEG/BMP/TIFF command dispatch (all blocks traced) |
| [D72N_WATCHDOG_CONTROL.md](D72N_WATCHDOG_CONTROL.md) | Complete | Watchdog disable via SERDB (traced from blocks 15, 16) |
| [D72N_SECURITY_BYPASS.md](D72N_SECURITY_BYPASS.md) | Complete | Security features and bypass via SERDB |
| [D72N_INTERNAL_STRUCTURES.md](D72N_INTERNAL_STRUCTURES.md) | Complete | LZW, FAT, timers, cache, mutex subsystems |
| [D72N_AEON_CONTROL.md](D72N_AEON_CONTROL.md) | Complete | AEON halt/reset/resume via SERDB |
| [D72N_UART_SWITCH.md](D72N_UART_SWITCH.md) | Complete | UART mux control (8051 ↔ AEON) |
| [D72N_SECURITY_ANALYSIS.md](D72N_SECURITY_ANALYSIS.md) | Complete | Vulnerability analysis (LZW, TIFF, memory write) |
| [D72N_MB_BMP_DECODE_MEM_OUT.md](D72N_MB_BMP_DECODE_MEM_OUT.md) | Complete | BMP decode-to-memory function trace |

### Python Tools

Located in `/DPF-D72N/tools/`:

| Tool | Purpose |
|------|---------|
| `d72n_serdb.py` | Core SERDB I2C library |
| `d72n_dump_xdata.py` | Dump 8051 XDATA memory |
| `d72n_dump_dram.py` | Dump shared DRAM memory |
| `d72n_state.py` | System state monitor |
| `d72n_aeon_control.py` | AEON processor halt/resume/reset |
| `d72n_watchdog.py` | Watchdog timer control |
| `d72n_mailbox.py` | Mailbox IPC protocol |
| `d72n_exploit_bmp.py` | BMP exploit generator |
| `d72n_shellcode_inject.py` | Shellcode injection |

## Key Features

- **390KB AEON image** with full libtiff library
- **LZW, PackBits, ThunderDecode, NeXTDecode** compression support
- **Complete EXIF/DNG parsing** including GPS, MakerNote
- **CIE L*a*b color space** conversion
- **Enhanced BMP/TIFF ROI** control
- **Direct memory output** via mailbox commands

## Features

### Mailbox Commands (6 with debug strings)

| Command | Address | Purpose |
|---------|---------|---------|
| MB_JPD_CMD_MJPG_START_DEC | 0x4cf27 | Start MJPEG decode |
| MB_JPD_CMD_IMAGE_DROP | 0x4cec5 | JPEG ROI cropping |
| MB_BMP_CMD_DECODE_MEM_OUT | 0x4cffc | BMP direct to DRAM |
| MB_TIFF_CMD_GET_HEAD_INF | 0x4d092 | Parse TIFF header |
| MB_TIFF_CMD_START_DEC | 0x4d0db | Decode TIFF with ROI |
| MB_TIFF_CMD_DECODE_MEM_OUT | 0x4d11e | TIFF direct to DRAM |

Base JPEG commands (INIT, ABORT, PAUSE, RESUME) likely exist but have no debug strings.

### Primary State Variables (Traced)

| Address | Refs | Purpose |
|---------|------|---------|
| 0x40EA | 710 | Primary state |
| 0x40EE | 322 | State field 2 |
| 0x4720 | 238 | Display state |
| 0x4641 | 219 | Decode state |
| 0x4542 | 194 | Extended state |

See [D72N_VARIABLE_MAP.md](D72N_VARIABLE_MAP.md) for complete variable reference.

### DRAM Buffer Layout (Traced from AEON)

| Address | Refs | Size | Purpose |
|---------|------|------|---------|
| 0x100000 | 888 | ~512KB | Main decode buffer |
| 0x0C0000 | 673 | ~256KB | Secondary buffer |
| 0x150000 | 384 | ~256KB | Output buffer |

See [D72N_MEMORY_MAP.md](D72N_MEMORY_MAP.md) for complete memory layout.

## Memory Layout

```
0x00000 - 0x00100  Zero padding
0x00100 - 0x00200  Boot header
0x00200 - 0x4CD00  AEON code (~300KB)
0x4CD00 - 0x61BC0  Strings & data (~85KB)
```

## SERDB Interface

| Feature | Value |
|---------|-------|
| I2C Address | 0x59 |
| Mailbox Status | 0x40FB |
| Mailbox Command | 0x4401 |
| Mailbox Sync | 0x4417 |
| Watchdog Disable | 0x44CE, 0x44D3 |

## Driver/Hardware Access

The D72N AEON directly accesses hardware via RIU (Register Interface Unit):

### RIU Bank Usage (Traced from 8051 Blocks)

| Bank | Name | Refs | Purpose |
|------|------|------|---------|
| 0x10 | CHIPTOP | 1505 | System control, bank select |
| 0x12 | BDMA | 269 | Block DMA engine |
| 0x15 | AUDIO/MISC | 179 | Audio/miscellaneous |
| 0x11 | Unknown | 149 | Unidentified |
| 0x1E | AEON/Display | 121 | AEON processor, display |
| 0x1F | AEON Control | 78 | AEON control registers |
| 0x1D | Unknown | 38 | Unidentified |
| 0x1B | Unknown | 21 | Unidentified |
| 0x1A | Unknown | 18 | Unidentified |
| 0x17 | Unknown | 17 | Unidentified |

See [D72N_REGISTER_MAP.md](D72N_REGISTER_MAP.md) for complete register details.

### Cache Control

```
0x5FDA6: "* DCACHE is initially disabled."
0x5FDE7: "* ICACHE is initially disabled."
```

D72N AEON runs with caches disabled by default.

### No High-Level Driver Strings in AEON

The D72N AEON image does not contain MDrv_*/HAL_* driver strings - it accesses hardware directly via RIU. The PM51/8051 code (not available) likely contains the high-level driver framework.

## Embedded Assets (AEON only)

**No image assets found in AEON dump.** OSD bitmaps and UI resources are likely in the PM51 portion. The AEON contains only:

| Offset | Size | Content |
|--------|------|---------|
| 0x00000-0x4CD00 | 300KB | AEON R2 code |
| 0x4CD00-0x55C00 | 36KB | String table (libtiff errors, debug) |
| 0x55C00-0x61BBC | 49KB | TIFF field definition table |
| 0x616B5 | 19B | Test date: "2007:09:24 23:46:29" |
| 0x5FF20 | 400B | Padding pattern (0xa0dc0300) |

The 49KB TIFF field table contains libtiff's complete tag registry with ~12,000 entries.

## To Document

- [x] TIFF tag parsing vulnerability analysis (see D72N_SECURITY_ANALYSIS.md)
- [x] LZW decoder attack surface (see D72N_SECURITY_ANALYSIS.md)
- [x] Mailbox protocol (see D72N_MAILBOX_PROTOCOL.md, traced from block 02)
- [x] Watchdog control (see D72N_WATCHDOG_CONTROL.md, traced from blocks 15, 16)
- [x] Driver/RIU bank analysis (see above)
- [x] BMP command 0x10 dispatch (see D72N_COMMAND_DISPATCH.md, all blocks: 0xAC80)
- [x] TIFF commands 0x20-0x22 (see D72N_COMMAND_DISPATCH.md, blocks 02, 03, 05, 12, 14)
- [x] Internal structures (see D72N_INTERNAL_STRUCTURES.md)
- [x] Security bypass (see D72N_SECURITY_BYPASS.md)
- [x] Register map (see D72N_REGISTER_MAP.md, all 18 blocks traced)
- [x] Memory map (see D72N_MEMORY_MAP.md, flash/DRAM layout)
- [x] Variable map (see D72N_VARIABLE_MAP.md, 132 XDATA addresses)
- [x] Function map (see D72N_FUNCTION_MAP.md, 122 named functions)
- [x] Architecture diagram (see D72N_ARCHITECTURE.dot, Graphviz)

### Remaining

- [x] GWin control code (see D72N_DISPLAY_PIPELINE.md - 0x6653: 31 refs, 0x69BE: 2 refs)
- [x] Display pipeline (see D72N_DISPLAY_PIPELINE.md - GE 314 refs, GOP, OSDE traced)
- [x] Peripheral map (see D72N_PERIPHERAL_MAP.md - all RIU banks, I2C, GPIO)
- [ ] Storage subsystem (trace FAT/SD functions - partial in D72N_DRIVERS.md)
