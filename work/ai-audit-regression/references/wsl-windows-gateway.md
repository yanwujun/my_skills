# WSL → Windows API Gateway Pattern

When the agents-platform API is unreachable from WSL (Connection refused) but works from Windows, run test scripts via `cmd.exe /c`.

## Quick check: which side can reach the API?

```bash
# From WSL (likely fails):
curl -s --max-time 5 http://192.168.2.166:30030/agents-platform/api/ok

# From Windows (should work):
cmd.exe /c "curl -s --max-time 5 http://192.168.2.166:30030/agents-platform/api/ok"
```

If WSL fails and Windows works → use the gateway pattern.

## Running a Python test script via cmd.exe

### 1. Script requirements (MUST add at top of every test script)

```python
import sys
sys.stdout.reconfigure(encoding='utf-8')  # Fix GBK crashes on Chinese chars
```

### 2. Output logging (REQUIRED — cmd pipe buffering kills real-time output)

```python
LOG_PATH = r"D:\项目\gitlib\智能审核\doc\output.log"

class _Tee:
    def __init__(self, *files): self.files = files
    def write(self, s):
        for f in self.files:
            f.write(s); f.flush()
    def flush(self):
        for f in self.files: f.flush()

_logf = open(LOG_PATH, 'w', encoding='utf-8', buffering=1)
sys.stdout = _Tee(sys.stdout, _logf)
```

### 3. Launch command

```bash
cmd.exe /c "chcp 65001 > NUL && cd /d D:\项目\gitlib\智能审核\doc && python -u test_script.py > NUL 2>&1"
```

Key flags:
- `chcp 65001` — set console to UTF-8 codepage
- `python -u` — unbuffered stdout
- `> NUL 2>&1` — discard console output (log goes to file via Tee)

### 4. Monitor progress from WSL

```bash
cat /mnt/d/项目/gitlib/智能审核/doc/output.log
```

### 5. Path translation

| WSL path | Windows path |
|----------|-------------|
| `/mnt/d/项目/gitlib/...` | `D:\项目\gitlib\...` |
| `/home/administrator/` | `\\wsl.localhost\Ubuntu\home\administrator\` |

Test scripts should use Windows paths (`D:\...`) for file I/O when run via cmd.exe.

### 6. cmd.exe URL escaping

The `&` character breaks cmd.exe. Escape as `^&`:
```bash
# Wrong:
cmd.exe /c "curl http://host/api?page=1&size=10"

# Right:
cmd.exe /c "curl http://host/api?page=1^&size=10"
```

## Known noise

- `'\\\\wsl.localhost\\Ubuntu\\home\\administrator'` and `UNC路径不受支持` — harmless, always appears when running cmd.exe from WSL
- `exit_code: 1` on success with non-zero return from curl searching for agents — may just mean the command succeeded but curl exit code reflects the last HTTP transfer

## Pitfalls

- **Skipping the Tee pattern = silent failure:** Redirecting Python stdout to a file via `>` in cmd.exe without the Tee class produces NO visible output until the script exits. The output file stays empty for the entire run. Always use the Tee class (with `buffering=1` on the log file) and `python -u`.
- **WSL path access from Windows Python:** `\\\\wsl.localhost\\Ubuntu\\...` paths are slow and sometimes fail from Windows Python. Copy any needed WSL files to a Windows path (`D:\\...`) before the script reads them.
- **Output file locks:** `cmd.exe /c type file.txt` may lock the file and prevent Python from appending. Read from WSL side (`cat /mnt/d/...`) instead of `type` from cmd.exe.
- **GBK encoding crashes:** Any emoji (✅❌) or full-width characters will crash `print()` on Windows cmd.exe if `sys.stdout.reconfigure(encoding='utf-8')` is missing. Add it as the FIRST line after imports.

## Real example (2026-06-24)

Ran the 13-category low-score retest via cmd.exe after WSL failed with Connection refused on both ports 30030 and 5175. The `goodsaudit-six` skill delivered 5/5 on UPS (vs 2/5 previously). Encoding fix (`reconfigure(encoding='utf-8')`) and Tee-based internal logging resolved three failed attempts.
