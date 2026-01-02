# D72N Driver Reference

Peripheral drivers for the DPF-D72N digital picture frame, traced from 8051 overlay blocks and AEON firmware.

## Driver Architecture

```
DPF-D72N Driver Stack
├── 8051 Drivers (Overlay Blocks)
│   ├── SPI Flash Driver (Block 01)
│   ├── NAND Driver (Block 05)
│   ├── USB/SCSI Driver (Block 06)
│   ├── SD/MMC/MS Driver (Block 07)
│   ├── FAT Filesystem (Block 08)
│   ├── Storage Monitor (Block 16)
│   └── Common: Mailbox, AEON Control, Watchdog
└── AEON Drivers (R2 Image)
    ├── JPEG/GIF Decoder
    ├── BMP Decoder
    ├── TIFF/LZW Decoder
    └── Display/OSD Engine
```

---

## 8051 Drivers

### SPI Flash Driver (Block 01)

Controls external SPI flash for firmware and configuration storage.

| Property | Value |
|----------|-------|
| Source Block | block_01_0x40000-0x50000.bin |
| Source File | `drvspi.c` |
| RIU Banks | 0x10 (CHIPTOP), 0x18/0x19 (NAND/SPI) |

#### Strings

| Offset | String |
|--------|--------|
| 0x0DD7 | `* SPI flash clock 40 MHz` |
| 0x0DF1 | `[Ceramal basic initialization complete]` |
| 0x0E67 | `Assert failed: gu8VendorId != SPIFLASH_VENDOR_SST` |
| 0x0EAC | `..\..\Customer\Driver\drvspi.c` |
| 0x0ECB | `Assert failed: length <= SPI_FLASH_PAGE_SIZE` |
| 0x0F0B | `drvspi: Invalid address` |
| 0x0F24 | `drvspi: Range exceed flash size` |
| 0x0F45 | `drvspi: block size must be power of two` |

#### Operations

- Page size: `SPI_FLASH_PAGE_SIZE` (likely 256 bytes)
- Clock: 40 MHz
- Vendor check: SST flash requires special handling
- Address validation before read/write

---

### NAND Driver (Block 05)

Controls internal NAND flash for storage and FAT filesystem.

| Property | Value |
|----------|-------|
| Source Block | block_05_0x80000-0x90000.bin |
| RIU Banks | 0x10 (CHIPTOP), 0x18/0x19 (NAND) |
| Page Types | 512B (small) and 2KB (large) |

#### Top Functions

| Address | Calls | Purpose |
|---------|-------|---------|
| 0x21E7 | 171 | NAND primary function |
| 0x475F | 125 | NAND block operation |
| 0x22BC | 81 | NAND read/write |
| 0x223E | 49 | NAND status check |
| 0x47AE | 49 | NAND ECC handling |
| 0x2419 | 41 | NAND page operation |
| 0x47F7 | 36 | NAND block erase |
| 0x4888 | 35 | NAND mark bad block |

#### Strings

| Offset | String |
|--------|--------|
| 0x0138 | `Nand total capacity = 0x%08lX` |
| 0x0158 | `This is a 2K page flash` |
| 0x0173 | `This is a 512 page flash` |
| 0x0261 | `Nand capacity = 0x%08lX` |
| 0x027F | `NAND Driver critical error, Erase CIS or Code area` |
| 0x0607 | `[drvNAND_BUILDCIS] create new flash cis !` |
| 0x0652 | `Format CIS Failed!!` |
| 0x0667 | `[NAND_FS_FmtCardToFAT] flash formating ...` |
| 0x0694 | `Create MBR Fail !!` |
| 0x06A8 | `NAND_FS_FmtCardToFAT error 1` |

#### Key Functions (Inferred)

```c
// From string references
drvNAND_BUILDCIS()          // Create CIS (Card Information Structure)
drvNAND_GetFreeBlock()      // Get next free block
drvNAND_MarkFormatedBlock() // Mark block as formatted
NAND_FS_FmtCardToFAT()      // Format NAND as FAT filesystem
```

---

### USB/SCSI Driver (Block 06)

USB host controller and SCSI mass storage class driver.

