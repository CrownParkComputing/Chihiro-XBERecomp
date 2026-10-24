#include "app/app.h"
#include "image_symbols.h"
#include "game/gun_input.h"
const app::GameInfo app::kGame = {
    .title = L"Ghost Squad",
    .short_title = L"GhostSquad",
    .name = L"GhostSquad",
    .log = "ghostsquad",
    .settings = "settings.toml",
    .splash = L"splash",
    .missing = L"Import Ghost Squad.7z before starting.",
    .images = {{IMAGE_XBE, "GhostSquad"}},
    .window = ghostsquad::MouseWindow,
    .pad = ghostsquad::MousePad,
    .keyboard_pad = true,
};
