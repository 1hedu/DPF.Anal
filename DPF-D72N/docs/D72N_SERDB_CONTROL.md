# D72N SERDB Control Reference

Complete register and variable reference for controlling the DPF-D72N firmware via SERDB.

## Architecture Note

The D72N uses a dual-processor architecture (PM51 + AEON R2). SERDB provides access to:
- **XDATA (0x80)**: PM51/8051 memory space - state variables, mailbox registers
- **DRAM (0x81)**: Shared memory - decode buffers, AEON data
- **RIU (0x83/0x84)**: Hardware registers

The XDATA addresses documented below are in PM51 memory space, accessible even though we only have the AEON dump for analysis.

## Verification Status

Addresses were verified by comparing code patterns with a known-working similar firmware:

| Status | Meaning |
|--------|---------|
| ✓ Confirmed | Identical patterns found, high confidence |
| ○ Likely | Patterns found, needs hardware verification |
| ? Assumed | Based on SDK patterns, unverified |

## Quick Reference

### SERDB Commands

```python
# SERDB I2C address: 0x59
# Channels:
#   0x80 = XDATA (64KB)
#   0x81 = DRAM
#   0x83 = PM RIU
#   0x84 = Non-PM RIU

def read_xdata(addr):
    bus.write_i2c_block_data(0x59, 0x80, [addr >> 8, addr & 0xFF])
    return bus.read_byte(0x59)

def write_xdata(addr, val):
    bus.write_i2c_block_data(0x59, 0x80, [addr >> 8, addr & 0xFF, val])

def read_dram(addr):
    bus.write_i2c_block_data(0x59, 0x81, [
        (addr >> 16) & 0xFF,
        (addr >> 8) & 0xFF,
        addr & 0xFF
    ])
    return bus.read_byte(0x59)

def write_dram(addr, val):
    bus.write_i2c_block_data(0x59, 0x81, [
        (addr >> 16) & 0xFF,
        (addr >> 8) & 0xFF,
        addr & 0xFF,
        val
    ])
```

---

## 1. Mailbox Protocol

### Mailbox Addresses

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x4400 | 483 | Mailbox base | ✓ Confirmed |
| 0x4401 | 42 | Command byte | ✓ Confirmed |
| 0x4402 | 17 | Params start | ✓ Confirmed |
| 0x4417 | 4 | Sync flag | ✓ Confirmed |
| 0x40FB | 4 | Status register | ✓ Confirmed |
| 0x40FC | 2 | Response[0] | ✓ Confirmed |
| 0x40FD | 4 | Response[1] | ✓ Confirmed |
| 0x40FE | 4 | Response[2] | ✓ Confirmed |
| 0x40FF | 46 | Response[3] | ✓ Confirmed |

```python
def send_mailbox_command(cmd, params=None):
    """Send command to AEON via mailbox"""
    # 1. Wait for ready
    while read_xdata(0x40FB) != 0xFE:
        time.sleep(0.001)

    # 2. Write command
    write_xdata(0x4401, cmd)

    # 3. Write params (up to 21 bytes)
    if params:
        for i, p in enumerate(params[:21]):
            write_xdata(0x4402 + i, p)

    # 4. Trigger (clear sync)
    write_xdata(0x4417, 0x00)

    # 5. Wait for completion
    while read_xdata(0x40FB) == 0x00:
        time.sleep(0.001)

    # 6. Read response
    return [read_xdata(0x40FC + i) for i in range(4)]
```

---

## 2. Mailbox Commands

### JPEG Commands (Verified from Similar MStar AEON Device + 8051 Analysis)

| Cmd | Name | Status | Evidence |
|-----|------|--------|----------|
| 0x01 | MB_JPD_CMD_INIT | ✓ Confirmed | Similar MStar AEON device protocol, 8051 dispatch |
| 0x02 | MB_JPD_CMD_MJPG_START_DEC | ✓ Confirmed | Debug string at 0x4CF27, 8051 at 0x22F2 |
| 0x03 | MB_JPD_CMD_ABORT | ✓ Confirmed | Similar MStar AEON device protocol, 8051 patterns |
| 0x04 | MB_JPD_CMD_PAUSE | ✓ Confirmed | Similar MStar AEON device protocol, 8051 patterns |
| 0x05 | MB_JPD_CMD_RESUME | ✓ Confirmed | Similar MStar AEON device protocol, 8051 patterns |
| 0x06 | MB_JPD_CMD_IMAGE_DROP | ○ Likely | Debug string at 0x4CEC5 |

### BMP Commands (From 8051 Analysis)

