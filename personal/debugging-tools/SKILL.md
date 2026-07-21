---
name: debugging-tools
description: "Debug Python and Node.js applications: pdb REPL, debugpy remote DAP, Node.js --inspect with CDP CLI, and systematic 4-phase root cause debugging methodology."
version: 1.0.0
author: Hermes Agent (consolidated)
license: MIT
metadata:
  hermes:
    tags: [debugging, python, nodejs, debugpy, pdb, inspect, devtools, methodology]
    related_skills: []
---

# Debugging Tools: Python, Node.js & Methodology

## Section A: Python Debugging

### Option 1: pdb (Insert REPL)

Add a breakpoint inline:
```python
import pdb; pdb.set_trace()
# or in Python 3.7+:
breakpoint()
```

When hit, the terminal becomes an interactive pdb REPL. Useful commands:
- `n` (next line), `s` (step into), `c` (continue)
- `l` (list source), `p var` (print variable), `pp var` (pretty-print)
- `q` (quit debugger)

### Option 2: debugpy (Remote DAP)

For debugging from an IDE (VS Code, PyCharm) or the Hermes TUI:

```bash
pip install debugpy
```

**Start a script with debugger attached:**
```bash
python -m debugpy --listen 5678 --wait-for-client script.py
```

**Attach to a running process:**
```python
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()  # blocks until IDE connects
```

Then connect VS Code's "Remote Attach" to localhost:5678.

### Option 3: remote-pdb (Simpler alternative)

```bash
pip install remote-pdb
```

```python
from remote_pdb import RemotePdb
RemotePdb('127.0.0.1', 4444).set_trace()
```

Then `telnet 127.0.0.1 4444` or `nc 127.0.0.1 4444` for a pdb REPL.

---

## Section B: Node.js Debugging

Use Chrome DevTools Protocol to debug Node.js apps via the `--inspect` flag.

### Start with inspector

```bash
node --inspect script.js
node --inspect-brk script.js    # Break on first line
# Listening at: ws://127.0.0.1:9229/...
```

### Chrome DevTools Protocol via CLI

Install: `npm install -g chrome-remote-interface`

```bash
# Connect and evaluate JavaScript
node -e "
const CDP = require('chrome-remote-interface');
CDP(async (client) => {
  const {Runtime} = client;
  const result = await Runtime.evaluate({expression: '1+1'});
  console.log(result.result.value);
}).on('error', (err) => console.error(err));
"
```

Or use curl against the HTTP endpoint:
```bash
# List available targets
curl -s http://127.0.0.1:9229/json
# Get version info
curl -s http://127.0.0.1:9229/json/version
```

### Breakpoints on file:line

```bash
# Build the project first, then use sb()
node -e "
const CDP = require('chrome-remote-interface');
CDP(async (client) => {
  const {Debugger} = client;
  await Debugger.enable();
  await Debugger.setBreakpointByUrl({
    urlRegex: 'app\\\\.js',
    lineNumber: 42
  });
  await Runtime.runIfWaitingForDebugger();
  Debugger.paused(() => {
    console.log('Breakpoint hit!');
    process.exit(0);
  });
}).on('error', (err) => console.error(err));
"
```

## Section C: Systematic Debugging Methodology

A 4-phase approach to root cause debugging: understand the bug before fixing it.

### Phase 1: Reproduce & Characterize
- Get exact steps to reproduce the bug
- Identify the minimal failing input/case
- Note the environment (OS, versions, config)
- Capture error messages, stack traces, logs

### Phase 2: Locate the Root Cause
- Follow the error trace to the code path
- Use the debuggers from Sections A/B to inspect state at the failure point
- Apply the scientific method: form a hypothesis, test it, refine
- Check inputs, state, assumptions at each layer

### Phase 3: Design the Fix
- Understand why the current code fails (not just where)
- Consider the full impact: what else calls this code?
- Write the minimal fix that addresses the root cause
- Add a regression test so it doesn't recur

### Phase 4: Verify & Learn
- Run the failing test case to confirm the fix works
- Run the full test suite to check for regressions
- Document the root cause and fix for future reference
- PR: include the regression test and explanation

### Decision Flow

```
Bug reported -> Can reproduce? No -> gather more info, Yes -> locate root cause
Root cause in my code? No -> dependency issue, Yes -> design the fix
Fix addresses root cause? No -> go back to Phase 2, Yes -> verify
Tests pass? No -> fix regressions, Yes -> done
```

### Do NOT
- Skip Phase 1 and jump to fixing — you'll fix symptoms, not causes
- Change unrelated code while debugging — change one variable at a time
- Submit a fix without a regression test
- Assume the bug is where you first see the symptom — follow the data flow backward
