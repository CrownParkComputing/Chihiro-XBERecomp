#include "app/app.h"
#include "image_symbols.h"
const app::GameInfo app::kGame = {
    .title = L"Wangan Midnight Maximum Tune 2",
    .short_title = L"MaximumTune2",
    .name = L"MaximumTune2",
    .log = "maximumtune2",
    .settings = "settings.toml",
    .splash = L"splash",
    .missing = L"Import Maximum Tune 2 (Export).7z before starting.",
    .images = {{IMAGE_XBE, "MaximumTune2"}},
    .keyboard_pad = true,
};
