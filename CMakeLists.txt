cmake_minimum_required(VERSION 3.22.1)
project(waitsys)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_ANDROID_STL_TYPE c++_static)

add_compile_options(-fno-exceptions -fno-rtti)

add_executable(waitsys waitsys.cpp logging.cpp)
target_link_libraries(waitsys binder utils log)

if ("${CMAKE_BUILD_TYPE}" STREQUAL "RelWithDebInfo")
    target_link_options( 
        waitsys PRIVATE
        -Wl,--exclude-libs,ALL
        -Wl,-z,start-stop-visibility=hidden
        -Wl,--gc-sections
        -Wl,--icf=all
    )
    target_compile_options(waitsys PRIVATE -O3 -flto -fvisibility=hidden)
endif()

add_subdirectory(stubs)
