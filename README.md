# Multi-Browser Automation Framework (POC)

## Overview

This project is a lightweight multi-browser automation framework designed to manage and control multiple isolated browser instances from a single interface.

It combines a PyQt-based GUI with Playwright-powered browser automation to provide:
- Periodic screenshot monitoring (not real-time)
- Macro execution across instances
- Scalable multi-session handling

This repository is a **proof-of-concept (POC)** and is not intended to be a production-ready system. There are no planned future developments.

---

## Development Hardware

- AMD Ryzen 7 5700X (8-core, 3.4 GHz)  
- 32 GB DDR4 RAM  
- NVIDIA GTX 3080 Ti  

This hardware is not modern high-end, but was sufficient for development and testing.

---

## Core Architecture

### GUI (HUDGUI)

The GUI is built using PyQt and is responsible for:
- Displaying browser instances in a grid
- Showing periodically updated screenshots
- Tracking process IDs (PID)
- Allowing macro selection and execution

The GUI does not rely on:
- Admin privileges  
- Process hooking  
- External APIs  

All data is handled locally and statically.

---

### Browser Engine

The project uses Playwright with **Firefox**, not Chrome.

This change was made because:
- Firefox provides more stable profile isolation across multiple instances
- Chrome-based approaches introduced issues with profile handling at scale

Each instance:
- Runs with its own persistent profile directory
- Uses a unique user agent
- Runs as an independent process

---

### Proxy Support

The parser currently supports:
- HTTP proxies  
- HTTPS proxies  

SOCKS5 support was intentionally removed from the parser because:
- Development and testing only used HTTP/HTTPS proxies
- Additional proxy formats were unnecessary for this use case

The parser can be extended to support SOCKS5 again if needed.

---

### Instance Launching

There is **no built-in launcher/orchestrator script** for spinning up multiple instances automatically.

Each browser instance is launched manually:

```
python codapp.py PROXY_IP PORT
```

or

```
python codapp.py PROXY_IP PORT USERNAME PASSWORD
```

If automation is required, users are expected to:
- Write their own launcher script
- Adapt it to their specific environment and use case

There is no universal launcher included because environments and requirements vary significantly.

---

### Instance Identification

Each browser instance:
- Loads a local HTML file (`titleselector.html`)
- Receives a unique identifier (`user1`, `user2`, etc.)
- Uses that identifier to map:
  - GUI display
  - Screenshot files
  - Macro targeting

---

### Screenshot System

Each instance:
- Captures screenshots at a fixed interval
- Saves them as:

```
/screenshots/user{N}.png
```

The GUI updates when files change.

This is **not real-time streaming**, only periodic capture.

---

### Macro System

Macros are plain `.txt` files stored in the `MACROS/` directory.

Execution behavior:
- Selecting a macro copies it to `macro.txt`
- All instances detect and execute it

Instance-specific macros:
```
macro1.txt → instance 1 only
macro2.txt → instance 2 only
```

Macros are:
- Parsed in chunks
- Executed sequentially
- Based on simple Python-style instructions (keyboard input, delays, navigation)

---

## Performance Notes

Testing showed:
- 16 browser instances ran without exceeding ~50% CPU usage on the development machine

This is **not a hard limit**.

The 16-instance count was simply the limit for the developer’s hardware and original use case.

With stronger hardware:
- More instances can be handled
- Scaling is primarily CPU-dependent

---

## Limitations

- Proof-of-concept only
- No automated launcher system
- Limited proxy parser (HTTP/HTTPS only)
- No fault tolerance or recovery system
- Macro system requires manual scripting

---

## Final Notes

This project exists to demonstrate:
- Efficient multi-instance browser handling
- Reduced overhead compared to traditional approaches
- A simplified architecture for browser orchestration

Only functionality that is implemented and observable in the codebase is documented here.
