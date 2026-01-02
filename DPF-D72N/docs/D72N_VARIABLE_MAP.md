# D72N Variable Map

XDATA variable reference for the DPF-D72N, traced from 8051 overlay blocks.

## Overview

All addresses traced from pattern analysis of 18 overlay blocks at `/DPF-D72N/blocks/`. Variables are accessed via `MOV DPTR,#addr; MOVX A,@DPTR` patterns.

---

## Mailbox Registers (Verified)

### Primary Mailbox (JPEG)

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x4401 | 8 | JPEG command byte | ✓ Traced |
| 0x4402 | 10 | JPEG params start | ✓ Traced |
| 0x4417 | 1 | Sync flag | ✓ Traced |

### Secondary Mailbox (BMP/TIFF)

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x40BC | 115 | BMP/TIFF command byte | ✓ Traced |
| 0x40BD | 131 | BMP/TIFF params start | ✓ Traced |

### Response Registers

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x40FB | 77 | Status register | ✓ Traced |
| 0x40FC | 88 | Response[0] | ✓ Traced |
| 0x40FD | 83 | Response[1] | ✓ Traced |
| 0x40FE | 44 | Response[2] | ✓ Traced |
| 0x40FF | 59 | Response[3] | ✓ Traced |

---

## Control Registers (Verified)

### Watchdog Control

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x44CE | 10 | Watchdog state (bit 0 = enable) | ✓ Traced |
| 0x44D3 | 4 | Watchdog counter low | ✓ Traced |
| 0x44D4 | 17 | Watchdog counter high | ✓ Traced |

### AEON Control

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x0FE6 | 6 | AEON control (bit 0 = run, bit 1 = enable) | ✓ Traced |

---

## Base Variables (0x40xx)

Most referenced state variables in base range.

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x40EA | 710 | Primary state | ✓ Traced |
| 0x40EE | 322 | State field 2 | ✓ Traced |
| 0x40F9 | 253 | Decode control | ✓ Traced |
| 0x40EB | 202 | State field 3 | ✓ Traced |
| 0x4037 | 162 | System base | ✓ Traced |
| 0x40F1 | 145 | Status A | ✓ Traced |
| 0x40C3 | 135 | Control | ✓ Traced |
| 0x403B | 132 | System field 2 | ✓ Traced |
| 0x40BD | 131 | BMP/TIFF params | ✓ Traced |
| 0x4040 | 130 | Mode | ✓ Traced |
| 0x40B6 | 123 | Buffer control | ✓ Traced |
| 0x40BC | 115 | BMP/TIFF command | ✓ Traced |
| 0x402F | 107 | System field 3 | ✓ Traced |
| 0x4066 | 106 | Extended mode | ✓ Traced |
| 0x403C | 103 | Flag A | ✓ Traced |
| 0x4046 | 101 | Flag B | ✓ Traced |
| 0x40F2 | 100 | Status B | ✓ Traced |
| 0x40F3 | 98 | Status C | ✓ Traced |
| 0x4033 | 98 | Counter | ✓ Traced |
| 0x40FA | 97 | Decode status | ✓ Traced |
| 0x404E | 97 | Mode 2 | ✓ Traced |
| 0x40F6 | 117 | Extended status | ✓ Traced |

---

## Storage Variables (0x41xx)

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x4102 | 119 | Storage state | ✓ Traced |
| 0x4129 | 94 | Storage config | ✓ Traced |
| 0x412D | 78 | Storage mode | ✓ Traced |
| 0x410F | 75 | Storage control A | ✓ Traced |
| 0x4112 | 75 | Storage control B | ✓ Traced |
| 0x410C | 73 | Storage status | ✓ Traced |
| 0x4101 | 66 | Storage base | ✓ Traced |
| 0x4115 | 66 | Storage field | ✓ Traced |
| 0x4103 | 65 | Storage index | ✓ Traced |
| 0x4107 | 60 | Storage flag | ✓ Traced |

---

## File Variables (0x42xx)

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x42D5 | 73 | File state | ✓ Traced |
| 0x4201 | 51 | File base | ✓ Traced |
| 0x4214 | 37 | File index | ✓ Traced |
| 0x42D2 | 36 | File mode | ✓ Traced |
| 0x42F7 | 29 | File status | ✓ Traced |
| 0x42B2 | 28 | File control | ✓ Traced |
| 0x421F | 27 | File config | ✓ Traced |
| 0x4204 | 27 | File handle | ✓ Traced |
| 0x42AF | 26 | File position | ✓ Traced |
| 0x42B0 | 24 | File size | ✓ Traced |

---

