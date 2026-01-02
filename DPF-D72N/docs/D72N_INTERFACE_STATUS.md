# D72N Interface Status

Hardware interface verification status for the DPF-D72N digital picture frame.

## Interface Summary

| Interface | I2C Addr | Status | Evidence |
|-----------|----------|--------|----------|
| **SERDB** | 0x59 | ✅ **CONFIRMED** | Firmware trace (blocks 01, 05, 11, 12, 13, 14, 15, 17) |
| **ISP** | 0x49 | ✅ **CONFIRMED** | Firmware trace (blocks 05, 10, 12, 14, 17) |
| **UART** | N/A | ⚠️ Assumed | Same 38400 baud as similar MStar devices |

---

## SERDB Protocol (Confirmed)

### Firmware Trace Evidence

SERDB I2C address 0x59 found in **8 out of 18** 8051 overlay blocks:

| Block | Offset | Evidence |
|-------|--------|----------|
| 01 | 0x735E | `MOV A,#0x59` in SERDB handler |
| 05 | multiple | I2C address reference |
| 11 | 0x7250-0x7280 | Full SERDB command sequence |
| 12 | multiple | I2C address reference |
| 13 | multiple | I2C address reference |
| 14 | multiple | I2C address reference |
| 15 | multiple | I2C address reference |
| 17 | multiple | I2C address reference |

All SERDB commands found across firmware:

| Command | Name | Found In |
|---------|------|----------|
| 0x10 | BUS_ACCESS | Block 11 |
| 0x34 | DISABLE_ACCESS | Blocks 11, multiple |
| 0x35 | ENABLE_ACCESS | Blocks 11, multiple |
| 0x36 | RESUME_MCU | Blocks 11, multiple |
| 0x37 | STOP_MCU | Blocks 11, multiple |
| 0x45 | EXIT | Multiple blocks |
| 0x51 | BEFORE_STOP | Multiple blocks |
| 0x53 | NOT_STOPPING | Multiple blocks |
| 0x71 | I2C_RESHAPE | Multiple blocks |
| 0x80-0x85 | CHANNEL_BITS | Multiple blocks |

### Block 11 SERDB Handler (0x7250-0x7280)

```asm
; SERDB command sequence at 0x7250
7255: 74 34       MOV A,#0x34    ; CMD_DISABLE_ACCESS
7257: F0          MOVX @DPTR,A
725D: 74 35       MOV A,#0x35    ; CMD_ENABLE_ACCESS
726D: 74 37       MOV A,#0x37    ; CMD_STOP_MCU
7275: 74 36       MOV A,#0x36    ; CMD_RESUME_MCU
735E: 74 59       MOV A,#0x59    ; SERDB I2C ADDR
```

### Protocol Details

Based on linux-chenxing.org documentation and firmware trace:

1. **Magic String**: "SERDB" (5 bytes)
2. **Channel Selection**: Bit commands 0x80-0x85
3. **Initialization**: 0x53, 0x7F, 0x35, 0x71
4. **Bus Access**: Command 0x10 with 4-byte big-endian address

Channels:
| Channel | Bus |
|---------|-----|
| 0 | 8051 XDATA |
| 3 | PM RIU |
| 4 | Non-PM RIU |

---

## ISP Protocol (Confirmed)

### Firmware Trace Evidence

ISP I2C address 0x49 found in **5 out of 18** 8051 overlay blocks:
- Blocks: 05, 10, 12, 14, 17

These blocks handle flash read/write/erase operations.

### Protocol Details

Standard MStar ISP over I2C:
- Address: 0x49
- Commands: Read, Write, Erase (sector/chip)
- SPI passthrough to external flash

---

## UART (Assumed)

Based on similar MStar AEON devices:
- Baud: 38400
- Output only (TX from AEON)
- Shared pins with I2C debug

Requires hardware verification.

---

## References

- [linux-chenxing.org SERDB](https://linux-chenxing.org/msc313e/ip/serdb/) - Protocol documentation
- [D72N_SERDB_CONTROL.md](../docs/D72N_SERDB_CONTROL.md) - Control reference
- [D72N blocks](../blocks/) - Firmware overlay blocks analyzed