| Property | Value |
|----------|-------|
| Source Block | block_06_0x90000-0xA0000.bin |
| RIU Banks | 0x22, 0x23 (USB), 0x1F (AEON) |
| AEON Accesses | 52 (highest of all blocks) |

#### Top Functions

| Address | Calls | Purpose |
|---------|-------|---------|
| 0x3B90 | 67 | USB transfer handler |
| 0x4722 | 61 | SCSI command dispatch |
| 0x2782 | 32 | USB endpoint handling |
| 0x6151 | 29 | USB bulk transfer |
| 0x79A3 | 28 | USB timeout handler |
| 0x2715 | 25 | USB status check |

#### Strings

| Offset | String |
|--------|--------|
| 0x00B0 | `not mass storage class!` |
| 0x00CB | `Mass storage device..` |
| 0x0135 | `error, timeout sec is zero` |
| 0x01ED | `Device type unsuport, it's not a scsi disk` |
| 0x023B | `SCSI CAPACITY : SCSI Device total block <0x%lx` |
| 0x026D | `SCSI CAPACITY : SCSI Product block size <0x%lx bytes>` |
| 0x02CC | `Scsi Device not ready (Lun=%bx).` |
| 0x02F0 | `Scsi inquiry failed (Lun=%bx).` |
| 0x0312 | `Read CAPACITY failed.` |
| 0x032B | `Scsi READ_10 command failed.` |
| 0x034B | `Scsi WRITE_10 command failed.` |

#### SCSI Commands Supported

- INQUIRY
- READ CAPACITY
- READ(10)
- WRITE(10)
- REQUEST SENSE (implied by error handling)

---

### SD/MMC/MS Driver (Block 07)

Multi-card reader driver supporting SD, MMC, CF, MS, and XD cards.

| Property | Value |
|----------|-------|
| Source Block | block_07_0xA0000-0xB0000.bin |
| RIU Banks | 0x14 (FCIE), 0x20 (GE - 314 accesses!) |
| Primary Role | Card detection, initialization, read/write |

#### Top Functions

| Address | Calls | Purpose |
|---------|-------|---------|
| 0xF470 | 115 | Card primary handler |
| 0x0720 | 103 | Card init sequence |
| 0x62F9 | 75 | Card read operation |
| 0xF46A | 54 | Card write operation |
| 0xF404 | 40 | Card status check |
| 0x074A | 38 | Card power control |
| 0x6CC7 | 34 | Card DMA transfer |
| 0x5774 | 31 | Card error handling |
| 0x8063 | 27 | MS card specific |

#### Strings

| Offset | String |
|--------|--------|
| 0x00AD | `ZSTG2 partial write FAIL` |
| 0x00C8 | `Program Fail` |
| 0x00E9 | `Wait SDMSXD CardReady fail` |
| 0x0106 | `Wait CF CardReady fail` |
| 0x011F | `read fail` |
| 0x0137 | `[NAND_Read_Error]gu8DeviceRWStatus:%bx` |
| 0x0195 | `USB write error retry %bx times!` |
| 0x01B7 | `write fail` |
| 0x01C3 | `Card write fail, quit` |
| 0x01E7 | `CF write fail, quit` |
| 0x0282 | `MS card initial OK` |
| 0x0297 | `MS card initial fail!!!` |
| 0x02C5 | `Error!!! Switch fail!` |
| 0x02DD | `Turn off power for T8-003 2-8-3` |

#### Card Types

- SD (Secure Digital)
- MMC (MultiMediaCard)
- CF (CompactFlash)
- MS (Memory Stick)
- XD (xD-Picture Card)

---

### FAT Filesystem Driver (Block 08)

FAT12/FAT16/FAT32 filesystem implementation.

| Property | Value |
|----------|-------|
| Source Block | block_08_0xB0000-0xC0000.bin |
| Supported | FAT12, FAT16, FAT32 |
| Key Function | 0x1193 (948 calls - memcpy) |

#### Top Functions

| Address | Calls | Purpose |
|---------|-------|---------|
| 0x1193 | 948 | lib_memcpy (FAT buffer ops) |
| 0x11C8 | 259 | FAT cluster operation |
| 0x11C9 | 250 | FAT chain traversal |
| 0x11FD | 217 | FAT entry read |
| 0x11E2 | 153 | FAT entry write |
| 0x1231 | 143 | Directory entry parse |
| 0x11E5 | 141 | Cluster allocation |
| 0x3112 | 111 | FAT32 specific |
| 0x124B | 82 | Directory search |
| 0x121A | 72 | File open |

