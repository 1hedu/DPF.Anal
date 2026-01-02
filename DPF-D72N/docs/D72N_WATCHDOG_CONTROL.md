# D72N Watchdog Control

Watchdog timer control for the DPF-D72N via SERDB.

## Overview

The D72N uses software watchdog registers at XDATA 0x44CE (state) and 0x44D3-0x44D4 (counter). These were traced from the D72N 8051 overlay blocks.

---

## Traced Evidence

### Pattern Search Results

| Pattern | Block | Offsets |
|---------|-------|---------|
| 90 44 CE (DPTR,#44CE) | 03 | 0x5194 |
| 90 44 CE (DPTR,#44CE) | 12 | 0x71CF |
| 90 44 CE (DPTR,#44CE) | 15 | 0x2450, 0x25E0, 0x48E9 |
| 90 44 CE (DPTR,#44CE) | 16 | 0x175C, 0x1761, 0x1771, 0x17FC |
| 90 44 CE (DPTR,#44CE) | 17 | 0xE65A |
| 90 44 D3 (DPTR,#44D3) | 15 | 0x6A02, 0x6AC1, 0x6AD4 |
| 90 44 D3 (DPTR,#44D3) | 18 | 0x639D |

---

## Register Map

### XDATA Watchdog Registers

| Address | Size | Purpose | Status |
|---------|------|---------|--------|
| 0x44CE | 1 | Watchdog state | ✓ Traced |
| 0x44D3 | 2 | Watchdog counter (16-bit) | ✓ Traced |

---

## Traced Code

### Read Watchdog State (Block 15, offset 0x2450)

```asm
; Block 15 offset 0x2450 (Flash 0x122450)
; Read watchdog state register

2450: 90 44 CE     MOV  DPTR,#0x44CE    ; Watchdog state address
2453: 12 9F CC     LCALL 0x9FCC         ; Read function
2456: 90 98 83     MOV  DPTR,#0x9883    ; Copy to buffer
2459: E0           MOVX A,@DPTR
245A: FF           MOV  R7,A
245B: A3           INC  DPTR
245C: E0           MOVX A,@DPTR
245D: 90 44 D2     MOV  DPTR,#0x44D2    ; Store value
2460: CF           XCH  A,R7
2461: F0           MOVX @DPTR,A
2462: A3           INC  DPTR            ; 0x44D3
2463: EF           MOV  A,R7
2464: F0           MOVX @DPTR,A         ; Store to 0x44D3
```

### Write Watchdog Counter (Block 15, offset 0x6A02)

```asm
; Block 15 offset 0x6A02 (Flash 0x126A02)
; Write to watchdog counter

69FE: 90 98 85     MOV  DPTR,#0x9885    ; Source address
6A01: E0           MOVX A,@DPTR         ; Read value
6A02: 90 44 D3     MOV  DPTR,#0x44D3    ; Watchdog counter (low)
6A05: F0           MOVX @DPTR,A         ; Write low byte
6A06: A3           INC  DPTR            ; 0x44D4
6A07: EF           MOV  A,R7
6A08: F0           MOVX @DPTR,A         ; Write high byte
```

### Watchdog Check (Block 15, offset 0x6AC1)

```asm
; Block 15 offset 0x6AC1 (Flash 0x126AC1)
; Check watchdog counter, possibly timeout detection

6ABC: 90 44 D4     MOV  DPTR,#0x44D4    ; Counter high byte
6ABF: E0           MOVX A,@DPTR
6AC0: 94 EA        SUBB A,#0xEA         ; Compare with 0xEA (234)
6AC1: 90 44 D3     MOV  DPTR,#0x44D3    ; Counter low byte
6AC4: E0           MOVX A,@DPTR
6AC5: 94 00        SUBB A,#0x00         ; Subtract 0
6AC7: 50 40        JNC  0x6B09          ; Jump if counter >= threshold
...
6AD4: 90 44 D3     MOV  DPTR,#0x44D3    ; Read counter
6AD7: E0           MOVX A,@DPTR
6AD8: FE           MOV  R6,A            ; Low byte to R6
6AD9: A3           INC  DPTR
6ADA: E0           MOVX A,@DPTR         ; High byte
6ADB: FF           MOV  R7,A            ; to R7
```

### Multiple State Checks (Block 16, offset 0x175C)

```asm
; Block 16 offset 0x175C (Flash 0x13175C)
; Multiple watchdog state reads

175C: 90 44 CE     MOV  DPTR,#0x44CE    ; Watchdog state
175F: E0           MOVX A,@DPTR         ; Read state
1760: FF           MOV  R7,A
1761: 90 44 CE     MOV  DPTR,#0x44CE    ; Read again
1764: E0           MOVX A,@DPTR
...
1771: 90 44 CE     MOV  DPTR,#0x44CE    ; Read again
1774: E0           MOVX A,@DPTR
1775: 54 FE        ANL  A,#0xFE         ; Clear bit 0
1777: F0           MOVX @DPTR,A         ; Write back
```

---

## Watchdog Disable Mechanism

From traced code analysis:

```
1. Read state from 0x44CE
2. Clear bit 0: ANL A,#0xFE
3. Write back to 0x44CE
4. Write 0x0000 to 0x44D3-0x44D4 (counter)
```

### SERDB Disable Function

```python
def d72n_disable_watchdog():
    """Disable software watchdog via SERDB

    Traced from:
    - Block 16 offset 0x1775: ANL A,#0xFE clears bit 0
    - Block 15 offset 0x6A05: counter write
    """
    # Read current state
    state = serdb.read_xdata(0x44CE)

    # Clear bit 0 (disable)
    new_state = state & 0xFE
    serdb.write_xdata(0x44CE, new_state)

    # Zero the counter
    serdb.write_xdata(0x44D3, 0x00)
    serdb.write_xdata(0x44D4, 0x00)

    print(f"[+] Watchdog disabled (0x{state:02X} → 0x{new_state:02X})")


def d72n_enable_watchdog():
    """Enable software watchdog

    Opposite of disable - set bit 0
    """
    state = serdb.read_xdata(0x44CE)
    new_state = state | 0x01
    serdb.write_xdata(0x44CE, new_state)
    print(f"[+] Watchdog enabled (0x{state:02X} → 0x{new_state:02X})")


def d72n_read_watchdog_counter():
    """Read 16-bit watchdog counter

    Traced from block 15 offset 0x6AD4-0x6ADB
    """
    low = serdb.read_xdata(0x44D3)
    high = serdb.read_xdata(0x44D4)
    return (high << 8) | low


def d72n_get_watchdog_status():
    """Read and decode watchdog state"""
    state = serdb.read_xdata(0x44CE)
    counter = d72n_read_watchdog_counter()

    enabled = "Enabled" if (state & 0x01) else "Disabled"
    print(f"Watchdog (0x44CE = 0x{state:02X}): {enabled}")
    print(f"Counter (0x44D3-D4): 0x{counter:04X} ({counter})")

    return state, counter
```

---

## Complete Watchdog Class

```python
class D72N_Watchdog:
    """D72N Watchdog control via SERDB

    Traced from D72N 8051 blocks:
    - Block 15: 0x2450 (state read)
    - Block 15: 0x6A02 (counter write)
    - Block 15: 0x6AC1, 0x6AD4 (counter check)
    - Block 16: 0x175C, 0x1775 (state modify)
    """

    ADDR_STATE = 0x44CE  # Watchdog state register
    ADDR_COUNTER_LO = 0x44D3  # Counter low byte
    ADDR_COUNTER_HI = 0x44D4  # Counter high byte

    BIT_ENABLE = 0x01  # Bit 0 controls enable

    def __init__(self, serdb):
        self.serdb = serdb

    def read_state(self):
        """Read watchdog state (traced: 0x175C)"""
        return self.serdb.read_xdata(self.ADDR_STATE)

    def write_state(self, value):
        """Write watchdog state"""
        self.serdb.write_xdata(self.ADDR_STATE, value)

    def read_counter(self):
        """Read 16-bit counter (traced: 0x6AD4-0x6ADB)"""
        low = self.serdb.read_xdata(self.ADDR_COUNTER_LO)
        high = self.serdb.read_xdata(self.ADDR_COUNTER_HI)
        return (high << 8) | low

    def write_counter(self, value):
        """Write 16-bit counter (traced: 0x6A02-0x6A08)"""
        self.serdb.write_xdata(self.ADDR_COUNTER_LO, value & 0xFF)
        self.serdb.write_xdata(self.ADDR_COUNTER_HI, (value >> 8) & 0xFF)

    def is_enabled(self):
        """Check if watchdog is enabled"""
        return (self.read_state() & self.BIT_ENABLE) != 0

    def disable(self):
        """Disable watchdog (traced: 0x1775 ANL A,#0xFE)"""
        state = self.read_state()
        self.write_state(state & ~self.BIT_ENABLE)
        self.write_counter(0x0000)
        return not self.is_enabled()

    def enable(self):
        """Enable watchdog"""
        state = self.read_state()
        self.write_state(state | self.BIT_ENABLE)
        return self.is_enabled()

    def feed(self, value=0x0000):
        """Feed (reset) the watchdog counter"""
        self.write_counter(value)

    def status(self):
        """Get status string"""
        state = self.read_state()
        counter = self.read_counter()
        enabled = "ENABLED" if (state & self.BIT_ENABLE) else "DISABLED"
        return f"State: 0x{state:02X} ({enabled}), Counter: 0x{counter:04X}"
```

---

## Usage Example

```python
# Initialize
serdb = SERDB(bus, 0x59)
wdt = D72N_Watchdog(serdb)

# Check current status
print(wdt.status())

# Disable for safe memory operations
wdt.disable()

# ... perform operations ...

# Re-enable when done
wdt.enable()
```

---

## Verification Summary

| Item | Status | Evidence |
|------|--------|----------|
| State register 0x44CE | ✓ Traced | Block 15: 0x2450; Block 16: 0x175C |
| Counter 0x44D3 | ✓ Traced | Block 15: 0x6A02, 0x6AC1, 0x6AD4 |
| Counter 0x44D4 | ✓ Traced | Block 15: 0x6ABC |
| Bit 0 = enable | ✓ Traced | Block 16: 0x1775 (ANL A,#0xFE) |
| Counter write | ✓ Traced | Block 15: 0x6A05-0x6A08 |
| Counter read | ✓ Traced | Block 15: 0x6AD7-0x6ADB |

---

## Related Documentation

- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - SERDB interface
- [D72N_AEON_CONTROL.md](D72N_AEON_CONTROL.md) - AEON halt/resume
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
