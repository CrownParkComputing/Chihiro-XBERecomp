cmake_minimum_required(VERSION 3.22)
project(xbe_android_port LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_C_STANDARD 11)
get_filename_component(XBE_REPO_DIR "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(XBE_SDK_DIR "${XBE_REPO_DIR}/sdk")
set(XBE_TITLE "OutRun2")
set(XBE_GAME_XBE "outrun2.xbe")
set(XBE_INPUT_DEFINE "")
foreach(required XBE_DEPS_SOURCE XBE_DEPS_BUILD)
    if(NOT DEFINED ${required})
        message(FATAL_ERROR "Missing ${required}; use stage_port.py")
    endif()
endforeach()
set(common "${CMAKE_CURRENT_LIST_DIR}/app/src/main/cpp")
set(gen "${XBE_REPO_DIR}/generated/game")
add_library(SDL3 SHARED IMPORTED)
set_target_properties(SDL3 PROPERTIES IMPORTED_LOCATION "${XBE_DEPS_BUILD}/sdl3-build/libSDL3.so"
    INTERFACE_INCLUDE_DIRECTORIES "${XBE_DEPS_SOURCE}/sdl3-src/include")
file(GLOB runtime CONFIGURE_DEPENDS "${XBE_SDK_DIR}/runtime/*/*.cpp")
list(FILTER runtime EXCLUDE REGEX "/app/(main|splash|handover|system_info)\\.cpp$|/gpu/(d3d12|vk_shaders)\\.cpp$|/audio/xaudio2\\.cpp$")
file(GLOB host CONFIGURE_DEPENDS "${XBE_REPO_DIR}/src/*/*.cpp")
list(FILTER host EXCLUDE REGEX "/src/game/")
file(GLOB game CONFIGURE_DEPENDS "${XBE_REPO_DIR}/src/game/*.cpp")
# The desktop movie replacement uses FFmpeg. Keep the original guest movie
# routines in these builds, as in the existing Burnout Android port.
list(FILTER game EXCLUDE REGEX "native_(movie|fmv)\\.cpp$")
file(GLOB generated CONFIGURE_DEPENDS "${gen}/x86_func_mapping.cpp" "${gen}/x86_recomp.*.cpp")
if(NOT XBE_GAME_XBE)
    set(XBE_GAME_XBE "default.xbe")
endif()
file(SHA1 "${XBE_REPO_DIR}/assets/${XBE_GAME_XBE}" sha)
file(CONFIGURE OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/image_hash.cpp" CONTENT "extern const char kImageSha1[] = \"${sha}\";\n")
set(imgui "${XBE_DEPS_SOURCE}/imgui-src")
add_library(main SHARED ${runtime} ${host} ${game} ${generated}
    "${imgui}/imgui.cpp" "${imgui}/imgui_draw.cpp" "${imgui}/imgui_tables.cpp" "${imgui}/imgui_widgets.cpp"
    "${imgui}/backends/imgui_impl_sdl3.cpp" "${imgui}/backends/imgui_impl_vulkan.cpp"
    "${common}/vk_shaders_glslang.cpp" "${common}/document_tree.cpp" "${CMAKE_CURRENT_BINARY_DIR}/image_hash.cpp")
target_include_directories(main BEFORE PRIVATE "${XBE_PORT_INCLUDE}")
target_include_directories(main PRIVATE "${XBE_SDK_DIR}/runtime" "${XBE_SDK_DIR}/runtime/platform/compat"
    "${XBE_REPO_DIR}/src" "${gen}")
target_include_directories(main SYSTEM PRIVATE "${imgui}" "${XBE_DEPS_SOURCE}/vma-src/include"
    "${XBE_DEPS_SOURCE}/tomlplusplus-src/include" "${XBE_DEPS_SOURCE}/glslang-src")
target_compile_definitions(main PRIVATE _stricmp=strcasecmp _strnicmp=strncasecmp ENABLE_HLSL=1
    XBE_ANDROID_LOG_TAG="${XBE_TITLE}")
if(XBE_INPUT_DEFINE)
    target_compile_definitions(main PRIVATE "${XBE_INPUT_DEFINE}=1")
endif()
target_compile_options(main PRIVATE -fno-strict-aliasing -Wno-parentheses-equality)
set_source_files_properties(${generated} PROPERTIES COMPILE_OPTIONS "-w")
target_link_libraries(main PRIVATE SDL3
    "${XBE_DEPS_BUILD}/glslang-build/glslang/libglslang.a"
    "${XBE_DEPS_BUILD}/glslang-build/SPIRV/libSPIRV.a"
    "${XBE_DEPS_BUILD}/glslang-build/glslang/libglslang-default-resource-limits.a"
    "${XBE_DEPS_BUILD}/spirv_tools-build/source/opt/libSPIRV-Tools-opt.a"
    "${XBE_DEPS_BUILD}/spirv_tools-build/source/libSPIRV-Tools.a"
    vulkan log android)
target_link_options(main PRIVATE -Wl,-z,max-page-size=16384)