#### Strings

| Offset | String |
|--------|--------|
| 0x00AD | `ZFat_PartitionTableRead fail!` |
| 0x00CD | `Fat_BootSectorRead fail!` |
| 0x00E8 | `Fat_FATStructureReadRoot fail!` |
| 0x0109 | `Fat_DirectoryEntryReadRoot fail!` |
| 0x013E | `FAT12, TotalFreeSpace:%ld Bytes` |
| 0x015F | `FAT16, TotalFreeSpace:%ld Bytes` |
| 0x0180 | `FAT32, TotalFreeSpace:%ld Bytes` |
| 0x01A3 | `Fat_DirectoryEntryGetFree return NULL` |
| 0x01E6 | `DirectoryOpen error 1` |
| 0x01FD | `DirectoryOpen error 2` |
| 0x0215 | `Read DIR fail` |
| 0x0233 | `[Fat_FileClose]` |
| 0x0244 | `[Fat_FileClose]No such file` |
| 0x0262 | `[Fat_FileClose]Fat_DirectoryRead fail` |
| 0x029B | `[Fat_FileWrite2] No Free Cluster` |

#### Key Functions (Inferred)

```c
// FAT layer
Fat_PartitionTableRead()
Fat_BootSectorRead()
Fat_FATStructureReadRoot()
Fat_DirectoryEntryReadRoot()
Fat_DirectoryEntryGetFree()
Fat_DirectoryRead()
Fat_FileClose()
Fat_FileWrite2()
```

---

### Storage Monitor (Block 16)

Hot-plug detection for removable storage cards.

| Property | Value |
|----------|-------|
| Source Block | block_16_0x130000-0x140000.bin |
| Purpose | Card insertion/removal detection |

#### Monitored Devices

Based on string references in block 15:

| Device | Detection Method |
|--------|-----------------|
| NAND | Always present |
| CF | GPIO/card detect pin |
| SD/MMC | FCIE card detect |
| XD | GPIO/card detect pin |
| MS | GPIO/card detect pin |
| USB | EHCI port status |

#### Related Strings (Block 15)

| Offset | String |
|--------|--------|
| 0x01B2 | `gu16StgFlag=%x---gu16FailStg=%x` |
| 0x03A3 | `[FM]%d no file in NAND` |
| 0x0438 | `[FileMark] Init Failed, not support` |
| 0x0479 | `[FM]%d Load DB from flash` |
| 0x049E | `[FM]%d Save DB to flash` |
| 0x05E7 | `SS(%d) storage change #2!!` |

---

### MIU Driver (Block 01)

Memory Interface Unit - DRAM controller and bus arbitration.

| Property | Value |
|----------|-------|
| Source Block | block_01_0x40000-0x50000.bin |
| RIU Bank | 0x12 (BDMA), 0x10 (CHIPTOP) |

#### Strings

| Offset | String |
|--------|--------|
| 0x0C93 | `MIU clock running in 120MHz by default...` |
| 0x0CBE | `Initialize memory...` |
| 0x0CE9 | `Memory initialization` |
| 0x0D0D | `failed !` |

#### Memory Configuration

- MIU Clock: 120 MHz default
- DRAM range: 0x000000 - 0x1FFFFF (typical 2MB)
- Access via BDMA or direct mapping

---

### OSDE Driver (Blocks 02, 14)

On-Screen Display Engine for UI rendering.

| Property | Value |
|----------|-------|
| Source Blocks | block_02, block_14 |
| RIU Banks | 0x2F, 0x30 (OSD) |

#### Strings

