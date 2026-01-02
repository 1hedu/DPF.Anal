# D72N Peripheral Map

Complete peripheral and hardware interface reference for the DPF-D72N, traced from 8051 overlay blocks.

## System Overview

```
DPF-D72N SoC (MSPD21D assumed)
├── 8051 MCU (PM51)
│   ├── GPIO Ports (P0, P1, P3)
│   ├── SFR Timers
│   └── I2C Master
├── AEON R2 (32-bit RISC)
│   └── Display/Decode processors
├── RIU Peripherals (0x10xx-0x32xx)
│   ├── System/Clocks (0x10, 0x11)
│   ├── BDMA (0x12)
│   ├── Audio (0x15)
│   ├── Display (0x1E, 0x1F, 0x20, 0x2F, 0x30)
│   ├── USB (0x22, 0x23, 0x24, 0x25, 0x26)
│   └── Misc (0x27, 0x28, 0x2B, 0x31)
└── External I2C Devices
    ├── ISP (0x49)
    ├── SERDB (0x59)
    └── Other (EEPROM, RTC, etc.)
```

---

## RIU Peripheral Banks

### System Control Banks

| Bank | Refs | Primary Block | Purpose |
|------|------|---------------|---------|
| 0x10 | 1505 | 01 (110 refs) | CHIPTOP - System control |
| 0x11 | 149 | 15 (10 refs) | System misc |
| 0x12 | 269 | 01 (135 refs) | BDMA - Block DMA |
| 0x2B | 912 | 01 (71 refs) | System extended |
| 0x31 | 90 | All blocks | System config |

#### Bank 0x10 (CHIPTOP) - 1505 refs

| Offset | Purpose |
|--------|---------|
| 0x08-0x0F | Clock control |
| 0x19 | Bank select (237 refs) |
| 0x1A-0x1F | System config |

#### Bank 0x12 (BDMA) - 269 refs

| Offset | Purpose |
|--------|---------|
| 0x00-0x02 | Source address |
| 0x06-0x07 | Destination address |
| 0x09-0x0B | Transfer control |

### Storage Banks

| Bank | Refs | Primary Block | Purpose |
|------|------|---------------|---------|
| 0x13 | 9 | 01 (3 refs) | Storage misc |
| 0x14 | 1 | 12 | FCIE - Card interface |
| 0x15 | 179 | 05 (116 refs) | Audio/Storage DMA |
| 0x18 | 1 | 16 | NAND control |
| 0x19 | 1 | 12 | SPI control |

#### Bank 0x15 - 179 refs

| Offset | Purpose |
|--------|---------|
| 0x00-0x04 | DMA control |
| 0x06-0x08 | Buffer addresses |

### Display Banks

| Bank | Refs | Primary Block | Purpose |
|------|------|---------------|---------|
| 0x1E | 121 | 07 (29 refs) | JPD - JPEG decoder |
| 0x1F | 78 | 06 (52 refs) | AEON control |
| 0x20 | 336 | 07 (314 refs) | GE - Graphics Engine |
| 0x2F | 39 | Multi | OSDE - OSD Engine |
| 0x30 | 19 | 16 (2 refs) | GOP - Graphics Output |

#### Bank 0x1E (JPD) - 121 refs

| Offset | Purpose |
|--------|---------|
| 0x00 | JPD control |
| 0x10-0x14 | Bitstream control |
| 0x22, 0x45 | Decode config |
| 0x6C, 0xC1 | Status (common) |
| 0x78-0x83 | Frame buffer control |
| 0xCE, 0xCF | Decode complete |

#### Bank 0x1F (AEON) - 78 refs

| Offset | Purpose |
|--------|---------|
| 0x00-0x03 | Status/Control/Reset |
| 0x06-0x07 | Clock/Memory |
| 0x09-0x0A | Interrupt |
| 0x17 | Common control (all blocks) |
| 0x27-0x2C | Debug/Mailbox |

#### Bank 0x20 (GE) - 336 refs

**Block 07 has 314 refs** - Primary GE driver