| Cmd | Name | Status | Evidence |
|-----|------|--------|----------|
| 0x10 | MB_BMP_CMD_DECODE_MEM_OUT | ○ Likely | Debug string at 0x4CFFC, 8051 at 0xAC80 |

### TIFF Commands (Inferred from Debug Strings)

| Cmd | Name | Status | Evidence |
|-----|------|--------|----------|
| 0x20 | MB_TIFF_CMD_GET_HEAD_INF | ? Assumed | Debug string at 0x4D092 |
| 0x21 | MB_TIFF_CMD_START_DEC | ? Assumed | Debug string at 0x4D0DB |
| 0x22 | MB_TIFF_CMD_DECODE_MEM_OUT | ? Assumed | Debug string at 0x4D11E |

### Analysis Methodology

**8051 code analysis** revealed command byte patterns by searching for:
- `MOV DPTR, #4401h` (90 44 01) - mailbox command address
- `MOV A, #XX; MOVX @DPTR, A` (74 XX F0) - write command byte
- `MOV R6, #XX` (7E XX) before mailbox function calls

Key findings from D72N 8051 blocks (`/DPF-D72N/blocks/`):
- Block_02 at 0x22F0: Commands 0x01, 0x02 written to mailbox
- Block_01/02 at 0xAC80: Command 0x10 (BMP) found
- Block_01/02 at 0xAC96: Command 0x08 found
- Mailbox send function at 0x2830-0x2845 writes R6 to 0x4401

**Similar MStar AEON device cross-reference** confirms JPEG commands 0x01-0x05 are identical across MStar firmware variants.

**TIFF commands** (0x20-0x22) are D72N-specific and require hardware verification.

```python
# Send TIFF header info request
def get_tiff_header():
    return send_mailbox_command(TIFF_GET_HEAD_INF)

# Start TIFF decode with ROI
def decode_tiff_roi(left, top, width, height):
    params = [
        left & 0xFF, (left >> 8) & 0xFF,
        top & 0xFF, (top >> 8) & 0xFF,
        width & 0xFF, (width >> 8) & 0xFF,
        height & 0xFF, (height >> 8) & 0xFF,
    ]
    return send_mailbox_command(TIFF_START_DEC, params)
```

---

## 3. Primary State Variables

### Core State (Most Referenced)

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x4800 | 1330 | Primary state machine | ✓ Confirmed |
| 0x4801 | 520 | State machine field 2 | ✓ Confirmed |
| 0x4185 | 559 | Secondary state | ✓ Confirmed |
| 0x4A9D | 288 | Decode state | ✓ Confirmed |
| 0x4018 | 255 | System state | ✓ Confirmed |
| 0x4000 | 215 | Base pointer | ✓ Confirmed |
| 0x43A9 | 155 | Process state | ✓ Confirmed |
| 0x4100 | 140 | Storage state | ✓ Confirmed |

```python
def dump_d72n_state():
    """Dump D72N primary state variables"""
    print("=== D72N State ===")
    print(f"Primary state: 0x{read_xdata(0x4800):02X}{read_xdata(0x4801):02X}")
    print(f"Secondary:     0x{read_xdata(0x4185):02X}")
    print(f"Storage:       0x{read_xdata(0x4100):02X}")
    print(f"Mailbox:       0x{read_xdata(0x40FB):02X}")
```

### Mailbox Parameter Registers

| Address | Refs | Purpose |
|---------|------|---------|
| 0x4404 | 86 | Param word 0 |
| 0x4408 | 38 | Param word 2 |
| 0x440C | 51 | Param word 4 |
| 0x4410 | 51 | Param word 6 |
| 0x4414 | 53 | Param word 8 |
| 0x4418 | 42 | Param word 10 |
| 0x441C | 58 | Param word 12 |

---

## 4. Display/Graphics Control

### GWin Variables

| Address | Refs | Purpose | Status |
|---------|------|---------|--------|
| 0x6EA8 | 116 | Primary GWin control | ✓ Confirmed |
| 0x6FA8 | 106 | Secondary GWin control | ✓ Confirmed |
| 0x6E84 | 23 | GWin state A | ✓ Confirmed |
| 0x6F84 | 23 | GWin state B | ✓ Confirmed |
| 0x6E9C | 14 | GWin config A | ✓ Confirmed |
| 0x6F9C | 20 | GWin config B | ✓ Confirmed |
| 0x6EE0 | 14 | GWin enable A | ✓ Confirmed |
| 0x6F00 | 16 | GWin base B | ✓ Confirmed |
| 0x6EBD | 10 | GWin lock | ○ Likely |
| 0x6EFF | 10 | GWin status | ✓ Confirmed |