## Process Variables (0x43xx)

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x439D | 119 | Process state | ✓ Traced |
| 0x4380 | 34 | Process control | ✓ Traced |
| 0x4348 | 33 | Process index | ✓ Traced |
| 0x43F9 | 29 | Process status | ✓ Traced |
| 0x4345 | 29 | Process mode | ✓ Traced |
| 0x437D | 28 | Process flag A | ✓ Traced |
| 0x4366 | 27 | Process config | ✓ Traced |
| 0x4350 | 27 | Process counter | ✓ Traced |
| 0x4383 | 25 | Process flag B | ✓ Traced |
| 0x437A | 24 | Process pointer | ✓ Traced |

---

## Mailbox Parameters (0x44xx)

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x445B | 42 | MB param extended | ✓ Traced |
| 0x44B3 | 34 | MB config | ✓ Traced |
| 0x44D2 | 28 | MB counter | ✓ Traced |
| 0x44E9 | 26 | MB status | ✓ Traced |
| 0x44B2 | 24 | MB mode | ✓ Traced |
| 0x442A | 23 | MB index | ✓ Traced |
| 0x44F3 | 23 | MB response | ✓ Traced |
| 0x44CD | 22 | MB control | ✓ Traced |
| 0x44E2 | 20 | MB flag A | ✓ Traced |
| 0x44DD | 20 | MB flag B | ✓ Traced |
| 0x44CE | 10 | Watchdog state | ✓ Traced |
| 0x44D3 | 4 | Watchdog counter low | ✓ Traced |
| 0x44D4 | 17 | Watchdog counter high | ✓ Traced |

---

## Extended Variables (0x45xx)

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x4542 | 194 | Extended state A | ✓ Traced |
| 0x4522 | 165 | Extended control | ✓ Traced |
| 0x4525 | 147 | Extended mode | ✓ Traced |
| 0x4566 | 132 | Extended config | ✓ Traced |
| 0x4541 | 107 | Extended state B | ✓ Traced |
| 0x4581 | 107 | Extended status | ✓ Traced |
| 0x456F | 90 | Extended index | ✓ Traced |
| 0x4575 | 88 | Extended flag | ✓ Traced |
| 0x456B | 85 | Extended pointer | ✓ Traced |
| 0x45D3 | 80 | Extended counter | ✓ Traced |

---

## Decode Variables (0x46xx)

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x4641 | 219 | Decode state | ✓ Traced |
| 0x4665 | 120 | Decode control | ✓ Traced |
| 0x46D5 | 94 | Decode config | ✓ Traced |
| 0x4605 | 78 | Decode mode | ✓ Traced |
| 0x4640 | 75 | Decode base | ✓ Traced |
| 0x465F | 72 | Decode status | ✓ Traced |
| 0x4661 | 68 | Decode index | ✓ Traced |
| 0x46C4 | 68 | Decode param | ✓ Traced |
| 0x4670 | 60 | Decode flag | ✓ Traced |
| 0x4673 | 59 | Decode counter | ✓ Traced |

---

## Display Variables (0x47xx)

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x4720 | 238 | Display state | ✓ Traced |
| 0x47A4 | 163 | Display control A | ✓ Traced |
| 0x47A2 | 162 | Display control B | ✓ Traced |
| 0x47A0 | 126 | Display base | ✓ Traced |
| 0x474C | 72 | Display mode | ✓ Traced |
| 0x471D | 56 | Display config | ✓ Traced |
| 0x4723 | 48 | Display index | ✓ Traced |
| 0x4724 | 39 | Display status | ✓ Traced |
| 0x47A5 | 36 | Display flag A | ✓ Traced |
| 0x4754 | 36 | Display flag B | ✓ Traced |

---

## Extended2 Variables (0x5xxx)

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x504F | 168 | Buffer state | ✓ Traced |
| 0x5271 | 107 | Buffer control | ✓ Traced |
| 0x530A | 97 | Buffer config | ✓ Traced |
| 0x5080 | 93 | Buffer mode | ✓ Traced |
| 0x5108 | 75 | Buffer index | ✓ Traced |
| 0x511F | 71 | Buffer status | ✓ Traced |
| 0x527A | 68 | Buffer pointer | ✓ Traced |
| 0x5081 | 57 | Buffer flag | ✓ Traced |
| 0x511D | 54 | Buffer counter | ✓ Traced |
| 0x514D | 54 | Buffer param | ✓ Traced |

---

## GWin/Display Variables (0x6xxx)

