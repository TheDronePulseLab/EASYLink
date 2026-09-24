from easylink import Drone

def main():
    # 1. Instantiate & auto-connect (supports SITL or hardware serial)
    print("Initiating EASYLink connection...")
    drone = Drone()
    drone.connect()
    
    # 2. Pre-flight health check
    if drone.preflight_check():
        print("Pre-flight safety checks PASSED!")
    else:
        print("Pre-flight checks FAILED!")
        return

    # 3. Flight sequence
    print("Arming drone...")
    drone.arm()

    print("Taking off to 10.0m...")
    drone.takeoff(10.0)

    # 4. Read telemetry
    pos = drone.position
    att = drone.attitude
    bat = drone.battery
    print(f"Telemetry -> Pos: Lat={pos.lat}, Lon={pos.lon}, Alt={pos.alt}m")
    print(f"Telemetry -> Attitude: Roll={att.roll:.1f}°, Pitch={att.pitch:.1f}°, Yaw={att.yaw:.1f}°")
    print(f"Telemetry -> Battery: Voltage={bat.voltage}V ({bat.remaining_pct}%)")

    # 5. Hover and Return to Launch (blocking)
    print("Hovering for 5 seconds...")
    drone.hover(5.0)

    print("Returning home and landing...")
    drone.home(blocking=True)

    drone.disconnect()
    print("Flight sequence complete!")

if __name__ == "__main__":
    main()
