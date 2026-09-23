cmake_minimum_required(VERSION 3.22.1)
project(waitsys)

set(CMAKE_CXX_STANDARD 23)

add_compile_options(-fno-exceptions -fno-rtti)

if ("${CMAKE_BUILD_TYPE}" STREQUAL "RelWithDebInfo")
    add_compile_options(-O3 -flto -ffunction-sections -fdata-sections)
endif()

add_subdirectory(external)
link_libraries(cxx)
add_subdirectory(stubs)

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
    target_compile_options(waitsys PRIVATE -fvisibility=hidden)
endif()
