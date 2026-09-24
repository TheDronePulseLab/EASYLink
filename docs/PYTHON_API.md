<div align="center">

<img src="../public/EASYLink.png" alt="EASYLink" width="320"/>

<br/>

# Python SDK Reference

### `easylink-mavlink`

[![PyPI](https://img.shields.io/pypi/v/easylink-mavlink.svg?color=0a7bcc&style=flat-square)](https://pypi.org/project/easylink-mavlink/)
[![Python](https://img.shields.io/pypi/pyversions/easylink-mavlink.svg?color=2ea44f&style=flat-square)](https://pypi.org/project/easylink-mavlink/)

</div>

---

## Installation

```bash
pip install easylink-mavlink
```

**Dependency**: `pymavlink >= 2.4.41` (auto-installed)

---

## Connection & Lifecycle

### `Drone(target: str = None)`
Primary entry point. Accepts optional connection string.

```python
from easylink import Drone

# Auto-discover SITL (scans 14550, 14551, 5760) or hardware serial
drone = Drone()
drone.connect(timeout=15.0)

# Explicit target
drone = Drone("udp:127.0.0.1:14550")
drone.connect()

# Or use the SITL factory (connects automatically)
drone = Drone.sitl()
```

### `drone.connect(timeout: float = 15.0)`
Establishes MAVLink connection. Auto-detects ArduPilot vs PX4 from HEARTBEAT.

### `drone.disconnect()`
Stops telemetry dispatcher thread and closes the connection socket.

---

## Actions

All action methods send the corresponding MAVLink `COMMAND_LONG` and wait for confirmation via the background packet dispatcher.

| Method | MAVLink Command | Behavior |
| :--- | :--- | :--- |
| `drone.arm(timeout=15.0)` | `MAV_CMD_COMPONENT_ARM_DISARM` p1=1 | Switches to STABILIZE → arms → switches to GUIDED. Blocks until armed HEARTBEAT. |
| `drone.disarm(timeout=15.0)` | `MAV_CMD_COMPONENT_ARM_DISARM` p1=0 | Blocks until disarmed HEARTBEAT. |
| `drone.takeoff(altitude, timeout=30.0)` | `MAV_CMD_NAV_TAKEOFF` p7=alt | Blocks until 90% of target altitude reached via `GLOBAL_POSITION_INT`. |
| `drone.land(blocking=True, timeout=60.0)` | `MAV_CMD_NAV_LAND` | If `blocking=True`, waits until motors disarm (vehicle on ground). |
| `drone.home(blocking=True, timeout=90.0)` | Mode switch → RTL | Triggers Return-To-Launch. Blocks until vehicle lands & disarms. |
| `drone.rtl(...)` | *(alias for `home()`)* | |
| `drone.back(...)` | *(alias for `home()`)* | |
| `drone.kill()` | `MAV_CMD_COMPONENT_ARM_DISARM` p2=21196 | Immediate motor kill regardless of flight state. **Use with extreme caution.** |

### Examples

```python
drone.arm()
drone.takeoff(10.0)                 # Blocks until ~9m altitude
drone.land(blocking=True)           # Blocks until touchdown & disarm
drone.home(blocking=True)           # RTL, blocks until landed
drone.kill()                        # Emergency — instant motor cutoff
```

---

## Navigation

All navigation commands are non-blocking fire-and-forget MAVLink sends.

| Method | MAVLink Command | Parameters |
| :--- | :--- | :--- |
| `drone.goto(lat, lon, alt)` | `MAV_CMD_DO_REPOSITION` | Global GPS coordinates, relative altitude (m) |
| `drone.goto_relative(n, e, d)` | `SET_POSITION_TARGET_LOCAL_NED` | North/East/Down offsets in meters (NED frame) |
| `drone.set_speed(speed_ms)` | `MAV_CMD_DO_CHANGE_SPEED` | Groundspeed in m/s |
| `drone.set_heading(deg, relative=False)` | `MAV_CMD_CONDITION_YAW` | Target yaw angle (0–360°) |
| `drone.hover(duration)` | `MAV_CMD_NAV_LOITER_TIME` | Loiter in place for `duration` seconds (blocking) |
| `drone.orbit(radius, speed, center_lat, center_lon)` | `MAV_CMD_DO_ORBIT` | Orbit radius (m), orbit speed (m/s) |

### Examples

```python
drone.goto(22.5039, 88.2937, 15.0)       # Fly to GPS position at 15m
drone.goto_relative(10.0, 5.0, 0.0)      # Move 10m north, 5m east
drone.set_speed(3.0)                      # Set speed to 3 m/s
drone.set_heading(180.0)                  # Face south
drone.hover(5.0)                          # Hold position for 5 seconds
drone.orbit(20.0, speed=2.0)             # Orbit 20m radius at 2 m/s
```

---

## Mission Engine

Fluent builder pattern for waypoint mission construction, upload, and execution.

### Building & Uploading

```python
drone.mission.clear() \
     .add_takeoff(alt=15.0) \
     .add_waypoint(lat=22.5039, lon=88.2937, alt=15.0) \
     .add_waypoint(lat=22.5040, lon=88.2938, alt=20.0) \
     .add_land()

drone.mission.upload(timeout=10.0)
```

### Execution Control

| Method | Description |
| :--- | :--- |
| `drone.mission.start(blocking=True, timeout=120.0)` | Sets AUTO mode, sends `MAV_CMD_MISSION_START`. If blocking, waits until mission completes or vehicle disarms. |
| `drone.mission.pause()` | Switches to GUIDED mode (vehicle loiters at current position). |
| `drone.mission.resume()` | Re-enters AUTO mode to continue mission. |
| `drone.mission.progress` | Returns progress string like `"2/4"` (current_seq / total_items). |

### Full Mission Example

```python
drone.arm()
drone.mission.start(blocking=True)   # Blocks until all waypoints completed
print(f"Final: {drone.mission.progress}")
drone.home(blocking=True)
```

---

## Telemetry Properties

All properties are read from the **PacketDispatcher** — a background thread that continuously decodes incoming MAVLink packets. Thread-safe, zero packet-stealing.

| Property | Return Type | MAVLink Source |
| :--- | :--- | :--- |
| `drone.position` | `Position(lat, lon, alt)` | `GLOBAL_POSITION_INT` |
| `drone.attitude` | `Attitude(roll, pitch, yaw)` | `ATTITUDE` |
| `drone.battery` | `Battery(voltage, remaining_pct)` | `SYS_STATUS` |
| `drone.gps_info` | `GPSInfo(fix_type, satellites_visible)` | `GPS_RAW_INT` |
| `drone.groundspeed` | `float` (m/s) | `VFR_HUD` |
| `drone.heading` | `float` (degrees) | `VFR_HUD` / `GLOBAL_POSITION_INT` |
| `drone.is_armed` | `bool` | `HEARTBEAT` base_mode flag |
| `drone.mode` | `str` (e.g. `"GUIDED"`, `"AUTO"`, `"RTL"`) | `HEARTBEAT` custom_mode |
| `drone.available_modes` | `list[str]` | Flight controller mode mapping |

### `drone.mode = "RTL"` (setter)
Directly sets flight mode via `MAV_CMD_DO_SET_MODE`.

---

## Parameters

| Method | MAVLink Message | Description |
| :--- | :--- | :--- |
| `drone.params.get(name)` | `PARAM_REQUEST_READ` → `PARAM_VALUE` | Read a named flight controller parameter |
| `drone.params.set(name, value)` | `PARAM_SET` → `PARAM_VALUE` | Write a parameter value |

```python
fs_value = drone.params.get("FS_THR_ENABLE")
drone.params.set("WPNAV_SPEED", 500.0)   # 5 m/s in cm/s
```

---

## Event System

Register callbacks for real-time telemetry events.

```python
@drone.on("position")
def on_position(pos):
    print(f"Position update: {pos.lat}, {pos.lon}, {pos.alt}m")

@drone.on("armed")
def on_armed():
    print("Vehicle armed!")

@drone.on("disarmed")
def on_disarmed():
    print("Vehicle disarmed!")

@drone.on("battery_low")
def on_low_batt(bat):
    print(f"Battery warning: {bat.remaining_pct}%")
```

---

## Safety & Diagnostics

| Method | Description |
| :--- | :--- |
| `drone.preflight_check()` | Runs diagnostic check on GPS fix, battery, and connection state. Returns `bool`. |
| `drone.set_failsafe(action="RTL")` | Configures GCS connection-loss failsafe behavior. |

---

## Exceptions

```python
from easylink import (
    EASYLinkError,         # Base exception
    ConnectionError,       # Connection failures
    ArmingError,           # Arm/disarm rejections or timeouts
    CommandTimeoutError,   # Command ACK timeouts
    ModeError,             # Flight mode switch failures
    PreFlightCheckError    # Pre-flight diagnostic failures
)
```

---

<div align="center">
<sub>EASYLink Python SDK · DronePulse Labs · MIT License</sub>
</div>
