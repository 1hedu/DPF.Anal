# D72N AEON Processor Control

AEON R2 processor control, reset, and enable mechanisms for the DPF-D72N.

## Overview

The D72N uses XDATA register 0x0FE6 to control the AEON R2 processor. The 8051 MCU can halt, resume, and reset AEON via this register.

---

## Traced Evidence

### String Locations (Block 1: 0x40000-0x50000)

| Block Offset | Flash Offset | String |
|--------------|--------------|--------|
| 0x1203 | 0x41203 | `# AEON reset & enable ...` |
| 0x1220 | 0x41220 | `..Set SPI base to 0xf0000000` |
| 0x1240 | 0x41240 | `..Set QMEM base to 0xC0000000` |
| 0x1336 | 0x41336 | `%s Aeon not running [%d]` |
| 0x1350 | 0x41350 | `[Aeon Soft Watchdog]` |
| 0x1365 | 0x41365 | `%s restart Aeon...` |
| 0x1379 | 0x41379 | `Loading Aeon image...` |
| 0x139b | 0x4139b | `Resetting Aeon ...` |
| 0x13b6 | 0x413b6 | `Aeon reset failed, try again ...` |
| 0x13d8 | 0x413d8 | `Aeon back...` |
| 0x16da | 0x416da | `%s mapping Xdata into Aeon memory space [0x%lX]` |
| 0x180d | 0x4180d | `Aeon image offset = 0x%lx, size=0x%lx` |

### AEON Control Register Access (Block 1)

| Block Offset | Flash Offset | Operation |
|--------------|--------------|-----------|
| 0x3CDF | 0x43CDF | Read 0x0FE6, ORL #0x01 (set RUN) |
| 0x3D25 | 0x43D25 | Read 0x0FE6, ANL #0xFE (clear RUN) |
| 0xD96C | 0x4D96C | Read 0x0FE6, ORL #0x02 (set ENABLE) |

### AEON Control Register Access (Block 16: 0x130000-0x140000)

| Block Offset | Flash Offset | Operation |
|--------------|--------------|-----------|
| 0x66D7 | 0x1366D7 | Read 0x0FE6 |
| 0x66DF | 0x1366DF | ORL #0x01 (set RUN) |
| 0x671E | 0x13671E | Read 0x0FE6 |

---

## Disassembly

### Resume AEON (Block 1, offset 0x3CDF)

```asm
; Block 1 offset 0x3CDF (Flash 0x43CDF)
; Resume AEON - set RUN bit

3CDF: 90 0F E6        MOV  DPTR,#0x0FE6     ; AEON control register
3CE2: E0              MOVX A,@DPTR          ; Read current value
3CE3: 44 01           ORL  A,#0x01          ; Set bit 0 (RUN)
3CE5: F0              MOVX @DPTR,A          ; Write back
```

### Halt AEON (Block 1, offset 0x3D25)

```asm
; Block 1 offset 0x3D25 (Flash 0x43D25)
; Halt AEON - clear RUN bit

3D25: 90 0F E6        MOV  DPTR,#0x0FE6     ; AEON control register
3D28: E0              MOVX A,@DPTR          ; Read current value
3D29: 54 FE           ANL  A,#0xFE          ; Clear bit 0 (HALT)
3D2B: F0              MOVX @DPTR,A          ; Write back
```

### Enable AEON (Block 1, offset 0xD96C)

```asm
; Block 1 offset 0xD96C (Flash 0x4D96C)
; Enable AEON - set ENABLE bit

D96C: 90 0F E6        MOV  DPTR,#0x0FE6     ; AEON control register
D96F: E0              MOVX A,@DPTR          ; Read current value
D970: 44 02           ORL  A,#0x02          ; Set bit 1 (ENABLE)
D972: F0              MOVX @DPTR,A          ; Write back
```

### Resume AEON (Block 16, offset 0x66DF)

```asm
; Block 16 offset 0x66DF (Flash 0x1366DF)
; Resume AEON in watchdog recovery

66D7: 90 0F E6        MOV  DPTR,#0x0FE6     ; AEON control register
66DA: E0              MOVX A,@DPTR
66DB: 90 45 E1        MOV  DPTR,#0x45E1     ; State storage
66DE: F0              MOVX @DPTR,A
66DF: 90 0F E6        MOV  DPTR,#0x0FE6
66E2: E0              MOVX A,@DPTR
66E3: 44 01           ORL  A,#0x01          ; Set bit 0 (RUN)
66E5: F0              MOVX @DPTR,A
```