```python
def enable_gwin():
    """Enable graphics window"""
    write_xdata(0x6EA8, 0x01)
    write_xdata(0x6FA8, 0x01)

def disable_gwin():
    """Disable graphics window"""
    write_xdata(0x6EA8, 0x00)
    write_xdata(0x6FA8, 0x00)
```

---

## 5. DRAM Buffer Map

### Primary Buffers (from code analysis)

| Address | Refs | Size (est) | Purpose | Status |
|---------|------|------------|---------|--------|
| 0x100000 | 876 | ~512KB | Main decode buffer | ✓ Confirmed |
| 0x0C0000 | 665 | ~256KB | Secondary buffer | ✓ Confirmed |
| 0x150000 | 372 | ~256KB | Output buffer | ✓ Confirmed |

### Buffer Sub-regions

| Address | Refs | Purpose |
|---------|------|---------|
| 0x100100 | 151 | Buffer +0x100 |
| 0x100600 | 126 | Buffer +0x600 |
| 0x100400 | 121 | Buffer +0x400 |
| 0x0C0100 | 84 | Secondary +0x100 |
| 0x100030 | 74 | Buffer +0x30 |

```python
def read_decode_buffer(offset, length):
    """Read from main decode buffer"""
    base = 0x100000
    result = []
    for i in range(length):
        result.append(read_dram(base + offset + i))
    return bytes(result)

def write_decode_buffer(offset, data):
    """Write to main decode buffer"""
    base = 0x100000
    for i, b in enumerate(data):
        write_dram(base + offset + i, b)
```

---

## 6. TIFF-Specific Control

### TIFF Global Variables

Based on debug strings:
- `gSRC_BUF` - Source buffer address
- `gSRC_BUF_SIZE` - Source buffer size
- `gTIFF_STRIP_BUF_BASEADDDR` - Strip buffer base
- `gTIFF_STRIP_BUF_SIZE` - Strip buffer size

### TIFF ROI Parameters

```python
# From string: "TIFF roi L %u T %u W %u H %u"
# ROI parameters are passed via mailbox

def set_tiff_roi(left, top, width, height):
    """Set TIFF region of interest"""
    # Pack as 16-bit LE values
    params = [
        left & 0xFF, (left >> 8) & 0xFF,
        top & 0xFF, (top >> 8) & 0xFF,
        width & 0xFF, (width >> 8) & 0xFF,
        height & 0xFF, (height >> 8) & 0xFF,
    ]
    send_mailbox_command(TIFF_CMD_START_DEC, params)
```

### LZW Decoder State

D72N includes full libtiff LZW with error handling:
- Scanline-based decode
- Strip buffer management
- Corruption detection

---

## 7. BMP Enhanced Control

### BMP ROI Parameters

```python
# From string: "BMP roi L %u T %u W %u H %u"

def decode_bmp_roi(left, top, width, height, out_addr, pitch, downscale):
    """Decode BMP with ROI and direct memory output"""
    params = [
        left & 0xFF, (left >> 8) & 0xFF,
        top & 0xFF, (top >> 8) & 0xFF,
        width & 0xFF, (width >> 8) & 0xFF,
        height & 0xFF, (height >> 8) & 0xFF,
        out_addr & 0xFF, (out_addr >> 8) & 0xFF,
        (out_addr >> 16) & 0xFF, (out_addr >> 24) & 0xFF,
        pitch & 0xFF, (pitch >> 8) & 0xFF,
        downscale,
    ]
    send_mailbox_command(BMP_CMD_DECODE_MEM_OUT, params)
```

### BMP Scaling Variables

Referenced in strings:
- `u16ScalePix` - Scale pixel count
- `gBMP_SKIPLINE_CNT` - Line skip count
- `ScaledPix`, `LineSize` - Output dimensions

---

## 8. JPEG Enhanced Control (ROI Drop)

### Image Drop Command

```python
# From string: "[MB_JPD_CMD_IMAGE_DROP] gROI_offsetX %u  gROI_offsetY %u U=%d, D=%d, R=%d, L=%d"

def jpeg_image_drop(offset_x, offset_y, up, down, right, left):
    """Drop/crop JPEG with directional control"""
    params = [
        offset_x & 0xFF, (offset_x >> 8) & 0xFF,
        offset_y & 0xFF, (offset_y >> 8) & 0xFF,
        up, down, right, left,
    ]
    send_mailbox_command(JPD_CMD_IMAGE_DROP, params)
```

---

## 9. EXIF/Metadata Control

