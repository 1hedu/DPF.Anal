# D72N UART Switch Mechanism

UART multiplexer control for the DPF-D72N digital picture frame.

## Overview

The D72N uses a UART multiplexer controlled by RIU register 0x0F55 to switch UART output between the 8051 MCU and AEON R2 processor.

---

## Traced Evidence

### String Locations (Block 14: 0x110000-0x120000)

| Block Offset | Flash Offset | String |
|--------------|--------------|--------|
| 0x7B7 | 0x1107B7 | `[Note] switch UART to aeon` |
| 0x7D3 | 0x1107D3 | `[Note] switch UART to 51` |

### UART Switch Code (Block 1: 0x40000-0x50000)

The UART mux control code is located in block 1 with RIU 0x0F55 access at multiple offsets:

| Block Offset | Flash Offset | Operation |
|--------------|--------------|-----------|
| 0xE4D4 | 0x4E4D4 | RIU read 0x0F55 |
| 0xE513 | 0x4E513 | RIU write 0x0F55 |
| 0xE520 | 0x4E520 | RIU read 0x0F55 |
| 0xE55F | 0x4E55F | RIU write 0x0F55 |

### Disassembly of UART Switch (Block 1, offset 0xE4D0)

```asm
; Block 1 offset 0xE4D0 (Flash 0x4E4D0)
; UART mux state machine

E4D0: 90 45 83        MOV  DPTR,#0x4583     ; State storage
E4D3: EF              MOV  A,R7
E4D4: F0              MOVX @DPTR,A
E4D5: 7F 55           MOV  R7,#0x55         ; RIU addr low
E4D7: 7E 0F           MOV  R6,#0x0F         ; RIU addr high (0x0F55)
E4D9: 12 C6 DD        LCALL 0xC6DD          ; riu_read() → A

E4DC: 90 40 06        MOV  DPTR,#0x4006     ; Temp storage
E4DF: EF              MOV  A,R7
E4E0: F0              MOVX @DPTR,A
E4E1: 54 E0           ANL  A,#0xE0          ; Mask bits [7:5], CLEAR [4:0]

E4E3: F0              MOVX @DPTR,A          ; Store masked value
E4E4: 90 45 83        MOV  DPTR,#0x4583
E4E7: E0              MOVX A,@DPTR
E4E8: 14              DEC  A                ; Test state == 1
E4E9: 60 11           JZ   0xE4FC           ; State 1 → set 0x04
E4EB: 14              DEC  A                ; Test state == 2
E4EC: 60 16           JZ   0xE504           ; State 2 → set 0x0C (AEON)
E4EE: 24 FE           ADD  A,#0xFE          ; Test state == 3
E4F0: 60 1A           JZ   0xE50C           ; State 3 → set 0x1C
E4F2: 24 04           ADD  A,#0x04
E4F4: 70 25           JNZ  0xE51B           ; Invalid → exit

; State 0: UART to 8051 (bits = 0b000)
E4F6: 90 40 06        MOV  DPTR,#0x4006
E4F9: E0              MOVX A,@DPTR          ; Get masked value
E4FA: 80 16           SJMP 0xE512           ; No ORL, bits stay 0

; State 1: Mode 1 (bits = 0b001)
E4FC: 90 40 06        MOV  DPTR,#0x4006
E4FF: E0              MOVX A,@DPTR
E500: 44 04           ORL  A,#0x04          ; Set bit 2
E502: 80 0E           SJMP 0xE512

; State 2: UART to AEON (bits = 0b011)
E504: 90 40 06        MOV  DPTR,#0x4006
E507: E0              MOVX A,@DPTR
E508: 44 0C           ORL  A,#0x0C          ; Set bits 3,2
E50A: 80 06           SJMP 0xE512

; State 3: Mode 3 (bits = 0b111)
E50C: 90 40 06        MOV  DPTR,#0x4006
E50F: E0              MOVX A,@DPTR
E510: 44 1C           ORL  A,#0x1C          ; Set bits 4,3,2

; Write to RIU
E512: F0              MOVX @DPTR,A
E513: FD              MOV  R5,A             ; R5 = new value
E514: 7F 55           MOV  R7,#0x55
E516: 7E 0F           MOV  R6,#0x0F
E518: 12 C6 D0        LCALL 0xC6D0          ; riu_write(0x0F55, R5)

E51B: 22              RET
```

---

## Control Register

### RIU 0x0F55 - UART Multiplexer

**RIU Address:** 0x0F55
**XDATA Address:** 0x1EAA (RIU × 2)

| Bits [4:2] | Value | UART Destination |
|------------|-------|------------------|
| 0b000 | 0x00 | 8051 MCU |
| 0b001 | 0x04 | Mode 1 |
| 0b011 | 0x0C | AEON R2 |
| 0b111 | 0x1C | Mode 3 |

**Bit Operations (from traced code):**
```
Read:  ANL A,#0xE0   ; Preserve bits [7:5]
Write: ORL A,#0x04   ; Set bits [4:2] = 0b001 (Mode 1)
       ORL A,#0x0C   ; Set bits [4:2] = 0b011 (AEON)
       ORL A,#0x1C   ; Set bits [4:2] = 0b111 (Mode 3)
       (no ORL)      ; Bits [4:2] = 0b000 (8051)
```

---

## SERDB Control

### Switch UART to AEON

