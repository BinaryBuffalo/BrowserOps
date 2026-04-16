# BrowserOps
This project is a POC lightweight multi-browser automation framework built to efficiently manage and control multiple isolated browser instances from a single interface. It combines a PyQt-based GUI with Playwright-powered browser automation to provide periodic screenshot monitoring, macro execution, and scalable session handling.


# Multi-Browser Automation Framework (POC)

## Overview

This project is a proof-of-concept (POC) multi-browser automation framework designed to manage and coordinate multiple isolated browser instances with minimal resource overlap.

The system focuses on:
- Efficient multi-instance browser control
- Lightweight GUI-based management
- Macro-driven automation
- Reduced system overhead compared to traditional approaches (e.g., Selenium)

This is **not a final production release**, but a functional prototype intended for experimentation, learning, and further development.

---

## Development Hardware

- **CPU:** AMD Ryzen 7 5700X (8-core, 3.4 GHz)  
- **RAM:** 32 GB DDR4  
- **GPU:** NVIDIA GTX 3080 Ti (MSI)

While not cutting-edge, this hardware provides a cost-effective and capable environment for development and testing.

---

## Project Intent

This project is intended to demonstrate:
- How large-scale browser orchestration can be implemented efficiently
- Alternative architectural approaches to traditional automation frameworks
- A foundation that may later evolve into an API-driven automation system

This repository is provided for **educational and research purposes only**.

---

## Core Architecture

### 1. GUI Management (HUDGUI)

The system uses a custom PyQt-based GUI (`hudgui.py`) that:
- Displays all active browser instances in a grid layout
- Shows live screenshots of each instance
- Tracks process IDs (PIDs)
- Allows interaction with individual browser windows
- Provides macro selection and execution control

Key design choices:
- No admin privileges required
- No process hooking
- Static data handling instead of continuous API polling

---

### 2. Browser Instance Management

Each browser instance is launched via:

```bash
python codapp.py PROXY_IP PORT
```

or with authentication:

```bash
python codapp.py PROXY_IP PORT USERNAME PASSWORD
```

#### Features:
- Each instance runs in its own persistent profile directory
- Unique user agent per instance (from `useragents.txt`)
- Isolated process execution to prevent resource contention
- Proxy support (HTTP only)

---

### 3. Instance Identification

Each browser instance:
- Loads `titleselector.html`
- Receives a unique identifier (`user1`, `user2`, etc.) via query parameters
- Synchronizes instance identity before profile data loads

This ensures consistent mapping between:
- GUI elements
- Browser instances
- Screenshot feeds
- Macro execution targets

---

### 4. Screenshot Monitoring

Each instance:
- Captures screenshots at regular intervals
- Saves them as:

```
/screenshots/user{N}.png
```

The GUI automatically updates using a file watcher, providing near real-time visibility into all running sessions.

---

### 5. Macro Execution System

Macros are simple `.txt` files stored in the `MACROS/` directory.

#### Execution Model:
- Selecting a macro copies it to:
  ```
  ./macro.txt
  ```
- All instances detect and execute it

#### Instance-Specific Macros:

```
macro1.txt → only runs on instance 1
macro2.txt → only runs on instance 2
```

#### Macro Format:
- Parsed in chunks
- Supports:
  - Keyboard input
  - Navigation
  - Delays (`time.sleep`)
- Executed sequentially using async locking

---

## Why Not Selenium?

Traditional tools like Selenium introduce several limitations:

- Excessive abstraction and unused code
- Limited control over low-level behavior
- Poor handling of multi-instance scaling
- Shared process/resource contention

### Key Issue

When multiple browser instances share a parent PID:
- Threads compete for the same CPU core
- Resource contention increases
- Performance degrades significantly

---

## Design Advantages

This implementation avoids those issues by:

- Assigning independent processes per instance
- Using Playwright with persistent contexts
- Avoiding shared execution pipelines
- Minimizing background overhead

### Result

- Lower CPU usage
- Reduced memory overhead
- Improved scalability

---

## Performance Observations

Testing with 16 simultaneous browser instances showed:

- CPU usage remained below ~50%
- Stable memory consumption
- Minimal performance degradation

Primary bottlenecks:
- CPU limitations
- Page complexity (heavy sites increase load times)

---

## Scalability Considerations

For larger workloads:
- Splitting instances across multiple machines is recommended
- Example:
  - Machine A: 8 instances
  - Machine B: 8 instances

This improves:
- Load distribution
- Responsiveness
- Stability

---

## Limitations

- Not production hardened
- Limited proxy protocol support (HTTP only)
- No built-in fault tolerance
- Macro system requires manual scripting knowledge

---

## Future Development

Planned improvements include:

- Conversion into a structured API
- Improved macro scripting interface
- Enhanced error handling
- Broader proxy support
- Performance optimizations

---

## Disclaimer

This project is provided strictly for educational and research purposes.

Users are responsible for ensuring their use of this software complies with:
- Applicable laws
- Platform terms of service
- Ethical standards

---

## Summary

This project demonstrates an alternative approach to browser automation focused on:
- Efficiency
- Scalability
- Simplicity

It serves as a foundation for further experimentation and development in multi-instance browser orchestration.
