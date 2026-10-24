#include "game/gun_input.h"
#ifdef CHIHIRO_SDL_INPUT
#include <SDL3/SDL.h>
#include <algorithm>
#include <cmath>
#include <mutex>
#include "app/app.h"
#include "core/input.h"
#include "core/log.h"
namespace ghostsquad {
namespace {
std::mutex lock;
SDL_WindowID window_id = 0;
float x = 0, y = 0, width = 1, height = 1;
bool active = false, mouse_mode = false;
uint32_t held = 0;
uint64_t fire_until = 0, reload_until = 0;
bool SDLCALL Watch(void*, SDL_Event* event) {
    std::lock_guard guard(lock);
    if (event->type == SDL_EVENT_MOUSE_MOTION && event->motion.windowID == window_id) {
        x = event->motion.x; y = event->motion.y; mouse_mode = true;
    } else if ((event->type == SDL_EVENT_MOUSE_BUTTON_DOWN || event->type == SDL_EVENT_MOUSE_BUTTON_UP)
        && event->button.windowID == window_id) {
        x = event->button.x; y = event->button.y; mouse_mode = true;
        const uint32_t bit = SDL_BUTTON_MASK(event->button.button);
        if (event->button.down && active) {
            held |= bit;
            // Keep a very short tap visible for at least two 60 Hz polls.
            if (event->button.button == SDL_BUTTON_LEFT) fire_until = SDL_GetTicks() + 50;
            if (event->button.button == SDL_BUTTON_RIGHT) reload_until = SDL_GetTicks() + 50;
        } else held &= ~bit;
    } else if (event->type == SDL_EVENT_WINDOW_RESIZED && event->window.windowID == window_id) {
        width = float(event->window.data1); height = float(event->window.data2);
    } else if (event->type == SDL_EVENT_WINDOW_FOCUS_GAINED && event->window.windowID == window_id) {
        active = true;
    } else if ((event->type == SDL_EVENT_WINDOW_FOCUS_LOST || event->type == SDL_EVENT_WINDOW_MOUSE_LEAVE)
        && event->window.windowID == window_id) {
        active = false; held = 0; fire_until = reload_until = 0;
    } else if (event->type == SDL_EVENT_WINDOW_MOUSE_ENTER && event->window.windowID == window_id) active = true;
    return true;
}
}
void MouseWindow(void* window) {
    auto* handle = static_cast<SDL_Window*>(window);
    int w = 1, h = 1; SDL_GetWindowSize(handle, &w, &h);
    {
        std::lock_guard guard(lock);
        window_id = SDL_GetWindowID(handle);
        width = float(w); height = float(h);
        SDL_GetMouseState(&x, &y);
        active = (SDL_GetWindowFlags(handle) & SDL_WINDOW_INPUT_FOCUS) != 0;
    }
    SDL_AddEventWatch(Watch, nullptr);
    if (auto* cursor = SDL_CreateSystemCursor(SDL_SYSTEM_CURSOR_CROSSHAIR)) SDL_SetCursor(cursor);
    SDL_ShowCursor();
    LOGI("GhostSquad: mouse/touch aiming enabled");
}
void MousePad(int port, input::Pad& pad) {
    if (port != 0) return;
    std::lock_guard guard(lock);
    if (!active || app::Unfocused() || app::GraphicsMenuOpen()) {
        held = 0; fire_until = reload_until = 0; return;
    }
    if (std::abs(int(pad.lx)) > 4096 || std::abs(int(pad.ly)) > 4096) mouse_mode = false;
    if (!mouse_mode || width <= 0 || height <= 0) return;
    const float aspect = app::Widescreen() ? 16.f / 9.f : 4.f / 3.f;
    const float w = std::min(width, height * aspect), h = w / aspect;
    const float u = (x - (width - w) * .5f) / w;
    const float v = (y - (height - h) * .5f) / h;
    const bool outside = u < 0 || u >= 1 || v < 0 || v >= 1;
    pad.connected = true;
    pad.lx = int16_t(std::lround(std::clamp(u, 0.f, 1.f) * 65535.f) - 32768);
    pad.ly = int16_t(32767 - std::lround(std::clamp(v, 0.f, 1.f) * 65535.f));
    const auto now = SDL_GetTicks();
    const bool fire = (held & SDL_BUTTON_LMASK) || now < fire_until;
    const bool reload = (held & SDL_BUTTON_RMASK) || now < reload_until || (fire && outside);
    if (fire || reload) pad.analog[0] = 255;
    if (reload) pad.analog[1] = 255;
    if (held & SDL_BUTTON_MMASK) pad.analog[2] = 255;
}
}
#else
namespace ghostsquad {
void MouseWindow(void*) {}
void MousePad(int, input::Pad&) {}
}
#endif
