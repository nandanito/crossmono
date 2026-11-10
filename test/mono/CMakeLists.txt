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
add_test(NAME mono_release_license COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_release_license.py)
add_test(NAME mono_stack_budget COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_stack_budget.py)

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

add_executable(MonoKeyChordTest KeyChordTest.cpp)

target_include_directories(MonoKeyChordTest PRIVATE ${REPO_ROOT}/src)

target_link_libraries(MonoKeyChordTest PRIVATE
  crosspoint_test_common
  GTest::gtest_main
)

gtest_discover_tests(MonoKeyChordTest)

add_executable(MonoCuesTest CuesTest.cpp)

target_include_directories(MonoCuesTest PRIVATE ${REPO_ROOT}/src)

target_link_libraries(MonoCuesTest PRIVATE
  crosspoint_test_common
  GTest::gtest_main
)

gtest_discover_tests(MonoCuesTest)