| Offset | Block | String |
|--------|-------|--------|
| 0x0BA6 | 02 | `[MDrv_OSDE_CreateFb] Cannot create buffer` |
| 0x0BD3 | 02 | `MApi_Osd_Create_GC pGC->u8FBID==0xff` |
| 0x0BFA | 02 | `MDrv_OSDE_CreateFb fails pGC->s16Width=%d` |
| 0x0C39 | 02 | `MDrv_OSDE_Fb_CompressMode fails!!` |
| 0x0C5D | 02 | `MDrv_OSDE_Fb_ColorKey fails!!` |
| 0x00CC | 14 | `OSDcp_LoadIcon2POOL()` |
| 0x0109 | 14 | `OSDcp_readbin_info_init()` |
| 0x03F3 | 14 | `InitGDI: create Main GC fail` |
| 0x0411 | 14 | `InitGDI: create Buff GC fail` |
| 0x042F | 14 | `InitGDI: create ThirdGC fail` |

#### Key Functions (Inferred)

```c
MDrv_OSDE_CreateFb()       // Create framebuffer
MDrv_OSDE_Fb_CompressMode() // Set compression
MDrv_OSDE_Fb_ColorKey()    // Set color key
MApi_Osd_Create_GC()       // Create graphics context
OSDcp_LoadIcon2POOL()      // Load icon to pool
InitGDI()                  // Initialize GDI system
```

---

### GE Driver (Block 07)

Graphics Engine for 2D acceleration (blitting, scaling, color conversion).

| Property | Value |
|----------|-------|
| Source Block | block_07_0xA0000-0xB0000.bin |
| RIU Bank | 0x20 (GE) |
| RIU Accesses | 314 (highest of any driver!) |

The 314 GE accesses in block 07 indicate heavy use of hardware-accelerated graphics operations for:
- Image scaling during decode
- Format conversion (YUV to RGB)
- Bitblit operations
- ROI (Region of Interest) cropping

---

### AEON Control Driver (Blocks 01, 06, 16)

Controls the AEON R2 coprocessor.

| Property | Value |
|----------|-------|
| Source Blocks | block_01 (primary), block_06, block_16 |
| RIU Bank | 0x1F (AEON) |
| XDATA | 0x0FE6 (control register) |

#### Key Functions

| Address | Block | Purpose |
|---------|-------|---------|
| 0x3D25 | 01 | AEON_Halt |
| 0x3CDF | 01 | AEON_Resume |
| 0xD970 | 16 | AEON_Enable |

#### Related Strings

| Offset | Block | String |
|--------|-------|--------|
| 0x07B7 | 14 | `[Note] switch UART to aeon` |
| 0x0F6F | all | `[MB_ISR] Warning : Aeon2MCU status register still not zero !` |
| 0x0FAD | all | `[MB_ISR] Warning : AEON to MCU force interrupt might not clear !` |

---

### Mailbox Driver (All Blocks)

Inter-processor communication between 8051 and AEON.

| Property | Value |
|----------|-------|
| Source | All overlay blocks (common code) |
| XDATA | 0x4401 (JPEG), 0x40BC (BMP/TIFF) |

#### Key Functions (Block 02)

| Address | Calls | Purpose |
|---------|-------|---------|
| 0x2830 | - | MB_SendCommand |
| 0x22F2 | - | MB_SelectJPEGCmd |
| 0x22F7 | - | MB_SelectTIFFCmd |
| 0x0F6F | - | MB_ISR (interrupt handler) |

#### Common Warning (All Blocks)

```
[MB_ISR] Warning : Aeon2MCU status register still not zero !
[MB_ISR] Warning : AEON to MCU force interrupt might not clear !
```

This appears at offset 0x0F6F in every block, indicating shared mailbox ISR code.

---

### Watchdog Driver (Blocks 15, 16)

System watchdog timer control.

| Property | Value |
|----------|-------|
| Source Blocks | block_15, block_16 |
| XDATA | 0x44CE, 0x44D3 |

#### Key Functions

| Address | Block | Purpose |
|---------|-------|---------|
| 0x1775 | 15/16 | WDT_Disable |
| 0x2450 | 15/16 | WDT_ReadState |

See [D72N_WATCHDOG_CONTROL.md](D72N_WATCHDOG_CONTROL.md) for SERDB-based disable sequence.

---

### JPD Driver (Block 17)

JPEG decode control on 8051 side.

| Property | Value |
|----------|-------|
| Source Block | block_17_0x140000-0x150000.bin |
| RIU Bank | 0x1E (JPD) |

#### Strings

