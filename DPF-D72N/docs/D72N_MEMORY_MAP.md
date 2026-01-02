# D72N Memory Map

Flash and DRAM memory layout for the DPF-D72N, traced from firmware analysis.

## Overview

The D72N uses a dual-processor architecture with shared memory:

```
DPF-D72N Memory Architecture
├── Flash (NAND: Samsung K9F1G08U0C, 1Gbit = 128MB)
│   ├── 8051 Bootstrap (0x02000-0x0FFFF) - Not available
│   ├── 8051 Overlays (0x40000-0x160000) - 18 × 64KB blocks
│   └── AEON Image (after NAND processing) - 390KB
└── DRAM
    ├── 0x000000-0x0BFFFF - System/Reserved
    ├── 0x0C0000-0x0FFFFF - Secondary buffer (~256KB)
    ├── 0x100000-0x17FFFF - Main decode buffer (~512KB)
    └── 0x150000-0x1AFFFF - Output buffer (~256KB)
```

---

## Flash Layout

### Source

| Property | Value |
|----------|-------|
| Flash Chip | Samsung K9F1G08U0C NAND |
| Capacity | 1Gbit (128MB) |
| Page Size | 2KB + 64B spare |
| Block Size | 64 pages = 128KB + 4KB spare |

### 8051 Overlay Blocks (Traced)

18 overlay blocks extracted from flash, each 64KB:

| Block | Flash Range | Bank | File | Status |
|-------|-------------|------|------|--------|
| 01 | 0x40000-0x4FFFF | 0x01 | block_01_0x40000-0x50000.bin | ✓ Traced |
| 02 | 0x50000-0x5FFFF | 0x02 | block_02_0x50000-0x60000.bin | ✓ Traced |
| 03 | 0x60000-0x6FFFF | 0x03 | block_03_0x60000-0x70000.bin | ✓ Traced |
| 04 | 0x70000-0x7FFFF | 0x04 | block_04_0x70000-0x80000.bin | ✓ Traced |
| 05 | 0x80000-0x8FFFF | 0x05 | block_05_0x80000-0x90000.bin | ✓ Traced |
| 06 | 0x90000-0x9FFFF | 0x06 | block_06_0x90000-0xA0000.bin | ✓ Traced |
| 07 | 0xA0000-0xAFFFF | 0x07 | block_07_0xA0000-0xB0000.bin | ✓ Traced |
| 08 | 0xB0000-0xBFFFF | 0x08 | block_08_0xB0000-0xC0000.bin | ✓ Traced |
| 09 | 0xC0000-0xCFFFF | 0x09 | block_09_0xC0000-0xD0000.bin | ✓ Traced |
| 10 | 0xD0000-0xDFFFF | 0x0A | block_10_0xD0000-0xE0000.bin | ✓ Traced |
| 11 | 0xE0000-0xEFFFF | 0x0B | block_11_0xE0000-0xF0000.bin | ✓ Traced |
| 12 | 0xF0000-0xFFFFF | 0x0C | block_12_0xF0000-0x100000.bin | ✓ Traced |
| 13 | 0x100000-0x10FFFF | 0x0D | block_13_0x100000-0x110000.bin | ✓ Traced |
| 14 | 0x110000-0x11FFFF | 0x0E | block_14_0x110000-0x120000.bin | ✓ Traced |
| 15 | 0x120000-0x12FFFF | 0x0F | block_15_0x120000-0x130000.bin | ✓ Traced |
| 16 | 0x130000-0x13FFFF | 0x10 | block_16_0x130000-0x140000.bin | ✓ Traced |
| 17 | 0x140000-0x14FFFF | 0x11 | block_17_0x140000-0x150000.bin | ✓ Traced |
| 18 | 0x150000-0x15FFFF | 0x12 | block_18_0x150000-0x160000.bin | ✓ Traced |

**Total 8051 overlay size:** 18 × 64KB = 1,152KB (1.125MB)

### AEON Image