---

## Control Register

### XDATA 0x0FE6 - AEON Run Control

**Address:** XDATA 0x0FE6 (accessible via SERDB at I2C 0x59)

| Bit | Name | Function | Traced Evidence |
|-----|------|----------|-----------------|
| 0 | RUN | 1=running, 0=halted | ORL #0x01, ANL #0xFE |
| 1 | ENABLE | Enable processor | ORL #0x02 |
| 2 | RESET_N | Release reset | (combined with ENABLE) |
| 7:3 | Reserved | Unknown | - |

**Bit Operations (from traced code):**
```
Halt:   ANL A,#0xFE  ; Clear bit 0 (traced at 0x3D29)
Resume: ORL A,#0x01  ; Set bit 0 (traced at 0x3CE3, 0x66E3)
Enable: ORL A,#0x02  ; Set bit 1 (traced at 0xD970)
```

**Control Values:**
```
0x00 = AEON fully disabled (reset held)
0x02 = AEON enabled but halted (bit 1 set)
0x06 = AEON enabled, reset released (bits 1,2 set)
0x07 = AEON running (bits 0,1,2 set)
```

---

## SERDB Control

### Halt AEON

```python
def d72n_halt_aeon():
    """Halt AEON processor

    Traced from block 1 offset 0x3D25-0x3D2B
    ANL A,#0xFE clears bit 0
    """
    current = serdb.read_xdata(0x0FE6)
    new_value = current & 0xFE  # Clear bit 0
    serdb.write_xdata(0x0FE6, new_value)
    print(f"[+] AEON halted (0x{current:02X} → 0x{new_value:02X})")
```

### Resume AEON

```python
def d72n_resume_aeon():
    """Resume AEON processor

    Traced from block 1 offset 0x3CDF-0x3CE5
    ORL A,#0x01 sets bit 0
    """
    current = serdb.read_xdata(0x0FE6)
    new_value = current | 0x01  # Set bit 0
    serdb.write_xdata(0x0FE6, new_value)
    print(f"[+] AEON resumed (0x{current:02X} → 0x{new_value:02X})")
```

### Full Reset AEON

```python
def d72n_reset_aeon():
    """Full reset and restart AEON processor

    Traced from block 1 offset 0xD96C (enable sequence)
    Combined with halt/resume patterns
    """
    import time

    # 1. Halt AEON (ANL #0xFE from 0x3D29)
    current = serdb.read_xdata(0x0FE6)
    serdb.write_xdata(0x0FE6, current & 0xFE)
    print("[*] AEON halted")
    time.sleep(0.1)

    # 2. Disable completely (hold in reset)
    serdb.write_xdata(0x0FE6, 0x00)
    print("[*] AEON disabled")
    time.sleep(0.1)

    # 3. Enable (ORL #0x02 from 0xD970, plus reset release)
    serdb.write_xdata(0x0FE6, 0x06)
    print("[*] AEON enabled")
    time.sleep(0.1)

    # 4. Start running (ORL #0x01 from 0x3CE3)
    current = serdb.read_xdata(0x0FE6)
    serdb.write_xdata(0x0FE6, current | 0x01)
    print("[+] AEON running")
```

### Get AEON Status

```python
def d72n_get_aeon_status():
    """Read and decode AEON control register"""
    val = serdb.read_xdata(0x0FE6)

    running = "Running" if (val & 0x01) else "Halted"
    enabled = "Enabled" if (val & 0x02) else "Disabled"
    reset_n = "Released" if (val & 0x04) else "In Reset"

    print(f"AEON Status (0x0FE6 = 0x{val:02X}):")
    print(f"  Bit 0 (RUN):     {running}")
    print(f"  Bit 1 (ENABLE):  {enabled}")
    print(f"  Bit 2 (RESET_N): {reset_n}")

    return val
```

---

## Complete AEON Controller Class

