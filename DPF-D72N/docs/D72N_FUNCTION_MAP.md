# D72N Function Map

Combined 8051 MCU and AEON R2 function reference for the DPF-D72N, traced from firmware analysis.

## Overview

The D72N uses a dual-processor architecture where the 8051 MCU handles system control and the AEON R2 handles media decoding. Functions are traced from:
- **8051**: 18 overlay blocks at `/DPF-D72N/blocks/` (LCALL pattern analysis)
- **AEON**: 390KB image (debug string analysis)

---

## Architecture Diagram

See [D72N_ARCHITECTURE.dot](D72N_ARCHITECTURE.dot) for Graphviz visualization.

```
┌─────────────────────────────────────────────────────────────────┐
│                        8051 MCU (PM51)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Library      │  │ Mailbox      │  │ Control      │          │
│  │ Functions    │  │ Functions    │  │ Functions    │          │
│  │ (0x9xxx)     │  │ (0x2xxx)     │  │ (0x3xxx-Dxxx)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                 │                  │                  │
│         └─────────────────┼──────────────────┘                  │
│                           │                                     │
│                    ┌──────▼──────┐                              │
│                    │  Mailbox    │                              │
│                    │  0x4401     │                              │
│                    │  0x40BC     │                              │
│                    └──────┬──────┘                              │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                     ┌──────▼──────┐
                     │   DRAM      │
                     │  Shared     │
                     └──────┬──────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                    ┌──────▼──────┐                              │
│                    │  Mailbox    │                              │
│                    │  Handler    │                              │
│                    └──────┬──────┘                              │
│         ┌─────────────────┼─────────────────┐                   │
│         │                 │                 │                   │
│  ┌──────▼──────┐  ┌───────▼───────┐  ┌──────▼──────┐           │
│  │ JPEG/GIF    │  │ BMP Decoder   │  │ TIFF/LZW    │           │
│  │ Decoder     │  │               │  │ Decoder     │           │
│  │ (0x4Cxxx)   │  │ (0x4Cxxx)     │  │ (0x4Dxxx+)  │           │
│  └─────────────┘  └───────────────┘  └─────────────┘           │
│                        AEON R2                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8051 MCU Functions

### Library Functions (Common Code)

High call-count functions present in all overlay blocks.

| Address | Name | Calls | Description |
|---------|------|-------|-------------|
| 0x9FCC | lib_read_xdata | 1827 | Read from XDATA via DPTR |
| 0x9FD8 | lib_write_xdata | 1245 | Write to XDATA via DPTR |
| 0x1193 | lib_memcpy | 948 | Memory copy routine |
| 0xA783 | lib_delay | 660 | Delay/wait function |
| 0x99E7 | lib_compare | 600 | Value comparison |
| 0x7E1D | lib_string_op | 596 | String operation |
| 0x9E01 | lib_math_mul | 551 | Multiply operation |
| 0x9E12 | lib_math_div | 406 | Divide operation |
| 0x9A00 | lib_buffer_op | 306 | Buffer operation |
| 0x7E2F | lib_string_cmp | 304 | String compare |
| 0x9A82 | lib_bit_op | 289 | Bit manipulation |
| 0x9B53 | lib_array_op | 276 | Array operation |
| 0x9CB3 | lib_io_op | 256 | I/O operation |
| 0xA718 | lib_timer | 252 | Timer function |
| 0xB610 | lib_flash | 252 | Flash access |
| 0x9D3E | lib_state | 242 | State machine |
| 0x9B7F | lib_index | 236 | Index calculation |
| 0x9BAA | lib_pointer | 224 | Pointer operation |
| 0x9B69 | lib_mask | 215 | Mask operation |
| 0x948D | lib_check | 212 | Value check |

### Mailbox Functions (Block 02)

| Address | Name | Block | Description |
|---------|------|-------|-------------|
| 0x2830 | MB_SendCommand | 02 | Send mailbox command to AEON |
| 0x22F2 | MB_SelectJPEGCmd | 02 | Select JPEG command byte |
| 0x22F7 | MB_WriteJPEGInit | 02 | Write JPEG init (0x01) |
| 0x22E2 | MB_DispatchCmd | 02 | Command dispatch logic |
| 0x24AA | MB_SetSync | 02 | Set sync flag 0x4417 |

```asm
; MB_SendCommand at 0x2830
; Input: R6=command, R7=param
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

