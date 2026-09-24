from easylink import Drone

def main():
    drone = Drone.sitl()
    print("Connected to SITL!")

    # Fluent mission builder chain
    print("Building mission waypoints...")
    drone.mission.clear() \
         .add_takeoff(alt=15.0) \
         .add_waypoint(22.5039, 88.2937, 15.0) \
         .add_waypoint(22.5040, 88.2938, 20.0) \
         .add_land()

    print("Uploading mission to vehicle...")
    drone.mission.upload()
    print("Upload complete!")

    print("Arming drone...")
    drone.arm()

    print("Starting mission execution...")
    drone.mission.start(blocking=True)

    print("Mission finished! Returning home...")
    drone.home(blocking=True)

    drone.disconnect()
    print("Done!")

if __name__ == "__main__":
    main()
