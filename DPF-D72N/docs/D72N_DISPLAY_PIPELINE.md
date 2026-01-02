# D72N Display Pipeline

Complete display subsystem documentation for the DPF-D72N, traced from 8051 blocks and AEON firmware.

## Architecture Overview

```
Image File (SD/USB/NAND)
         │
         ▼
┌─────────────────────┐
│   8051 MCU          │
│   File System       │ ← Blocks 05, 07, 08 (Storage drivers)
│   Menu/UI Logic     │ ← Blocks 03, 09, 11-14 (Primary state 0x40EA)
└─────────────────────┘
         │ Mailbox IPC (0x4401)
         ▼
┌─────────────────────┐     ┌─────────────────┐
│   AEON R2 Core      │────▶│  JPD (0x1E)     │
│   Media Decoder     │     │  JPEG/BMP/TIFF  │
└─────────────────────┘     └─────────────────┘
         │                           │
         ▼                           ▼
┌─────────────────────┐     ┌─────────────────┐
│   GE (0x20)         │     │  DRAM           │
│   Graphics Engine   │     │  Framebuffers   │
│   (314 refs blk 07) │     │  0x0C0000+      │
└─────────────────────┘     └─────────────────┘
         │                           │
         ▼                           ▼
┌─────────────────────┐     ┌─────────────────┐
│   OSDE (0x2F)       │◀────│  GWin Control   │
│   OSD Engine        │     │  0x6653, 0x69BE │
└─────────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────────┐
│   GOP (0x30)        │
│   Graphics Output   │
└─────────────────────┘
         │
         ▼
    ┌─────────┐
    │  Panel  │  7" Analog TFT
    │  Output │  ~480x234
    └─────────┘
```

---

## RIU Display Banks (Traced)

| Bank | Name | Block 07 | Other Blocks | Purpose |
|------|------|----------|--------------|---------|
| 0x1E | JPD | 29 refs | 2-20 refs | JPEG/Image decoder |
| 0x1F | AEON | 1 ref | 1-52 refs* | AEON processor control |
| 0x20 | GE | **314 refs** | 1-5 refs | Graphics Engine (2D) |
| 0x2F | OSDE | 2 refs | 2-3 refs | OSD Engine |
| 0x30 | GOP | 1 ref | 1-2 refs | Graphics Output |

*Block 06 has 52 AEON control refs (primary AEON management block)

### GE Register Offsets (Block 07)

| Offset | Purpose (Inferred) |
|--------|-------------------|
| 0x00 | GE control |
| 0x02 | GE config |
| 0x04 | Source X |
| 0x06 | Source Y |
| 0x08 | Destination X |
| 0x09 | Destination Y |
| 0x0A | Width |
| 0x0C | Height |
| 0x0E | Pitch |
| 0x10 | Color/Alpha |

### JPD Register Offsets (Traced)

| Offset | Block | Purpose |
|--------|-------|---------|
| 0x00 | 01 | JPD control |
| 0x10, 0x11, 0x14 | 05 | Bitstream control |
| 0x22, 0x45 | 01 | Decode config |
| 0x6C | All | JPD status (common) |
| 0x78, 0x79 | 07 | Frame buffer control |
| 0x80, 0x81, 0x83 | 01, 06 | Output buffer |
| 0xA1 | 06 | Extended control |
| 0xC1 | All | Status read (common) |
| 0xCE, 0xCF | 01, 05, 14, 16 | Decode complete |
| 0xE3 | 14 | Error status |

### AEON Control Register Offsets (Block 06)

| Offset | Purpose |
|--------|---------|
| 0x00 | AEON status |
| 0x01 | AEON control |
| 0x03 | Reset control |
| 0x06 | Clock control |
| 0x07 | Memory control |
| 0x09 | Interrupt control |
| 0x0A | Interrupt status |
| 0x27 | Debug control |
| 0x29 | Debug status |
| 0x2C | Mailbox |

---

## DRAM Buffer Layout (Traced from AEON)