| Offset | Purpose |
|--------|---------|
| 0x00-0x02 | GE control/config |
| 0x04-0x06 | Source X/Y |
| 0x08-0x0A | Dest X/Y, Width |
| 0x0C-0x10 | Height, Color |
| 0x1F | Status (all blocks) |

### USB Banks

| Bank | Refs | Primary Block | Purpose |
|------|------|---------------|---------|
| 0x22 | 3 | 01, 07, 11 | EHCI status |
| 0x23 | 3 | 17, 15 | EHCI control |
| 0x24 | 94 | 06 (76 refs) | USB extended |
| 0x25 | 29 | 06 (11 refs) | USB config |
| 0x26 | 112 | 06 (111 refs) | USB transfer |

#### Bank 0x26 (USB Transfer) - 112 refs

| Offset | Purpose |
|--------|---------|
| 0x00-0x02 | Endpoint control |
| 0x04, 0x06 | Buffer addresses |
| 0x0A-0x0E | Transfer config |

### Misc Banks

| Bank | Refs | Primary Block | Purpose |
|------|------|---------------|---------|
| 0x16 | 3 | 01, 14 | Timer/misc |
| 0x17 | 17 | 15 (14 refs) | Extended timer |
| 0x1A | 18 | All blocks | System misc |
| 0x1B | 21 | 01 (3 refs) | Power control |
| 0x1C | 2 | 02, 12 | Config |
| 0x1D | 38 | 02, 15 | Extended config |
| 0x27 | 37 | 14 (3 refs) | Audio/misc |
| 0x28 | 37 | 06 (3 refs) | Extended I/O |
| 0x2C | 20 | 16 (3 refs) | GPIO control |
| 0x2D | 36 | All blocks | System flags |
| 0x2E | 2 | 12, 16 | Extended |
| 0x32 | 25 | 16 (6 refs) | Power management |

---

## I2C Devices

### Debug Interfaces

| Address | Device | Primary Blocks | Purpose |
|---------|--------|----------------|---------|
| 0x49 | ISP | 11 (6), 15 (10), 14 (6) | Flash programming |
| 0x59 | SERDB | 11 (12), 12 (13), 17 (6) | Debug/memory access |

### Storage/Peripherals

| Address | Device | Primary Blocks | Purpose |
|---------|--------|----------------|---------|
| 0x50 | EEPROM | 12 (8), 15 (4) | Configuration storage |
| 0x68 | RTC | 17 (28), 02 (14), 15 (11) | Real-time clock |

### Possible Addresses

| Address | Device | Refs | Notes |
|---------|--------|------|-------|
| 0x20 | I/O Expander | 491 total | May be GPIO address |
| 0x38 | Touch/I2C | 25 total | Possible touch interface |
| 0x3C | Display | 77 total | Possible panel I2C |
| 0x76 | Sensor | 14 total | Possible light sensor |

---

## GPIO Ports (SFR)

### Port Access Summary

| Port | SFR | Total Refs | Heavy Users |
|------|-----|------------|-------------|
| P0 | 0x80 | ~120 | Blk 01 (10), Blk 15 (9) |
| P1 | 0x90 | ~1400 | Blk 08 (228), Blk 03 (86), Blk 17 (86) |
| P2 | 0xA0 | 0 | Not used |
| P3 | 0xB0 | ~20 | Blk 18 (5) |

### P1 Heavy Usage (Block 08)

Block 08 (FAT filesystem) has 228 P1 references:
- Likely card detect / write protect pins
- Storage status indicators

### P0 Usage

10 refs in block 01 (initialization):
- System control pins
- LED/status indicators

---

## Watchdog Timer

### XDATA Registers

| Address | Refs | Blocks | Purpose |
|---------|------|--------|---------|
| 0x44CE | 14 | 15 (6), 16 (4) | WDT control |
| 0x44D3 | - | 15, 16 | WDT status |

### Watchdog Control Blocks

| Block | WDT Refs | Purpose |
|-------|----------|---------|
| 15 | 6 | Primary watchdog control |
| 16 | 4 | Storage monitor watchdog |
| 03, 12, 17, 18 | 1 each | Common access |

---

## Timers and Clocks

### MIU Clock (Block 01)

```
String: "MIU clock running in 120MHz by default..."
```
- Memory Interface Unit clock: 120 MHz

