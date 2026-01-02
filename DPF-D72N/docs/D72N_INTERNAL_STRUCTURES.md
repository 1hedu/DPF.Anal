# D72N Internal Structures

Internal firmware subsystems and data structures for the DPF-D72N.

## Overview

The D72N firmware contains the same major subsystems as other MStar-based picture frames, traced from the AEON image and 8051 overlay blocks.

---

## Traced Evidence

### String Locations

| Subsystem | Location | Block/Offset | String |
|-----------|----------|--------------|--------|
| LZW Decoder | AEON | 0x5E3EA | `TIFFInitLZW` |
| LZW State | AEON | 0x4D55C | `gNEXT_CODE: %d` |
| LZW State | AEON | 0x4D56F | `gCUR_CODESIZE: %d` |
| GIF Decoder | AEON | 0x4D4C7 | `[GIF]enter while loop to wait...,stack depth:%d` |
| Cache Control | AEON | 0x5FDA6 | `* DCACHE is initially disabled.` |
| Cache Control | AEON | 0x5FDE7 | `* ICACHE is initially disabled.` |
| Mutex | AEON | 0x4E329 | `for locking mutex #%d !(thread %X)` |
| FAT Library | Block 05 | 0x0679 | `Create MBR Fail` |
| FAT Library | Block 08 | 0x00B2 | `Fat_PartitionTableRead fail!` |
| Stack Monitor | Block 14 | 0x07A3 | `maximum stack depth=0x%bx` |
| Watchdog | Block 01 | 0x117A | `SW watchdog timeout, SP=0x` |
| AEON Control | Block 01 | 0x1205 | `# AEON reset & enable ...` |

---

## 1. LZW Decompression (GIF/TIFF)

### AEON LZW Implementation

The D72N AEON includes full LZW decoder for both GIF and TIFF formats.

#### Debug Strings (AEON)

| Offset | String |
|--------|--------|
| 0x4D4C7 | `[GIF]enter while loop to wait...,stack depth:%d` |
| 0x4D4F8 | `[GIF]will abort here...` |
| 0x4D50B | `[GIF]leave while loop to wait...` |
| 0x4D55C | `gNEXT_CODE: %d` |
| 0x4D56F | `gCUR_CODESIZE: %d` |
| 0x4D580 | `shit!!!` |
| 0x4D589 | `max stack depth is %d` |
| 0x4D5A0 | `[GIF]leave due to max stack depth` |
| 0x5E3EA | `TIFFInitLZW` |
| 0x5E3FB | `No space for LZW state block` |
| 0x5E40B | `LZWDecode: Bogus encoding, loop in the code table` |
| 0x5E464 | `No space for LZW code table` |

#### LZW State Variables

| Variable | Description |
|----------|-------------|
| gNEXT_CODE | Next available dictionary code |
| gCUR_CODESIZE | Current code width (bits, 3-12) |

#### LZW Algorithm Constants

```
CLEAR_CODE    = 2^min_code_size
END_CODE      = CLEAR_CODE + 1
FIRST_CODE    = END_CODE + 1
MAX_CODE      = 4095 (12-bit max)
MAX_STACK     = 4096
```

---

## 2. Cache Control (AEON)

### Cache Initialization Strings

| Offset | String |
|--------|--------|
| 0x5FDA6 | `* DCACHE is initially disabled.` |
| 0x5FDC8 | `* DCACHE is initially enabled.` |
| 0x5FDE7 | `* ICACHE is initially disabled.` |
| 0x5FE08 | `* ICACHE is initially enabled.` |

### Cache Status

D72N AEON runs with caches **disabled by default** (confirmed by string analysis).

---

## 3. Mutex System (AEON)

### Mutex Strings

| Offset | String |
|--------|--------|
| 0x4E321 | `(%d) for locking mutex #%d !(thread %X)` |
| 0x4E359 | `Try to unlock mutex owned by other ! Ignored !` |

### Mutex Architecture

AEON uses mutexes for thread-safe access to shared resources:
- Mailbox buffers
- Decode buffers
- Display output

---

## 4. FAT Filesystem Library

### 8051 FAT Strings (Block 05, 08)

| Block | Offset | String |
|-------|--------|--------|
| 05 | 0x0679 | `flash formating ...` |
| 05 | 0x06B9 | `FAT32` |
| 05 | 0x06DF | `NAND_FS_FmtCardToFAT error` |
| 05 | 0x06FD | `Create MBR OK !!` |
| 08 | 0x00B2 | `Fat_PartitionTableRead fail!` |
| 08 | 0x00CC | `Fat_BootSectorRead fail!` |
| 08 | 0x0292 | `No Free Cluster` |

### Supported Filesystems

| Type | Status |
|------|--------|
| FAT12 | Supported |
| FAT16 | Supported |
| FAT32 | Supported |
| NTFS | Not supported |

---

## 5. Stack Monitor (8051)

### Stack Strings