```
DRAM Address Space
==================
0x000000 ┌─────────────────────────────┐
         │   System/Reserved           │
         │   (AEON code, stack)        │
0x0C0000 ├─────────────────────────────┤
         │   Secondary Buffer          │  673 refs
         │   ~256KB                    │
         │   +0x100: 84 refs           │
         │   +0x400: 68 refs           │
         │   +0x600: 83 refs           │
0x100000 ├─────────────────────────────┤
         │   Main Decode Buffer        │  888 refs (most used)
         │   ~512KB                    │
         │   +0x030: 74 refs (header)  │
         │   +0x100: 152 refs          │
         │   +0x600: 126 refs          │
         │   +0x1004: 52 refs (struct) │
0x150000 ├─────────────────────────────┤
         │   Output Buffer             │  384 refs
         │   ~256KB                    │
         │   +0x100: 67 refs           │
         │   +0x400: 56 refs           │
0x1B0000 └─────────────────────────────┘
```

### Buffer Sub-regions

| Address | Refs | Offset | Purpose |
|---------|------|--------|---------|
| 0x100000 | 888 | Base | Main decode buffer base |
| 0x100100 | 152 | +0x100 | Decoded image data |
| 0x100600 | 126 | +0x600 | Secondary data region |
| 0x100030 | 74 | +0x30 | Buffer header/metadata |
| 0x101004 | 52 | +0x1004 | Decode structure |
| 0x0C0000 | 673 | Base | Secondary buffer base |
| 0x0C0600 | 83 | +0x600 | Secondary data |
| 0x150000 | 384 | Base | Output/display buffer |
| 0x150100 | 67 | +0x100 | Display data |

---

## GWin Control (Traced)

Graphics Window control via XDATA:

| Address | Refs | Blocks | Purpose |
|---------|------|--------|---------|
| 0x6653 | 31 | 05 | GWin primary control |
| 0x6653 | 13 | 07 | GWin primary control |
| 0x69BE | 2 | All | GWin secondary |
| 0x6D2C | 2 | All | GWin tertiary |

### GWin Configuration

Block 05 (31 refs to 0x6653) handles primary GWin setup:
- NAND driver configures display windows
- Sets framebuffer addresses
- Configures display dimensions

Block 07 (13 refs to 0x6653) handles GWin during:
- Card read operations
- Image scaling/conversion

---

## Display State Variables (XDATA)

### Primary State (0x40EA)

| Block | Refs | Purpose |
|-------|------|---------|
| 03 | 128 | Menu/navigation state |
| 12 | 160 | Extended state |
| 11 | 103 | UI state |
| 14 | 102 | OSD loading state |
| 13 | 98 | Configuration state |
| 09 | 82 | Display mode |
| 16 | 21 | Storage monitor |
| 18 | 15 | File copy state |

### Display State (0x4720)

| Block | Refs | Purpose |
|-------|------|---------|
| 15 | 38 | Slideshow display |
| 16 | 32 | Storage display |
| 18 | 26 | Copy progress |
| 06 | 18 | USB display |
| 17 | 17 | JPEG display |
| 05 | 13 | NAND display |
| 07 | 11 | Card display |

### Decode State (0x4641)

All blocks: 12 refs (common decode status)

### Image Address (0x404C)

All blocks: 2-7 refs (current framebuffer address)

---

## AEON Decode Handlers

### JPEG/GIF Decoder (0x4CE66)

```
Strings traced:
0x4CE66: JPG/GIF Decoder
0x4CE76: * JPG/GIF Decoder id [%X]
0x4CF7F: [JPD]frame buffer2 addr:0x%08x
0x4D680: [JPD]width:%d height:%d
0x4E0C3: [JPD]scalefac:%d
0x4E149: [JPD]frame buffer1 addr:0x%08x, size:0x%lx
0x4E175: [PJPD]gTARGET_BUF:0x%08x,imagewidth:%d, scale: %d
```

### BMP Decoder (0x4CFFC)

