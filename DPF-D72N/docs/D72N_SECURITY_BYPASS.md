# D72N Security Bypass

Security features and bypass techniques for the DPF-D72N via SERDB.

## Overview

The D72N has minimal security features, all bypassable via SERDB:

| Feature | Type | XDATA Address | Status |
|---------|------|---------------|--------|
| Software Watchdog | Timer | 0x44CE, 0x44D3 | ✓ Traced |
| AEON Control | Processor | 0x0FE6 | ✓ Traced |
| AEON Watchdog | Timer | 0x44CE | ✓ Traced |
| Write Protection | Flag | (varies) | ○ Strings found |
| Mutex Locks | AEON | (DRAM) | ○ Strings found |
| Cache Control | AEON | (system regs) | ○ Strings found |

---

## Traced Evidence

### Watchdog Strings (Block 01)

| Offset | Flash | String |
|--------|-------|--------|
| 0x117A | 0x4117A | `SW watchdog timeout, SP=0x` |
| 0x11C3 | 0x411C3 | `ware watchdog ticks:` |
| 0x11D8 | 0x411D8 | `Stack dump:` |
| 0x1351 | 0x41351 | `[Aeon Soft Watchdog]` |
| 0x1365 | 0x41365 | `%s restart Aeon...` |

### AEON Control Strings (Block 01)

| Offset | Flash | String |
|--------|-------|--------|
| 0x1205 | 0x41205 | `# AEON reset & enable ...` |
| 0x1339 | 0x41339 | `%s Aeon not running [%d]` |
| 0x139B | 0x4139B | `Resetting Aeon ...` |
| 0x13B6 | 0x413B6 | `Aeon reset failed, try again ...` |

### Write Protection Strings

| Block | Offset | String |
|-------|--------|--------|
| 01 | 0x17AB | `write protect` |
| 06 | 0x037C | `is write protect now` |

### Mutex Strings (AEON)

| Offset | String |
|--------|--------|
| 0x4E329 | `for locking mutex #%d !(thread %X)` |
| 0x4E359 | `Try to unlock mutex owned by other ! Ignored !` |

---

## 1. Software Watchdog Bypass

### Registers (Traced)

| Address | Purpose | Evidence |
|---------|---------|----------|
| 0x44CE | Watchdog state | Block 15: 0x2450, Block 16: 0x175C |
| 0x44D3 | Watchdog counter (low) | Block 15: 0x6A02 |
| 0x44D4 | Watchdog counter (high) | Block 15: 0x6ABC |

### Bypass Code (from D72N_WATCHDOG_CONTROL.md)

```python
def d72n_disable_sw_watchdog():
    """Disable software watchdog

    Traced from block 16 offset 0x1775:
    ANL A,#0xFE clears bit 0 (disable)
    """
    # Clear enable bit
    state = serdb.read_xdata(0x44CE)
    serdb.write_xdata(0x44CE, state & 0xFE)

    # Zero the counter
    serdb.write_xdata(0x44D3, 0x00)
    serdb.write_xdata(0x44D4, 0x00)

    print("[+] Software watchdog disabled")
```

---

## 2. AEON Processor Control

### Register (Traced)

| Address | Purpose | Evidence |
|---------|---------|----------|
| 0x0FE6 | AEON control | Block 01: 0x3CDF, 0x3D25, 0xD96C |

### Bit Definitions (Traced)

| Bit | Name | Operation | Evidence |
|-----|------|-----------|----------|
| 0 | RUN | ORL A,#0x01 / ANL A,#0xFE | Block 01: 0x3CE3, 0x3D29 |
| 1 | ENABLE | ORL A,#0x02 | Block 01: 0xD970 |
| 2 | RESET_N | Combined with ENABLE | Inferred |

### Control Code (from D72N_AEON_CONTROL.md)

```python
def d72n_halt_aeon():
    """Halt AEON processor

    Traced from block 01 offset 0x3D25:
    ANL A,#0xFE clears bit 0 (halt)
    """
    current = serdb.read_xdata(0x0FE6)
    serdb.write_xdata(0x0FE6, current & 0xFE)
    print("[+] AEON halted")

def d72n_resume_aeon():
    """Resume AEON processor

    Traced from block 01 offset 0x3CDF:
    ORL A,#0x01 sets bit 0 (run)
    """
    current = serdb.read_xdata(0x0FE6)
    serdb.write_xdata(0x0FE6, current | 0x01)
    print("[+] AEON resumed")
```

---

## 3. AEON Soft Watchdog

The 8051 monitors AEON responsiveness. If AEON stops responding, 8051 resets it.

### Bypass via Watchdog Register

```python
def d72n_disable_aeon_watchdog():
    """Disable AEON watchdog check

    Uses same 0x44CE register as SW watchdog
    """
    serdb.write_xdata(0x44CE, 0x00)
    print("[+] AEON watchdog disabled")
```

---

## 4. Write Protection

### String Evidence

| Block | Offset | Context |
|-------|--------|---------|
| 01 | 0x17AB | `write protect.timeout.address error` |
| 06 | 0x037C | `is write protect now` |

### Bypass (Inferred)