| Offset | String |
|--------|--------|
| 0x116D | `[JPD]_bZeroimage;%bd` |
| 0x118B | `[MApp_JPEG_Begin] open file failed` |
| 0x11B0 | `[MApp_JPEG_ParseHeader] read data from flash error!!!` |
| 0x1267 | `SetRoiRect fail` |
| 0x12B2 | `jpeg before mirrorotate %bu` |
| 0x134B | `[JPD]before image width:%d,imagepitch:%d,imageheight:%d` |
| 0x1384 | `[JPD]unavailable scaling factor` |
| 0x13A6 | `[JPD]after image width:%d,imagepitch:%d,imageheight:%d` |
| 0x1417 | `[JPEG]boom and wont fire` |
| 0x14CD | `[JPD]scaledwidth %d imageheight %d scalefac` |
| 0x1510 | `[JPD] ImgWidth:%d ImgHeight:%d ImgPitch:%d ImgStartX:%d` |
| 0x1549 | `[JPD]ScaledWidth:%d ScaledHeight:%d` |

#### Key Functions (Inferred)

```c
MApp_JPEG_Begin()       // Start JPEG decode
MApp_JPEG_ParseHeader() // Parse JPEG header
SetRoiRect()            // Set region of interest
// Mirror/rotate operations
// Scaling operations
```

---

## AEON Drivers

### JPEG/GIF Decoder

Hardware-accelerated JPEG and GIF decoding.

| Property | Value |
|----------|-------|
| Source | AEON image 0x4CE66+ |
| Mailbox | 0x4CF27 (MB_JPD_CMD_MJPG_START_DEC) |

#### Key Functions

| Address | Function |
|---------|----------|
| 0x4CE66 | JPG_GIF_Decoder |
| 0x4CF27 | MB_JPD_CMD_MJPG_START_DEC |
| 0x4CEC5 | MB_JPD_CMD_IMAGE_DROP |
| 0x4D5D4 | GIF_EnterDecoder |
| 0x4D5EA | GIF_DecodeDone |

#### Strings

| Address | String |
|---------|--------|
| 0x4CE66 | `JPG/GIF Decoder` |
| 0x4CE76 | `* JPG/GIF Decoder id [%X]` |
| 0x4D5D4 | `[A_GIF]enter decoder` |
| 0x4D5EA | `[GIF]decode done.Data ends at 0x%x` |

---

### BMP Decoder

BMP format decoder with ROI and memory output support.

| Property | Value |
|----------|-------|
| Source | AEON image 0x4E538+ |
| Mailbox | 0x4CFFC (MB_BMP_CMD_DECODE_MEM_OUT) |
| Command | 0x10 |

#### Key Functions

| Address | Function |
|---------|----------|
| 0x4CFFC | MB_BMP_CMD_DECODE_MEM_OUT |
| 0x4E538 | BMP decoder main |
| 0x4E71D | BMP timing |
| 0x4E74B | BMP abort |
| 0x4E764 | BMP decode done |

#### Strings

| Address | String |
|---------|--------|
| 0x4CFDF | `BMP roi L %u T %u W %u H %u` |
| 0x4CFFC | `[MB_BMP_CMD_DECODE_MEM_OUT] addr %lx pitch %u down factor %u` |
| 0x4D03A | `[BMP] CHANGE_SCALEFACT scale fact %d` |
| 0x4E538 | `[BMP%dBitMode] ScaledPix %u LineSize %u` |
| 0x4E62F | `[BMP] scale Pix %d, width %d height %d` |
| 0x4E71D | `[BMP]start %d, end %d, time taken : %d ticks` |
| 0x4E74B | `[BMP] SEND ABORT DONE!!` |
| 0x4E764 | `[BMP]decode done.Data ends at 0x%x` |

---

### TIFF/LZW Decoder

Full libtiff library with multiple compression codec support.

| Property | Value |
|----------|-------|
| Source | AEON image 0x4D092+ |
| Size | ~85KB of TIFF code |
| Commands | 0x20, 0x21, 0x22 |

#### Key Functions