```
Strings traced:
0x4CFDF: BMP roi L %u T %u W %u H %u
0x4CFFC: [MB_BMP_CMD_DECODE_MEM_OUT] addr %lx pitch %u down factor %u
0x4E538: [BMP%dBitMode] ScaledPix %u LineSize %u
0x4E62F: [BMP] scale Pix %d, width %d height %d
0x4E671: base addr of ROI %lx pitch %x
```

### TIFF Decoder (0x4D092)

```
Strings traced:
0x4D0B9: [TIFF] Stretch ROI %d %d %d %d
0x4D11E: [MB_TIFF_CMD_DECODE_MEM_OUT] addr %lx pitch %u down pix %u
0x4D15A: TIFF roi L %u T %u W %u H %u
0x4EE2E: [PLANAR_MEM_OUT] re calculate scale factors
0x4EE80: [DIRECT_MEM_OUT] re calculate scale factors
0x4EED2: [ROI_MEM_OUT] re calculate scale factors
```

### MJPEG Video (0x4D7C0)

```
Strings traced:
0x4D7C0: [MJPG]frames to add one ms:%d
0x4D7E0: [MJPG]%d ms per frame....
0x4D81C: [MJPG]total frame count is:%d
0x4D83B: [MJPG]avi width is:%d
0x4D852: [MJPG]avi height is:%d
```

---

## OSD Subsystem

### OSD Buffers (XDATA)

| Address | Refs | Purpose |
|---------|------|---------|
| 0x4479 | 13 (blk 05) | osdcp_text_addr |
| 0x447D | 4 (blk 02, 05) | image_width |
| 0x447F | - | image_height |

### OSD Functions (Traced from Blocks)

| Block | String | Purpose |
|-------|--------|---------|
| 02 | `[MDrv_OSDE_CreateFb] Cannot create buffer` | Framebuffer create |
| 02 | `MApi_Osd_Create_GC pGC->u8FBID==0xff` | Graphics context |
| 02 | `MDrv_OSDE_Fb_CompressMode fails!!` | Compression |
| 02 | `MDrv_OSDE_Fb_ColorKey fails!!` | Color key |
| 11 | `ZGet GUI OSD from CFG %bu` | OSD config |
| 11 | `[page init] black screen` | Display init |
| 11 | `Unknow OSD` | Error |
| 14 | `OSDcp_LoadIcon2POOL()` | Icon loading |
| 14 | `OSDcp_readbin_info_init()` | Binary info |
| 14 | `MApp_LoadFont_OSD()` | Font loading |

### OSD RIU Control

| Bank | Offset | Block | Purpose |
|------|--------|-------|---------|
| 0x2F | 0x1E | All | OSDE control |
| 0x2F | 0x59 | All | OSDE status |
| 0x2F | 0x90 | 15 | Extended control |
| 0x2F | 0xFD | 06 | Config |
| 0x2F | 0xFF | 02 | Status |
| 0x30 | 0x00 | 16 | GOP control |
| 0x30 | 0xE8 | All | GOP status |

---

## Display Pipeline Flow

### Image Decode Path

```
1. 8051 File Read
   ├─► Storage driver (blocks 05, 07, 08)
   ├─► Read image from SD/USB/NAND
   └─► Store to DRAM 0x100000 (main buffer)

2. Mailbox Command
   ├─► 8051 writes to 0x4401 (JPEG) or 0x40BC (BMP/TIFF)
   ├─► Command includes:
   │   ├─► Source buffer address
   │   ├─► Destination buffer address
   │   ├─► Image dimensions
   │   └─► Scale factor / ROI
   └─► Trigger AEON interrupt

3. AEON Decode
   ├─► JPD hardware decode (0x1E bank)
   ├─► Output to DRAM buffer
   ├─► ROI cropping if needed
   └─► Scale via GE if needed

4. GE Processing (Block 07)
   ├─► 314 GE operations
   ├─► Color conversion
   ├─► Scaling / rotation
   └─► Bitblit to display buffer

5. OSDE Overlay
   ├─► OSD text/icons loaded
   ├─► Alpha blending
   └─► Combined with image layer

6. GOP Output
   ├─► Framebuffer → panel timing
   ├─► RGB output to panel
   └─► Refresh at panel rate
```