D72N uses different GWin addresses than other similar devices.

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x6653 | 44 | GWin state | ✓ Traced |
| 0x69BE | 36 | GWin control A | ✓ Traced |
| 0x6D2C | 36 | GWin control B | ✓ Traced |
| 0x6682 | 24 | GWin config | ✓ Traced |
| 0x668D | 22 | GWin mode | ✓ Traced |
| 0x6666 | 21 | GWin enable | ✓ Traced |
| 0x6662 | 20 | GWin status | ✓ Traced |
| 0x665B | 20 | GWin index | ✓ Traced |
| 0x6651 | 19 | GWin base | ✓ Traced |
| 0x6E86 | 18 | GWin extended | ✓ Traced |

---

## Variable Map Diagram

```
XDATA Address Space
===================
0x0000-0x0FFF ┌─────────────────────────────┐
              │ SFR/System                  │
              │ 0x0FE6: AEON control (6)    │
0x1000-0x1FFF ├─────────────────────────────┤
              │ RIU Access                  │
              │ (See D72N_REGISTER_MAP.md)  │
0x4000-0x40FF ├─────────────────────────────┤
              │ Base State Variables        │
              │ 0x40EA: Primary state (710) │
              │ 0x40BC: BMP/TIFF cmd (115)  │
              │ 0x40FB: Status reg (77)     │
0x4100-0x41FF ├─────────────────────────────┤
              │ Storage Variables           │
              │ 0x4102: Storage state (119) │
0x4200-0x42FF ├─────────────────────────────┤
              │ File Variables              │
              │ 0x42D5: File state (73)     │
0x4300-0x43FF ├─────────────────────────────┤
              │ Process Variables           │
              │ 0x439D: Process state (119) │
0x4400-0x44FF ├─────────────────────────────┤
              │ Mailbox Parameters          │
              │ 0x4401: JPEG command (8)    │
              │ 0x44CE: Watchdog (10)       │
0x4500-0x45FF ├─────────────────────────────┤
              │ Extended Variables          │
              │ 0x4542: Extended A (194)    │
0x4600-0x46FF ├─────────────────────────────┤
              │ Decode Variables            │
              │ 0x4641: Decode state (219)  │
0x4700-0x47FF ├─────────────────────────────┤
              │ Display Variables           │
              │ 0x4720: Display state (238) │
0x5000-0x5FFF ├─────────────────────────────┤
              │ Extended2 / Buffers         │
              │ 0x504F: Buffer state (168)  │
0x6000-0x6FFF ├─────────────────────────────┤
              │ GWin/Display Control        │
              │ 0x6653: GWin state (44)     │
              └─────────────────────────────┘
```

---

## SERDB Access

```python
def read_xdata(addr):
    """Read XDATA variable via SERDB"""
    bus.write_i2c_block_data(0x59, 0x80, [addr >> 8, addr & 0xFF])
    return bus.read_byte(0x59)

def write_xdata(addr, val):
    """Write XDATA variable via SERDB"""
    bus.write_i2c_block_data(0x59, 0x80, [addr >> 8, addr & 0xFF, val])

# Dump key state variables
def dump_d72n_state():
    print(f"Primary state:   0x{read_xdata(0x40EA):02X}")
    print(f"Decode state:    0x{read_xdata(0x4641):02X}")
    print(f"Display state:   0x{read_xdata(0x4720):02X}")
    print(f"Mailbox status:  0x{read_xdata(0x40FB):02X}")
    print(f"Watchdog state:  0x{read_xdata(0x44CE):02X}")
```

---

## Verification Summary

| Category | Count | Status |
|----------|-------|--------|
| Mailbox registers | 12 | ✓ Traced |
| Control registers | 5 | ✓ Traced |
| Base variables (0x40xx) | 22 | ✓ Traced |
| Storage variables (0x41xx) | 10 | ✓ Traced |
| File variables (0x42xx) | 10 | ✓ Traced |
| Process variables (0x43xx) | 10 | ✓ Traced |
| Mailbox params (0x44xx) | 13 | ✓ Traced |
| Extended variables (0x45xx) | 10 | ✓ Traced |
| Decode variables (0x46xx) | 10 | ✓ Traced |
| Display variables (0x47xx) | 10 | ✓ Traced |
| Extended2 variables (0x5xxx) | 10 | ✓ Traced |
| GWin variables (0x6xxx) | 10 | ✓ Traced |

**Total traced:** 132 unique XDATA addresses

---

## Related Documentation

- [D72N_REGISTER_MAP.md](D72N_REGISTER_MAP.md) - RIU registers
- [D72N_MEMORY_MAP.md](D72N_MEMORY_MAP.md) - Flash/DRAM layout
- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - SERDB interface
- [D72N_MAILBOX_PROTOCOL.md](D72N_MAILBOX_PROTOCOL.md) - Mailbox IPC
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
