# CrossMono host tests. test/CMakeLists.txt includes this file with one line;
# add our tests here, not there.
find_package(Python3 REQUIRED COMPONENTS Interpreter)

add_test(NAME mono_partitions COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_partitions.py)
add_test(NAME mono_size_gate COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_size_gate.py)