### SPI Clock (Block 01)

```
String: "* SPI flash clock 40 MHz"
```
- SPI flash interface: 40 MHz

### PWM (Block 02)

```
Strings:
"PWM 2 = %d"
"[DPWM] Retry Success"
"[DPWM] Retry Fail, Check hardware"
```
- PWM output for backlight/audio

### OP2 Clock (Block 02)

```
String: "error OP2 clock modify: M setting error!!"
```
- Secondary oscillator/PLL error

---

## UART

### UART Switch (Block 14)

```
Strings:
"[Note] switch UART to aeon"
"[Note] switch UART to 51"
```

Control via RIU 0x0F55 (see D72N_UART_SWITCH.md)

---

## Storage Interfaces

### NAND (Block 05)

```
Strings:
"This is a 2K page flash"
"This is a 512 page flash"
"_fsinfo.u8SecNumofBlk = %d"
```

### SPI Flash (Block 01)

```
Source file: ..\..\Customer\Driver\drvspi.c
Strings:
"drvspi: Invalid address"
"drvspi: Range exceed flash size"
"drvspi: block size must be power of two"
```

### Storage Monitor (Block 16)

```
Strings:
"[Stg_Monitor]Send KEY_BADCARD_REMOVED Event #1=%x"
"[Stg_Monitor]Send KEY_BADCARD_REMOVED Event #2=%x"
```

---

## Peripheral Block Ownership

### Block 01 (Initialization)

| Peripheral | Refs | Purpose |
|------------|------|---------|
| Bank 0x10 (CHIPTOP) | 110 | System init |
| Bank 0x12 (BDMA) | 135 | DMA init |
| Bank 0x2B | 71 | Extended init |

### Block 05 (NAND Driver)

| Peripheral | Refs | Purpose |
|------------|------|---------|
| Bank 0x15 | 116 | NAND DMA |
| GWin 0x6653 | 31 | Display config |

### Block 06 (USB/AEON)

| Peripheral | Refs | Purpose |
|------------|------|---------|
| Bank 0x1F (AEON) | 52 | AEON control |
| Bank 0x24 | 76 | USB extended |
| Bank 0x26 | 111 | USB transfer |

### Block 07 (GE/Cards)

| Peripheral | Refs | Purpose |
|------------|------|---------|
| Bank 0x20 (GE) | 314 | Graphics engine |
| Bank 0x15 | 60 | Card DMA |
| Bank 0x1E (JPD) | 29 | JPEG decode |

---

## Interrupt Sources

### Mailbox Interrupt (All Blocks)

```
String: "[MB_ISR] Warning : AEON to MCU force interrupt might not clear !"
Location: 0x0FAD in every block
```

Common ISR handling code.

### Storage Events (Block 16)

```
Strings:
"KEY_BADCARD_REMOVED Event #1"
"KEY_BADCARD_REMOVED Event #2"
```

Card insertion/removal interrupts.

---

## Memory-Mapped I/O Summary

### XDATA Ranges

| Range | Purpose | Key Addresses |
|-------|---------|---------------|
| 0x1000-0x1FFF | RIU access | Bank select at 0x1019 |
| 0x4000-0x4FFF | Mailbox/State | 0x4401, 0x40EA, 0x4720 |
| 0x6000-0x6FFF | GWin control | 0x6653, 0x69BE, 0x6D2C |

### RIU Bank Formula

```
XDATA address = 0x1000 + (bank_offset & 0xFF)
Where bank is set via 0x1019
```

---

## Related Documentation

- [D72N_REGISTER_MAP.md](D72N_REGISTER_MAP.md) - RIU register details
- [D72N_DRIVERS.md](D72N_DRIVERS.md) - Driver implementation
- [D72N_DISPLAY_PIPELINE.md](D72N_DISPLAY_PIPELINE.md) - Display subsystem
- [D72N_WATCHDOG_CONTROL.md](D72N_WATCHDOG_CONTROL.md) - Watchdog control
- [D72N_UART_SWITCH.md](D72N_UART_SWITCH.md) - UART configuration
- [D72N_INDEX.md](D72N_INDEX.md) - Documentation index