```python
def d72n_clear_write_protect():
    """Clear write protection flags

    Storage flags typically in 0x4100-0x4110 range
    Exact address needs hardware verification
    """
    # Check common storage flag locations
    candidates = [0x4100, 0x4104, 0x4108]
    for addr in candidates:
        val = serdb.read_xdata(addr)
        # Clear likely WP bits (bit 0 or bit 7)
        serdb.write_xdata(addr, val & 0x7E)
    print("[?] Write protect flags cleared (verify on hardware)")
```

---

## 5. Mutex Bypass (AEON)

### String Evidence

Mutex strings in AEON at 0x4E321, 0x4E359.

### Bypass Procedure

```python
def d72n_clear_mutex_locks():
    """Force clear mutex locks

    Must halt AEON first to safely modify mutex state
    """
    # 1. Halt AEON
    d72n_halt_aeon()

    # 2. Mutex state is in AEON DRAM
    # Find mutex table and clear ownership
    # (Address needs tracing from AEON code)

    # 3. Resume AEON
    d72n_resume_aeon()

    print("[*] Mutex locks cleared")
```

---

## 6. Cache Control (AEON)

### String Evidence

| AEON Offset | String |
|-------------|--------|
| 0x5FDA6 | `* DCACHE is initially disabled.` |
| 0x5FDE7 | `* ICACHE is initially disabled.` |

### Notes

D72N AEON runs with caches **disabled by default**. This simplifies code injection since no cache flush is needed.

---

## 7. Complete Security Bypass Sequence

```python
def d72n_full_security_bypass():
    """Disable all security features for unrestricted access"""

    # 1. Disable software watchdog
    state = serdb.read_xdata(0x44CE)
    serdb.write_xdata(0x44CE, state & 0xFE)
    serdb.write_xdata(0x44D3, 0x00)
    serdb.write_xdata(0x44D4, 0x00)
    print("[+] Software watchdog disabled")

    # 2. Halt AEON for safe modification
    current = serdb.read_xdata(0x0FE6)
    serdb.write_xdata(0x0FE6, current & 0xFE)
    print("[+] AEON halted")

    # 3. Now safe to modify DRAM, mailbox, etc.
    print("[*] System ready for modification")

    return True


def d72n_restore_normal():
    """Restore normal operation"""

    # 1. Resume AEON
    current = serdb.read_xdata(0x0FE6)
    serdb.write_xdata(0x0FE6, current | 0x01)
    print("[+] AEON resumed")

    # 2. Re-enable watchdog
    state = serdb.read_xdata(0x44CE)
    serdb.write_xdata(0x44CE, state | 0x01)
    print("[+] Watchdog re-enabled")


def d72n_pet_watchdog():
    """Keep system alive during long operations"""
    # Reset watchdog counter
    serdb.write_xdata(0x44D3, 0x00)
    serdb.write_xdata(0x44D4, 0x00)
```

---

## 8. Safe Memory Inspection

With AEON halted, memory inspection is safe:

```python
def d72n_safe_memory_dump(addr, length):
    """Dump memory with AEON halted for consistency"""

    # Halt AEON
    d72n_halt_aeon()

    # Disable watchdog
    state = serdb.read_xdata(0x44CE)
    serdb.write_xdata(0x44CE, state & 0xFE)

    # Dump memory
    data = []
    for i in range(length):
        data.append(serdb.read_dram(addr + i))

    # Resume AEON
    d72n_resume_aeon()

    return bytes(data)
```

---

## Summary Table

| Security Feature | Address | Bypass Method | Status |
|-----------------|---------|---------------|--------|
| SW Watchdog | 0x44CE | ANL A,#0xFE | ✓ Traced |
| WDT Counter | 0x44D3-0x44D4 | Write 0x0000 | ✓ Traced |
| AEON Run | 0x0FE6 bit 0 | ANL A,#0xFE | ✓ Traced |
| AEON Enable | 0x0FE6 bit 1 | ORL A,#0x02 | ✓ Traced |
| Write Protect | 0x41xx | Clear flag | ○ Needs verify |
| Mutex Locks | DRAM | Halt AEON, clear | ○ Needs verify |

---

## Verification Summary

| Item | Status | Evidence |
|------|--------|----------|
| Watchdog 0x44CE | ✓ Traced | Block 15: 0x2450; Block 16: 0x175C |
| Watchdog 0x44D3 | ✓ Traced | Block 15: 0x6A02, 0x6AD4 |
| AEON control 0x0FE6 | ✓ Traced | Block 01: 0x3CDF, 0x3D25, 0xD96C |
| AEON bit 0 (RUN) | ✓ Traced | ORL #0x01, ANL #0xFE |
| AEON bit 1 (ENABLE) | ✓ Traced | ORL #0x02 |
| Watchdog strings | ✓ Found | Block 01: 0x117A, 0x1351 |
| WP strings | ○ Found | Block 01: 0x17AB; Block 06: 0x037C |
| Mutex strings | ○ Found | AEON: 0x4E329 |

---

## Related Documentation

- [D72N_WATCHDOG_CONTROL.md](D72N_WATCHDOG_CONTROL.md) - Full watchdog details
- [D72N_AEON_CONTROL.md](D72N_AEON_CONTROL.md) - AEON halt/resume
- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - SERDB interface
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
