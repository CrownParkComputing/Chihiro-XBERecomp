cmake_minimum_required(VERSION 3.25)
project(GhostSquadNative LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/Dependencies.cmake")
include("${CMAKE_CURRENT_SOURCE_DIR}/sdk/cmake/XbeRecomp.cmake")
file(GLOB XBE_HOST_SOURCES CONFIGURE_DEPENDS src/common/*.cpp)
add_xbe_image(GhostSquad vsg.xbe game.toml 32 game)
set_target_properties(GhostSquad PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

set_source_files_properties("${CMAKE_CURRENT_SOURCE_DIR}/src/game/cabinet_input.cpp" PROPERTIES COMPILE_DEFINITIONS CHIHIRO_SDL_INPUT=1)

set_source_files_properties("${CMAKE_CURRENT_SOURCE_DIR}/src/game/mouse_sdl.cpp" PROPERTIES COMPILE_DEFINITIONS CHIHIRO_SDL_INPUT=1)
