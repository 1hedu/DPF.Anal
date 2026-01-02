# D72N Register Map

RIU (Register Interface Unit) register reference for the DPF-D72N, traced from 8051 overlay blocks.

## Overview

The D72N accesses hardware via RIU memory-mapped registers. All addresses traced from pattern analysis of 18 overlay blocks at `/DPF-D72N/blocks/`.

### RIU Access Patterns

```asm
; 8051 RIU access via XDATA
; RIU Address = Register Address × 2 (word-aligned)
MOV  DPTR,#0x1019   ; Bank select register
MOVX A,@DPTR        ; Read
MOV  A,#0x01        ; Value
MOVX @DPTR,A        ; Write
```

---

## Traced Evidence

### Bank Reference Summary

| Bank | Name | Refs | Purpose |
|------|------|------|---------|
| 0x10 | CHIPTOP | 1505 | System control, bank select, clocks |
| 0x11 | Unknown | 149 | Unidentified (possibly timer) |
| 0x12 | BDMA | 269 | Block DMA engine |
| 0x13 | Unknown | 9 | Unidentified |
| 0x14 | JPD | 1 | JPEG decoder hardware |
| 0x15 | AUDIO/MISC | 179 | Audio or miscellaneous |
| 0x16 | FCIE | 3 | Flash card interface |
| 0x17 | Unknown | 17 | Unidentified |
| 0x18 | Unknown | 1 | Unidentified |
| 0x19 | Unknown | 1 | Unidentified |
| 0x1A | Unknown | 18 | Unidentified |
| 0x1B | Unknown | 21 | Unidentified |
| 0x1C | Unknown | 2 | Unidentified |
| 0x1D | Unknown | 38 | Unidentified |
| 0x1E | AEON/Display | 121 | AEON processor, display engine |
| 0x1F | AEON Control | 78 | AEON control registers |

---

## Bank 0x10 - CHIPTOP (System Control)

Most heavily referenced bank (1505 total refs).

### Top Registers

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x1019 | 237 | **Bank Select** - Flash overlay bank | ✓ Traced |
| 0x1010 | 131 | Main control register | ✓ Traced |
| 0x1018 | 111 | Timer/Clock control | ✓ Traced |
| 0x1014 | 76 | Auxiliary control 4 | ✓ Traced |
| 0x1012 | 74 | Auxiliary control 2 | ✓ Traced |
| 0x100C | 73 | General control 4 | ✓ Traced |
| 0x1008 | 73 | General control 0 | ✓ Traced |
| 0x1016 | 73 | Auxiliary control 6 | ✓ Traced |
| 0x100D | 72 | General control 5 | ✓ Traced |
| 0x1009 | 72 | General control 1 | ✓ Traced |
| 0x1015 | 72 | Auxiliary control 5 | ✓ Traced |
| 0x1011 | 72 | Auxiliary control 1 | ✓ Traced |
| 0x1017 | 72 | Auxiliary control 7 | ✓ Traced |
| 0x1013 | 72 | Auxiliary control 3 | ✓ Traced |
| 0x100A | 58 | General control 2 | ✓ Traced |
| 0x100E | 57 | General control 6 | ✓ Traced |
| 0x100F | 54 | General control 7 | ✓ Traced |
| 0x100B | 54 | General control 3 | ✓ Traced |

### Bank Select Register (0x1019)

Most referenced register (237 refs). Controls 64KB flash overlay banks.

```asm
; Traced from block 01 offset 0x1114
90 10 19     MOV  DPTR,#0x1019    ; Bank select register
74 01        MOV  A,#0x01         ; Bank 1
F0           MOVX @DPTR,A         ; Write bank value
```

| Value | Bank | Flash Range |
|-------|------|-------------|
| 0x01 | Block 01 | 0x40000-0x4FFFF |
| 0x02 | Block 02 | 0x50000-0x5FFFF |
| ... | ... | ... |
| 0x12 | Block 18 | 0x150000-0x15FFFF |

---

## Bank 0x11 - Unknown (149 refs)

| Address | Refs | Purpose |
|---------|------|---------|
| 0x116E | 144 | Primary function - unknown |

---

## Bank 0x12 - BDMA (Block DMA)

Block DMA engine for memory transfers (269 refs).

### Top Registers

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x121A | 27 | DMA control A | ✓ Traced |
| 0x121B | 24 | DMA control B | ✓ Traced |
| 0x1219 | 20 | DMA status | ✓ Traced |
| 0x129F | 13 | DMA config | ✓ Traced |
| 0x1244 | 13 | DMA transfer | ✓ Traced |
| 0x1207 | 12 | DMA base | ✓ Traced |
| 0x12EF | 9 | DMA interrupt | ✓ Traced |
| 0x1226 | 7 | DMA address low | ✓ Traced |
| 0x1254 | 6 | DMA address mid | ✓ Traced |
| 0x1257 | 6 | DMA address high | ✓ Traced |
| 0x12D5 | 6 | DMA size | ✓ Traced |
| 0x123D | 6 | DMA source | ✓ Traced |
| 0x123C | 6 | DMA dest | ✓ Traced |
| 0x1224 | 6 | DMA config 2 | ✓ Traced |

---

## Bank 0x15 - AUDIO/MISC (179 refs)