```python
def d72n_switch_uart_to_aeon():
    """Switch UART output to AEON processor

    Traced from block 1 offset 0xE504-0xE512
    """
    # Read current RIU 0x0F55 value
    # XDATA address = 0x0F55 * 2 = 0x1EAA
    current = serdb.read_xdata(0x1EAA)

    # ANL A,#0xE0 - preserve bits [7:5], clear [4:0]
    # ORL A,#0x0C - set bits [4:2] = 0b011
    new_val = (current & 0xE0) | 0x0C

    serdb.write_xdata(0x1EAA, new_val)
    print(f"[+] UART→AEON (0x{current:02X} → 0x{new_val:02X})")
```

### Switch UART to 8051

```python
def d72n_switch_uart_to_8051():
    """Switch UART output to 8051 MCU

    Traced from block 1 offset 0xE4F6-0xE512
    """
    # Read current RIU 0x0F55 value
    current = serdb.read_xdata(0x1EAA)

    # ANL A,#0xE0 - preserve bits [7:5], clear [4:0]
    # No ORL - bits stay 0b000
    new_val = current & 0xE0

    serdb.write_xdata(0x1EAA, new_val)
    print(f"[+] UART→8051 (0x{current:02X} → 0x{new_val:02X})")
```

### Get UART State

```python
def d72n_get_uart_state():
    """Read and decode current UART mux state

    Bit decoding from traced switch table at 0xE4E8-0xE510
    """
    val = serdb.read_xdata(0x1EAA)
    bits = (val >> 2) & 0x07  # Extract bits [4:2]

    states = {
        0b000: "8051 MCU",
        0b001: "Mode 1",
        0b011: "AEON R2",
        0b111: "Mode 3"
    }
    state = states.get(bits, f"Unknown (0b{bits:03b})")
    print(f"UART Mux: 0x{val:02X} → bits[4:2]=0b{bits:03b} → {state}")
    return state
```

---

## Complete UART Controller Class

```python
class D72N_UART:
    """D72N UART multiplexer control via SERDB

    Based on traced code from block 1 offset 0xE4D0-0xE51B
    """

    XDATA_UART_MUX = 0x1EAA  # RIU 0x0F55 × 2

    # UART destinations (bits [4:2])
    UART_8051  = 0x00  # 0b000
    UART_MODE1 = 0x04  # 0b001
    UART_AEON  = 0x0C  # 0b011
    UART_MODE3 = 0x1C  # 0b111

    def __init__(self, serdb):
        self.serdb = serdb

    def read_mux(self):
        """Read current UART mux register"""
        return self.serdb.read_xdata(self.XDATA_UART_MUX)

    def write_mux(self, value):
        """Write UART mux register"""
        self.serdb.write_xdata(self.XDATA_UART_MUX, value)

    def switch_to_aeon(self):
        """Switch UART to AEON (bits [4:2] = 0b011)"""
        current = self.read_mux()
        new_val = (current & 0xE0) | self.UART_AEON
        self.write_mux(new_val)
        return True

    def switch_to_8051(self):
        """Switch UART to 8051 (bits [4:2] = 0b000)"""
        current = self.read_mux()
        new_val = current & 0xE0  # Clear bits [4:0]
        self.write_mux(new_val)
        return True

    def get_state(self):
        """Get current UART destination"""
        val = self.read_mux()
        bits = val & 0x1C  # Mask bits [4:2]

        if bits == self.UART_8051:
            return "8051"
        elif bits == self.UART_MODE1:
            return "Mode1"
        elif bits == self.UART_AEON:
            return "AEON"
        elif bits == self.UART_MODE3:
            return "Mode3"
        else:
            return f"Unknown(0x{bits:02X})"
```

---

## RIU Access Functions

### riu_read (Block 1, offset 0xC6DD)

```asm
; Read RIU register
; Input: R6:R7 = RIU address
; Output: R7 = register value
;
; XDATA address = (R6:R7) × 2

C6DD: LCALL addr_setup    ; DPTR = R6:R7 × 2
C6E0: MOVX A,@DPTR        ; Read register
C6E1: MOV  R7,A           ; Return in R7
C6E2: RET
```

### riu_write (Block 1, offset 0xC6D0)

```asm
; Write RIU register
; Input: R6:R7 = RIU address, R5 = value
;
; XDATA address = (R6:R7) × 2

C6D0: LCALL addr_setup    ; DPTR = R6:R7 × 2
C6D3: MOV  A,R5           ; Get value
C6D4: MOVX @DPTR,A        ; Write register
C6D5: RET
```

---

## Verification Summary

| Item | Status | Evidence |
|------|--------|----------|
| RIU 0x0F55 controls UART | ✓ Traced | Block 1 offsets 0xE4D4, 0xE513 |
| XDATA 0x1EAA mapping | ✓ Traced | RIU × 2 formula in riu_read/write |
| Bits [4:2] encoding | ✓ Traced | ORL patterns at 0xE500, 0xE508, 0xE510 |
| 0b000 = 8051 | ✓ Traced | No ORL at 0xE4F6 path |
| 0b011 = AEON | ✓ Traced | ORL A,#0x0C at 0xE508 |
| 0b111 = Mode3 | ✓ Traced | ORL A,#0x1C at 0xE510 |
| String locations | ✓ Confirmed | Block 14 at 0x7B7, 0x7D3 |

---

## Related Documentation

- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - SERDB interface
- [D72N_AEON_CONTROL.md](D72N_AEON_CONTROL.md) - AEON halt/reset/resume
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
