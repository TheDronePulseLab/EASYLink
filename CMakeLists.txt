cmake_minimum_required(VERSION 3.16)
project(easylink-cpp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 1. Include public headers
target_include_directories(easylink_cpp INTERFACE 
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# 2. Auto-fetch MAVLink C headers dependency
include(FetchContent)
FetchContent_Declare(
    mavlink
    GIT_REPOSITORY https://github.com/mavlink/c_library_v2.git
    GIT_TAG master
)
FetchContent_MakeAvailable(mavlink)

# 3. Create interface library for user project inclusion
add_library(easylink_cpp INTERFACE)
target_include_directories(easylink_cpp INTERFACE 
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${mavlink_SOURCE_DIR}
)

# 4. Link required system sockets
if(WIN32)
    target_link_libraries(easylink_cpp INTERFACE ws2_32)
else()
    find_package(Threads REQUIRED)
    target_link_libraries(easylink_cpp INTERFACE Threads::Threads)
endif()

# 5. Helper option to build public examples
option(BUILD_EXAMPLES "Build C++ example applications" ON)
if(BUILD_EXAMPLES)
    add_subdirectory(examples/cpp)
endif()