### Watchdog Functions (Blocks 15, 16)

| Address | Name | Block | Description |
|---------|------|-------|-------------|
| 0x2450 | WDT_ReadState | 15 | Read watchdog state 0x44CE |
| 0x175C | WDT_CheckState | 16 | Check watchdog state |
| 0x1775 | WDT_Disable | 16 | Disable watchdog (ANL #0xFE) |
| 0x6A02 | WDT_WriteCounter | 15 | Write watchdog counter 0x44D3 |
| 0x6ABC | WDT_CheckTimeout | 15 | Check timeout (compare 0xEA) |
| 0x6AD4 | WDT_ReadCounter | 15 | Read 16-bit counter |

```asm
; WDT_Disable at 0x1775
1771: 90 44 CE     MOV  DPTR,#0x44CE    ; Watchdog state
1774: E0           MOVX A,@DPTR
1775: 54 FE        ANL  A,#0xFE         ; Clear bit 0
1777: F0           MOVX @DPTR,A         ; Write back
```

### AEON Control Functions (Block 01)

| Address | Name | Block | Description |
|---------|------|-------|-------------|
| 0x3CDF | AEON_Resume | 01 | Resume AEON (ORL #0x01) |
| 0x3D25 | AEON_Halt | 01 | Halt AEON (ANL #0xFE) |
| 0xD96C | AEON_ReadCtrl | 01 | Read AEON control 0x0FE6 |
| 0xD970 | AEON_Enable | 01 | Enable AEON (ORL #0x02) |

```asm
; AEON_Halt at 0x3D25
3D25: 90 0F E6     MOV  DPTR,#0x0FE6    ; AEON control
3D28: E0           MOVX A,@DPTR
3D29: 54 FE        ANL  A,#0xFE         ; Clear bit 0 (halt)
3D2B: F0           MOVX @DPTR,A

; AEON_Resume at 0x3CDF
3CDF: 90 0F E6     MOV  DPTR,#0x0FE6
3CE2: E0           MOVX A,@DPTR
3CE3: 44 01        ORL  A,#0x01         ; Set bit 0 (run)
3CE5: F0           MOVX @DPTR,A
```

### Command Dispatch Functions (Common Code)

| Address | Name | Block | Description |
|---------|------|-------|-------------|
| 0xAC80 | BMP_DecodeMemOut | all | BMP command 0x10 to 0x40BC |
| 0xAC95 | BMP_AltCommand | all | BMP command 0x08 |
| 0xC5A9 | Display_CheckJPEG | all | Check JPEG status 0x1E6C |

```asm
; BMP_DecodeMemOut at 0xAC80
AC7D: 90 40 BC     MOV  DPTR,#0x40BC    ; BMP command address
AC80: 74 10        MOV  A,#0x10         ; DECODE_MEM_OUT
AC82: F0           MOVX @DPTR,A         ; Write command
```

### TIFF Command Functions

| Address | Name | Block | Description |
|---------|------|-------|-------------|
| 0x4B07 | TIFF_StartDec | 12 | TIFF command 0x21 |
| 0x0CC7 | TIFF_StartDec | 14 | TIFF command 0x21 (alt) |
| 0x49BE | TIFF_DecMemOut | 03 | TIFF command 0x22 |
| 0x3C32 | TIFF_DecMemOut | 02 | TIFF command 0x22 (alt) |
| 0x1796 | TIFF_DecMemOut | 05 | TIFF command 0x22 (alt) |

### Display/JPEG Functions (Block 01)

| Address | Name | Block | Description |
|---------|------|-------|-------------|
| 0x586F | Display_StatusMask | 01 | Read 0x1ECE status mask |
| 0x585E | Display_StatusCheck | 01 | Read 0x1ECF status |
| 0xCACD | JPEG_Enable | 01 | Enable JPEG (ORL #0x10 at 0x1E11) |

### Bank Switching (Block 01)

| Address | Name | Block | Description |
|---------|------|-------|-------------|
| 0x1114 | Bank_Switch | 01 | Bank switch via 0x1019 |
| 0x1008 | Bank_Init | 01 | Bank initialization |

### ISR Handlers

| Address | Name | Block | Description |
|---------|------|-------|-------------|
| 0x0F6F | MB_ISR_Warning | 01 | Mailbox ISR warning |
| 0x0FAD | MB_ISR_IntClear | 01 | Clear interrupt |

---

## AEON R2 Functions

### Mailbox Command Handlers

| Address | Name | Description |
|---------|------|-------------|
| 0x4CF27 | MB_JPD_CMD_MJPG_START_DEC | Start MJPEG decode |
| 0x4CEC5 | MB_JPD_CMD_IMAGE_DROP | JPEG ROI cropping |
| 0x4CFFC | MB_BMP_CMD_DECODE_MEM_OUT | BMP direct to DRAM |
| 0x4D092 | MB_TIFF_CMD_GET_HEAD_INF | Parse TIFF header |
| 0x4D0DB | MB_TIFF_CMD_START_DEC | Decode TIFF with ROI |
| 0x4D11E | MB_TIFF_CMD_DECODE_MEM_OUT | TIFF direct to DRAM |

### JPEG/GIF Decoder

| Address | Name | Description |
|---------|------|-------------|
| 0x4CE66 | JPG_GIF_Decoder | JPG/GIF decoder ID string |
| 0x4CE76 | JPG_GIF_DecoderID | Decoder ID format |
| 0x4D904 | JPD_EntryAbort | JPD entry abort |

### GIF Decoder

| Address | Name | Description |
|---------|------|-------------|
| 0x4D4C6 | GIF_WaitLoop | GIF decode wait loop |
| 0x4D4F7 | GIF_AbortHere | GIF abort point |
| 0x4D510 | GIF_LeaveWait | GIF leave wait loop |
| 0x4D5C1 | GIF_NotGIF | Not a GIF file error |
| 0x4D5D4 | GIF_EnterDecoder | GIF decoder entry |
| 0x4D5EA | GIF_DecodeDone | GIF decode completion |

### LZW Decoder

| Address | Name | Description |
|---------|------|-------------|
| 0x4D55B | LZW_gNEXT_CODE | LZW next code debug |
| 0x4D56A | LZW_gCUR_CODESIZE | LZW code size debug |
| 0x4D580 | LZW_Error | LZW error marker |
| 0x4D589 | LZW_MaxStackDepth | LZW max stack depth |
| 0x5E3E2 | TIFFInitLZW | Initialize LZW decoder |
| 0x5E3EE | LZW_NoSpace | No space for LZW state |
| 0x5E40B | LZWDecode_Loop | LZW loop in code table |
| 0x5E44A | LZWPreDecode | LZW pre-decode setup |
| 0x5E457 | LZW_NoCodeTable | No space for code table |
| 0x5E473 | LZWDecodeCompat_Corrupt | LZW compat corrupt |
| 0x5E540 | LZWDecode_Corrupt | LZW corrupted table |
| 0x5E5FB | LZW_OldStyle | Old-style LZW codes |
| 0x5E61D | LZWSetupDecode | LZW decode setup |

### TIFF Core Functions

| Address | Name | Description |
|---------|------|-------------|
| 0x4ED95 | TIFF_OpenError | TIFF format open error |
| 0x4EDBC | TIFF_WaitStart | Wait for decode start |
| 0x4EE11 | TIFF_StartDecode | Start TIFF decode |
| 0x4EF21 | TIFF_ScalePix | TIFF scale pixel debug |
| 0x4EFDB | TIFF_SendAbort | Send abort done |
| 0x4EFF5 | TIFF_SendDone | Send decode done |
| 0x51483 | TIFFReadDirectory | Read TIFF directory |
| 0x51458 | TIFFReadCustomDirectory | Read custom directory |
| 0x5E848 | TIFFClientOpen | Open TIFF client |
| 0x5F2AA | TIFFOpen | Open TIFF file |
| 0x5F29F | TIFFFdOpen | Open TIFF fd |

### TIFF I/O Functions

| Address | Name | Description |
|---------|------|-------------|
| 0x5EE8C | TIFFReadEncodedStrip | Read encoded strip |
| 0x5EEA1 | TIFFFillTile | Fill tile buffer |
| 0x5EEAE | TIFFFillStrip | Fill strip buffer |
| 0x5EED3 | TIFFRasterScanlineSize | Raster scanline size |
| 0x5EEEA | TIFFNumberOfStrips | Get strip count |
| 0x5EF17 | TIFFScanlineSize | Get scanline size |
| 0x5EF28 | TIFFVStripSize | Virtual strip size |
| 0x5F1F0 | TIFFTileRowSize | Tile row size |
| 0x5F200 | TIFFNumberOfTiles | Get tile count |
| 0x5F212 | TIFFVTileSize | Virtual tile size |

### TIFF Compression Codecs

| Address | Name | Description |
|---------|------|-------------|
| 0x51594 | TIFFInitCCITTFax3 | Init CCITT Fax3 |
| 0x519BC | Fax3Decode1D | Fax3 1D decode |
| 0x519C9 | Fax3Decode2D | Fax3 2D decode |
| 0x519D6 | Fax3DecodeRLE | Fax3 RLE decode |
| 0x519F8 | Fax4Decode | Fax4 decode |
| 0x5E62D | NeXTDecode | NeXT decode |
| 0x5E8F4 | PackBitsDecode | PackBits decode |
| 0x5EAFE | TIFF_FILL_STRIP | Fill strip |
| 0x5F14B | ThunderDecode | Thunder decode |

### TIFF Field/Tag Functions

| Address | Name | Description |
|---------|------|-------------|
| 0x4F389 | TIFFSetField | Set TIFF field |
| 0x4F3D4 | _TIFFVGetField | Get TIFF field |
| 0x4F640 | TIFFAdvanceDirectory | Advance directory |
| 0x4F655 | _TIFFVSetField | Set TIFF field (V) |
| 0x4F6A3 | TIFFFieldWithName | Get field by name |
| 0x4F6D4 | TIFFFieldWithTag | Get field by tag |
| 0x4F1C0 | TIFFUnRegisterCODEC | Unregister codec |
| 0x4F2FF | TIFFRegisterCODEC | Register codec |

### EXIF Parsing

| Address | Name | Description |
|---------|------|-------------|
| 0x4D178 | TIFF_ExifInfo | TIFF EXIF info |
| 0x4D1BC | TIFF_ExifDateOnly | Decode EXIF date only |
| 0x4EC22 | TIFF_Orientation | TIFF orientation tag |
| 0x4EC3C | TIFF_Make | TIFF make tag |
| 0x4EC50 | TIFF_Model | TIFF model tag |
| 0x4E9F2 | TIFF_ParseByte | Parse BYTE field |
| 0x4EA22 | TIFF_ParseShort | Parse SHORT field |
| 0x4EA53 | TIFF_ParseLong | Parse LONG field |
| 0x4EA83 | TIFF_ParseSLong | Parse SLONG field |
| 0x4EAB4 | TIFF_ParseUndef | Parse UNDEFINED field |
| 0x4EAE9 | TIFF_ParseRat | Parse RATIONAL field |
| 0x4EB20 | TIFF_ParseSRat | Parse SRATIONAL field |
| 0x4EB58 | TIFF_ParseASCII | Parse ASCII field |

### Thread/Mutex

| Address | Name | Description |
|---------|------|-------------|
| 0x4E2F8 | AEON_MutexWait | Mutex lock wait warning |
| 0x4E341 | AEON_MutexError | Mutex unlock error |
| 0x5FEE7 | IdleThread | Idle thread |

### Buffer Management

| Address | Name | Description |
|---------|------|-------------|
| 0x4D063 | TIFF_SrcBuf | Source buffer info |
| 0x4E83B | TIFF_BufReqAbort | Buffer request abort |
| 0x4E867 | TIFF_FastWaitAbort | Fast wait abort |
| 0x4EB89 | TIFF_ReadBufAbort | Read buffer abort |
| 0x4EBE3 | TIFF_ReadBufFastAbort | Fast read abort |
| 0x4EF72 | TIFF_Decode2Mem | Decode to memory |
| 0x4F0BD | TIFF_Close2 | Close TIFF (2) |
| 0x4F0DE | TIFF_Close3 | Close TIFF (3) |
| 0x4F0F3 | TIFF_Close4 | Close TIFF (4) |

---

## Function Call Flow

### JPEG Decode Flow

```
8051                              AEON
────                              ────
MB_SendCommand(0x01)    →    [Mailbox Receive]
    ↓                              ↓
MB_SelectJPEGCmd        →    MB_JPD_CMD_MJPG_START_DEC
    ↓                              ↓
JPEG_Enable             ←    JPG_GIF_Decoder
    ↓                              ↓
Display_CheckJPEG       ←    [Decode Complete]
```

### TIFF Decode Flow

```
8051                              AEON
────                              ────
TIFF_StartDec(0x21)     →    MB_TIFF_CMD_START_DEC
    ↓                              ↓
[Wait Status]           ←    TIFFReadDirectory
                               ↓
                         TIFFInitLZW / PackBitsDecode
                               ↓
TIFF_DecMemOut(0x22)    →    MB_TIFF_CMD_DECODE_MEM_OUT
    ↓                              ↓
[Read DRAM]             ←    TIFF_SendDone
```

### BMP Decode Flow

```
8051                              AEON
────                              ────
BMP_DecodeMemOut(0x10)  →    MB_BMP_CMD_DECODE_MEM_OUT
    ↓                              ↓
[Wait Status]           ←    [Decode to DRAM addr]
    ↓                              ↓
[Read DRAM]             ←    [Complete]
```

---

## Verification Summary

| Category | Count | Status |
|----------|-------|--------|
| 8051 Library Functions | 20 | ✓ Traced (LCALL patterns) |
| 8051 Mailbox Functions | 5 | ✓ Traced (block 02) |
| 8051 Watchdog Functions | 6 | ✓ Traced (blocks 15, 16) |
| 8051 AEON Control | 4 | ✓ Traced (block 01) |
| 8051 Command Dispatch | 8 | ✓ Traced (all blocks) |
| AEON Mailbox Handlers | 6 | ✓ Traced (strings) |
| AEON JPEG/GIF | 6 | ✓ Traced (strings) |
| AEON LZW | 12 | ✓ Traced (strings) |
| AEON TIFF Core | 11 | ✓ Traced (strings) |
| AEON TIFF I/O | 10 | ✓ Traced (strings) |
| AEON TIFF Codecs | 9 | ✓ Traced (strings) |
| AEON TIFF Fields | 10 | ✓ Traced (strings) |
| AEON EXIF | 12 | ✓ Traced (strings) |
| AEON Thread/Mutex | 3 | ✓ Traced (strings) |

**Total: 122 named functions**

---

## Related Documentation

- [D72N_REGISTER_MAP.md](D72N_REGISTER_MAP.md) - RIU registers
- [D72N_VARIABLE_MAP.md](D72N_VARIABLE_MAP.md) - XDATA variables
- [D72N_MAILBOX_PROTOCOL.md](D72N_MAILBOX_PROTOCOL.md) - Mailbox IPC
- [D72N_COMMAND_DISPATCH.md](D72N_COMMAND_DISPATCH.md) - Command dispatch
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
