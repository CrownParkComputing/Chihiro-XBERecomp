#include "app/app.h"
#include "image_symbols.h"
const app::GameInfo app::kGame = {
    .title = L"Wangan Midnight Maximum Tune",
    .short_title = L"MaximumTune1",
    .name = L"MaximumTune1",
    .log = "maximumtune1",
    .settings = "settings.toml",
    .splash = L"splash",
    .missing = L"Import Maximum Tune 1 (Export).7z before starting.",
    .images = {{IMAGE_XBE, "MaximumTune1"}},
    .keyboard_pad = true,
};
