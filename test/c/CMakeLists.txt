set(gtest_header ${THIRDPARTY_PATH}/googletest/googletest/include/)
string(APPEND CMAKE_CXX_FLAGS " -fprofile-arcs -ftest-coverage -lgcov")
string(APPEND CMAKE_C_FLAGS " -fprofile-arcs -ftest-coverage -lgcov")

add_executable(mstx_test_${LANG} test_core_api.c)
add_library(mstx_static_lib_${LANG} STATIC test_core.cpp)


if ("${LANG}" STREQUAL "C")
    add_definitions(-DLANG_C_TEST)
    set(CMAKE_C_COMPILER "gcc")
else()
    set(CMAKE_C_COMPILER "g++")
endif()



target_include_directories(mstx_test_${LANG} PUBLIC ${gtest_header} ${MSTX_HEADER})
target_include_directories(mstx_static_lib_${LANG} PUBLIC ${gtest_header} ${MSTX_HEADER})
# gtest 用例通过静态注册生效，必须用 --whole-archive 强制链入静态库，
# 否则 test_core.cpp 中的用例会被链接器丢弃，导致实际执行 0 个用例。
target_link_libraries(mstx_test_${LANG} gtest_main
                      "-Wl,--whole-archive" mstx_static_lib_${LANG} "-Wl,--no-whole-archive"
                      dl pthread)

add_library(injection_test SHARED injection_stub.cpp)

target_include_directories(injection_test PUBLIC ${gtest_header} ${MSTX_HEADER})

add_executable(mstx_test_lib_${LANG} test_c_cpp_lib.cpp)

if ("${LANG}" STREQUAL "C")
    add_definitions(-DLANG_C_TEST)
    set(CMAKE_C_COMPILER "gcc")
else()
    set(CMAKE_C_COMPILER "g++")
endif()

target_include_directories(mstx_test_lib_${LANG} PUBLIC ${gtest_header})
target_link_libraries(mstx_test_lib_${LANG} gtest_main dl pthread)
