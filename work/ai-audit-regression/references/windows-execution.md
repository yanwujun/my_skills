# Windows-Side Execution for WSL-Blocked API

## Problem

The agents-platform API at `192.168.2.166:30030` may be accessible from Windows but **blocked from WSL** (Connection refused). This is a Windows Firewall / network isolation issue — the API responds on the Windows host but WSL's virtual network adapter can't reach it.

**Detection:** `curl 192.168.2.166:30030/agents-platform/api/ok` from WSL → Connection refused, but same from cmd.exe → `{"ok":true}`.

## Workaround: Run Python via cmd.exe

Since WSL can't reach the API, run the test script from Windows side using `cmd.exe /c`:

```bash
cmd.exe /c "chcp 65001 > NUL && cd /d D:\path\to\script && python -u script.py > output.log 2>&1"
```

### Encoding Fixes (Critical)

Windows cmd.exe uses GBK by default, which **cannot** encode Chinese characters in print statements. Three layers of fix needed:

1. **`chcp 65001`** — sets console code page to UTF-8 (before Python starts)
2. **`sys.stdout.reconfigure(encoding='utf-8')`** — inside Python script, first thing
3. **`python -u`** — unbuffered stdout (needed when piping to file)

Without all three, you'll get: `UnicodeEncodeError: 'gbk' codec can't encode character`

### Output Buffering (Critical)

When stdout is redirected to a file via `>` in cmd.exe, Python fully buffers output. You'll see zero log output for minutes even though the script is running. Fixes:

- `python -u` flag (unbuffered) — works for most cases
- Internal file logging with `buffering=1` + explicit `.flush()` — most reliable

**Most reliable approach** — write to log file INSIDE Python, not via shell redirect:

```python
import sys
LOG_PATH = r"D:\path\to\log.txt"
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

This sidesteps both cmd.exe pipe buffering AND encoding issues.

### Monitoring from WSL

When script writes to a D: drive path, monitor from WSL at `/mnt/d/...`:

```bash
tail -f "/mnt/d/path/to/log.txt"
```

But note: WSL may cache file metadata. Use `cat` directly instead of `read_file` for fresh reads.

### Path Translation

| WSL path | Windows path |
|----------|-------------|
| `/mnt/d/项目/gitlib/智能审核/doc/` | `D:\项目\gitlib\智能审核\doc\` |
| `/home/administrator/script.py` | `\\wsl.localhost\Ubuntu\home\administrator\script.py` |

Prefer D: drive paths — UNC paths (`\\wsl.localhost\...`) cause cmd.exe warnings.

### Dependency Note

The `enrich_audit_training_data.py` import (`extract_detail_image_urls`) uses `bs4` (BeautifulSoup). Windows Python may not have this. Fallback: inline a regex-based extraction in the script itself.
