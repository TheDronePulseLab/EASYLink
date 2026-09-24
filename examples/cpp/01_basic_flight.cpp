#include <easylink/drone.hpp>
#include <iostream>

int main() {
    std::cout << "Connecting to drone via EASYLink-CPP..." << std::endl;
    easylink::Drone drone("udp:127.0.0.1:14550");
    
    if (!drone.connect()) {
        std::cerr << "Failed to establish connection!" << std::endl;
        return 1;
    }

    std::cout << "Arming vehicle..." << std::endl;
    drone.arm();

    std::cout << "Taking off to 10m..." << std::endl;
    drone.takeoff(10.0f);

    auto pos = drone.position();
    std::cout << "Position: Lat=" << pos.lat << ", Lon=" << pos.lon << ", Alt=" << pos.alt << "m" << std::endl;

    std::cout << "Hovering for 5 seconds..." << std::endl;
    drone.hover(5.0f);

    std::cout << "Returning home..." << std::endl;
    drone.home(true);

    drone.disconnect();
    std::cout << "Flight complete!" << std::endl;
    return 0;
}