| Address | Function |
|---------|----------|
| 0x4D092 | MB_TIFF_CMD_GET_HEAD_INF |
| 0x4D0DB | MB_TIFF_CMD_START_DEC |
| 0x4D11E | MB_TIFF_CMD_DECODE_MEM_OUT |
| 0x5E3E2 | TIFFInitLZW |
| 0x5E44A | LZWPreDecode |
| 0x5E61D | LZWSetupDecode |
| 0x5E62D | NeXTDecode |
| 0x5E8F4 | PackBitsDecode |
| 0x5F14B | ThunderDecode |
| 0x51483 | TIFFReadDirectory |
| 0x5EE8C | TIFFReadEncodedStrip |
| 0x5EEAE | TIFFFillStrip |
| 0x5F2AA | TIFFOpen |
| 0x4EFF5 | TIFF_SendDone |

#### Compression Codecs

| Codec | Address | Status |
|-------|---------|--------|
| LZW | 0x5E3E2 | ✓ Traced |
| PackBits | 0x5E8F4 | ✓ Traced |
| NeXTDecode | 0x5E62D | ✓ Traced |
| ThunderDecode | 0x5F14B | ✓ Traced |
| Fax3 | 0x519BC-0x519F8 | ✓ Traced |

#### Strings

| Address | String |
|---------|--------|
| 0x4D092 | `[TIFF MAIL] MB_TIFF_CMD_GET_HEAD_INF` |
| 0x4D0B9 | `[TIFF] Stretch ROI %d %d %d %d` |
| 0x4D0DB | `[TIFF MAIL] MB_TIFF_CMD_START_DEC` |
| 0x4D11E | `[MB_TIFF_CMD_DECODE_MEM_OUT] addr %lx pitch %u` |
| 0x4D15A | `TIFF roi L %u T %u W %u H %u` |
| 0x4ED95 | `[TIFF]TIFF FORMAT OPEN Error` |
| 0x4EDBC | `[TIFF]Wait for Start Decode` |
| 0x4EE11 | `[TIFF] Start Decode TIFF` |
| 0x4EFDB | `[TIFF] SEND ABORT DONE!!` |
| 0x4EFF5 | `[TIFF] SEND DECODE DONE!!` |

---

## RIU Bank Summary

Summary of RIU bank usage across all drivers:

| Bank | Name | Primary Blocks | Accesses | Purpose |
|------|------|----------------|----------|---------|
| 0x10 | CHIPTOP | All | 1505 | System control |
| 0x12 | BDMA | 01, 05 | 269 | Block DMA |
| 0x14 | FCIE | 07, 12 | ~30 | SD/MMC interface |
| 0x18/0x19 | NAND | All | ~19/block | NAND flash |
| 0x1E | JPD | 01, 05, 06, 07 | ~20+ | JPEG decoder |
| 0x1F | AEON | 06, 01 | 52, 6 | AEON control |
| 0x20 | GE | 07 | 314 | Graphics engine |
| 0x22/0x23 | USB | 06 | ~5 | USB host |
| 0x2F/0x30 | OSDE | 02, 14, 15 | ~4/block | OSD engine |

---

## Block-to-Driver Mapping

Quick reference for which overlay block contains which driver:

| Block | Primary Driver | Secondary |
|-------|----------------|-----------|
| 01 | SPI Flash, MIU | AEON Control |
| 02 | OSDE, Mailbox | JPEG commands |
| 03 | File operations | Mailbox |
| 04 | Generic | Mailbox |
| 05 | NAND | JPD |
| 06 | USB/SCSI | AEON (52 refs) |
| 07 | SD/MMC/MS, GE (314) | Card I/O |
| 08 | FAT Filesystem | - |
| 09-11 | Application | Mailbox |
| 12 | Application | SD |
| 13 | Config Flash | Mailbox |
| 14 | OSDE, GDI | UART switch |
| 15 | File sort/mark | Watchdog |
| 16 | Storage monitor | AEON, Watchdog |
| 17 | JPD control | USB |
| 18 | File copy | Mailbox |

---

## Related Documentation

- [D72N_REGISTER_MAP.md](D72N_REGISTER_MAP.md) - RIU register details
- [D72N_FUNCTION_MAP.md](D72N_FUNCTION_MAP.md) - Combined function reference
- [D72N_MAILBOX_PROTOCOL.md](D72N_MAILBOX_PROTOCOL.md) - 8051↔AEON IPC
- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - Debug interface
- [D72N_INDEX.md](D72N_INDEX.md) - Documentation index