### EXIF String Indicators

| String Offset | Content |
|---------------|---------|
| 0x4D878 | "EXIF", "Exif" markers |
| 0x4D91E | "[JPD] APP1 base offset" |
| 0x4D95A | "[JPD-0th] 0th IFD offset" |
| 0x4D9AD | "[JPD-1st] 1st IFD offset" |
| 0x4D9CF | "[JPD-1st] EXIF IFD offset" |

### EXIF State Variables

Based on string `gMy_exif_info`:
- EXIF info struct is at a global address
- Contains orientation, date, flash, lightsource

---

## 10. Watchdog Control

| Address | Purpose | Status |
|---------|---------|--------|
| 0x44CE | Watchdog state (2 refs) | ○ Likely |
| 0x44D3 | Watchdog disable (1 ref) | ○ Likely |

```python
def disable_watchdog():
    """Disable software watchdog"""
    write_xdata(0x44D3, 0x00)
    write_xdata(0x44CE, 0x00)
```

---

## 11. Complete State Dump

```python
def dump_d72n_full_state():
    """Complete D72N state dump via SERDB"""

    print("=== MAILBOX ===")
    print(f"Status:  0x{read_xdata(0x40FB):02X}")
    print(f"Command: 0x{read_xdata(0x4401):02X}")
    print(f"Sync:    0x{read_xdata(0x4417):02X}")
    print(f"Response: {[hex(read_xdata(0x40FC+i)) for i in range(4)]}")

    print("\n=== PRIMARY STATE ===")
    print(f"0x4800: 0x{read_xdata(0x4800):02X}{read_xdata(0x4801):02X}")
    print(f"0x4185: 0x{read_xdata(0x4185):02X}")
    print(f"0x4A9D: 0x{read_xdata(0x4A9D):02X}")
    print(f"0x4100: 0x{read_xdata(0x4100):02X}")

    print("\n=== GWIN ===")
    print(f"0x6EA8: 0x{read_xdata(0x6EA8):02X}")
    print(f"0x6FA8: 0x{read_xdata(0x6FA8):02X}")
    print(f"0x6EE0: 0x{read_xdata(0x6EE0):02X}")

    print("\n=== WATCHDOG ===")
    print(f"0x44CE: 0x{read_xdata(0x44CE):02X}")
    print(f"0x44D3: 0x{read_xdata(0x44D3):02X}")
```

---

## 12. Exploitation via SERDB

### Direct Memory Write Attack

D72N's `MB_*_DECODE_MEM_OUT` commands allow writing decoded image data to arbitrary DRAM addresses:

```python
def write_arbitrary_dram(addr, data):
    """Use BMP decode to write arbitrary data to DRAM"""
    # 1. Prepare crafted BMP in source buffer
    craft_bmp_with_payload(data)

    # 2. Trigger decode to target address
    decode_bmp_roi(0, 0, len(data), 1, addr, len(data), 1)

    # Result: data written to target DRAM address
```

### TIFF Parser Attack Surface

Full libtiff increases attack surface:
- LZW decompression bugs
- Strip/tile buffer overflows
- Tag parsing vulnerabilities

---

## 13. XDATA Reference Summary (Top 30)

| Rank | Address | Refs | Purpose |
|------|---------|------|---------|
| 1 | 0x4800 | 1330 | Primary state |
| 2 | 0x4185 | 559 | Secondary state |
| 3 | 0x4801 | 520 | State field 2 |
| 4 | 0x4400 | 483 | Mailbox base |
| 5 | 0x4A9D | 288 | Decode state |
| 6 | 0x4018 | 255 | System state |
| 7 | 0x4000 | 215 | Base pointer |
| 8 | 0x4019 | 209 | System field 2 |
| 9 | 0x401B | 166 | System field 3 |
| 10 | 0x409D | 166 | Status |
| 11 | 0x43A9 | 155 | Process state |
| 12 | 0x4100 | 140 | Storage state |
| 13 | 0x6EA8 | 116 | GWin primary |
| 14 | 0x4C00 | 115 | Buffer control |
| 15 | 0x6FA8 | 106 | GWin secondary |
| 16 | 0x4186 | 92 | State extension |
| 17 | 0x4200 | 91 | File state |
| 18 | 0x4DE4 | 89 | Extended state |
| 19 | 0x4404 | 86 | MB param 0 |
| 20 | 0x4ABD | 84 | Decode param |

---

## Related Documentation

- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
- [D72N_SECURITY_ANALYSIS.md](D72N_SECURITY_ANALYSIS.md) - Vulnerability analysis
