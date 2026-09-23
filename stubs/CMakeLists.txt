project(binderstubs)

# libutils stub
add_library(utils SHARED stub_utils.cpp)
target_include_directories(utils PUBLIC include)
# do not export libc++_static's symbols
target_link_options(utils PRIVATE -Wl,--exclude-libs,ALL)
target_compile_options(utils PRIVATE -fvisibility=default)

# libbinder stub
add_library(binder SHARED stub_binder.cpp)
target_include_directories(binder PUBLIC include)
target_link_libraries(binder PRIVATE utils)
target_link_options(binder PRIVATE -Wl,--exclude-libs,ALL)
target_compile_options(binder PRIVATE -fvisibility=default)
