<div align="center">

<img src="../public/EASYLink.png" alt="EASYLink" width="320"/>

<br/>

# C++ Core Reference

### `easylink-cpp` · C++17 Static Library

[![C++ Standard](https://img.shields.io/badge/C++-17-blue.svg?style=flat-square&logo=cplusplus&logoColor=white)]()
[![Build System](https://img.shields.io/badge/Build-CMake%203.16+-064F8C.svg?style=flat-square&logo=cmake&logoColor=white)]()

</div>

---

## Build Integration

### CMake FetchContent (Recommended)

Add these lines to your application's `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_drone_app LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)

# Fetch EASYLink C++ headers & automated library linkage
include(FetchContent)
FetchContent_Declare(
    easylink_cpp
    GIT_REPOSITORY https://github.com/TheDronePulseLab/EASYLink-Public.git
    GIT_TAG v0.1.0
)
FetchContent_MakeAvailable(easylink_cpp)

add_executable(my_drone_app main.cpp)
```

---

## Data Types

Defined in `<easylink/types.hpp>`:

```cpp
namespace easylink {

struct Position {
    double lat = 0.0;    // Latitude (degrees)
    double lon = 0.0;    // Longitude (degrees)
    float  alt = 0.0f;   // Relative altitude (meters)
};

struct Attitude {
    float roll  = 0.0f;  // Roll angle (degrees)
    float pitch = 0.0f;  // Pitch angle (degrees)
    float yaw   = 0.0f;  // Yaw angle (degrees)
};

struct Battery {
    float voltage       = 0.0f;  // Battery voltage (V)
    int   remaining_pct = 0;     // Remaining capacity (%)
};

struct GPSInfo {
    int fix_type           = 0;  // GPS fix type (0=no, 3=3D)
    int satellites_visible = 0;  // Number of visible satellites
};

enum class AutopilotType {
    ArduPilot,   // MAV_AUTOPILOT_ARDUPILOTMEGA
    PX4,         // MAV_AUTOPILOT_PX4
    Unknown
};

} // namespace easylink
```

---

## `easylink::Drone`

Primary class. Defined in `<easylink/drone.hpp>`.

### Construction & Connection

```cpp
#include <easylink/drone.hpp>

// Explicit target
easylink::Drone drone("udp:127.0.0.1:14550");

// Default (auto-connects to 127.0.0.1:14550)
easylink::Drone drone;

// SITL factory
auto drone = easylink::Drone::sitl();   // Connects immediately
```

| Method | Signature | Description |
| :--- | :--- | :--- |
| Constructor | `Drone(const std::string& target = "")` | Creates instance. Does not connect. |
| `sitl` | `static Drone sitl(const std::string& target = "udp:127.0.0.1:14550")` | Factory that auto-connects. |
| `connect` | `bool connect(float timeout_sec = 15.0f)` | Opens UDP socket, waits for HEARTBEAT, detects autopilot type, starts rx thread. |
| `disconnect` | `void disconnect()` | Stops rx thread, closes socket. |

> **Connection Behavior**: During `connect()`, the library listens for the first HEARTBEAT to auto-detect `target_system`, `target_component`, and whether the firmware is ArduPilot or PX4.

---

### Actions

All action methods send `COMMAND_LONG` MAVLink messages.

| Method | Signature | MAVLink Command |
| :--- | :--- | :--- |
| `arm` | `bool arm(float timeout = 15.0f)` | `MAV_CMD_COMPONENT_ARM_DISARM` p1=1 |
| `disarm` | `bool disarm(float timeout = 15.0f)` | `MAV_CMD_COMPONENT_ARM_DISARM` p1=0 |
| `takeoff` | `bool takeoff(float altitude, float timeout = 30.0f)` | `MAV_CMD_NAV_TAKEOFF` p7=alt |
| `land` | `bool land(bool blocking = true, float timeout = 60.0f)` | `MAV_CMD_NAV_LAND` |
| `home` | `bool home(bool blocking = true, float timeout = 90.0f)` | Mode switch → RTL (mode 6) |
| `rtl` | `bool rtl(...)` | *(alias for `home`)* |
| `back` | `bool back(...)` | *(alias for `home`)* |
| `kill` | `bool kill()` | `MAV_CMD_COMPONENT_ARM_DISARM` p2=21196 |

```cpp
drone.arm();                      // Blocks until armed
drone.takeoff(10.0f);             // Sends takeoff command
drone.land(true, 60.0f);          // Blocks until landed & disarmed
drone.home(true);                 // RTL, blocks until landed
drone.kill();                     // Emergency motor kill
```

---

### Navigation

Fire-and-forget commands. All non-blocking.

| Method | Signature | MAVLink Command |
| :--- | :--- | :--- |
| `goto_pos` | `void goto_pos(double lat, double lon, float alt)` | `MAV_CMD_DO_REPOSITION` |
| `goto_relative` | `void goto_relative(float n, float e, float d)` | `SET_POSITION_TARGET_LOCAL_NED` |
| `set_speed` | `void set_speed(float speed_ms)` | `MAV_CMD_DO_CHANGE_SPEED` |
| `set_heading` | `void set_heading(float deg, bool relative = false)` | `MAV_CMD_CONDITION_YAW` |
| `hover` | `void hover(float duration_sec)` | `MAV_CMD_NAV_LOITER_TIME` + sleep |
| `orbit` | `void orbit(float radius, float speed, double lat, double lon)` | `MAV_CMD_DO_ORBIT` |

```cpp
drone.goto_pos(22.5039, 88.2937, 15.0f);
drone.goto_relative(10.0f, 5.0f, 0.0f);  // 10m north, 5m east
drone.set_speed(3.0f);
drone.set_heading(180.0f);                 // Face south
drone.hover(5.0f);                         // Hold 5 seconds
drone.orbit(20.0f, 2.0f);                 // 20m radius, 2 m/s
```

---

### Mission Engine

Fluent builder pattern. Accessed via `drone.mission()`.

```cpp
drone.mission()
     .clear()
     .add_takeoff(15.0f)
     .add_waypoint(22.5039, 88.2937, 15.0f)
     .add_waypoint(22.5040, 88.2938, 20.0f)
     .add_land();

drone.mission().upload();
drone.arm();
drone.mission().start(true);   // blocking = true
```

| Method | Signature | Description |
| :--- | :--- | :--- |
| `clear` | `MissionManager& clear()` | Clears local waypoint list |
| `add_takeoff` | `MissionManager& add_takeoff(float alt, double lat=0, double lon=0)` | Adds `MAV_CMD_NAV_TAKEOFF` item |
| `add_waypoint` | `MissionManager& add_waypoint(double lat, double lon, float alt)` | Adds `MAV_CMD_NAV_WAYPOINT` item |
| `add_land` | `MissionManager& add_land(double lat=0, double lon=0)` | Adds `MAV_CMD_NAV_LAND` item |
| `upload` | `bool upload(float timeout = 10.0f)` | Sends mission items via MAVLink mission microservice |
| `start` | `bool start(bool blocking = true, float timeout = 120.0f)` | Sets AUTO mode + `MAV_CMD_MISSION_START` |
| `pause` | `bool pause()` | Switches to GUIDED (loiter in place) |
| `resume` | `bool resume()` | Re-enters AUTO to continue |
| `progress` | `std::string progress() const` | Returns `"current/total"` string |

---

### Telemetry

All getters are thread-safe (mutex-locked reads from `rx_loop`-updated state).

| Method | Return Type | MAVLink Source |
| :--- | :--- | :--- |
| `position()` | `Position` | `GLOBAL_POSITION_INT` |
| `attitude()` | `Attitude` | `ATTITUDE` |
| `battery()` | `Battery` | `SYS_STATUS` |
| `gps_info()` | `GPSInfo` | `GPS_RAW_INT` |
| `groundspeed()` | `float` | `VFR_HUD` |
| `heading()` | `float` | `VFR_HUD` / `GLOBAL_POSITION_INT` |
| `is_armed()` | `bool` | `HEARTBEAT` (atomic, lock-free) |
| `current_mission_seq()` | `int` | `MISSION_CURRENT` / `MISSION_ITEM_REACHED` |

---

<div align="center">
<sub>EASYLink C++ Core · DronePulse Labs · MIT License</sub>
</div>
