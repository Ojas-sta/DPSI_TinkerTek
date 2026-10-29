# ICRobot Serial / Script Upload Protocol

> **Platform:** ICRobot (ESP32-S3)  
> **Interface:** UART Serial over USB  
> **Baud rate:** 115200  
> **Document version:** 1.0 — ICRobot Open-Source Contributors

---

## Overview

The ICRobot accepts Python scripts over a serial connection from the controlling host (typically the Arduino Uno R4 WiFi, or a PC running TinkerCode). Scripts are uploaded to named slots on the ESP32-S3 flash filesystem and can be executed on demand.

---

## Connection Parameters

| Parameter | Value |
|-----------|-------|
| Baud rate | `115200` |
| Data bits | `8` |
| Stop bits | `1` |
| Parity | None |
| Flow control | None |

---

## Script Execution Slots

The ICRobot maintains **5 numbered execution slots** on its internal flash filesystem:

| Slot | Filename | Description |
|------|----------|-------------|
| 1 | `1.py` | User script slot 1 (default / primary) |
| 2 | `2.py` | User script slot 2 |
| 3 | `3.py` | User script slot 3 |
| 4 | `4.py` | User script slot 4 |
| 5 | `5.py` | User script slot 5 |

Scripts are stored in MicroPython-accessible flash and are persistent across reboots.

---

## Upload Command — JSON Protocol

Scripts are sent as a JSON command over the serial port. The command structure is:

```json
{
  "command": "upload_script",
  "params": {
    "name": "1.py",
    "script": "<URL-encoded or raw Python source>"
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `command` | string | Must be `"upload_script"` |
| `params.name` | string | Target filename — one of `"1.py"` through `"5.py"` |
| `params.script` | string | The MicroPython source code to upload |

### Example — Upload a "Hello World" to slot 1

```json
{"command":"upload_script","params":{"name":"1.py","script":"print('Hello ICRobot!')\n"}}
```

---

## Run Command

To execute a script that has already been uploaded:

```json
{
  "command": "run_script",
  "params": {
    "name": "1.py"
  }
}
```

---

## Stop Command

To halt a running script:

```json
{
  "command": "stop_script",
  "params": {}
}
```

---

## Response Format

The ICRobot responds to commands with a JSON acknowledgement:

```json
{"status": "ok", "command": "upload_script"}
```

On error:

```json
{"status": "error", "message": "file write failed"}
```

---

## Python Upload Example (Host-side)

```python
import serial
import json
import time

# Connect to ICRobot
ser = serial.Serial('/dev/cu.usbserial-110', 115200, timeout=2)
time.sleep(1)  # Wait for device ready

script_code = """
from icrobot_open import ICRobot
import time

robot = ICRobot()
robot.move('forward', duration_sec=2)
robot.stop()
"""

cmd = {
    "command": "upload_script",
    "params": {
        "name": "1.py",
        "script": script_code
    }
}

ser.write((json.dumps(cmd) + '\n').encode())
response = ser.readline()
print("Response:", response.decode())
ser.close()
```

---

## Notes

- The JSON command **must be terminated with a newline** (`\n`).
- Scripts containing double-quotes in string literals should escape them (`\"`) or use single quotes.
- Large scripts may need to be sent in chunks depending on the serial buffer size.
- The TinkerCode IDE uses this protocol to deploy block-generated Python to the robot.
- When using MicroPython REPL directly (without TinkerCode), you can also use `mpremote` or `ampy` to copy `.py` files to the device filesystem.

---

## Alternative: Direct MicroPython REPL

For development, you can bypass the JSON protocol entirely and use the MicroPython REPL:

```bash
# Install mpremote
pip install mpremote

# Copy a script to the device
mpremote connect /dev/cu.usbserial-110 cp my_script.py :1.py

# Execute it
mpremote connect /dev/cu.usbserial-110 run 1.py
```
