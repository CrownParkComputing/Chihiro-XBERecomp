// Exercise actual SDL devices through the SDK, including hotplug and routing.
#include <SDL3/SDL.h>
#include <cassert>
#include <cstring>
#include "app/app.h"
#include "core/input.h"
#include "game/mouse.h"

namespace {
app::Settings settings;
bool menu_open = false;
void Devices() {
    SDL_PumpEvents();
    SDL_Event e;
    while (SDL_PollEvent(&e))
        if (e.type == SDL_EVENT_GAMEPAD_ADDED || e.type == SDL_EVENT_GAMEPAD_REMOVED)
            input::OnDeviceEvent(e.type, e.gdevice.which);
    SDL_UpdateGamepads();
}
struct Controller {
    SDL_JoystickID id;
    SDL_Joystick* stick;
    explicit Controller(const char* name) {
        SDL_VirtualJoystickDesc desc{};
        SDL_INIT_INTERFACE(&desc);
        desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
        desc.naxes = SDL_GAMEPAD_AXIS_COUNT;
        desc.nbuttons = SDL_GAMEPAD_BUTTON_COUNT;
        desc.axis_mask = (1u << SDL_GAMEPAD_AXIS_COUNT) - 1;
        desc.button_mask = (1u << SDL_GAMEPAD_BUTTON_COUNT) - 1;
        desc.name = name;
        id = SDL_AttachVirtualJoystick(&desc);
        assert(id && SDL_IsGamepad(id));
        stick = SDL_OpenJoystick(id);
        assert(stick);
        Devices();
    }
    void Button(SDL_GamepadButton button, bool down) {
        assert(SDL_SetJoystickVirtualButton(stick, button, down));
        Devices();
    }
    void Axis(SDL_GamepadAxis axis, int16_t value) {
        assert(SDL_SetJoystickVirtualAxis(stick, axis, value));
        Devices();
    }
    void Remove() {
        SDL_CloseJoystick(stick);
        assert(SDL_DetachVirtualJoystick(id));
        Devices();
    }
};
}
namespace app {
const GameInfo kGame{.pad = vcop3::MousePad, .keyboard_pad = true};
Settings& Get() { return settings; }
bool GraphicsMenuOpen() { return menu_open; }
bool Unfocused() { return false; }
bool Widescreen() { return false; }
}

int main(int argc, char** argv) {
    assert(argc == 2);
    const bool mouse = !std::strcmp(argv[1], "mouse-controller");
    assert(SDL_setenv_unsafe("VCOP3_CONTROLS", argv[1], 1) == 0);
    SDL_SetHint(SDL_HINT_VIDEO_DRIVER, "dummy");
    assert(SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_GAMEPAD));
    auto* window = SDL_CreateWindow("VC3 players test", 800, 600, SDL_WINDOW_HIDDEN);
    assert(window);
    vcop3::HostInit();
    assert(vcop3::MouseEnabled() == mouse);
    input::Init();
    vcop3::MouseWindow(window);
    SDL_Event e{};
    e.type = SDL_EVENT_WINDOW_FOCUS_GAINED; e.window.windowID = SDL_GetWindowID(window);
    assert(SDL_PushEvent(&e));
    Devices();
    Controller first("VC3 first test controller");
    const int first_port = mouse ? 1 : 0;
    assert(input::Poll(first_port).connected);
    first.Button(SDL_GAMEPAD_BUTTON_START, true);
    first.Button(SDL_GAMEPAD_BUTTON_SOUTH, true);
    first.Axis(SDL_GAMEPAD_AXIS_LEFTX, 16384);
    auto report = input::Poll(first_port);
    assert((report.buttons & 16) && report.analog[0] == 255 && report.lx == 16384);
    assert(input::Poll(mouse ? 0 : 1).analog[0] == 0);
    if (mouse) {
        e = {}; e.type = SDL_EVENT_MOUSE_BUTTON_DOWN;
        e.button.windowID = SDL_GetWindowID(window);
        e.button.button = SDL_BUTTON_LEFT; e.button.down = true;
        e.button.x = 400; e.button.y = 300;
        assert(SDL_PushEvent(&e));
        Devices();
        vcop3::BeginGuestMousePoll();
        assert(input::Poll(0).analog[0] == 255);
        vcop3::EndGuestMousePoll();
        assert(input::Poll(1).lx == 16384);
    } else {
        Controller second("VC3 second test controller");
        second.Button(SDL_GAMEPAD_BUTTON_EAST, true);
        second.Axis(SDL_GAMEPAD_AXIS_LEFTY, -8192);
        assert(input::Poll(1).analog[1] == 255 && input::Poll(1).ly == 8191);
        assert(input::Poll(0).analog[1] == 0 && input::Poll(1).analog[0] == 0);
        first.Remove();
        assert(input::Poll(0).analog[0] == 0 && input::Poll(1).analog[1] == 255);
        Controller replacement("VC3 replacement controller");
        replacement.Button(SDL_GAMEPAD_BUTTON_WEST, true);
        assert(input::Poll(0).analog[2] == 255 && input::Poll(1).analog[2] == 0);
        replacement.Remove();
        second.Remove();
    }
    menu_open = true;
    assert(input::Poll(0).analog[0] == 0 && input::Poll(1).analog[0] == 0);
    menu_open = false;
    if (mouse) {
        first.Remove();
        assert(!input::Poll(1).connected);
        Controller replacement("VC3 replacement controller");
        replacement.Button(SDL_GAMEPAD_BUTTON_EAST, true);
        assert(input::Poll(1).analog[1] == 255 && input::Poll(0).analog[1] == 0);
        replacement.Remove();
    }
    SDL_Quit();
}