```python
class D72N_AEON_Control:
    """D72N AEON processor control via SERDB

    Based on traced code from block 1:
    - Resume: offset 0x3CDF (ORL #0x01)
    - Halt: offset 0x3D25 (ANL #0xFE)
    - Enable: offset 0xD96C (ORL #0x02)
    """

    AEON_CTRL = 0x0FE6

    # Control bits (traced from ORL/ANL operations)
    BIT_RUN     = 0x01  # ORL A,#0x01 / ANL A,#0xFE
    BIT_ENABLE  = 0x02  # ORL A,#0x02
    BIT_RESET_N = 0x04  # Combined with ENABLE

    def __init__(self, serdb):
        self.serdb = serdb

    def read_ctrl(self):
        """Read AEON control register"""
        return self.serdb.read_xdata(self.AEON_CTRL)

    def write_ctrl(self, value):
        """Write AEON control register"""
        self.serdb.write_xdata(self.AEON_CTRL, value)

    def is_running(self):
        """Check if AEON is running (bit 0)"""
        return (self.read_ctrl() & self.BIT_RUN) != 0

    def halt(self):
        """Halt AEON - ANL A,#0xFE (traced at 0x3D29)"""
        current = self.read_ctrl()
        self.write_ctrl(current & ~self.BIT_RUN)
        return not self.is_running()

    def resume(self):
        """Resume AEON - ORL A,#0x01 (traced at 0x3CE3)"""
        current = self.read_ctrl()
        self.write_ctrl(current | self.BIT_RUN)
        return self.is_running()

    def disable(self):
        """Fully disable AEON (hold in reset)"""
        self.write_ctrl(0x00)

    def enable(self):
        """Enable AEON without running - ORL A,#0x02 (traced at 0xD970)"""
        self.write_ctrl(self.BIT_ENABLE | self.BIT_RESET_N)

    def reset(self):
        """Full reset cycle"""
        import time
        self.halt()
        time.sleep(0.05)
        self.disable()
        time.sleep(0.05)
        self.enable()
        time.sleep(0.05)
        self.resume()
        return self.is_running()

    def status(self):
        """Get status string"""
        val = self.read_ctrl()
        bits = []
        if val & self.BIT_RUN:
            bits.append("RUN")
        if val & self.BIT_ENABLE:
            bits.append("ENABLE")
        if val & self.BIT_RESET_N:
            bits.append("RESET_N")
        return f"0x{val:02X} ({' | '.join(bits) if bits else 'DISABLED'})"
```

---

## AEON Watchdog

### Soft Watchdog Handler (from strings)

The 8051 monitors AEON responsiveness via mailbox:

```
1. Poll mailbox status (0x4045)
2. If timeout:
   a. "[Aeon Soft Watchdog]" (0x1350)
   b. "%s Aeon not running [%d]" (0x1336)
   c. "%s restart Aeon..." (0x1365)
3. ORL A,#0x01 (set RUN bit)
4. "Loading Aeon image..." (0x1379)
5. If still no response:
   a. "Resetting Aeon ..." (0x139b)
   b. ANL A,#0xFE (halt)
   c. ORL A,#0x01 (resume)
   d. Retry
6. If failed:
   a. "Aeon reset failed, try again ..." (0x13b6)
7. If success:
   a. "Aeon back..." (0x13d8)
```

---

## Exploitation Uses

### 1. Freeze Display

Halt AEON to freeze the current display frame:
```python
aeon.halt()
# Display frozen - useful for screenshots
```

### 2. Stop UART Output

All printf goes through AEON, so halting stops debug output:
```python
aeon.halt()
# UART silent - useful when debugging 8051 directly
```

### 3. Safe Memory Inspection

With AEON halted, DRAM buffers are stable:
```python
aeon.halt()
framebuffer = serdb.read_dram_range(0x180000, 0x40000)
aeon.resume()
```

### 4. Code Injection

Modify AEON code while halted:
```python
aeon.halt()
serdb.write_dram(0x14C340, shellcode)
aeon.resume()
```

### 5. Mailbox Manipulation

Safely modify mailbox buffers:
```python
aeon.halt()
serdb.write_xdata(0x4401, 0x02)  # Inject command
serdb.write_xdata(0x40FB, 0xFE)  # Set ready
aeon.resume()
```

---

## Verification Summary

| Item | Status | Evidence |
|------|--------|----------|
| Control register 0x0FE6 | ✓ Traced | Block 1: 0x3CDF, 0x3D25, 0xD96C |
| Bit 0 (RUN) | ✓ Traced | ORL #0x01 at 0x3CE3, ANL #0xFE at 0x3D29 |
| Bit 1 (ENABLE) | ✓ Traced | ORL #0x02 at 0xD970 |
| Boot strings | ✓ Confirmed | Block 1 at 0x1203+ |
| Watchdog strings | ✓ Confirmed | Block 1 at 0x1336+ |
| Block 16 references | ✓ Traced | 0x66D7, 0x66DF, 0x671E |

---

## Related Documentation

- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - SERDB interface
- [D72N_UART_SWITCH.md](D72N_UART_SWITCH.md) - UART mux control
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
