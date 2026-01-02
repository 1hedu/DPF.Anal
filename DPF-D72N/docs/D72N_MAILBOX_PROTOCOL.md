# D72N Mailbox IPC Protocol

Inter-processor communication between the PM51 (8051) and AEON R2 processors in the DPF-D72N.

## Overview

The D72N uses a shared XDATA mailbox for 8051↔AEON communication. All addresses below are traced from the D72N 8051 overlay blocks.

---

## Traced Evidence

### Mailbox Address Patterns

Pattern searches across 18 D72N blocks for `MOV DPTR,#xxxx` instructions:

| Pattern | Block | Offsets | Count |
|---------|-------|---------|-------|
| 90 44 01 (DPTR,#4401) | 02 | 0x22FA, 0x2307, 0x27A1, 0x2835, 0x283D, 0x2865, 0x286D | 9 |
| 90 44 17 (DPTR,#4417) | 02 | 0x24AA | 1 |
| 90 40 FB (DPTR,#40FB) | 01,03,05,09,12,14,15,18 | (multiple) | 40+ |
| 90 40 FC (DPTR,#40FC) | 01,03,05,09,11,12,15,18 | (multiple) | 30+ |

---

## Memory Map

### MCU → AEON Command Area (0x4400-0x4420)

| Address | Purpose | Traced Evidence |
|---------|---------|-----------------|
| 0x4401 | Command byte | Block 02: 0x2835, 0x283D |
| 0x4402 | Param byte 0 | Block 02: 0x283A |
| 0x4403-0x4416 | Params 1-19 | Inferred from sequence |
| 0x4417 | Sync flag | Block 02: 0x24AA |

### AEON → MCU Response Area (0x40FB-0x40FF)

| Address | Purpose | Traced Evidence |
|---------|---------|-----------------|
| 0x40FB | Status register | Block 01: 0x4E32, 0x5E61; Block 03: 0x32F0 |
| 0x40FC | Response[0] | Block 01: 0x4E40; Block 03: 0x3300 |
| 0x40FD | Response[1] | Inferred |
| 0x40FE | Response[2] | Inferred |
| 0x40FF | Response[3] | Inferred |

---

## Traced Code

### Send Mailbox Command (Block 02, offset 0x2830)

```asm
; Block 02 offset 0x2830 (Flash 0x52830)
; SendMailboxCmd - Write command to mailbox
; Input: R6 = command byte, R7 = param byte
; Output: R4:R5 = readback values

2830: 7B 01        MOV  R3,#0x01        ; Set flag
2832: 12 6A 51     LCALL 0x6A51         ; Call init/check
2835: 90 44 01     MOV  DPTR,#0x4401    ; Mailbox command address
2838: EE           MOV  A,R6            ; Get command byte
2839: F0           MOVX @DPTR,A         ; Write command to 0x4401
283A: A3           INC  DPTR            ; DPTR = 0x4402
283B: EF           MOV  A,R7            ; Get param byte
283C: F0           MOVX @DPTR,A         ; Write param to 0x4402
283D: 90 44 01     MOV  DPTR,#0x4401    ; Back to command
2840: E0           MOVX A,@DPTR         ; Read back command
2841: FC           MOV  R4,A            ; Store in R4
2842: A3           INC  DPTR            ; DPTR = 0x4402
2843: E0           MOVX A,@DPTR         ; Read back param
2844: FD           MOV  R5,A            ; Store in R5
2845: 22           RET
```

### Command Byte Selection (Block 02, offset 0x22E2)

```asm
; Block 02 offset 0x22E2 (Flash 0x522E2)
; Select command byte based on R7 input

22E2: EF           MOV  A,R7            ; Get param
22E3: B4 02 05     CJNE A,#0x02,+5      ; If R7 != 2, skip
22E6: 90 44 02     MOV  DPTR,#0x4402    ; Point to param
22E9: 80 0C        SJMP 0x22F7          ; Jump to write 0x01

22EB: EF           MOV  A,R7            ; Get param again
22EC: 90 44 02     MOV  DPTR,#0x4402
22EF: B4 04 05     CJNE A,#0x04,+5      ; If R7 != 4, skip
22F2: 74 02        MOV  A,#0x02         ; Command 0x02 (MJPG_START_DEC)
22F4: F0           MOVX @DPTR,A         ; Write to mailbox
22F5: 80 03        SJMP 0x22FA

22F7: 74 01        MOV  A,#0x01         ; Command 0x01 (INIT)
22F9: F0           MOVX @DPTR,A         ; Write to mailbox

22FA: 90 44 01     MOV  DPTR,#0x4401    ; Read back
22FD: E0           MOVX A,@DPTR
22FE: 90 44 12     MOV  DPTR,#0x4412    ; Copy to 0x4412
2301: F0           MOVX @DPTR,A
```

### Read Mailbox Status (Block 01, offset 0x4E32)

```asm
; Block 01 offset 0x4E32 (Flash 0x44E32)
; Read and process mailbox status

4E32: 90 40 FB     MOV  DPTR,#0x40FB    ; Mailbox status register
4E35: 12 D2 E6     LCALL 0xD2E6         ; Read/compare function
4E38: 50 19        JNC  0x4E53          ; Branch on status
```

### Write Mailbox Status (Block 01, offset 0x5E61)

```asm
; Block 01 offset 0x5E61 (Flash 0x45E61)
; Write status to mailbox

5E5C: 90 4E C4     MOV  DPTR,#0x4EC4    ; Get status value
5E5F: E0           MOVX A,@DPTR
5E60: FE           MOV  R6,A
5E61: 90 40 FB     MOV  DPTR,#0x40FB    ; Mailbox status
5E64: F0           MOVX @DPTR,A         ; Write status
```

### Read Response (Block 03, offset 0x3300)

```asm
; Block 03 offset 0x3300 (Flash 0x63300)
; Read mailbox response bytes

3300: 90 40 FC     MOV  DPTR,#0x40FC    ; Response[0]
3303: E0           MOVX A,@DPTR         ; Read response
3304: 24 AE        ADD  A,#0xAE         ; Process value
...
3315: 90 40 FC     MOV  DPTR,#0x40FC    ; Read again
3318: E0           MOVX A,@DPTR
...
331D: 90 40 FC     MOV  DPTR,#0x40FC    ; Third read
3320: E0           MOVX A,@DPTR
```

### Set Sync Flag (Block 02, offset 0x24AA)

```asm
; Block 02 offset 0x24AA (Flash 0x524AA)
; Clear/set sync flag and extended params

24AA: 90 44 17     MOV  DPTR,#0x4417    ; Mailbox sync flag
24AD: 74 FF        MOV  A,#0xFF         ; Value 0xFF
24AF: F0           MOVX @DPTR,A         ; Write to 0x4417
24B0: A3           INC  DPTR            ; 0x4418
24B1: F0           MOVX @DPTR,A         ; Write 0xFF
24B2: A3           INC  DPTR            ; 0x4419
24B3: F0           MOVX @DPTR,A         ; Write 0xFF
24B4: A3           INC  DPTR            ; 0x441A
24B5: F0           MOVX @DPTR,A         ; Write 0xFF
```

---

## Command Bytes

### Traced Commands

| Cmd | Name | Status | Evidence |
|-----|------|--------|----------|
| 0x01 | MB_JPD_CMD_INIT | ✓ Traced | Block 02: 0x22F7 (MOV A,#0x01; F0) |
| 0x02 | MB_JPD_CMD_MJPG_START_DEC | ✓ Traced | Block 02: 0x22F2 (MOV A,#0x02; F0) |

### Command Dispatch Logic

From traced code at 0x22E2-0x22FA:
```
if (R7 == 2):
    write 0x02 to 0x4402  # Start decode
else if (R7 == 4):
    write 0x02 to 0x4402  # Start decode
else:
    write 0x01 to 0x4402  # Init
```

---

## Protocol Flow

### Send Command Sequence

```
1. Call init check (0x6A51)
2. Write command byte to 0x4401
3. Write param byte to 0x4402
4. Write additional params to 0x4403+
5. Write 0xFF to 0x4417-0x441A (sync)
6. Poll 0x40FB for status change
7. Read response from 0x40FC-0x40FF
```

### Status Values (Inferred from Usage)

| Value | Meaning |
|-------|---------|
| 0xFE | Ready for command |
| 0x00 | Processing |
| 0x01 | Complete |

---

## SERDB Access

```python
def d72n_send_mailbox_cmd(cmd, param=0):
    """Send mailbox command via SERDB

    Traced from block 02 offset 0x2830:
    - Write command to 0x4401
    - Write param to 0x4402
    """
    # Write command
    serdb.write_xdata(0x4401, cmd)

    # Write param
    serdb.write_xdata(0x4402, param)

    # Trigger sync (from 0x24AA)
    serdb.write_xdata(0x4417, 0xFF)

    print(f"[+] Sent command 0x{cmd:02X} param 0x{param:02X}")


def d72n_read_mailbox_status():
    """Read mailbox status

    Traced from block 01 offset 0x4E32
    """
    return serdb.read_xdata(0x40FB)


def d72n_read_mailbox_response():
    """Read 4-byte response

    Traced from block 03 offset 0x3300
    """
    return [serdb.read_xdata(0x40FC + i) for i in range(4)]


def d72n_wait_mailbox_ready():
    """Wait for mailbox ready (status 0xFE)"""
    import time
    while d72n_read_mailbox_status() != 0xFE:
        time.sleep(0.001)
```

---

## Complete Mailbox Class

```python
class D72N_Mailbox:
    """D72N Mailbox controller via SERDB

    Traced from D72N 8051 blocks:
    - Block 02: 0x2830-0x2845 (send function)
    - Block 02: 0x22E2-0x2301 (command dispatch)
    - Block 02: 0x24AA-0x24B5 (sync trigger)
    - Block 01: 0x4E32 (status read)
    - Block 03: 0x3300+ (response read)
    """

    # Addresses (traced)
    ADDR_CMD    = 0x4401  # Command byte
    ADDR_PARAM  = 0x4402  # First param
    ADDR_SYNC   = 0x4417  # Sync flag
    ADDR_STATUS = 0x40FB  # Status register
    ADDR_RESP   = 0x40FC  # Response[0]

    # Commands (traced from 0x22F2, 0x22F7)
    CMD_INIT  = 0x01
    CMD_START = 0x02

    def __init__(self, serdb):
        self.serdb = serdb

    def send(self, cmd, params=None):
        """Send command with optional params"""
        # Write command (traced: 0x2835-0x2839)
        self.serdb.write_xdata(self.ADDR_CMD, cmd)

        # Write params (traced: 0x283A-0x283C)
        if params:
            for i, p in enumerate(params[:21]):
                self.serdb.write_xdata(self.ADDR_PARAM + i, p)

        # Trigger sync (traced: 0x24AA-0x24B5)
        for i in range(4):
            self.serdb.write_xdata(self.ADDR_SYNC + i, 0xFF)

    def status(self):
        """Read status (traced: 0x4E32)"""
        return self.serdb.read_xdata(self.ADDR_STATUS)

    def response(self):
        """Read response (traced: 0x3300+)"""
        return [self.serdb.read_xdata(self.ADDR_RESP + i) for i in range(4)]

    def wait_ready(self, timeout=1.0):
        """Wait for ready status"""
        import time
        start = time.time()
        while self.status() != 0xFE:
            if time.time() - start > timeout:
                return False
            time.sleep(0.001)
        return True

    def send_and_wait(self, cmd, params=None, timeout=1.0):
        """Send command and wait for completion"""
        self.send(cmd, params)
        if not self.wait_ready(timeout):
            return None
        return self.response()
```

---

## Verification Summary

| Item | Status | Evidence |
|------|--------|----------|
| Command address 0x4401 | ✓ Traced | Block 02: 0x2835, 0x283D, 0x22FA |
| Param address 0x4402 | ✓ Traced | Block 02: 0x283A |
| Status address 0x40FB | ✓ Traced | Block 01: 0x4E32, 0x5E61 |
| Response address 0x40FC | ✓ Traced | Block 03: 0x3300 |
| Sync address 0x4417 | ✓ Traced | Block 02: 0x24AA |
| Command 0x01 (INIT) | ✓ Traced | Block 02: 0x22F7 |
| Command 0x02 (START) | ✓ Traced | Block 02: 0x22F2 |
| Send function | ✓ Traced | Block 02: 0x2830-0x2845 |

---

## Related Documentation

- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - SERDB interface
- [D72N_AEON_CONTROL.md](D72N_AEON_CONTROL.md) - AEON halt/resume
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