| Block | Offset | String |
|-------|--------|--------|
| 01 | 0x117A | `SW watchdog timeout, SP=0x` |
| 01 | 0x11D8 | `Stack dump:` |
| 14 | 0x07A3 | `maximum stack depth=0x%bx` |

### Stack Layout (8051)

```
0x00-0x1F  Register Banks (R0-R7 × 4)
0x20-0x2F  Bit-addressable area
0x30-0x7F  General purpose / Stack
0x80-0xFF  SFRs
```

---

## 6. Timer System

### Timer Strings (Block 01)

| Offset | String |
|--------|--------|
| 0x11C3 | `ware watchdog ticks:` |
| 0x167C | `RTC reset ...` |

### Timer Usage

| Timer | Purpose |
|-------|---------|
| Timer0 | Slideshow timing, watchdog |
| Timer2 | Animation, button debounce |
| RTC | Date/time, auto power |

---

## 7. Configuration Storage

### Config Strings (AEON)

| Offset | String |
|--------|--------|
| 0x4F126 | `is not configured` |
| 0x4F93B | `PlanarConfiguration` |

### Settings Structure

Configuration stored in flash sector:
- Display settings (brightness, contrast)
- Slideshow settings (effect, interval)
- System settings (language, date)

---

## 8. Mailbox Dispatcher

### Mailbox Strings (8051)

| Block | Offset | String |
|-------|--------|--------|
| 01 | 0x0F82 | `Aeon2MCU status register still not zero` |
| 01 | 0x0FC0 | `AEON to MCU force interrupt might not cleared` |
| 03 | 0x0433 | `[Mailbox]TIFF head parse done!` |

### Mailbox Strings (AEON)

| Offset | String |
|--------|--------|
| 0x4CE6A | `JPG/GIF Decoder` |
| 0x4E35E | `[MB DSR] Warning` |

### Mailbox Architecture

```
8051 (PM51)                    AEON (R2)
    |                              |
    |-- Write cmd to 0x4401 ----->|
    |-- Set sync flag 0x4417 ---->|
    |                              |
    |<-- Set status 0x40FB -------|
    |<-- Write response 0x40FC ---|
```

---

## 9. AEON Boot/Reset

### AEON Control Strings (Block 01)

| Offset | String |
|--------|--------|
| 0x1205 | `# AEON reset & enable ...` |
| 0x1220 | `..Set SPI base to 0xf0000000` |
| 0x1240 | `..Set QMEM base to 0xC0000000` |
| 0x1339 | `%s Aeon not running [%d]` |
| 0x1351 | `[Aeon Soft Watchdog]` |
| 0x1370 | `Loading Aeon image...` |
| 0x1381 | `Resetting Aeon ...` |
| 0x13A5 | `Aeon reset failed, try again ...` |
| 0x13BB | `Aeon back...` |

### AEON Memory Map

```
0x00000000  DRAM (shared memory)
0x90000000  UART output
0xA0000000  RIU (hardware registers)
0xC0000000  QMEM base
0xF0000000  SPI base
```

---

## 10. Image Decoders

### Decoder Strings (AEON)

| Offset | String |
|--------|--------|
| 0x4CD04 | `GIF` |
| 0x4CD08 | `JPEG encode` |
| 0x4CD13 | `Motion JPEG` |
| 0x4CE6A | `JPG/GIF Decoder` |

### Supported Formats

| Format | Decoder | Location |
|--------|---------|----------|
| JPEG | Hardware + AEON | AEON 0x4CE6A |
| GIF | LZW (AEON) | AEON 0x4D4C7 |
| BMP | AEON | Mailbox 0x10 |
| TIFF | libtiff (AEON) | AEON 0x5E3EA |

---

## DRAM Buffer Layout

### Buffer Addresses (from code analysis)

| Address | Size | Purpose |
|---------|------|---------|
| 0x0C0000 | ~256KB | Secondary buffer |
| 0x100000 | ~512KB | Main decode buffer |
| 0x150000 | ~256KB | Output buffer |

---

## Summary Table

| Subsystem | Location | Key Address/Offset |
|-----------|----------|-------------------|
| LZW Decoder | AEON | 0x4D55C (gNEXT_CODE) |
| Cache Control | AEON | 0x5FDA6 |
| Mutex System | AEON | 0x4E321 |
| FAT Library | Block 05 | 0x0679 |
| Stack Monitor | Block 01 | 0x117A |
| Timer System | Block 01 | 0x11C3 |
| Mailbox | Block 01 | 0x0F82 |
| AEON Boot | Block 01 | 0x1205 |
| Image Decoders | AEON | 0x4CE6A |

---

## Related Documentation

- [D72N_MAILBOX_PROTOCOL.md](D72N_MAILBOX_PROTOCOL.md) - Mailbox IPC details
- [D72N_COMMAND_DISPATCH.md](D72N_COMMAND_DISPATCH.md) - Command dispatch
- [D72N_AEON_CONTROL.md](D72N_AEON_CONTROL.md) - AEON halt/resume
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
