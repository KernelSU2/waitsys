project(external)

macro(SET_OPTION option value)
    set(${option} ${value} CACHE INTERNAL "" FORCE)
endmacro()

# libcxx

set(CXX_DIR "libcxx/cxx/jni")

file(GLOB LIBCXX_SOURCES "${CXX_DIR}/libcxx/src/*.cpp" "${CXX_DIR}/libcxx/src/filesystem/*.cpp")

list(FILTER LIBCXX_SOURCES EXCLUDE REGEX ".*/(tzdb|time_zone|tzdb_list|tz|iostream|ostream|fstream|regex|ios.instantiations|strstream)\.cpp$")

message(STATUS "LIBCXX_SOURCES: ${LIBCXX_SOURCES}")

set(LIBCXX_EXPORT_FLAGS
        -DLIBCXX_BUILDING_LIBCXXABI
        -D_LIBCPP_HAS_NO_EXCEPTIONS
        -D_LIBCPP_NO_RTTI
        -D_LIBCPP_BUILDING_LIBRARY
        -D_LIBCPP_DISABLE_VISIBILITY_ANNOTATIONS
        -D_LIBCXXABI_NO_EXCEPTIONS
        -D_LIBCPP_HAS_NO_INCOMPLETE_PSTL
)
set(LIBCXX_FLAGS -fvisibility-global-new-delete=force-hidden)
set(LIBCXX_EXPORT_INCLUDES ${CXX_DIR}/libcxx/include)
set(LIBCXX_INCLUDES ${CXX_DIR}/libcxx/src)

set(LIBCXXABI_SOURCES
        abort_message.cpp
        cxa_aux_runtime.cpp
        cxa_default_handlers.cpp
        cxa_exception_storage.cpp
        cxa_guard.cpp
        cxa_handlers.cpp
        cxa_noexception.cpp
        cxa_thread_atexit.cpp
        cxa_vector.cpp
        cxa_virtual.cpp
        stdlib_exception.cpp
        stdlib_new_delete.cpp
        stdlib_stdexcept.cpp
        stdlib_typeinfo.cpp
)
list(TRANSFORM LIBCXXABI_SOURCES PREPEND ${CXX_DIR}/libcxxabi/src/)
set(LIBCXXABI_FLAGS
        -Wno-macro-redefined
        -Wno-unknown-attributes
        -DHAS_THREAD_LOCAL)
set(LIBCXXABI_INCLUDES ${CXX_DIR}/libcxxabi/include)

add_library(cxx STATIC ${LIBCXX_SOURCES} ${LIBCXXABI_SOURCES})
target_compile_options(cxx PUBLIC ${LIBCXX_EXPORT_FLAGS})
target_compile_options(cxx PRIVATE ${LIBCXX_FLAGS} ${LIBCXXABI_FLAGS} -ffunction-sections -fdata-sections)
target_include_directories(cxx PUBLIC ${LIBCXX_EXPORT_INCLUDES})
target_include_directories(cxx PRIVATE ${LIBCXX_INCLUDES} ${LIBCXXABI_INCLUDES})

# libcxx end
link_libraries(cxx)
