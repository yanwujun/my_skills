# Windows-side Python Script Execution

When WSL cannot reach `192.168.2.166:30030` (Connection refused), run Python test scripts via `cmd.exe` on the Windows host.

## The Encoding Problem

`cmd.exe` uses **GBK** (code page 936) by default. Python print output with Chinese characters or emoji crashes with:

```
UnicodeEncodeError: 'gbk' codec can't encode character '\u274c' in position 15: illegal multibyte sequence
```

## Three-Part Fix

### 1. In the Python script — force UTF-8 stdout (MUST be first lines after imports)

```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
```

### 2. In the cmd invocation — set UTF-8 code page (chcp 65001)

```cmd
cmd.exe /c "chcp 65001 >nul && python C:\Users\Public\test.py > out.txt 2>&1"
```

### 3. Avoid Unicode emoji in print output

Use ASCII substitutes: `MATCH`/`MISMATCH` instead of ✅/❌. Even with the UTF-8 fixes above, emoji can still crash the cmd.exe pipe in some cases.

## Full Windows Execution Pattern

```python
# test_script.py — MUST include at top:
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
```

```bash
# Run from WSL terminal:
cmd.exe /c "chcp 65001 >nul && python C:\Users\Public\test_script.py > C:\Users\Public\output.txt 2>&1"
```

```bash
# Read output from WSL:
cat /mnt/c/Users/Public/output.txt
```

## Background Execution

For long-running batch tests, run in background:

```bash
cmd.exe /c "chcp 65001 >nul && python C:\Users\Public\test_script.py > C:\Users\Public\output.txt 2>&1"
```

Then from Hermes: `terminal(background=true, notify_on_complete=true)`

## Known Failure Mode: UnicodeEncodeError Crashes Mid-Batch

If the script crashes after N items with `UnicodeEncodeError`, check:
1. Is `sys.stdout = io.TextIOWrapper(...)` at the very top?
2. Is `chcp 65001` in the cmd invocation?
3. Are there any emoji in print statements?

## Alternative: Write Results to File Instead of Printing

For maximum robustness, avoid print entirely for Chinese text. Write results to a pipe-delimited text file:

```python
with open(r"C:\Users\Public\results.txt", "a", encoding="utf-8") as f:
    f.write("cat|brand|model|gold|pred|match|elapsed|tid\n")
    f.write(f"{cat}|{brand}|{model}|{gold}|{pred}|{match}|{elapsed}|{tid}\n")
```

This avoids the cmd.exe stdout encoding issue entirely.
