# Multi-Browser Automation Framework (POC)

## Overview

This project is a lightweight multi-browser automation framework designed to manage and control multiple isolated browser instances from a single interface.

It combines a PyQt-based GUI with Playwright-powered Firefox automation to provide:
- Periodic screenshot-based monitoring (not real-time streaming)
- Macro execution across instances
- Scalable multi-session handling

This repository is a **proof-of-concept (POC)**. It is not production software and has no planned future development.

---

## Design Approach

This project was built with a different approach compared to traditional browser automation tools.

### Why Not Selenium

In testing, Selenium was unable to reliably handle even a single instance under the same workload without instability and excessive overhead. Its architecture introduces unnecessary abstraction layers, background processes, and resource contention that scale poorly when attempting multi-instance execution.

This implementation avoids those issues by:
- Using Playwright with Firefox persistent contexts
- Assigning a fully isolated profile per instance
- Avoiding shared parent process contention
- Keeping execution simple and predictable

---

## Browser Engine Choice

The framework uses **Playwright with Firefox**, not Chrome.

Reasoning:
- Firefox provides more reliable profile isolation across multiple instances
- Chrome-based approaches introduced instability and profile conflicts when scaled
- Firefox persistent contexts behave more predictably under concurrent workloads

---

## Screenshot-Based Monitoring (Design Rationale)

At a glance, using screenshots to represent browser state may appear inefficient or “caveman-like.” However, in this implementation, it is intentionally leveraged in an optimized way.

Key points:
- The browser is already rendering frames internally
- Playwright (Firefox) provides a built-in screenshot function
- This function is lightweight when used at controlled intervals

### Implementation

Each instance:
- Captures a screenshot at a fixed interval (default ~5–10 seconds)
- Saves to:
  ```
  /screenshots/user{N}.png
  ```
- The GUI updates using a file watcher

### Performance Characteristics

- At ~5 second intervals, overhead is negligible
- On stronger systems, 1 screenshot per second per instance is feasible
- No screen capture hooks or GPU duplication is used

This approach avoids:
- Streaming overhead
- Window capture APIs
- External rendering pipelines

---

## Proxy Parser

Supported:
- HTTP
- HTTPS

Removed:
- SOCKS5

Reason:
- Development only required HTTP/HTTPS proxies
- SOCKS5 support was removed to simplify the parser

The parser can be extended to support SOCKS5 again if required.

---

## Instance Launching

There is **no built-in launcher system**.

Instances are launched manually:

```
python codapp.py PROXY_IP PORT
```

or:

```
python codapp.py PROXY_IP PORT USERNAME PASSWORD
```

Automation is intentionally left to the user because:
- Launch strategies vary by environment
- Resource allocation differs per system
- Use cases are not standardized

Users can create custom scripts to spawn instances as needed.

---

## Macro System

Macros are stored as `.txt` files and executed dynamically.

### Execution Model
- Global macro: `macro.txt` → runs on all instances
- Instance macro: `macro1.txt`, `macro2.txt`, etc.

Macros are:
- Parsed in chunks
- Executed sequentially
- Interpreted at runtime

### Macro Builder

The project also includes a `macrobuilder.py` utility:

- Generates randomized macro sequences
- Helps automate repetitive input patterns
- Reduces manual scripting effort

---

## Authentic Execution Model

The system avoids artificial or injected behavior.

Actions are executed through:
- Playwright keyboard inputs
- Page navigation
- Timed delays

Because of this:
- Behavior is consistent with real user interaction
- No external hooks or memory manipulation are used
- Execution remains stable across instances

---

## Performance Observations

Testing was conducted using 16 concurrent browser instances running a browser-based game workload.

### Observed Metrics (ShellShockers Test)

- CPU Usage:
  - Average: 25–50%
  - Peak: ~55%
- RAM Usage:
  - Estimated 300–500 MB per instance
  - Total usage ~6–8 GB across all instances
- Stability:
  - No crashes observed during sustained runtime
  - No major frame or input desync issues

### Important Note

- 16 instances is **not a hard limit**
- This was the limit of the development machine and original use case

With stronger hardware:
- Higher instance counts are achievable
- Scaling is primarily CPU-bound

---

## Limitations

- Proof-of-concept only
- No built-in launcher/orchestration system
- Limited proxy parser (HTTP/HTTPS only)
- No fault tolerance system
- Macro system requires basic scripting understanding

---

## Final Notes

This project demonstrates:
- A low-overhead approach to multi-browser automation
- Practical scaling without heavy frameworks
- A simplified and controllable architecture

All functionality described here is directly based on the implemented codebase.
