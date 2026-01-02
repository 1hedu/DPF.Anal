# D72N Command Dispatch

Mailbox command dispatch for JPEG, BMP, and TIFF decoders in the DPF-D72N.

## Overview

The D72N uses multiple mailbox pathways for different decoder types:

| Decoder | Command Addr | Param Addr | Status Addr |
|---------|--------------|------------|-------------|
| JPEG | 0x4401 | 0x4402+ | 0x40FB |
| BMP | 0x40BC | 0x40BD+ | 0x40FB |
| TIFF | 0x40BC | 0x40BD+ | 0x40FB |

---

## Traced Evidence

### JPEG Commands (Block 02)

| Offset | Flash | Command | Evidence |
|--------|-------|---------|----------|
| 0x22F7 | 0x522F7 | 0x01 (INIT) | `74 01 F0` (MOV A,#0x01; MOVX @DPTR,A) |
| 0x22F2 | 0x522F2 | 0x02 (MJPG_START_DEC) | `74 02 F0` (MOV A,#0x02; MOVX @DPTR,A) |

### BMP Command (Common Code - All Blocks)

| Offset | Flash | Command | Evidence |
|--------|-------|---------|----------|
| 0xAC80 | varies | 0x10 (DECODE_MEM_OUT) | `74 10 F0` to 0x40BC |

### TIFF Commands (Multiple Blocks)

| Block | Offset | Command | Evidence |
|-------|--------|---------|----------|
| 12 | 0x4B07 | 0x21 (START_DEC) | `74 21 F0` |
| 14 | 0x0CC7 | 0x21 (START_DEC) | `74 21 F0` |
| 02 | 0x3C32 | 0x22 (DECODE_MEM_OUT) | `74 22 F0` |
| 03 | 0x49BE | 0x22 (DECODE_MEM_OUT) | `74 22 F0` |
| 05 | 0x1796 | 0x22 (DECODE_MEM_OUT) | `74 22 F0` |

---

## JPEG Command Dispatch

### Send Function (Block 02, offset 0x2830)

```asm
; Block 02 offset 0x2830 (Flash 0x52830)
; SendMailboxCmd - JPEG pathway
; Input: R6 = command, R7 = param

2830: 7B 01        MOV  R3,#0x01
2832: 12 6A 51     LCALL 0x6A51         ; Init
2835: 90 44 01     MOV  DPTR,#0x4401    ; Command address
2838: EE           MOV  A,R6            ; Get command
2839: F0           MOVX @DPTR,A         ; Write command
283A: A3           INC  DPTR            ; 0x4402
283B: EF           MOV  A,R7            ; Get param
283C: F0           MOVX @DPTR,A         ; Write param
283D: 90 44 01     MOV  DPTR,#0x4401
2840: E0           MOVX A,@DPTR         ; Readback
2841: FC           MOV  R4,A
2842: A3           INC  DPTR
2843: E0           MOVX A,@DPTR
2844: FD           MOV  R5,A
2845: 22           RET
```

### Command Selection (Block 02, offset 0x22E2)

```asm
; Block 02 offset 0x22E2 (Flash 0x522E2)
; Select JPEG command based on input

22E2: EF           MOV  A,R7            ; Get param
22E3: B4 02 05     CJNE A,#0x02,+5      ; If != 2
22E6: 90 44 02     MOV  DPTR,#0x4402
22E9: 80 0C        SJMP write_01

22EB: EF           MOV  A,R7
22EC: 90 44 02     MOV  DPTR,#0x4402
22EF: B4 04 05     CJNE A,#0x04,+5      ; If != 4
22F2: 74 02        MOV  A,#0x02         ; Command 0x02
22F4: F0           MOVX @DPTR,A
22F5: 80 03        SJMP done

write_01:
22F7: 74 01        MOV  A,#0x01         ; Command 0x01
22F9: F0           MOVX @DPTR,A

done:
22FA: 90 44 01     MOV  DPTR,#0x4401
22FD: E0           MOVX A,@DPTR
22FE: 90 44 12     MOV  DPTR,#0x4412    ; Copy command
2301: F0           MOVX @DPTR,A
```

---

## BMP Command Dispatch

### BMP Decode Function (Common Code, offset 0xAC70)

This code appears at offset 0xAC70 in all 18 blocks (common library).

```asm
; Common offset 0xAC70 (present in all blocks)
; BMP decode dispatch

AC70: B4 58 1C     CJNE A,#0x58,+0x1C   ; Compare with 'X'
AC73: 90 40 BD     MOV  DPTR,#0x40BD    ; BMP params
AC76: E0           MOVX A,@DPTR
AC77: F0           MOVX @DPTR,A
AC78: A3           INC  DPTR            ; 0x40BE
AC79: E0           MOVX A,@DPTR
AC7A: 44 01        ORL  A,#0x01         ; Set bit 0
AC7C: F0           MOVX @DPTR,A
AC7D: 90 40 BC     MOV  DPTR,#0x40BC    ; BMP command
AC80: 74 10        MOV  A,#0x10         ; DECODE_MEM_OUT
AC82: F0           MOVX @DPTR,A         ; Write command
AC83: 90 40 B7     MOV  DPTR,#0x40B7    ; More params
AC86: E4           CLR  A
AC87: 75 F0 02     MOV  B,#0x02
AC8A: 12 9B 53     LCALL 0x9B53
```

### Alternate Command 0x08 (offset 0xAC95)

```asm
AC8F: 90 40 BC     MOV  DPTR,#0x40BC
AC92: E0           MOVX A,@DPTR
AC93: 70 03        JNZ  skip
AC95: 74 08        MOV  A,#0x08         ; Alternate command
AC97: F0           MOVX @DPTR,A
```

---

## TIFF Command Dispatch

### TIFF START_DEC (Block 12, offset 0x4B03)

```asm
; Block 12 offset 0x4B03 (Flash 0xF4B03)
; TIFF start decode

4B03: 74 01        MOV  A,#0x01         ; Sub-command
4B05: F0           MOVX @DPTR,A
4B06: A3           INC  DPTR
4B07: 74 21        MOV  A,#0x21         ; START_DEC
4B09: F0           MOVX @DPTR,A
4B0A: 90 40 F9     MOV  DPTR,#0x40F9    ; Status area
4B0D: 12 22 98     LCALL 0x2298
```

### TIFF DECODE_MEM_OUT (Block 03, offset 0x49B6)

```asm
; Block 03 offset 0x49B6 (Flash 0x649B6)
; TIFF decode to memory

49B6: 90 40 FB     MOV  DPTR,#0x40FB    ; Status register
49B9: 12 4B 70     LCALL 0x4B70         ; Check status
49BC: 60 05        JZ   0x49C3          ; If zero, skip
49BE: 74 22        MOV  A,#0x22         ; DECODE_MEM_OUT
49C0: F0           MOVX @DPTR,A
49C1: 80 37        SJMP continue
49C3: 74 1C        MOV  A,#0x1C         ; Alternate (0x1C)
49C5: F0           MOVX @DPTR,A
```

---

## Command Summary

### JPEG Commands (via 0x4401)

| Cmd | Name | Block | Offset | Status |
|-----|------|-------|--------|--------|
| 0x01 | MB_JPD_CMD_INIT | 02 | 0x22F7 | ✓ Traced |
| 0x02 | MB_JPD_CMD_MJPG_START_DEC | 02 | 0x22F2 | ✓ Traced |

### BMP Commands (via 0x40BC)

| Cmd | Name | Block | Offset | Status |
|-----|------|-------|--------|--------|
| 0x08 | BMP_CMD_UNKNOWN | all | 0xAC95 | ✓ Traced |
| 0x10 | MB_BMP_CMD_DECODE_MEM_OUT | all | 0xAC80 | ✓ Traced |

### TIFF Commands (via 0x40BC)

| Cmd | Name | Block | Offset | Status |
|-----|------|-------|--------|--------|
| 0x20 | MB_TIFF_CMD_GET_HEAD_INF | multiple | various | ○ Pattern found |
| 0x21 | MB_TIFF_CMD_START_DEC | 12,14 | 0x4B07,0x0CC7 | ✓ Traced |
| 0x22 | MB_TIFF_CMD_DECODE_MEM_OUT | 02,03,05 | various | ✓ Traced |

---

## Address Map

### Primary Mailbox (JPEG)

| Address | Purpose |
|---------|---------|
| 0x4401 | JPEG command byte |
| 0x4402-0x4416 | JPEG params (21 bytes) |
| 0x4417 | Sync flag |
| 0x40FB | Status register |
| 0x40FC-0x40FF | Response (4 bytes) |

### Secondary Mailbox (BMP/TIFF)

| Address | Purpose |
|---------|---------|
| 0x40B7 | BMP param |
| 0x40BC | BMP/TIFF command byte |
| 0x40BD-0x40BF | BMP/TIFF params |
| 0x40FB | Status register (shared) |

### Display Control

| Address | Purpose |
|---------|---------|
| 0x41B0 | Display index (block 13: 0x4AB6, block 15: 0x6DBE) |
| 0x41BE | Bitstream address (block 13: 0x6206, block 15: 0x42FF) |

---

## SERDB Usage

```python
def d72n_send_jpeg_cmd(cmd, param=0):
    """Send JPEG command via primary mailbox"""
    serdb.write_xdata(0x4401, cmd)
    serdb.write_xdata(0x4402, param)
    serdb.write_xdata(0x4417, 0xFF)  # Trigger

def d72n_send_bmp_cmd(cmd, params=None):
    """Send BMP/TIFF command via secondary mailbox"""
    serdb.write_xdata(0x40BC, cmd)
    if params:
        for i, p in enumerate(params):
            serdb.write_xdata(0x40BD + i, p)

def d72n_trigger_bmp_decode():
    """Trigger BMP decode with memory output"""
    # Set flag (ORL A,#0x01 at 0xAC7A)
    val = serdb.read_xdata(0x40BE)
    serdb.write_xdata(0x40BE, val | 0x01)
    # Write command 0x10
    serdb.write_xdata(0x40BC, 0x10)

def d72n_trigger_tiff_decode():
    """Trigger TIFF decode"""
    serdb.write_xdata(0x40BC, 0x21)  # START_DEC

def d72n_trigger_tiff_mem_out():
    """Trigger TIFF decode to memory"""
    serdb.write_xdata(0x40BC, 0x22)  # DECODE_MEM_OUT
```

---

## Verification Summary

| Item | Status | Evidence |
|------|--------|----------|
| JPEG cmd 0x01 | ✓ Traced | Block 02: 0x22F7 |
| JPEG cmd 0x02 | ✓ Traced | Block 02: 0x22F2 |
| BMP cmd 0x10 | ✓ Traced | All blocks: 0xAC80 |
| BMP cmd 0x08 | ✓ Traced | All blocks: 0xAC95 |
| TIFF cmd 0x21 | ✓ Traced | Blocks 12,14 |
| TIFF cmd 0x22 | ✓ Traced | Blocks 02,03,05 |
| Primary mailbox 0x4401 | ✓ Traced | Block 02: 0x2835 |
| Secondary mailbox 0x40BC | ✓ Traced | All blocks: 0xAC7D |
| Display addr 0x41B0 | ✓ Traced | Blocks 13,15 |
| Display addr 0x41BE | ✓ Traced | Blocks 13,15 |

---

## Related Documentation

- [D72N_MAILBOX_PROTOCOL.md](D72N_MAILBOX_PROTOCOL.md) - Primary mailbox details
- [D72N_MB_BMP_DECODE_MEM_OUT.md](D72N_MB_BMP_DECODE_MEM_OUT.md) - BMP decode function
- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - SERDB interface
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
