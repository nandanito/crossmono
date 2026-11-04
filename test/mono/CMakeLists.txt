# CrossMono host tests. test/CMakeLists.txt includes this file with one line;
# add our tests here, not there.
find_package(Python3 REQUIRED COMPONENTS Interpreter)

add_test(NAME mono_partitions COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_partitions.py)
add_test(NAME mono_size_gate COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_size_gate.py)
add_test(NAME mono_version_flags COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_version_flags.py)
add_test(NAME mono_flash_slots COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_flash_slots.py)
add_test(NAME mono_make_logo COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_make_logo.py)
add_test(NAME mono_package_release COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_package_release.py)
add_test(NAME mono_changelog COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_changelog.py)

add_executable(MonoOtaReleaseTest
  OtaReleaseTest.cpp
  ${REPO_ROOT}/lib/JsonParser/ReleaseJsonParser.cpp
  ${REPO_ROOT}/freeink-sdk/libs/network/JsonSax/src/StreamingJsonParser.cpp
)

target_include_directories(MonoOtaReleaseTest PRIVATE
  ${REPO_ROOT}/src
  ${REPO_ROOT}/lib/JsonParser
  ${REPO_ROOT}/freeink-sdk/libs/network/JsonSax/include
)

target_link_libraries(MonoOtaReleaseTest PRIVATE
  crosspoint_test_common
  GTest::gtest_main
)

gtest_discover_tests(MonoOtaReleaseTest)

add_executable(MonoModelTest ModelTest.cpp)

target_include_directories(MonoModelTest PRIVATE ${REPO_ROOT}/src)

target_link_libraries(MonoModelTest PRIVATE
  crosspoint_test_common
  GTest::gtest_main
)

gtest_discover_tests(MonoModelTest)