| Property | Value |
|----------|-------|
| File | K9F1G08U0C@TSOP48_no_ecc_no_header_code_halved_aeon.bin |
| Size | 400,320 bytes (390KB) |
| Build Date | Jun 24 2009 |
| Toolchain | Mar 1 2008 |

#### AEON Internal Layout

| Offset | Size | Content | Status |
|--------|------|---------|--------|
| 0x00000-0x000FF | 256B | Zero padding | ✓ Verified |
| 0x00100-0x001FF | 256B | Boot header | ✓ Verified |
| 0x00200-0x4CCFF | ~300KB | AEON R2 code | ✓ Verified |
| 0x4CD00-0x55BFF | ~36KB | String table | ✓ Verified |
| 0x55C00-0x61BBF | ~49KB | TIFF field table | ✓ Verified |
| 0x616B5 | 19B | Test date: "2007:09:24 23:46:29" | ✓ Verified |
| 0x5FF20 | ~400B | Padding (0xa0dc0300) | ✓ Verified |

---

## DRAM Layout

### Buffer Addresses (Traced from AEON)

| Address | Refs | Size (est) | Purpose | Status |
|---------|------|------------|---------|--------|
| 0x0C0000 | 673 | ~256KB | Secondary buffer | ✓ Traced |
| 0x100000 | 888 | ~512KB | Main decode buffer | ✓ Traced |
| 0x150000 | 384 | ~256KB | Output buffer | ✓ Traced |

### Buffer Sub-regions (Traced)

| Address | Refs | Purpose |
|---------|------|---------|
| 0x100100 | 152 | Main buffer +0x100 |
| 0x100600 | 126 | Main buffer +0x600 |
| 0x100400 | 121 | Main buffer +0x400 |
| 0x0C0100 | 84 | Secondary +0x100 |
| 0x0C0600 | 83 | Secondary +0x600 |
| 0x100700 | 79 | Main buffer +0x700 |
| 0x100800 | 78 | Main buffer +0x800 |
| 0x100030 | 74 | Main buffer +0x30 |
| 0x0C0400 | 68 | Secondary +0x400 |
| 0x150100 | 67 | Output +0x100 |
| 0x100200 | 66 | Main buffer +0x200 |
| 0x150400 | 56 | Output +0x400 |
| 0x0C0700 | 55 | Secondary +0x700 |
| 0x101004 | 52 | Main buffer +0x1004 |
| 0x0C0200 | 49 | Secondary +0x200 |
| 0x10FFFF | 42 | Main buffer end |
| 0x0CFFFF | 41 | Secondary end |

### DRAM Map Diagram

```
DRAM Address Space
==================
0x000000 ┌─────────────────────────────┐
         │   System/Reserved           │
         │   (AEON code, stack, etc.)  │
0x0C0000 ├─────────────────────────────┤
         │   Secondary Buffer          │  673 refs
         │   ~256KB                    │
         │   +0x100: 84 refs           │
         │   +0x400: 68 refs           │
         │   +0x600: 83 refs           │
0x100000 ├─────────────────────────────┤
         │   Main Decode Buffer        │  888 refs (most used)
         │   ~512KB                    │
         │   +0x030: 74 refs           │
         │   +0x100: 152 refs          │
         │   +0x200: 66 refs           │
         │   +0x400: 121 refs          │
         │   +0x600: 126 refs          │
         │   +0x700: 79 refs           │
         │   +0x800: 78 refs           │
0x150000 ├─────────────────────────────┤
         │   Output Buffer             │  384 refs
         │   ~256KB                    │
         │   +0x100: 67 refs           │
         │   +0x400: 56 refs           │
0x1B0000 └─────────────────────────────┘
```

---

## AEON Memory Map

AEON R2 uses a 32-bit address space:

| Base Address | Name | Purpose |
|--------------|------|---------|
| 0x00000000 | DRAM | Shared memory with 8051 |
| 0x90000000 | UART | UART output |
| 0xA0000000 | RIU | Register Interface Unit |
| 0xC0000000 | QMEM | Quick memory (cache) |
| 0xF0000000 | SPI | SPI flash XIP base |

### AEON RIU Access

```
; AEON accesses RIU at 0xA0001xxx
; Example: JPEG status at RIU 0x1ECF
; AEON address = 0xA0001ECF

LW   r3, [0xA0001ECF]    ; Read JPEG status
```

---

## 8051 XDATA Map

8051 uses 64KB XDATA space for peripherals and variables:

| Range | Purpose | Status |
|-------|---------|--------|
| 0x0000-0x00FF | SFR mirror | ✓ Standard |
| 0x0100-0x0FFF | System area | ✓ Traced |
| 0x1000-0x1FFF | RIU access | ✓ Traced |
| 0x2000-0x3FFF | Reserved | ○ Unknown |
| 0x4000-0x4FFF | Mailbox/State | ✓ Traced |
| 0x5000-0x5FFF | Extended state | ✓ Traced |
| 0x6000-0x6FFF | GWin/Display | ✓ Traced |
| 0x7000-0xFFFF | Buffers/Stack | ○ Partial |

---

## SERDB Memory Access

Access all memory regions via SERDB I2C:

```python
# SERDB I2C address: 0x59
# Channels:
#   0x80 = XDATA (64KB)
#   0x81 = DRAM (24-bit)
#   0x83 = PM RIU
#   0x84 = Non-PM RIU

def read_xdata(addr):
    """Read 8051 XDATA (16-bit address)"""
    bus.write_i2c_block_data(0x59, 0x80, [addr >> 8, addr & 0xFF])
    return bus.read_byte(0x59)

def read_dram(addr):
    """Read DRAM (24-bit address)"""
    bus.write_i2c_block_data(0x59, 0x81, [
        (addr >> 16) & 0xFF,
        (addr >> 8) & 0xFF,
        addr & 0xFF
    ])
    return bus.read_byte(0x59)

# Dump main decode buffer
def dump_decode_buffer(length=256):
    data = []
    for i in range(length):
        data.append(read_dram(0x100000 + i))
    return bytes(data)
```

---

## Bank Switching

8051 uses bank switching to access overlay code:

```asm
; Bank switch via RIU 0x1019
; Traced from block 01 offset 0x1114

90 10 19     MOV  DPTR,#0x1019    ; Bank select register
74 02        MOV  A,#0x02         ; Bank 2
F0           MOVX @DPTR,A         ; Switch to bank 2
```

| Bank Value | Flash Range | Code Type |
|------------|-------------|-----------|
| 0x01 | 0x40000-0x4FFFF | AEON control, UART switch |
| 0x02 | 0x50000-0x5FFFF | Mailbox, JPEG commands |
| 0x05 | 0x80000-0x8FFFF | FAT filesystem |
| 0x08 | 0xB0000-0xBFFFF | FAT partition |
| 0x15-0x16 | 0x120000-0x13FFFF | Watchdog control |

---

## Verification Summary

| Item | Status | Evidence |
|------|--------|----------|
| 8051 blocks 0x40000-0x160000 | ✓ Traced | 18 × 64KB files |
| AEON image 390KB | ✓ Traced | AEON binary analyzed |
| DRAM 0x0C0000 | ✓ Traced | 673 refs in AEON |
| DRAM 0x100000 | ✓ Traced | 888 refs in AEON |
| DRAM 0x150000 | ✓ Traced | 384 refs in AEON |
| Bank switch 0x1019 | ✓ Traced | 237 refs in blocks |
| Buffer sub-regions | ✓ Traced | Multiple ref counts |

---

## Related Documentation

- [D72N_REGISTER_MAP.md](D72N_REGISTER_MAP.md) - RIU registers
- [D72N_VARIABLE_MAP.md](D72N_VARIABLE_MAP.md) - XDATA variables
- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - SERDB interface
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