### UI State Machine

```
Primary State (0x40EA)
         │
    ┌────┴────┐
    ▼         ▼
Slideshow   Menu
(0x4720)    (0x4074)
    │         │
    ▼         ▼
Display   OSD Load
Update    (blk 14)
```

---

## Slideshow Display

### Slideshow Strings (Block 15)

| Offset | String |
|--------|--------|
| 0x055E | `NextOneFrame` |
| 0x0768 | `NextOneFrame is failed` |
| 0x07E4 | `Image width %d height%d` |
| 0x05E7 | `SS(%d) storage change #2!!` |

### Slideshow State

| Address | Purpose |
|---------|---------|
| 0x4720 | Display state (38 refs in block 15) |
| 0x4641 | Decode state (12 refs all blocks) |
| 0x404C | Current image address |

---

## JPEG Decode Detail

### Block 17 JPD Strings

| Offset | String |
|--------|--------|
| 0x134B | `[JPD]before image width:%d,imagepitch:%d,imageheight:%d` |
| 0x13A6 | `[JPD]after image width:%d,imagepitch:%d,imageheight:%d` |
| 0x13DE | `[JPD ROI Mem]ScaleFact %bu image width:%u mem pitch %u` |
| 0x14A3 | `Change Scale Pix %u` |
| 0x1769 | `Zero Image ScalarLimit mode min scaled width` |
| 0x17CB | `Zero Image ScalarLimit mode Scale down limit` |
| 0x1BB2 | `[Hit Min] Zero Image Width %u Height %u` |
| 0x1BDD | `[Hit Max supprot] Zero Image Width %u Height %u` |

### Scale Factors

| Factor | Effect |
|--------|--------|
| 0 | 1:1 (no scaling) |
| 1 | 1:2 (half size) |
| 2 | 1:4 (quarter size) |
| 3 | 1:8 (eighth size) |

---

## Error Handling

### Decode Errors

| Block | String | Condition |
|-------|--------|-----------|
| 02 | `GE Hangup:0x%bx%bx` | GE timeout |
| 02 | `[MDrv_OSDE_CreateFb] Cannot create buffer` | OOM |
| 15 | `[FB]%d Incorrect magic number(%lX)` | Corrupt file |
| 17 | `[JPEG]boom and wont fire` | Decode failure |
| 18 | `decode failed` | Generic failure |

### Display Errors

| Block | String | Condition |
|-------|--------|-----------|
| 11 | `Unknow OSD` | Invalid OSD type |
| 11 | `[page init] black screen` | Init failure |
| 15 | `NextOneFrame is failed` | Frame advance fail |

---

## SERDB Display Access

### Write to Framebuffer

```python
# Write test pattern to main decode buffer
def write_framebuffer_test():
    for i in range(256):
        serdb.write_dram(0x100000 + i, 0xF8)  # Red in RGB565
```

### Read Display State

```python
# Read current display state
state_4720 = serdb.read_xdata(0x4720)
state_4641 = serdb.read_xdata(0x4641)
image_addr = (serdb.read_xdata(0x404F) << 24 |
              serdb.read_xdata(0x404E) << 16 |
              serdb.read_xdata(0x404D) << 8 |
              serdb.read_xdata(0x404C))
```

### Modify GWin

```python
# Modify GWin control (dangerous - may corrupt display)
serdb.write_xdata(0x6653, new_gwin_value)
```

---

## Related Documentation

- [D72N_MEMORY_MAP.md](D72N_MEMORY_MAP.md) - DRAM buffer details
- [D72N_REGISTER_MAP.md](D72N_REGISTER_MAP.md) - RIU register reference
- [D72N_VARIABLE_MAP.md](D72N_VARIABLE_MAP.md) - XDATA variables
- [D72N_MAILBOX_PROTOCOL.md](D72N_MAILBOX_PROTOCOL.md) - Decode commands
- [D72N_DRIVERS.md](D72N_DRIVERS.md) - Driver reference
- [D72N_INDEX.md](D72N_INDEX.md) - Documentation index