| Address | Refs | Purpose |
|---------|------|---------|
| 0x1588 | 65 | Primary register |
| 0x1516 | 12 | Secondary |
| 0x1500 | 10 | Base register |
| 0x1586 | 9 | Status |
| 0x158A | 7 | Config |
| 0x1509 | 6 | Control |
| 0x1514 | 6 | Setting |
| 0x1580 | 6 | Mode |
| 0x1507 | 5 | Enable |
| 0x1504 | 5 | Interrupt |

---

## Bank 0x1D - Unknown (38 refs)

| Address | Refs | Purpose |
|---------|------|---------|
| 0x1D12 | 19 | Primary |
| 0x1DE2 | 18 | Secondary |

---

## Bank 0x1E - AEON/Display (121 refs)

AEON processor interface and display control.

### Top Registers

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x1EC1 | 18 | AEON interface | ✓ Traced |
| 0x1E6C | 18 | Display/JPEG status | ✓ Traced |
| 0x1ECE | 16 | **Status Mask** - JPEG status mask | ✓ Traced |
| 0x1ECF | 15 | **Status Check** - JPEG status value | ✓ Traced |
| 0x1E78 | 7 | Display control A | ✓ Traced |
| 0x1E7A | 7 | Display control B | ✓ Traced |
| 0x1E11 | 6 | **JPEG Enable** - Set bit 4 | ✓ Traced |

### JPEG Decode Registers

```asm
; Traced from block 01 offset 0x585E
; Check JPEG status
90 1E CF     MOV  DPTR,#0x1ECF    ; Status check register
E0           MOVX A,@DPTR         ; Read status

; Traced from block 01 offset 0xCACD
; Enable JPEG
90 1E 11     MOV  DPTR,#0x1E11    ; JPEG enable register
E0           MOVX A,@DPTR         ; Read current
44 10        ORL  A,#0x10         ; Set bit 4
F0           MOVX @DPTR,A         ; Write back
```

---

## Bank 0x1F - AEON Control (78 refs)

AEON processor control registers.

### Top Registers

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x1F17 | 18 | AEON status | ✓ Traced |
| 0x1F06 | 12 | AEON interrupt | ✓ Traced |
| 0x1F09 | 11 | AEON control | ✓ Traced |
| 0x1F2C | 7 | AEON config | ✓ Traced |
| 0x1F00 | 7 | AEON base | ✓ Traced |

### AEON Control Access

```asm
; Traced from block 06 offset 0x0674
90 1F 06     MOV  DPTR,#0x1F06    ; AEON interrupt register
E0           MOVX A,@DPTR         ; Read
44 01        ORL  A,#0x01         ; Set bit 0
F0           MOVX @DPTR,A         ; Write
```

---

## SERDB Access

RIU registers accessible via SERDB I2C interface:

```python
def read_riu(bank, offset):
    """Read RIU register via SERDB

    SERDB channel 0x83 = PM RIU
    SERDB channel 0x84 = Non-PM RIU

    RIU Address = (bank << 8) | offset
    """
    addr = (bank << 8) | offset
    # For PM RIU (banks 0x10-0x1F)
    bus.write_i2c_block_data(0x59, 0x83, [addr >> 8, addr & 0xFF])
    return bus.read_byte(0x59)

def write_riu(bank, offset, value):
    """Write RIU register via SERDB"""
    addr = (bank << 8) | offset
    bus.write_i2c_block_data(0x59, 0x83, [addr >> 8, addr & 0xFF, value])

# Example: Read bank select
bank = read_riu(0x10, 0x19)
print(f"Current bank: {bank}")

# Example: Read JPEG status
status = read_riu(0x1E, 0xCF)
print(f"JPEG status: {status:02X}")
```

---

## Register Location Summary

### By Block

| Register | Blocks | First Offset |
|----------|--------|--------------|
| 0x1019 (Bank Select) | All 18 | 0x1008 |
| 0x1E6C | All 18 | 0xC5A9 (common code) |
| 0x1ECE | 01, 02, 05, 06, 07, 14, 16 | 0x586F |
| 0x1ECF | 01, 02, 05, 06, 07, 14, 16 | 0x585E |
| 0x1F06 | 06 | 0x0674 |
| 0x1F09 | 01, 06, 14, 16 | 0x558E |
| 0x1E11 | 01, 05, 07, 14 | 0xCACD |

---

## Verification Summary

| Register | Status | Evidence |
|----------|--------|----------|
| 0x1019 Bank Select | ✓ Traced | 237 refs, all blocks, value writes 0x01-0x12 |
| 0x1010 Main Control | ✓ Traced | 131 refs, paired with 0x1011-0x1017 |
| 0x1E6C Display/JPEG | ✓ Traced | 18 refs, common code at 0xC5A9 |
| 0x1ECE Status Mask | ✓ Traced | 16 refs, ANL operations |
| 0x1ECF Status Check | ✓ Traced | 15 refs, comparison operations |
| 0x1E11 JPEG Enable | ✓ Traced | 6 refs, ORL #0x10 pattern |
| 0x1F06 AEON Int | ✓ Traced | 12 refs, block 06 |
| 0x1F09 AEON Ctrl | ✓ Traced | 11 refs, multiple blocks |

---

## Related Documentation

- [D72N_MEMORY_MAP.md](D72N_MEMORY_MAP.md) - Flash/DRAM layout
- [D72N_VARIABLE_MAP.md](D72N_VARIABLE_MAP.md) - XDATA variables
- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - SERDB interface
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
